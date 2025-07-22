# main.py
# NOTE: Do not run this file directly. Use run_bot.py as the entry point.

# Standard library imports
import os
import asyncio
import warnings
import traceback

# Third-party imports
import nest_asyncio
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler
)
from telegram.error import NetworkError, TimedOut, RetryAfter
from telegram import BotCommand

# Local imports
from handlers.register import register_handler
from handlers.sethabits import set_habits_db_handler
from handlers.checkin import checkin_db_handler
from handlers.dnd import dnd_db_v2_handler
# Use the DB-backed scheduler
from scheduler import launch_scheduler
from utils.logger import get_logger
from utils.cached_db import DbCache

# Suppress PTBUserWarning about per_message settings - must be done before importing telegram
warnings.filterwarnings("ignore", category=UserWarning, module="telegram.ext._conversationhandler")
warnings.filterwarnings("ignore", message="If 'per_message=False', 'CallbackQueryHandler' will not be tracked")

# Initialize logger
logger = get_logger("main")

# Try to use centralized config, fallback to direct loading
try:
    from utils.config import BOT_TOKEN
except ImportError:
    if os.path.exists(".env"):
        from dotenv import load_dotenv
        load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")

nest_asyncio.apply()

async def setup_bot_commands(application):
    """
    Set up the bot commands menu to show available commands.
    """
    commands = [
        BotCommand("register", "Register your profile and set your details"),
        BotCommand("sethabits", "Set your core habits for the month"),
        BotCommand("checkin", "Check in your daily habits progress"),
        BotCommand("dnd", "Manage your Do Not Disturb periods")
    ]
    
    try:
        await application.bot.set_my_commands(commands)
        logger.story("✅ Bot commands menu set up successfully")
    except Exception as e:
        logger.error(f"❌ Failed to set up bot commands menu: {e}")

async def error_handler(update, context):
    """
    Handle errors that occur during bot operation.
    """
    # Log the error
    logger.error(f"❌ Error occurred: {context.error}")

    # Import SheetsError here to avoid circular import
    try:
        from utils.exceptions import SheetsError
    except ImportError:
        SheetsError = None

    # Handle specific network errors
    if isinstance(context.error, (NetworkError, TimedOut)):
        logger.error(f"🌐 Network error detected: {context.error}")
        # Inform user about network issues
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "🌐 The bot is having trouble connecting to Telegram. Please check your internet connection or try again in a few minutes."
                )
            except Exception as e:
                logger.error(f"❌ Could not send network error message to user: {e}")
        return

    if isinstance(context.error, RetryAfter):
        logger.error(f"⏳ Rate limited, retry after {context.error.retry_after} seconds")
        # Inform user about Telegram rate limiting
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "⏳ The bot is being rate limited by Telegram. Please wait a moment and try again."
                )
            except Exception as e:
                logger.error(f"❌ Could not send rate limit message to user: {e}")
        return

    # Handle Google Sheets API errors
    if SheetsError is not None and isinstance(context.error, SheetsError):
        logger.error(f"📄 Google Sheets API error: {context.error}")
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "📄 The bot is experiencing issues with Google Sheets (data storage). Please try again later. If this persists, contact the admin."
                )
            except Exception as e:
                logger.error(f"❌ Could not send Sheets error message to user: {e}")
        return

    # For other errors, log the full traceback
    logger.error(f"📋 Full traceback:")
    traceback.print_exception(type(context.error), context.error, context.error.__traceback__)

    # Optionally send a generic error message to the user
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Sorry, something went wrong. Please try again later."
            )
        except Exception as e:
            logger.error(f"❌ Could not send error message to user: {e}")

async def clear_all_keyboard_states(app, is_startup=True):
    """
    Clear any lingering keyboard states for all users.
    This removes any text suggestions or keyboard markups that might be lingering.
    
    Args:
        app: The bot application
        is_startup: True if called during startup, False if during shutdown
    """
    try:
        from telegram import ReplyKeyboardRemove
        # Get all registered users
        users = DbCache().get_all_users()
        cleared_count = 0
        
        for user in users:
            try:
                user_id_val = user.get("user_id") or user.get("UserID")
                if user_id_val is None:
                    logger.debug(f"Skipping user with missing user_id/UserID: {user}")
                    continue
                user_id = int(user_id_val)
                # Send a silent message with ReplyKeyboardRemove to clear any lingering keyboards
                await app.bot.send_message(
                    chat_id=user_id,
                    text="",  # Empty message
                    reply_markup=ReplyKeyboardRemove(selective=False)
                )
                cleared_count += 1
            except Exception as e:
                logger.debug(f"Could not clear keyboard for user {user.get('username', user.get('Username', 'Unknown'))}: {e}")
                continue
        
        logger.story(f"\U0001f5f9 Cleared keyboard states for {cleared_count} users")
        
    except Exception as e:
        import traceback
        logger.error(f"\u274c Error clearing keyboard states: {type(e).__name__}: {e}\n{traceback.format_exc()}")

async def run_bot():
    """
    Main bot function that initializes and runs the Telegram bot.
    
    Sets up the bot application, registers all handlers, launches the scheduler,
    and starts polling for updates. Handles graceful shutdown on interruption.
    """
    # Print configuration summary once at startup
    from utils.config import print_config_summary
    print_config_summary()
    
    logger.story("🚀 Starting Habit Snake bot...")
    logger.debug(f"🔐 BOT_TOKEN = {BOT_TOKEN}")

    # Configure the application with better error handling
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(30.0)  # 30 seconds connection timeout
        .read_timeout(30.0)     # 30 seconds read timeout
        .write_timeout(30.0)    # 30 seconds write timeout
        .pool_timeout(30.0)     # 30 seconds pool timeout
        .build()
    )

    # Add error handler
    app.add_error_handler(error_handler)

    # Register handlers
    handlers = [
        register_handler,
        set_habits_db_handler,
        checkin_db_handler,
        dnd_db_v2_handler
    ]
    for handler in handlers:
        app.add_handler(handler)

    # Launch scheduler
    logger.story("🕒 Launching scheduler...")
    launch_scheduler(app)

    # Clear any lingering keyboard states for all users on startup
    await clear_all_keyboard_states(app)
    
    # Set up bot commands
    await setup_bot_commands(app)

    # Run bot with retry logic
    logger.story("📡 Bot is now listening for messages...")
    await app.initialize()
    await app.start()
    
    # Start polling with error handling
    try:
        await app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"],
            timeout=30,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30
        )
    except Exception as e:
        logger.error(f"❌ Error starting polling: {e}")
        raise

    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.story("🛑 Shutting down...")
    except Exception as e:
        logger.error(f"❌ Unexpected error in main loop: {e}")
        raise

    # Graceful shutdown
    try:
        # Clear any lingering keyboard states for all users
        await clear_all_keyboard_states(app, is_startup=False)
        
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        logger.story("✅ Bot shut down cleanly.")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")
