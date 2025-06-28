# main.py
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from handlers.sethabits import set_habits_handler

# Load .env only if available (for local dev)
if os.path.exists(".env"):
    load_dotenv()

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register all command/conv handlers
    app.add_handler(set_habits_handler)

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
