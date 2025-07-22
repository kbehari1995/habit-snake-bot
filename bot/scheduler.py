# DB-backed scheduler (scheduler_db.py)
import os
import asyncio
from datetime import datetime, timedelta
import pytz
from telegram import Bot
from utils.cached_db import DbCache
from utils.logger import get_logger
from utils.exceptions import SchedulerError

# Initialize logger
logger = get_logger("scheduler_db")

from bot.utils.config import (
    SCHEDULER_START_HHMM, SCHEDULER_INTERVAL_HHMMSSS, SCHEDULER_RECHECK_MIN,
    SCHEDULER_AUTOMARK_HHMM, TIME_FOR_UPDATE, TELEGRAM_CHANNEL_ID
)

last_checkin_sent = {}
last_auto_x_sent = {}
summary_sent_today = None
reminder_counts = {}
last_reminder_time = {}

def parse_hhmm(hhmm: str):
    return int(hhmm[:2]), int(hhmm[2:])

def get_yesterday_date(now_local):
    return now_local.date() - timedelta(days=1)

def format_reminder_message(username, yesterday_date, reminder_count, auto_mark_minutes_remaining=None):
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_name = day_names[yesterday_date.weekday()]
    base_message = f"⏰ Time to checkin for yesterday i.e. {day_name},{yesterday_date.strftime('%Y-%m-%d')}.\n\nUse /checkin to get started!"
    if reminder_count == 3:
        warning = f"\nAll habits will be marked X in {auto_mark_minutes_remaining} minutes. Checkin now @{username}!"
        return f"**LAST REMINDER**\n{base_message}{warning}"
    else:
        return base_message

def reset_reminder_count(user_id):
    if user_id in reminder_counts:
        del reminder_counts[user_id]
    if user_id in last_reminder_time:
        del last_reminder_time[user_id]

def handle_successful_checkin(user_id):
    reset_reminder_count(user_id)
    logger.info(f"✅ User {user_id} checked in for yesterday, reset reminder count")

def daily_reset_if_needed():
    global reminder_counts, last_reminder_time, summary_sent_today
    now_utc = datetime.utcnow()
    ist = pytz.timezone("Asia/Kolkata")
    now_ist = pytz.utc.localize(now_utc).astimezone(ist)
    if summary_sent_today is not None and summary_sent_today != now_ist.date():
        reminder_counts.clear()
        last_reminder_time.clear()
        logger.story(f"🌅 New day started - resetting all reminder counts")
        summary_sent_today = now_ist.date()
    if summary_sent_today is None:
        summary_sent_today = now_ist.date()

def format_streak_summary(streak_rows, day_number):
    lines = [f"🐍 Day {day_number} log", ""]
    for row in streak_rows:
        username = row.get('username', row.get('Username', ''))
        score = row.get('score', 0)
        if score > 0:
            emoji = "🔵" * score
        elif score < 0:
            emoji = "🪦"
        else:
            emoji = ""
        lines.append(f"👤 {username}: {emoji}")
    lines.append("\nLet's do this!")
    return "\n".join(lines)

async def check_and_prompt(bot: Bot):
    global summary_sent_today
    daily_reset_if_needed()
    now_utc = datetime.utcnow()
    ist = pytz.timezone("Asia/Kolkata")
    now_ist = pytz.utc.localize(now_utc).astimezone(ist)
    local_str = now_ist.strftime("%H:%M")
    try:
        db = DbCache()
        users = db.get_all_users()
    except Exception as e:
        logger.error(f"❌ Error getting users from DB: {e}")
        return
    summary_hour, summary_min = parse_hhmm(TIME_FOR_UPDATE)
    if (now_ist.hour, now_ist.minute) == (summary_hour, summary_min):
        if summary_sent_today != now_ist.date():
            try:
                streak_rows = db.get_streak_summary(now_ist.date())
                summary = format_streak_summary(streak_rows, (now_ist - datetime(now_ist.year, now_ist.month, 1, tzinfo=ist)).days + 1)
                await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=summary)
                summary_sent_today = now_ist.date()
                logger.story(f"📊 Daily summary posted to channel")
            except Exception as e:
                logger.error(f"❌ Error sending summary: {e}")
    for user in users:
        try:
            # Safely extract user_id and username
            user_id = user.get("user_id") or user.get("UserID")
            if user_id is None:
                logger.error(f"User missing user_id: {user}")
                continue
            user_id = int(user_id)
            username = user.get("username") or user.get("Username") or str(user_id)
            timezone_str = user.get("timezone") or user.get("Timezone") or "Asia/Kolkata"
            try:
                tz = pytz.timezone(timezone_str)
            except Exception:
                tz = pytz.timezone("Asia/Kolkata")
            now_local = pytz.utc.localize(now_utc).astimezone(tz)
            yesterday_date = get_yesterday_date(now_local)
            current_year_month = yesterday_date.strftime("%Y%m")
            first_of_month = datetime.strptime(str(current_year_month) + "01", "%Y%m%d").date()
            habits = db.get_user_habits_for_date(user_id, first_of_month)
            if not isinstance(habits, list):
                logger.error(f"Expected list of dicts for habits, got {type(habits)}: {habits}")
                continue
            core_habits = [h for h in habits if isinstance(h, dict) and h.get('habit_type') == 'core']
            if not core_habits:
                logger.debug(f"⏭️ Skipping @{username} - no core habits set up for {current_year_month}")
                continue
            if db.has_already_checked_in(user_id, yesterday_date.strftime("%Y-%m-%d")):
                continue
            current_reminder_count = reminder_counts.get(user_id, 0)
            fallback_hour, fallback_min = parse_hhmm(SCHEDULER_AUTOMARK_HHMM)
            fallback_minutes = fallback_hour * 60 + fallback_min
            current_minutes = now_local.hour * 60 + now_local.minute
            if current_minutes >= fallback_minutes:
                last_auto = last_auto_x_sent.get(user_id)
                if not last_auto or (now_local - last_auto).total_seconds() > 86400:
                    has_checked_in = db.has_already_checked_in(user_id, yesterday_date.strftime("%Y-%m-%d"))
                    if not has_checked_in:
                        last_auto_x_sent[user_id] = now_local
                        try:
                            responses = []
                            dnd_count = 0
                            failed_count = 0
                            date_str = yesterday_date.strftime("%Y-%m-%d")
                            for habit in core_habits:
                                habit_id = habit.get('habit_id')
                                if habit_id is None:
                                    continue
                                if db.is_date_in_dnd_period(user_id, date_str, int(habit_id)):
                                    responses.append("⛔")
                                    dnd_count += 1
                                else:
                                    responses.append("❌")
                                    failed_count += 1
                            checkins = []
                            for habit, status in zip(core_habits, responses):
                                habit_id = habit.get('habit_id')
                                habit_text = habit.get('habit_text', '')
                                if habit_id is None:
                                    continue
                                checkins.append({
                                    "for_date": date_str,
                                    "year_month": current_year_month,
                                    "user_id": user_id,
                                    "username": username,
                                    "habit_id": int(habit_id),
                                    "habit_text": habit_text,
                                    "habit_status": status,
                                    "marked_by": "auto"
                                })
                            if checkins:
                                await db.log_checkin_to_db(checkins)
                                DbCache.refresh_cache()
                            if dnd_count > 0 and failed_count > 0:
                                message = f"⛔ Missed check-in. {failed_count} ❌ logged, {dnd_count} ⛔ (DND). Snake shrank by {failed_count}!"
                            elif dnd_count > 0 and failed_count == 0:
                                message = f"⛔ Missed check-in. All {dnd_count} habits were on DND (⛔). No snake impact!"
                            else:
                                message = f"⛔ Missed check-in. {failed_count} ❌ logged. Snake shrank by {failed_count}!"
                            await bot.send_message(chat_id=user_id, text=message)
                            reset_reminder_count(user_id)
                            logger.story(f"❌ Auto-marked @{username} for missed check-in ({failed_count} failed, {dnd_count} DND)")
                        except Exception as e:
                            logger.error(f"Auto-mark error for {username}: {e}")
                continue
            start_hour, start_min = parse_hhmm(SCHEDULER_START_HHMM)
            start_minutes = start_hour * 60 + start_min
            if current_minutes < start_minutes:
                continue
            if current_reminder_count >= 3:
                continue
            last_reminder = last_reminder_time.get(user_id)
            if last_reminder:
                time_since_last = (now_local - last_reminder).total_seconds() / 60
                if time_since_last < SCHEDULER_RECHECK_MIN:
                    continue
            if db.has_already_checked_in(user_id, yesterday_date.strftime("%Y-%m-%d")):
                continue
            try:
                reminder_count = current_reminder_count + 1
                auto_mark_minutes_remaining = fallback_minutes - current_minutes
                message = format_reminder_message(
                    username, yesterday_date, reminder_count, 
                    auto_mark_minutes_remaining if reminder_count == 3 else None
                )
                await bot.send_message(chat_id=user_id, text=message)
                reminder_counts[user_id] = reminder_count
                last_reminder_time[user_id] = now_local
                if reminder_count == 1:
                    logger.story(f"⏰ Sending 1st check-in reminder to @{username} for yesterday ({yesterday_date.strftime('%Y-%m-%d')})")
                elif reminder_count == 2:
                    logger.story(f"⏰ 2nd reminder sent to @{username} ({SCHEDULER_RECHECK_MIN}min since last)")
                elif reminder_count == 3:
                    logger.story(f"⚠️  Final warning sent to @{username} - auto-mark in {auto_mark_minutes_remaining}min")
            except Exception as e:
                logger.error(f"Reminder error for {username}: {e}")
        except Exception as e:
            logger.error(f"User processing error for {user.get('username', 'Unknown')}: {e}")

async def scheduler_loop(app):
    bot = app.bot
    while True:
        try:
            await check_and_prompt(bot)
        except Exception as e:
            logger.error(f"❌ Error in scheduler loop: {e}")
        sleep_sec = int(SCHEDULER_INTERVAL_HHMMSSS[:2]) * 3600 + int(SCHEDULER_INTERVAL_HHMMSSS[2:4]) * 60
        await asyncio.sleep(sleep_sec)

def launch_scheduler(app):
    asyncio.create_task(scheduler_loop(app)) 