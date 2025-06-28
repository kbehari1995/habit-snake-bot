# main.py
from telegram.ext import Updater
from handlers.sethabits import set_habits_handler

from config import BOT_TOKEN

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Register handlers
    dp.add_handler(set_habits_handler)

    print("✅ Bot running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
