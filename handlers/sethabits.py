# handlers/sethabits.py
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
from datetime import datetime
from utils.sheets import add_habits

CORE, BONUS = range(2)

def start_set_habits(update: Update, context: CallbackContext):
    update.message.reply_text("🧱 Please enter 2–4 core habits (comma-separated):")
    return CORE

def get_core_habits(update: Update, context: CallbackContext):
    core = [h.strip() for h in update.message.text.split(",") if h.strip()]
    if not (2 <= len(core) <= 4):
        update.message.reply_text("❗ Enter between 2 and 4 core habits.")
        return CORE
    context.user_data['core_habits'] = core
    update.message.reply_text("✨ Now enter up to 5 bonus habits (comma-separated), or type 'skip':")
    return BONUS

def get_bonus_habits(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    bonus = [] if text.lower() == 'skip' else [h.strip() for h in text.split(",") if h.strip()]
    if len(bonus) > 5:
        update.message.reply_text("❗ Max 5 bonus habits. Try again:")
        return BONUS
    context.user_data['bonus_habits'] = bonus

    username = update.message.from_user.username or update.message.from_user.first_name
    ym = datetime.today().strftime("%Y-%m")
    add_habits(username, ym, context.user_data['core_habits'], bonus)

    update.message.reply_text("✅ Habits saved!")
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("🚫 Habit setup cancelled.")
    return ConversationHandler.END

set_habits_handler = ConversationHandler(
    entry_points=[CommandHandler('sethabits', start_set_habits)],
    states={
        CORE: [MessageHandler(Filters.text & ~Filters.command, get_core_habits)],
        BONUS: [MessageHandler(Filters.text & ~Filters.command, get_bonus_habits)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)
