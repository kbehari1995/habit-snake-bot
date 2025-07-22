"""
Utility modules package.

This package contains utility functions and classes used throughout the bot,
including configuration, logging, validation, and helper functions.
"""

from .config import (
    BOT_TOKEN, SHEET_ID, HABITS_SHEET_NAME, CREDS_JSON,
    SCHEDULER_START_HHMM, SCHEDULER_INTERVAL_HHMMSSS,
    SCHEDULER_RECHECK_MIN, SCHEDULER_AUTOMARK_HHMM,
    TIME_FOR_UPDATE, TELEGRAM_CHANNEL_ID, COLLECT_HABITS_YYYYMM,
    print_config_summary
)

from .logger import get_logger, EmojiLogger
from .exceptions import (
    BotError, UserRegistrationError, HabitSettingError,
    CheckInError, SheetsError, ValidationError, SchemaError,
    ConfigError, SchedulerError
)

__all__ = [
    # Config exports
    'BOT_TOKEN', 'SHEET_ID', 'HABITS_SHEET_NAME', 'CREDS_JSON',
    'SCHEDULER_START_HHMM', 'SCHEDULER_INTERVAL_HHMMSSS',
    'SCHEDULER_RECHECK_MIN', 'SCHEDULER_AUTOMARK_HHMM',
    'TIME_FOR_UPDATE', 'TELEGRAM_CHANNEL_ID', 'COLLECT_HABITS_YYYYMM',
    'print_config_summary',
    
    # Logger exports
    'get_logger', 'EmojiLogger',
    
    # Exception exports
    'BotError', 'UserRegistrationError', 'HabitSettingError',
    'CheckInError', 'SheetsError', 'ValidationError', 'SchemaError',
    'ConfigError', 'SchedulerError'
] 