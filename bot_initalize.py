from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv

# Load .env only locally
if os.path.exists(".env"):
    load_dotenv()

# Securely get environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Simple /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I’m your first bot 🐣")

# Build and run the bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
