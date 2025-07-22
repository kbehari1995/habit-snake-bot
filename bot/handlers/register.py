import warnings
warnings.filterwarnings("ignore", message="If 'per_message=False', 'CallbackQueryHandler' will not be tracked")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, MessageHandler, ConversationHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from bot.utils.cached_db import DbCache
import pytz
from datetime import datetime
import emoji as emoji_lib
from utils.logger import get_logger

dbCache = DbCache()

# Initialize logger
logger = get_logger("register_db")

NAME, USERMOJI, DOB, TIMEZONE, EMAIL, CONFIRM = range(6)

async def start_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print("DEBUG: Entered start_register handler")
        user = update.message.from_user
        print(f"DEBUG: User: {user.id} - {user.username}")
        dbCache.refresh_cache()
        existing_user = dbCache.get_user_by_id(user.id)
        if existing_user:
            logger.info(f"User {user.id} already registered. Showing details.")
            # Show current details and edit profile button
            text = (
                "🤔 Hmm? You're already registered!\n\n"
                "🧱 Your current details are:\n\n"
                f"1. *Nickname*: {existing_user.get('nickname', '')}\n"
                f"2. *UserMoji*: {existing_user.get('user_moji', '')}\n"
                f"3. *DOB*: {existing_user.get('dob', '')}\n"
                f"4. *Timezone*: {existing_user.get('timezone', '')}\n"
                f"5. *Email*: {existing_user.get('email', 'Not set')}"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Edit Profile", callback_data="go|edit")]
            ])
            await update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            print("DEBUG: Exiting start_register: user already registered.")
            return ConversationHandler.END

        context.user_data['db'] = dbCache
        print(f"DEBUG: User {user.id} not registered. Asking for nickname.")
        await update.message.reply_text("👋 Welcome! What are your initials/shortest nickname? This will be used in displaying scores.")
        return NAME
    except Exception as e:
        print(f"EXCEPTION in start_register: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

async def start_edit_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("DEBUG: Entered start_edit_flow handler")
    user = update.callback_query.from_user
    print(f"DEBUG: User: {user.id} - {user.username}")
    dbCache.refresh_cache()
    record = dbCache.get_user_by_id(user.id)
    if not record:
        logger.info(f"User {user.id} not found in DB during edit flow.")
        await update.callback_query.edit_message_text("⚠️ You don't seem to be registered yet. Try /register first.")
        print("DEBUG: Exiting start_edit_flow: user not registered.")
        return ConversationHandler.END

    context.user_data.update({
        "name": record.get("nickname", ""),
        "usermoji": record.get("user_moji", ""),
        "dob": record.get("dob", ""),
        "timezone": record.get("timezone", ""),
        "email": record.get("email", ""),
        "edit_mode": True,
        "db": dbCache
    })
    print(f"DEBUG: User {user.id} entering edit mode with data: {context.user_data}")
    return await show_summary(update, context)

async def show_summary(update, context):
    print("DEBUG: Entered show_summary handler")
    u = context.user_data
    print(f"DEBUG: Current user_data: {u}")
    text = (
        "🧱 Your current details are:\n\n"
        f"1. *Nickname*: {u['name']}\n"
        f"2. *UserMoji*: {u['usermoji']}\n"
        f"3. *DOB*: {u['dob']}\n"
        f"4. *Timezone*: {u['timezone']}\n"
        f"5. *Email*: {u.get('email', 'Not set')}"
    )
    buttons = [
        [InlineKeyboardButton("✅ Confirm", callback_data="rr|confirm")],
        [InlineKeyboardButton("1", callback_data="rr|edit|name"), InlineKeyboardButton("2", callback_data="rr|edit|usermoji"), InlineKeyboardButton("3", callback_data="rr|edit|dob"), InlineKeyboardButton("4", callback_data="rr|edit|timezone"), InlineKeyboardButton("5", callback_data="rr|edit|email")],
        [InlineKeyboardButton("❌ Cancel", callback_data="rr|cancel")]
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
    print("DEBUG: Exiting show_summary handler")
    return CONFIRM

async def confirm_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("DEBUG: Entered confirm_router handler")
    query = update.callback_query
    await query.answer()
    action = query.data.split("|")
    print(f"DEBUG: Action: {action}")
    db = context.user_data.get('db', dbCache)
    if action[1] == "confirm":
        user = query.from_user
        logger.info(f"User {user.id} confirming details: {context.user_data}")
        # Update user in db
        success = db.update_user(
            user_id=user.id,
            nickname=context.user_data["name"],
            user_moji=context.user_data["usermoji"],
            dob=context.user_data["dob"],
            timezone=context.user_data["timezone"],
            email=context.user_data.get("email", "")
        )
        if success:
            logger.info(f"User {user.id} updated successfully.")
            await query.edit_message_text("✅ Your details were updated successfully. Use /sethabits to set your habits")
        else:
            logger.warning(f"User {user.id} update failed: not registered.")
            await query.edit_message_text("⚠️ You don't seem to be registered yet. Try /register first.")
        print("DEBUG: Exiting confirm_router after confirm action.")
        return ConversationHandler.END
    elif action[1] == "cancel":
        logger.info(f"User {query.from_user.id} cancelled update.")
        await query.edit_message_text("🚫 Update cancelled.")
        print("DEBUG: Exiting confirm_router after cancel action.")
        return ConversationHandler.END
    elif action[1] == "edit":
        field = action[2]
        print(f"DEBUG: User {query.from_user.id} editing field: {field}")
        if field == "name":
            await query.edit_message_text("✏️ Enter your updated nickname:")
            return NAME
        elif field == "usermoji":
            await query.edit_message_text("🧡 What emoji would you like to represent you? (Only one emoji)")
            return USERMOJI
        elif field == "dob":
            await query.edit_message_text("🗓️ What's your Date of Birth? Please enter in YYYY-MM-DD format")
            return DOB
        elif field == "timezone":
            tz_buttons = [
                [InlineKeyboardButton("Asia/Kolkata", callback_data="tz|Asia/Kolkata")],
                [InlineKeyboardButton("Asia/Dubai", callback_data="tz|Asia/Dubai")],
                [InlineKeyboardButton("Asia/Singapore", callback_data="tz|Asia/Singapore")]
            ]
            await query.edit_message_text("⏰ Select your timezone:", reply_markup=InlineKeyboardMarkup(tz_buttons))
            return TIMEZONE
        elif field == "email":
            await query.edit_message_text("📧 Enter your email address:")
            return EMAIL
    print("DEBUG: Exiting confirm_router handler")
    return CONFIRM

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("DEBUG: Entered get_name handler")
    context.user_data["name"] = update.message.text.strip()
    print(f"DEBUG: User {update.message.from_user.id} set name: {context.user_data['name']}")
    if 'edit_mode' in context.user_data:
        print("DEBUG: In edit mode, showing summary.")
        return await show_summary(update, context)
    await update.message.reply_text("🧡 What emoji would you like to represent you? (Only one emoji)")
    print("DEBUG: Exiting get_name handler")
    return USERMOJI

async def get_usermoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("DEBUG: Entered get_usermoji handler")
    emoji_input = update.message.text.strip()
    if not emoji_lib.is_emoji(emoji_input):
        logger.warning(f"User {update.message.from_user.id} entered invalid emoji: {emoji_input}")
        await update.message.reply_text("❗ Please enter a single valid emoji.")
        return USERMOJI
    context.user_data["usermoji"] = emoji_input
    print(f"DEBUG: User {update.message.from_user.id} set usermoji: {emoji_input}")
    if 'edit_mode' in context.user_data:
        print("DEBUG: In edit mode, showing summary.")
        return await show_summary(update, context)
    await update.message.reply_text("🗓️ What's your Date of Birth? Please enter in YYYY-MM-DD format")
    print("DEBUG: Exiting get_usermoji handler")
    return DOB

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("DEBUG: Entered get_dob handler")
    dob = update.message.text.strip()
    try:
        datetime.strptime(dob, "%Y-%m-%d")
    except ValueError:
        logger.warning(f"User {update.message.from_user.id} entered invalid DOB: {dob}")
        await update.message.reply_text("❗ Invalid format. Please enter your DOB as YYYY-MM-DD (e.g., 1990-12-31)")
        return DOB
    context.user_data["dob"] = datetime.strptime(dob, "%Y-%m-%d")
    print(f"DEBUG: User {update.message.from_user.id} set dob: {dob}")
    if 'edit_mode' in context.user_data:
        print("DEBUG: In edit mode, showing summary.")
        return await show_summary(update, context)
    tz_buttons = [
        [InlineKeyboardButton("Asia/Kolkata", callback_data="tz|Asia/Kolkata")],
        [InlineKeyboardButton("Asia/Dubai", callback_data="tz|Asia/Dubai")],
        [InlineKeyboardButton("Asia/Singapore", callback_data="tz|Asia/Singapore")]
    ]
    await update.message.reply_text("⏰ Select your timezone:", reply_markup=InlineKeyboardMarkup(tz_buttons))
    print("DEBUG: Exiting get_dob handler")
    return TIMEZONE

async def get_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("DEBUG: Entered get_timezone handler")
    query = update.callback_query
    tz = query.data.split("|")[1]
    context.user_data["timezone"] = tz
    print(f"DEBUG: User {query.from_user.id} set timezone: {tz}")
    if 'edit_mode' in context.user_data:
        print("DEBUG: In edit mode, showing summary.")
        return await show_summary(update, context)
    await query.edit_message_text("📧 Enter your email address:")
    print("DEBUG: Exiting get_timezone handler")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("DEBUG: Entered get_email handler")
    email = update.message.text.strip()
    context.user_data["email"] = email
    print(f"DEBUG: User {update.message.from_user.id} set email: {email}")
    if 'edit_mode' in context.user_data:
        print("DEBUG: In edit mode, showing summary.")
        return await show_summary(update, context)
    # Add user to db
    user = update.message.from_user
    db = context.user_data.get('db', dbCache)
    logger.info(f"Registering new user: {user.id} - {user.username} - {context.user_data}")
    # 1. Add user to the database (persistent)
    await db.add_user_to_db(
        user_id=user.id,
        username=user.username or user.first_name,
        nickname=context.user_data["name"],
        user_moji=context.user_data["usermoji"],
        dob=context.user_data["dob"],
        timezone=context.user_data["timezone"],
        email=context.user_data["email"]
    )
    # 2. Refresh the cache from the DB
    DbCache.refresh_cache()
    # 3. (Optional) Add to in-memory cache for immediate access
    db.add_user(
        user_id=user.id,
        username=user.username or user.first_name,
        nickname=context.user_data["name"],
        user_moji=context.user_data["usermoji"],
        dob=context.user_data["dob"],
        timezone=context.user_data["timezone"],
        email=context.user_data["email"]
    )
    logger.info(f"👤 New user registered: @{user.username or user.first_name} ({context.user_data['name']})")
    await update.message.reply_text("✅ You are registered. Use /sethabits to set your habits")
    print("DEBUG: Exiting get_email handler")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("DEBUG: Entered cancel handler")
    if update.callback_query:
        await update.callback_query.edit_message_text("🚫 Registration cancelled.")
    else:
        await update.message.reply_text("🚫 Registration cancelled.")
    logger.info(f"User cancelled registration: {getattr(update.effective_user, 'id', None)}")
    print("DEBUG: Exiting cancel handler")
    return ConversationHandler.END

register_handler = ConversationHandler(
    entry_points=[CommandHandler("register", start_register)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        USERMOJI: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_usermoji)],
        DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)],
        TIMEZONE: [CallbackQueryHandler(get_timezone, pattern="^tz\|.*")],
        EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        CONFIRM: [CallbackQueryHandler(confirm_router, pattern="^rr\|.*")],
    },
    fallbacks=[CommandHandler("cancel", cancel), CallbackQueryHandler(cancel, pattern="^rr\|cancel")],
    allow_reentry=True
) 