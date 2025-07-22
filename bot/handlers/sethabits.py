import warnings
warnings.filterwarnings("ignore", message="If 'per_message=False', 'CallbackQueryHandler' will not be tracked")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler, MessageHandler, ConversationHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from datetime import datetime
import os
import re
from bot.utils.cached_db import DbCache
from utils.config import TELEGRAM_CHANNEL_ID
from utils.logger import get_logger

logger = get_logger("sethabits_db")

WAIT_FOR_MONTH_CONFIRM, CORE, WAIT_FOR_CORE_CONFIRM, BONUS, WAIT_FOR_BONUS_CONFIRM, EDIT_CORE = range(6)

def format_habit_announcement(username, habits, yyyymm):
    year = yyyymm[:4]
    month = yyyymm[4:]
    month_name = datetime.strptime(month, "%m").strftime("%B")
    habits_text = "\n".join([f"• {habit}" for habit in habits])
    message = f"🎯 {username} just set their core habits for {month_name} {year}!\n\n"
    message += f"{habits_text}\n\n"
    message += f"📊 Total: {len(habits)} core habits"
    return message

async def send_habit_announcement(username, habits, yyyymm, bot):
    try:
        msg = format_habit_announcement(username, habits, yyyymm)
        await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=msg)
        logger.story(f"📢 Habit announcement sent for @{username} ({len(habits)} habits)")
    except Exception as e:
        logger.error(f"❌ Failed to send habit announcement for {username}: {e}")

def validate_habit_emoji(habit_text):
    try:
        import emoji
    except ImportError:
        # Fallback: always return True if emoji is not installed
        return True
    words = habit_text.strip().split()
    if not words:
        return False
    last_part = words[-1]
    if emoji.is_emoji(last_part):
        return True
    emoji_list = emoji.emoji_list(last_part)
    if emoji_list:
        return True
    if emoji.emoji_count(last_part) > 0:
        return True
    common_symbols = ['✅', '❌', '⭐', '💯', '🔥', '💪', '🎯', '📈', '🎉', '🏆', '💎', '🌟']
    if last_part in common_symbols:
        return True
    return False

async def start_set_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("[DEBUG] start_set_habits called")
    DbCache.refresh_cache()
    db = DbCache()
    context.user_data['db'] = db
    print("[DEBUG] DbCache initialized and set in context.user_data")
    COLLECT_HABITS_YYYYMM = os.getenv("COLLECT_HABITS_YYYYMM")
    if update.callback_query:
        user = update.callback_query.from_user
        message = update.callback_query.message
    else:
        user = update.message.from_user
        message = update.message
    print(f"[DEBUG] User: {user.id} - {user.username}")
    if not COLLECT_HABITS_YYYYMM:
        print("[DEBUG] COLLECT_HABITS_YYYYMM not set")
        await message.reply_text(
            "❌ Configuration error: COLLECT_HABITS_YYYYMM environment variable is not set. Please contact an administrator."
        )
        return ConversationHandler.END
    today = datetime.today()
    configured_month = datetime.strptime(COLLECT_HABITS_YYYYMM, "%Y%m")
    if today.strftime("%Y%m") != COLLECT_HABITS_YYYYMM:
        print("[DEBUG] Month mismatch, prompting user for confirmation")
        await message.reply_text(
            f"👋 Just to be on the same page — you're about to set habits for *{today.strftime('%b, %y')}*\n\n"
            f"But the system is currently collecting habits for *{configured_month.strftime('%b, %y')}*.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Yeah I know", callback_data="confirm_habit_month")],
                [InlineKeyboardButton("❌ No! Cancel", callback_data="cancel_habit_setup")]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        return WAIT_FOR_MONTH_CONFIRM
    user_id = user.id
    username = user.username or user.first_name
    yyyymm = COLLECT_HABITS_YYYYMM
    print(f"[DEBUG] Checking for existing core habits for user_id={user_id}, yyyymm={yyyymm}")
    if db.has_existing_core_habits(user_id, yyyymm):
        print("[DEBUG] User already has core habits for this month")
        first_of_month = datetime.strptime(yyyymm + "01", "%Y%m%d").date()
        core_habits = [h['habit_text'] for h in db.get_user_habits_for_month(user_id, yyyymm) if h['habit_type'] == 'core']
        timestamp = db.get_habit_timestamp(user_id, yyyymm)
        core_text = "\n".join([f"{i+1}\u20E3 {habit}" for i, habit in enumerate(core_habits)])
        await message.reply_text(
            f"Hey! You already set core habits for *{yyyymm}* at *{timestamp}* ⏰\n\n"
            f"{core_text}\n\n"
            f"Contact an admin to make changes.",
            parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END
    print("[DEBUG] No existing core habits found, proceeding to prompt_core_habits")
    return await prompt_core_habits(update, context)

async def handle_month_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    return await prompt_core_habits(update.callback_query, context)

async def prompt_core_habits(updateable, context):
    message = None
    if hasattr(updateable, 'message') and updateable.message is not None:
        message = updateable.message
    elif hasattr(updateable, 'callback_query') and updateable.callback_query is not None and hasattr(updateable.callback_query, 'message'):
        message = updateable.callback_query.message
    elif hasattr(updateable, 'data') and hasattr(updateable, 'message') and updateable.message is not None:
        message = updateable.message
    if message is None:
        raise RuntimeError("Could not find a message object to reply to in prompt_core_habits.")
    await message.reply_text(
        "🧱 Please enter *2–4 core habits* (comma-separated).\n\n"
        "✅ *Core habits must be:*\n"
        "- Daily (can be done every day)\n"
        "- Binary (yes or no answer)\n"
        "- Actionable (a concrete behavior you control)\n\n"
        "💡 *Examples:*\n"
        "- Meditate 🧘‍♂️\n"
        "- No sugar 🚫🍭\n"
        "- Sleep before 11pm 🌙\n\n"
        "✍️ Type them like this:\n"
        "Meditate 🧘‍♂️, Sleep before 11pm 🌙, No sugar 🚫🍭",
        parse_mode=ParseMode.MARKDOWN
    )
    return CORE

async def get_core_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("[DEBUG] get_core_habits called")
    core = [h.strip() for h in update.message.text.split(",") if h.strip()]
    print(f"[DEBUG] User entered core habits: {core}")
    if not (2 <= len(core) <= 4):
        print("[DEBUG] Invalid number of core habits")
        await update.message.reply_text("❗ Please enter between 2 and 4 core habits.")
        return CORE
    if any(not validate_habit_emoji(habit) for habit in core):
        print("[DEBUG] One or more core habits failed emoji validation")
        await update.message.reply_text("❗ Each core habit must end with an emoji. Please revise:")
        return CORE
    context.user_data['core_habits'] = core
    print(f"[DEBUG] core_habits set in context.user_data: {core}")
    core_text = "\n".join([f"{i+1}. {habit}" for i, habit in enumerate(core)])
    numbered_buttons = [InlineKeyboardButton(f"{i+1}️⃣", callback_data=f"edit_core_{i}") for i in range(len(core))]
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="confirm_core")],
        numbered_buttons,
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_habit_setup")]
    ]
    await update.message.reply_text(
        f"🧱 You've entered the following *core habits:*\n\n{core_text}\n\nThese will be locked for the month and can only be edited next month. Do you want to save these?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    return WAIT_FOR_CORE_CONFIRM

async def edit_core_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    idx = int(update.callback_query.data.split("_")[-1])
    context.user_data['edit_core_index'] = idx
    await update.callback_query.message.reply_text(f"✏️ What should replace core habit #{idx+1}?")
    return EDIT_CORE

async def save_edited_core_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data.get('edit_core_index')
    new_text = update.message.text.strip()
    if not validate_habit_emoji(new_text):
        await update.message.reply_text("❗ The new habit must end with an emoji. Try again:")
        return EDIT_CORE
    context.user_data['core_habits'][idx] = new_text
    core = context.user_data['core_habits']
    core_text = "\n".join([f"{i+1}. {habit}" for i, habit in enumerate(core)])
    numbered_buttons = [InlineKeyboardButton(f"{i+1}️⃣", callback_data=f"edit_core_{i}") for i in range(len(core))]
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="confirm_core")],
        numbered_buttons,
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_habit_setup")]
    ]
    await update.message.reply_text(
        f"🧱 You've updated your *core habits:*\n\n{core_text}\n\nThese will be locked for the month and can only be edited next month. Do you want to save these?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    return WAIT_FOR_CORE_CONFIRM

async def cancel_habit_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if hasattr(update, "callback_query"):
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("🚫 Habit setup cancelled.")
    else:
        await update.message.reply_text("🚫 Habit setup cancelled.")
    return ConversationHandler.END

async def save_core_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("[DEBUG] save_core_habits called")
    await update.callback_query.answer()
    user = update.callback_query.from_user
    user_id = user.id
    username = user.username or user.first_name
    yyyymm = os.getenv("COLLECT_HABITS_YYYYMM").strip()
    if not yyyymm:
        print("[DEBUG] COLLECT_HABITS_YYYYMM not set in save_core_habits")
        await update.callback_query.message.reply_text(
            "❌ Configuration error: COLLECT_HABITS_YYYYMM environment variable is not set. Please contact an administrator."
        )
        return ConversationHandler.END
    db = context.user_data.get('db', None)
    if db is None:
        db = DbCache()
    print(f"[DEBUG] Checking for duplicate core habits for user_id={user_id}, yyyymm={yyyymm}")
    if db.has_existing_core_habits(user_id, yyyymm):
        print("[DEBUG] Duplicate core habits found, aborting save")
        await update.callback_query.message.reply_text(
            f"⚠️ You've already submitted core habits for *{yyyymm}*. Contact an admin to make changes.",
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END
    print(f"[DEBUG] Inserting core habits into DB for user_id={user_id}, yyyymm={yyyymm}")
    await db.add_habits_to_db(user_id=user_id, username=username, year_month=yyyymm, habit_texts=context.user_data['core_habits'], habit_type='core')
    print("[DEBUG] Refreshing DbCache after insert")
    DbCache.refresh_cache()
    print("[DEBUG] DbCache refreshed")
    habits_text = ", ".join(context.user_data['core_habits'])
    logger.story(f"🎯 @{username} set {len(context.user_data['core_habits'])} core habits: {habits_text}")
    await send_habit_announcement(username, context.user_data['core_habits'], yyyymm, context.bot)
    await update.callback_query.message.reply_text("✅ Core habits saved successfully!")
    return ConversationHandler.END

set_habits_db_handler = ConversationHandler(
    entry_points=[CommandHandler("sethabits", start_set_habits)],
    states={
        WAIT_FOR_MONTH_CONFIRM: [
            CallbackQueryHandler(handle_month_confirm, pattern="^confirm_habit_month$"),
            CallbackQueryHandler(cancel_habit_setup, pattern="^cancel_habit_setup$")
        ],
        CORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_core_habits)],
        WAIT_FOR_CORE_CONFIRM: [
            CallbackQueryHandler(save_core_habits, pattern="^confirm_core$"),
            CallbackQueryHandler(cancel_habit_setup, pattern="^cancel_habit_setup$"),
            CallbackQueryHandler(edit_core_habit, pattern="^edit_core_\\d+$")
        ],
        EDIT_CORE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, save_edited_core_habit)
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel_habit_setup)],
) 