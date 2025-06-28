# main.py
from telegram.ext import Updater
from handlers.sethabits import set_habits_handler
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SHEET_ID = os.getenv("SHEET_ID")


def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Register handlers
    #dp.add_handler(set_habits_handler)

    print("✅ Bot running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
