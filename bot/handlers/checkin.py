#!/usr/bin/env python3
"""
Check-in handler for the Telegram bot (DB version).
Handles user check-ins for habits with smart date selection and dual check-in capability, using DbCache.
"""

import os
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler
import asyncio

from bot.utils.cached_db import DbCache
from bot.scheduler import handle_successful_checkin
from bot.utils.logger import logger
from bot.utils.config import TELEGRAM_CHANNEL_ID

print('Loaded checkin_db.py')

def format_date_button(date) -> str:
    print(f'Formatting date button for: {date}')
    day = date.day
    suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    month = date.strftime("%B")
    day_name = date.strftime("%a")
    return f"[{day}{suffix} {month}, {day_name}]"

def format_checkin_announcement(username, date, summary):
    print(f'Formatting checkin announcement for {username} on {date} with summary: {summary}')
    completed = [f"✅ {h}" for h, s in summary if s == "✅"]
    missed = [f"❌ {h}" for h, s in summary if s == "❌"]
    skipped = [f"⏭️ {h}" for h, s in summary if s == "⏭️"]
    dnd = [f"⛔ {h}" for h, s in summary if s == "⛔"]
    missed_count = len(missed)
    snake_delta = "+1" if missed_count == 0 else f"-{missed_count}"
    message = f"👀 {username} Check-in Complete for {date.strftime('%Y-%m-%d')}!\n\n"
    message += "\n".join(dnd + completed + missed + skipped)
    message += f"\n🐍 Snake grew by {snake_delta}" if missed_count == 0 else f"\n🐍 Snake shrank by {snake_delta}"
    return message

def format_existing_checkin(username, date, summary, timestamp):
    print(f'Formatting existing checkin for {username} on {date} at {timestamp}')
    completed = [f"✅ {h}" for h, s in summary if s == "✅"]
    missed = [f"❌ {h}" for h, s in summary if s == "❌"]
    skipped = [f"⏭️ {h}" for h, s in summary if s == "⏭️"]
    missed_count = len(missed)
    snake_delta = "+1" if missed_count == 0 else f"-{missed_count}"
    ist_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime("%I:%M%p").lower()
    message = f"Hey! You already checked-in for *{date.strftime('%Y-%m-%d')}* at *{ist_time} IST*!\n\n"
    message += "\n".join(completed + missed + skipped)
    message += f"\n🐍 Snake grew by {snake_delta}" if missed_count == 0 else f"\n🐍 Snake shrank by {snake_delta}"
    return message

async def send_checkin_announcement(user_id, username, date, bot):
    print(f'[send_checkin_announcement] user_id={user_id}, username={username}, date={date}')
    db = DbCache()
    summary_rows = db.get_user_checkin_summary(user_id, date.strftime("%Y-%m-%d"))
    print(f'[send_checkin_announcement] summary_rows={summary_rows}')
    if not summary_rows:
        logger.debug(f"[ANNOUNCE] No summary data for {username} on {date}, skipping announcement.")
        return
    log_txt_json = summary_rows[0].get("log_txt_json")
    print(f'[send_checkin_announcement] log_txt_json={log_txt_json}')
    if not log_txt_json:
        logger.debug(f"[ANNOUNCE] No log_txt_json for {username} on {date}, skipping announcement.")
        return
    summary_data = [(h["habit_text"], h["habit_status"]) for h in json.loads(log_txt_json)]
    print(f'[send_checkin_announcement] summary_data={summary_data}')
    if all(s == "⛔" for _, s in summary_data):
        logger.debug(f"[ANNOUNCE] All habits DND for {username} on {date}, skipping announcement.")
        return
    msg = format_checkin_announcement(username, date, summary_data)
    await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=msg)

async def log_and_announce_checkin(user_id, username, habits, responses, date, bot):
    print(f'[log_and_announce_checkin] user_id={user_id}, username={username}, date={date}, habits={habits}, responses={responses}')
    db = DbCache()
    year_month = date.strftime('%Y%m')
    habit_dicts = db.get_user_habits_for_month(user_id, year_month)
    print(f'[log_and_announce_checkin] habit_dicts={habit_dicts}')
    habit_text_to_id = {h['habit_text']: h['habit_id'] for h in habit_dicts}
    print(f'[log_and_announce_checkin] habit_text_to_id={habit_text_to_id}')
    checkins = []
    for (habit_id, habit_text), status in zip(habits, responses):
        checkins.append({
            "for_date": date,
            "year_month": year_month,
            "user_id": user_id,
            "username": username,
            "habit_id": habit_id,
            "habit_text": habit_text,
            "habit_status": status,
            "marked_by": "manual"
        })
    await db.log_checkin_to_db(checkins)
    print('[log_and_announce_checkin] Called db.log_checkin_to_db')
    DbCache.refresh_cache()
    print('[log_and_announce_checkin] Refreshed cache')
    await send_checkin_announcement(user_id, username, date, bot)

DATE_SELECTION, HABIT_CHECKIN, DUAL_CHECKIN_PROMPT = range(3)
user_checkin_states = {}

async def start_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('[start_checkin] Called')
    DbCache.refresh_cache()
    print('[start_checkin] Refreshed cache')
    db = DbCache()
    context.user_data['db'] = db
    original_username = (update.effective_user.username or update.effective_user.first_name).strip()
    user_id = update.effective_user.id
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    print(f'[start_checkin] user_id={user_id}, today={today}, yesterday={yesterday}')
    has_today = db.has_already_checked_in(user_id, today.strftime("%Y-%m-%d"))
    has_yesterday = db.has_already_checked_in(user_id, yesterday.strftime("%Y-%m-%d"))
    print(f'[start_checkin] has_today={has_today}, has_yesterday={has_yesterday}')
    if has_today and has_yesterday:
        print('[start_checkin] Already checked in for both days')
        await update.message.reply_text("✅ You've already checked in for both today and yesterday!")
        return ConversationHandler.END
    selected_date = None
    if not has_yesterday:
        selected_date = yesterday
    elif not has_today:
        selected_date = today
    else:
        print('[start_checkin] Already checked in for both days (else)')
        await update.message.reply_text("✅ You've already checked in for both today and yesterday!")
        return ConversationHandler.END
    print(f'[start_checkin] selected_date={selected_date}')
    other_date = yesterday if selected_date == today else today
    dual_checkin_available = not db.has_already_checked_in(user_id, other_date.strftime("%Y-%m-%d"))
    print(f'[start_checkin] dual_checkin_available={dual_checkin_available}, other_date={other_date}')
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(format_date_button(selected_date), callback_data=f"date_select|{selected_date.strftime('%Y-%m-%d')}")]
    ])
    await update.message.reply_text(
        "📅 Check-in for:",
        reply_markup=keyboard
    )
    return DATE_SELECTION

async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('[handle_date_selection] Called')
    query = update.callback_query
    await query.answer()
    db = context.user_data.get('db')
    user_id = query.from_user.id
    original_username = (query.from_user.username or query.from_user.first_name).strip()
    _, date_str = query.data.split("|")
    selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    print(f'[handle_date_selection] user_id={user_id}, selected_date={selected_date}')
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    other_date = yesterday if selected_date == today else today
    dual_checkin_available = not db.has_already_checked_in(user_id, other_date.strftime("%Y-%m-%d"))
    print(f'[handle_date_selection] dual_checkin_available={dual_checkin_available}, other_date={other_date}')
    await start_habit_checkin(update, context, selected_date, original_username, dual_checkin_available)
    return HABIT_CHECKIN

async def start_habit_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE, date, username, dual_checkin_available):
    print('[start_habit_checkin] Called')
    db = context.user_data.get('db')
    user_id = update.effective_user.id if hasattr(update, 'effective_user') else update.callback_query.from_user.id
    year_month = date.strftime('%Y%m')
    habit_dicts = db.get_user_habits_for_month(user_id, year_month)
    print(f'[start_habit_checkin] user_id={user_id}, year_month={year_month}, habit_dicts={habit_dicts}')
    # Build habits as list of (habit_id, habit_text)
    habits = [(h['habit_id'], h['habit_text']) for h in habit_dicts]
    print(f'[start_habit_checkin] habits={habits}')
    if not habits:
        message = "⚠️ No core habits found for this month. Please use /sethabits to set your core habits."
        print(f'[start_habit_checkin] {message}')
        if update.message is not None:
            await update.message.reply_text(message)
        elif update.callback_query is not None:
            await update.callback_query.edit_message_text(message)
        else:
            await context.bot.send_message(chat_id=user_id, text=message)
        return ConversationHandler.END
    date_str = date.strftime("%Y-%m-%d")
    dnd_habits = []
    available_habits = []
    dnd_mask = []
    for habit_id, habit_text in habits:
        if db.is_date_in_dnd_period(user_id, date_str, habit_id):
            dnd_habits.append(habit_text)
            dnd_mask.append(True)
        else:
            available_habits.append(habit_text)
            dnd_mask.append(False)
    print(f'[start_habit_checkin] dnd_habits={dnd_habits}, available_habits={available_habits}, dnd_mask={dnd_mask}')
    if not available_habits and dnd_habits:
        message = f"⚠️ The following habits are on DND for {date_str}:\n"
        for habit in dnd_habits:
            message += f"⛔ {habit}\n"
        print(f'[start_habit_checkin] {message}')
        # Log all ⛔ for this date
        await log_and_announce_checkin(user_id, username, [h[1] for h in habits], ["⛔"] * len(habits), date, context.bot)
        if update.message is not None:
            await update.message.reply_text(message)
        elif update.callback_query is not None:
            await update.callback_query.edit_message_text(message)
        else:
            await context.bot.send_message(chat_id=user_id, text=message)
        if len(dnd_habits) <= 2:
            await asyncio.sleep(5)
        return ConversationHandler.END
    if dnd_habits:
        info_message = f"🚫 You are on DND for {date_str}.\nThe following habits are excluded:\n"
        for habit in dnd_habits:
            info_message += f"• {habit}\n"
        print(f'[start_habit_checkin] {info_message}')
        if update.message is not None:
            await update.message.reply_text(info_message)
        elif update.callback_query is not None:
            await update.callback_query.edit_message_text(info_message)
        else:
            await context.bot.send_message(chat_id=user_id, text=info_message)
        if len(dnd_habits) <= 2:
            await asyncio.sleep(5)
    # Store both habit_id and habit_text in state
    user_checkin_states[user_id] = {
        "habits": habits,  # list of (habit_id, habit_text)
        "responses": [],
        "idx": 0,
        "date": date,
        "username": username,
        "dual_checkin_available": dual_checkin_available,
        "dnd_mask": dnd_mask
    }
    print(f'[start_habit_checkin] user_checkin_states[{user_id}]={user_checkin_states[user_id]}')
    await ask_next_habit(update, context)

async def ask_next_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('[ask_next_habit] Called')
    db = context.user_data.get('db')
    user_id = update.effective_user.id if hasattr(update, 'effective_user') else update.callback_query.from_user.id
    state = user_checkin_states[user_id]
    idx = state["idx"]
    habit_id, habit_text = state["habits"][idx]
    dnd_mask = state.get("dnd_mask", [False]*len(state["habits"]))
    print(f'[ask_next_habit] user_id={user_id}, idx={idx}, habit_id={habit_id}, habit_text={habit_text}, dnd_mask={dnd_mask}')
    logger.debug(f"[DEBUG] ask_next_habit: user_id={user_id}, idx={idx}, habit='{habit_text}'")
    if dnd_mask[idx]:
        state["responses"].append("⛔")
        state["idx"] += 1
        if state["idx"] < len(state["habits"]):
            return await ask_next_habit(update, context)
        else:
            await complete_checkin(update.callback_query if hasattr(update, 'callback_query') and update.callback_query else update, context, state)
            if state["dual_checkin_available"]:
                return await prompt_dual_checkin(update.callback_query if hasattr(update, 'callback_query') and update.callback_query else update, context, state)
            else:
                return ConversationHandler.END
    # Use habit_id for rest day eligibility
    rest_day_available = db.check_rest_day_eligibility(user_id, habit_id, state["date"].strftime("%Y-%m-%d"))
    print(f'[ask_next_habit] user_id={user_id}, idx={idx}, habit_id={habit_id}, habit_text={habit_text}, rest_day_available={rest_day_available}, date={state["date"]}')
    logger.debug(f"[DEBUG] ask_next_habit: user_id={user_id}, idx={idx}, habit='{habit_text}', rest_day_available={rest_day_available}, date={state['date']}")
    keyboard_buttons = [
        [InlineKeyboardButton("✅", callback_data="habit|✅"), InlineKeyboardButton("❌", callback_data="habit|❌")]
    ]
    if rest_day_available:
        keyboard_buttons.append([InlineKeyboardButton("⏭️ Rest Day", callback_data="habit|⏭️")])
    keyboard = InlineKeyboardMarkup(keyboard_buttons)
    message = f"Did you do: *{habit_text}*?"
    if update.message is not None:
        await update.message.reply_text(message, reply_markup=keyboard, parse_mode='Markdown')
    elif update.callback_query is not None:
        await update.callback_query.edit_message_text(message, reply_markup=keyboard, parse_mode='Markdown')
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text=message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    return HABIT_CHECKIN

async def handle_habit_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('[handle_habit_response] Called')
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    state = user_checkin_states.get(user_id)
    if not state:
        await query.edit_message_text("⚠️ No check-in session found. Use /checkin to start.")
        return ConversationHandler.END
    _, status = query.data.split("|")
    habit_id, habit_text = state["habits"][state["idx"]]
    state["responses"].append(status)
    state["idx"] += 1
    if state["idx"] < len(state["habits"]):
        return await ask_next_habit(update, context)
    else:
        await complete_checkin(query, context, state)
        if state["dual_checkin_available"]:
            return await prompt_dual_checkin(query, context, state)
        else:
            return ConversationHandler.END

async def complete_checkin(query, context, state):
    print('[complete_checkin] Called')
    user_id = query.from_user.id
    await log_and_announce_checkin(
        user_id=user_id,
        username=state["username"],
        habits=state["habits"],
        responses=state["responses"],
        date=state["date"],
        bot=context.bot,
    )
    yesterday_date = datetime.now().date() - timedelta(days=1)
    if state["date"] == yesterday_date:
        handle_successful_checkin(user_id)
        logger.info(f"✅ User {user_id} checked in for yesterday, reset reminder count")
    else:
        logger.info(f"✅ User {user_id} checked in for {state['date']}, reminder count unchanged")
    completed_count = sum(1 for r in state["responses"] if r == "✅")
    total_count = len(state["responses"])
    logger.story(f"✅ @{state['username']} completed check-in for {state['date']} ({completed_count}/{total_count} habits done)")
    await query.edit_message_text(f"✅ Check-in completed for {state['date'].strftime('%Y-%m-%d')}!")
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="",
            reply_markup=ReplyKeyboardRemove(selective=False)
        )
    except Exception as e:
        logger.debug(f"Could not clear keyboard for user {user_id}: {e}")

async def prompt_dual_checkin(query, context, state):
    print('[prompt_dual_checkin] Called')
    db = context.user_data.get('db')
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    other_date = yesterday if state["date"] == today else today
    if db.has_already_checked_in(query.from_user.id, other_date.strftime("%Y-%m-%d")):
        return ConversationHandler.END
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Yes", callback_data="dual_checkin|yes")],
        [InlineKeyboardButton("No", callback_data="dual_checkin|no")]
    ])
    await query.edit_message_text(
        f"Would you like to check in for {format_date_button(other_date)} as well?",
        reply_markup=keyboard
    )
    return DUAL_CHECKIN_PROMPT

async def handle_dual_checkin_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('[handle_dual_checkin_response] Called')
    query = update.callback_query
    await query.answer()
    db = context.user_data.get('db')
    user_id = query.from_user.id
    _, response = query.data.split("|")
    if response == "no":
        await query.edit_message_text("✅ Check-in session completed!")
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="",
                reply_markup=ReplyKeyboardRemove(selective=False)
            )
        except Exception as e:
            logger.debug(f"Could not clear keyboard for user {user_id}: {e}")
        return ConversationHandler.END
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    other_date = yesterday if db.has_already_checked_in(user_id, today.strftime("%Y-%m-%d")) else today
    if db.has_already_checked_in(user_id, other_date.strftime("%Y-%m-%d")):
        await query.edit_message_text("⚠️ The other date is no longer available for check-in.")
        return ConversationHandler.END
    original_username = None
    for uid, state_ in user_checkin_states.items():
        if uid == user_id:
            original_username = state_["username"]
            break
    if not original_username:
        await query.edit_message_text("⚠️ Error: Could not find user session.")
        return ConversationHandler.END
    await start_habit_checkin(update, context, other_date, original_username, False)
    return HABIT_CHECKIN

checkin_db_handler = ConversationHandler(
    entry_points=[CommandHandler("checkin", start_checkin)],
    states={
        DATE_SELECTION: [CallbackQueryHandler(handle_date_selection, pattern="^date_select\\|")],
        HABIT_CHECKIN: [CallbackQueryHandler(handle_habit_response, pattern="^habit\\|")],
        DUAL_CHECKIN_PROMPT: [CallbackQueryHandler(handle_dual_checkin_response, pattern="^dual_checkin\\|")]
    },
    fallbacks=[],
) 