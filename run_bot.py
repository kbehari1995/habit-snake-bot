#!/usr/bin/env python3
"""
Entry point script to run the Telegram bot.
This script runs the bot from the new bot/ directory structure.
"""
import sys
import os

# Add the bot directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

# from bot.utils.config import initialize_schema_system
# initialize_schema_system()

# Import and run the bot
import main
import asyncio

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main.run_bot()) 
    