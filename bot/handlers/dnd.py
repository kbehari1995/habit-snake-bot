from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, ContextTypes, filters
from datetime import datetime, date
from utils.logger import get_logger
import os
import json
from dotenv import load_dotenv
from bot.utils.cached_db import DbCache

# Initialize logger
logger = get_logger("dnd_db")

# Load environment variables
if os.path.exists(".env"):
    load_dotenv()

# Conversation states
HABIT_SELECTION, DATE_INPUT, CONFIRMATION, DND_LIST, DND_EDIT_SELECT, DND_EDIT_ACTION, DND_EDIT_DATES, DND_EDIT_HABIT, DND_EDIT_CONFIRM_DELETE, DND_EDIT_CONTINUE = range(10)

def format_date_display(date_str: str) -> str:
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    day = date_obj.day
    month = date_obj.strftime("%B")
    day_name = date_obj.strftime("%a")
    return f"{day} {month} {day_name}"

def calculate_days_difference(start_date: str, end_date: str) -> int:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    return (end - start).days + 1

# ===================== DND EDIT/DELETE FLOW ===================== 

# --- BEGIN: DND DB I/O MINIMIZATION PATCH ---
# Patch: operate on cache only during session, batch DB writes at exit

# Helper to record pending changes
# Each entry: (op, data) where op is 'add', 'edit', 'delete', data is relevant

def _init_pending_dnd_changes(context):
    if 'pending_dnd_changes' not in context.user_data:
        context.user_data['pending_dnd_changes'] = []

def _record_pending(context, op, data):
    _init_pending_dnd_changes(context)
    context.user_data['pending_dnd_changes'].append((op, data))
    print('[DND_V2] Pending DND changes:', context.user_data['pending_dnd_changes'])

async def _apply_pending_dnd_changes(context):
    db = context.user_data.get('db')
    changes = context.user_data.get('pending_dnd_changes', [])
    print('[DND_V2] Applying pending DND changes:', changes)
    for op, data in changes:
        if op == 'add':
            await db.add_dnd_period_to_db(**data)
        elif op == 'edit':
            await db.update_dnd_entry_in_db(**data)
        elif op == 'delete':
            await db.delete_dnd_entry_in_db(data['dnd_log_id'])
    DbCache.refresh_cache()
    context.user_data['pending_dnd_changes'] = []
    print('[DND_V2] Pending DND changes after apply:', context.user_data['pending_dnd_changes'])

# Patch all DND add/edit/delete handlers to operate on cache and record pending changes
# Patch all session exit points to call _apply_pending_dnd_changes

# --- PATCH: dnd_command ---
async def dnd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("[dnd_command] Entry point called")
    print("[dnd_command] Entry point called")
    DbCache.refresh_cache()
    user = update.message.from_user
    user_id = user.id
    username = user.username or user.first_name
    db = DbCache()
    context.user_data['db'] = db
    _init_pending_dnd_changes(context)
    user_entries = db.get_dnd_entries_for_user(user_id)
    logger.debug(f"[dnd_command] user_id={user_id}, entries={user_entries}")
    print(f"[dnd_command] user_id={user_id}, entries={user_entries}")
    if user_entries:
        lines = ["🛡️ <b>Your DND entries:</b>"]
        for idx, entry in enumerate(user_entries, 1):
            habit = entry.get("habit_text", "?")
            start = entry.get("start_date", "?")
            end = entry.get("end_date", "?")
            lines.append(f"{idx}. <i>{habit}</i>: <b>{start}</b> → <b>{end}</b> 💤")
        message = "\n".join(lines)
    else:
        message = "🛡️ <b>No DND entries found.</b>\n\nYou have not set any Do Not Disturb periods yet."
    keyboard = [
        [
            InlineKeyboardButton("➕ Add DND", callback_data="dnd_add"),
            InlineKeyboardButton("✏️ Edit/Delete", callback_data="dnd_edit"),
            InlineKeyboardButton("🏁 Done", callback_data="dnd_done")
        ]
    ]
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return DND_LIST

# --- PATCH: dnd_list_entrypoint ---
async def dnd_list_entrypoint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("[dnd_list_entrypoint] called")
    print("[dnd_list_entrypoint] called")
    query = update.callback_query
    await query.answer()
    logger.debug(f"[dnd_list_entrypoint] query.data={query.data}")
    print(f"[dnd_list_entrypoint] query.data={query.data}")
    if query.data == "dnd_add":
        return await start_add_dnd_flow(query, context)
    elif query.data == "dnd_edit":
        return await show_dnd_list(query, context)
    elif query.data == "dnd_done":
        await _apply_pending_dnd_changes(context)
        await query.edit_message_text("🏁 <b>DND session ended.</b>\n\nStay focused and have a great day!", parse_mode="HTML")
        return ConversationHandler.END

# --- PATCH: dnd_edit_action ---
async def dnd_edit_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("[dnd_edit_action] called")
    print("[dnd_edit_action] called")
    query = update.callback_query
    await query.answer()
    _, action = query.data.split("|")
    db = context.user_data.get('db')
    entry = context.user_data.get("edit_entry")
    logger.debug(f"[dnd_edit_action] action={action}, entry={entry}")
    print(f"[dnd_edit_action] action={action}, entry={entry}")
    if action == "habit":
        user = query.from_user
        user_id = user.id
        current_month = datetime.now().strftime("%Y%m")
        habits = db.get_user_habits_for_month(user_id, current_month)
        keyboard = [[InlineKeyboardButton(h["habit_text"], callback_data=f"dndedithabit|{i}")] for i, h in enumerate(habits)]
        await query.edit_message_text(
            "🔄 <b>Select a new habit:</b>\n\nChoose wisely, your future self is watching! 🔍",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        context.user_data["edit_habits"] = habits
        return DND_EDIT_HABIT
    elif action == "dates":
        await query.edit_message_text(
            "📅 <b>Enter new start and end dates in YYYY-MM-DD YYYY-MM-DD format:</b>\n\nExample: <code>2025-01-15 2025-01-20</code>\n\nNo, you can't pick 1999. Sorry, Prince.",
            parse_mode="HTML"
        )
        return DND_EDIT_DATES
    elif action == "delete":
        if entry:
            dnd_log_id = entry['dnd_log_id']
            db.delete_dnd_entry_from_cache(dnd_log_id)
            _record_pending(context, 'delete', {'dnd_log_id': dnd_log_id})
        await query.edit_message_text("🗑️ <b>DND entry deleted.</b>\n\nGone, but not forgotten. Unless you delete it again.", parse_mode="HTML")
        return await show_dnd_list(query, context)
    elif action == "back":
        return await show_dnd_list(query, context)

# --- PATCH: dnd_edit_habit ---
async def dnd_edit_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("[dnd_edit_habit] called")
    print("[dnd_edit_habit] called")
    query = update.callback_query
    await query.answer()
    _, idx = query.data.split("|")
    idx = int(idx)
    habits = context.user_data["edit_habits"]
    new_habit = habits[idx]
    entry = context.user_data["edit_entry"]
    db = context.user_data.get('db')
    logger.debug(f"[dnd_edit_habit] idx={idx}, new_habit={new_habit}, entry={entry}")
    print(f"[dnd_edit_habit] idx={idx}, new_habit={new_habit}, entry={entry}")
    dnd_log_id = entry['dnd_log_id']
    db.update_dnd_entry_to_cache(dnd_log_id, new_habit_text=new_habit["habit_text"])
    _record_pending(context, 'edit', {'dnd_log_id': dnd_log_id, 'new_habit_text': new_habit["habit_text"]})
    await query.edit_message_text(f"✅ <b>Habit updated to <i>{new_habit['habit_text']}</i>.</b>\n\nChange is good. Unless it's socks. 🤔", parse_mode="HTML")
    return await show_dnd_list(query, context)

# --- PATCH: dnd_edit_dates ---
async def dnd_edit_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("[dnd_edit_dates] called")
    print("[dnd_edit_dates] called")
    text = update.message.text.strip()
    logger.debug(f"[dnd_edit_dates] text={text}")
    print(f"[dnd_edit_dates] text={text}")
    try:
        start, end = text.split()
        start_dt = datetime.strptime(start, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end, "%Y-%m-%d").date()
        if start_dt > end_dt:
            await update.message.reply_text("❌ <b>Start date cannot be after end date.</b>\n\nEven Marty McFly couldn't pull that off.", parse_mode="HTML")
            return DND_EDIT_DATES
    except Exception:
        await update.message.reply_text("❌ <b>Invalid format.</b> Use <code>YYYY-MM-DD YYYY-MM-DD</code>.\n\nExample: <code>2025-01-15 2025-01-20</code>", parse_mode="HTML")
        return DND_EDIT_DATES
    entry = context.user_data["edit_entry"]
    db = context.user_data.get('db')
    dnd_log_id = entry['dnd_log_id']
    db.update_dnd_entry_to_cache(dnd_log_id, new_start_date=start, new_end_date=end)
    _record_pending(context, 'edit', {'dnd_log_id': dnd_log_id, 'new_start_date': start, 'new_end_date': end})
    await update.message.reply_text(f"✅ <b>Dates updated to <i>{start}</i> → <i>{end}</i>.</b>\n\nTime travel successful!", parse_mode="HTML")
    class FakeQuery:
        def __init__(self, message):
            self.from_user = message.from_user
            self.edit_message_text = message.reply_text
    fake_query = FakeQuery(update.message)
    return await show_dnd_list(fake_query, context)

# --- PATCH: handle_confirmation (add DND) ---
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("[handle_confirmation] called")
    print("[handle_confirmation] called")
    query = update.callback_query
    await query.answer()
    action = query.data
    logger.debug(f"[handle_confirmation] action={action}")
    print(f"[handle_confirmation] action={action}")
    if action == "cancel_dnd":
        await query.edit_message_text("❌ <b>DND setup cancelled.</b>\n\nCommitment issues? It's okay, we all have them.", parse_mode="HTML")
        return ConversationHandler.END
    elif action == "edit_start":
        await query.edit_message_text(
            "📅 <b>Please enter the new start date in YYYY-MM-DD format:</b>\n\nExample: <code>2025-01-15</code>",
            parse_mode="HTML"
        )
        return DATE_INPUT
    elif action == "edit_end":
        await query.edit_message_text(
            "📅 <b>Please enter the new end date in YYYY-MM-DD format:</b>\n\nExample: <code>2025-01-20</code>",
            parse_mode="HTML"
        )
        return DATE_INPUT
    elif action == "confirm_dnd":
        user = query.from_user
        user_id = user.id
        username = user.username or user.first_name
        start_date = context.user_data["start_date"]
        end_date = context.user_data["end_date"]
        habits = context.user_data["habits"]
        selected_habits = context.user_data["selected_habits"]
        db = context.user_data.get('db')
        success_count = 0
        current_month = datetime.now().strftime("%Y%m")
        for habit_idx in selected_habits:
            habit = habits[habit_idx - 1]
            db.add_dnd_period_to_cache(current_month, username, user_id, habit["habit_id"], habit["habit_text"], start_date, end_date)
            _record_pending(context, 'add', {
                'year_month': current_month,
                'username': username,
                'user_id': user_id,
                'habit_id': habit["habit_id"],
                'habit_text': habit["habit_text"],
                'start_date': start_date,
                'end_date': end_date
            })
            success_count += 1
        await _apply_pending_dnd_changes(context)
        await query.edit_message_text(
            f"✅ <b>DND periods added successfully!</b>\n\n"
            f"📅 <b>Period:</b> <i>{start_date}</i> to <i>{end_date}</i>\n"
            f"✅ <b>{success_count} habit(s) excluded from check-ins.</b>\n\n"
            "Congratulations, you are now officially unavailable. Your future self thanks you! 🎉",
            parse_mode="HTML"
        )
        return ConversationHandler.END

# --- END: DND DB I/O MINIMIZATION PATCH --- 

# Add the missing show_dnd_list handler from the original dnd_db.py
async def show_dnd_list(query, context):
    logger.debug("[show_dnd_list] called")
    print("[show_dnd_list] called")
    user = query.from_user
    user_id = user.id
    db = context.user_data.get('db')
    user_entries = db.get_dnd_entries_for_user(user_id)
    logger.debug(f"[show_dnd_list] user_id={user_id}, entries={user_entries}")
    print(f"[show_dnd_list] user_id={user_id}, entries={user_entries}")
    if not user_entries:
        await query.edit_message_text("🛡️ <b>No DND entries found.</b>\n\nYou have not set any Do Not Disturb periods yet.", parse_mode="HTML")
        return DND_EDIT_CONTINUE
    lines = ["🛡️ <b>Your DND entries:</b>"]
    for idx, entry in enumerate(user_entries, 1):
        habit = entry.get("habit_text", "?")
        start = entry.get("start_date", "?")
        end = entry.get("end_date", "?")
        lines.append(f"{idx}. <i>{habit}</i>: <b>{start}</b> → <b>{end}</b> 💤")
    keyboard = []
    edit_buttons = []
    for idx in range(len(user_entries)):
        emoji_numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        btn_emoji = emoji_numbers[idx] if idx < len(emoji_numbers) else str(idx+1)
        edit_buttons.append(InlineKeyboardButton(f"✏️ Edit {btn_emoji}", callback_data=f"dndedit|{idx}"))
    keyboard.append(edit_buttons)
    keyboard.append([
        InlineKeyboardButton("🏁 Done", callback_data="dnd_done"),
        InlineKeyboardButton("⬅️ Back", callback_data="dndedit_action|back")
    ])
    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return DND_EDIT_SELECT

# Add the missing dnd_edit_select handler from the original dnd_db.py
async def dnd_edit_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("[dnd_edit_select] called")
    print("[dnd_edit_select] called")
    query = update.callback_query
    await query.answer()
    _, idx = query.data.split("|")
    idx = int(idx)
    user_id = query.from_user.id
    db = context.user_data.get('db')
    user_entries = db.get_dnd_entries_for_user(user_id)
    logger.debug(f"[dnd_edit_select] idx={idx}, user_id={user_id}, entries={user_entries}")
    print(f"[dnd_edit_select] idx={idx}, user_id={user_id}, entries={user_entries}")
    if idx >= len(user_entries):
        await query.edit_message_text("❌ <b>Entry not found.</b>\n\nDid you just time travel? Try again!", parse_mode="HTML")
        return await show_dnd_list(query, context)
    entry = user_entries[idx]
    context.user_data["edit_idx"] = idx
    context.user_data["edit_entry"] = entry
    habit = entry.get("habit_text", "?")
    start = entry.get("start_date", "?")
    end = entry.get("end_date", "?")
    keyboard = [
        [
            InlineKeyboardButton("✏️ Change Habit", callback_data="dndedit_action|habit"),
            InlineKeyboardButton("✏️ Edit Dates", callback_data="dndedit_action|dates")
        ],
        [
            InlineKeyboardButton("🗑️ Delete", callback_data="dndedit_action|delete"),
            InlineKeyboardButton("⬅️ Back", callback_data="dndedit_action|back")
        ]
    ]
    await query.edit_message_text(
        f"🛠️ <b>What would you like to do with this entry?</b>\n<i>{habit}</i>: <b>{start}</b> → <b>{end}</b> 💤",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return DND_EDIT_ACTION

# Add the missing start_add_dnd_flow handler from the original dnd_db.py
async def start_add_dnd_flow(query, context):
    logger.debug("[start_add_dnd_flow] called")
    print("[start_add_dnd_flow] called")
    user = query.from_user
    user_id = user.id
    username = user.username or user.first_name
    db = context.user_data.get('db')
    current_month = datetime.now().strftime("%Y%m")
    habits = db.get_user_habits_for_month(user_id, current_month)
    logger.debug(f"[start_add_dnd_flow] user_id={user_id},year_mo={current_month}, habits={habits}")
    print(f"[start_add_dnd_flow] user_id={user_id}, habits={habits}")
    if not habits:
        await query.edit_message_text(
            "⚠️ <b>No habits found for this month.</b>\n\nSet your core habits first to use DND.",
            parse_mode="HTML"
        )
        return ConversationHandler.END
    context.user_data["habits"] = habits
    context.user_data["selected_habits"] = []
    habits_text = "\n".join([f"• <i>{habit['habit_text']}</i>" for habit in habits])
    emoji_numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    habit_buttons = [InlineKeyboardButton(emoji_numbers[i], callback_data=f"habit_select|{i+1}") for i in range(len(habits))]
    keyboard = [habit_buttons]
    keyboard.append([InlineKeyboardButton("🌈 All", callback_data="habit_select|all")])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="habit_select|cancel")])
    await query.edit_message_text(
        f"🎯 <b>Your core habits for {datetime.now().strftime('%B %Y')}:</b>\n\n"
        f"{habits_text}\n\n"
        "Select habits to set DND:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return HABIT_SELECTION

# Add the missing handle_habit_selection handler from the original dnd_db.py
async def handle_habit_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("[handle_habit_selection] called")
    print("[handle_habit_selection] called")
    query = update.callback_query
    await query.answer()
    _, selection = query.data.split("|")
    logger.debug(f"[handle_habit_selection] selection={selection}")
    print(f"[handle_habit_selection] selection={selection}")
    if selection == "cancel":
        await query.edit_message_text("❌ <b>DND setup cancelled.</b>\n\nThat was quick. Maybe next time!", parse_mode="HTML")
        return ConversationHandler.END
    habits = context.user_data["habits"]
    selected_habits = context.user_data.get("selected_habits", [])
    if selection == "all":
        selected_habits = list(range(1, len(habits) + 1))
    else:
        habit_num = int(selection)
        if habit_num in selected_habits:
            selected_habits.remove(habit_num)
        else:
            selected_habits.append(habit_num)
    context.user_data["selected_habits"] = selected_habits
    if not selected_habits:
        await query.edit_message_text("❌ <b>Please select at least one habit.</b>\n\nZero is not a number here!", parse_mode="HTML")
        return ConversationHandler.END
    selected_habits_text = "\n".join([f"• <i>{habits[i-1]['habit_text']}</i>" for i in selected_habits])
    await query.edit_message_text(
        f"✅ <b>Selected habits:</b>\n\n{selected_habits_text}\n\n"
        "📅 <b>Please enter the start date and end date in YYYY-MM-DD format.</b>\n\n"
        "Example: <code>2025-01-15 2025-01-20</code>\n\n"
        "(No, you can't pick your birthday. Unless you really want to.)",
        parse_mode="HTML"
    )
    return DATE_INPUT

# Add the missing handle_date_input handler from the original dnd_db.py
async def handle_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("[handle_date_input] called")
    print("[handle_date_input] called")
    user = update.message.from_user
    date_input = update.message.text.strip()
    logger.debug(f"[handle_date_input] user_id={user.id}, date_input={date_input}")
    print(f"[handle_date_input] user_id={user.id}, date_input={date_input}")
    try:
        dates = date_input.split()
        if len(dates) != 2:
            await update.message.reply_text(
                "❌ <b>Please enter exactly two dates separated by space.</b>\n\nExample: <code>2025-01-15 2025-01-20</code>",
                parse_mode="HTML"
            )
            return DATE_INPUT
        start_date_str, end_date_str = dates
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        if start_date > end_date:
            await update.message.reply_text("❌ <b>Start date cannot be after end date.</b>\n\nEven Marty McFly couldn't pull that off.", parse_mode="HTML")
            return DATE_INPUT
    except ValueError:
        await update.message.reply_text(
            "❌ <b>Invalid date format.</b> Please use <code>YYYY-MM-DD</code> format.\n\nExample: <code>2025-01-15 2025-01-20</code>",
            parse_mode="HTML"
        )
        return DATE_INPUT
    context.user_data["start_date"] = start_date_str
    context.user_data["end_date"] = end_date_str
    start_display = format_date_display(start_date_str)
    end_display = format_date_display(end_date_str)
    days_diff = calculate_days_difference(start_date_str, end_date_str)
    habits = context.user_data["habits"]
    selected_habits = context.user_data["selected_habits"]
    selected_habits_text = "\n".join([f"• <i>{habits[i-1]['habit_text']}</i>" for i in selected_habits])
    keyboard = [
        [InlineKeyboardButton("Confirm", callback_data="confirm_dnd")],
        [InlineKeyboardButton("Edit Start", callback_data="edit_start"), InlineKeyboardButton("Edit End", callback_data="edit_end")],
        [InlineKeyboardButton("Cancel", callback_data="cancel_dnd")]
    ]
    await update.message.reply_text(
        f"📅 <b>DND Period:</b> <i>{start_display}</i> to <i>{end_display}</i> ({days_diff} days)\n\n"
        f"For the following habits:\n{selected_habits_text}\n\n"
        "If you mess this up, don't worry, you can edit it later. Or just blame the bot. 🤷‍♂️",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return CONFIRMATION

# Ensure ConversationHandler uses the patched handler functions

dnd_db_v2_handler = ConversationHandler(
    entry_points=[CommandHandler("dnd", dnd_command)],
    states={
        DND_LIST: [CallbackQueryHandler(dnd_list_entrypoint, pattern="^dnd_(add|edit|done)$")],
        DND_EDIT_SELECT: [
            CallbackQueryHandler(dnd_edit_select, pattern="^dndedit\\|\\d+$"),
            CallbackQueryHandler(dnd_list_entrypoint, pattern="^dnd_done$")
        ],
        DND_EDIT_ACTION: [CallbackQueryHandler(dnd_edit_action, pattern="^dndedit_action\\|.*$")],
        DND_EDIT_HABIT: [CallbackQueryHandler(dnd_edit_habit, pattern="^dndedithabit\\|\\d+$")],
        DND_EDIT_DATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, dnd_edit_dates)],
        HABIT_SELECTION: [CallbackQueryHandler(handle_habit_selection, pattern="^habit_select\\|")],
        DATE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date_input)],
        CONFIRMATION: [CallbackQueryHandler(handle_confirmation, pattern="^(confirm_dnd|edit_start|edit_end|cancel_dnd)$")],
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
) 