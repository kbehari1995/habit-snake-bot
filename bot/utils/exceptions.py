"""
Custom exceptions for the Telegram bot.
These provide better error handling and user experience.
"""

class BotError(Exception):
    """Base exception for all bot-related errors"""
    pass

class UserRegistrationError(BotError):
    """Raised when user registration fails"""
    pass

class HabitSettingError(BotError):
    """Raised when habit setting fails"""
    pass

class CheckInError(BotError):
    """Raised when check-in fails"""
    pass

class SheetsError(BotError):
    """Raised when Google Sheets operations fail"""
    pass

class ValidationError(BotError):
    """Raised when data validation fails"""
    pass

class SchemaError(BotError):
    """Raised when schema operations fail"""
    pass

class ConfigError(BotError):
    """Raised when configuration is invalid"""
    pass

class SchedulerError(BotError):
    """Raised when scheduler operations fail"""
    pass 