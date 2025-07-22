import os
import asyncio
import matplotlib.pyplot as plt
from telegram.ext import ApplicationBuilder

# Kunj's Telegram user ID
KUNJ_USER_ID = 7601874368

# Load the bot token from environment or config
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    try:
        from bot.utils.config import BOT_TOKEN as CONFIG_BOT_TOKEN
        BOT_TOKEN = CONFIG_BOT_TOKEN
    except ImportError:
        raise RuntimeError("BOT_TOKEN not found in environment or config.")

IMAGE_PATH = "sample_plot.png"

# Generate and save a sample matplotlib plot
def create_sample_plot(path):
    plt.figure(figsize=(6, 4))
    x = [1, 2, 3, 4, 5, 6, 7, 8,9,10]
    y = [1, 1, 1, 1, 1, 1,-1,-2,1, 1]
    plt.plot(x, y, marker='o', color='royalblue')
    plt.title("Snake Growth")
    plt.xlabel("Streak Day")
    plt.ylabel("Snake Score")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

async def send_graph_and_message():
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )
    await app.initialize()
    await app.start()
    try:
        # Send a text message first
        await app.bot.send_message(chat_id=KUNJ_USER_ID, text="Here is a sample matplotlib graph! 📊")
        # Then send the image
        with open(IMAGE_PATH, "rb") as img_file:
            await app.bot.send_photo(chat_id=KUNJ_USER_ID, photo=img_file, caption="Sample graph below.")
        print(f"✅ Message and image sent to Kunj (user_id={KUNJ_USER_ID})")
    finally:
        await app.stop()
        await app.shutdown()

async def main():
    create_sample_plot(IMAGE_PATH)
    print(f"✅ Sample plot saved to {IMAGE_PATH}")
    await send_graph_and_message()

if __name__ == "__main__":
    asyncio.run(main()) 