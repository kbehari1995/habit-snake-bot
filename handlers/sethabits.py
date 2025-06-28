from telegram import Update
from telegram.ext import (
    CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)
from datetime import datetime
from utils.sheets import add_habits

CORE, BONUS = range(2)

async def start_set_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧱 Please enter 2–4 core habits (comma-separated):")
    return CORE

async def get_core_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    core = [h.strip() for h in update.message.text.split(",") if h.strip()]
    if not (2 <= len(core) <= 4):
        await update.message.reply_text("❗ Please enter between 2 and 4 core habits.")
        return CORE
    context.user_data['core_habits'] = core
    await update.message.reply_text("✨ Now enter up to 5 bonus habits (comma-separated), or type 'skip':")
    return BONUS

async def get_bonus_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    bonus = [] if text.lower() == 'skip' else [h.strip() for h in text.split(",") if h.strip()]
    if len(bonus) > 5:
        await update.message.reply_text("❗ Max 5 bonus habits. Try again:")
        return BONUS
    context.user_data['bonus_habits'] = bonus

    username = update.message.from_user.username or update.message.from_user.first_name
    year_month = datetime.today().strftime("%Y-%m")

    add_habits(username, year_month, context.user_data['core_habits'], bonus)
    await update.message.reply_text("✅ Habits saved successfully!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Habit setup cancelled.")
    return ConversationHandler.END

set_habits_handler = ConversationHandler(
    entry_points=[CommandHandler("sethabits", start_set_habits)],
    states={
        CORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_core_habits)],
        BONUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bonus_habits)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
