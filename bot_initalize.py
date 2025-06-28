from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I’m your first bot 🐣")

app = ApplicationBuilder().token("8159556087:AAEXRFmt3jtJ4KFkTUXGym-XBXScEAN-2Ts").build()
app.add_handler(CommandHandler("start", start))

app.run_polling()
