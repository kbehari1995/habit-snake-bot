"""
Validation utilities for the Telegram bot.
Centralized validation functions for user inputs and data.
"""
import re
from datetime import datetime
from typing import Optional, Tuple, Union
import emoji as emoji_lib
import pytz

from .constants import (
    EMOJI_PATTERN, DATE_PATTERN, EMAIL_PATTERN,
    SUPPORTED_TIMEZONES, HABIT_CATEGORIES,
    INVALID_EMOJI_ERROR, INVALID_DATE_ERROR, INVALID_EMAIL_ERROR
)
from .exceptions import ValidationError


def validate_emoji(emoji_input: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that input is a single valid emoji.
    
    Args:
        emoji_input: The emoji string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not emoji_input or not emoji_input.strip():
        return False, "Emoji cannot be empty"
    
    emoji_input = emoji_input.strip()
    
    # Check if it's a single emoji using emoji library
    if not emoji_lib.is_emoji(emoji_input):
        return False, INVALID_EMOJI_ERROR
    
    # Additional regex check for comprehensive emoji validation
    if not EMOJI_PATTERN.match(emoji_input):
        return False, INVALID_EMOJI_ERROR
    
    return True, None


def validate_date_format(date_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validate date format (YYYY-MM-DD).
    
    Args:
        date_str: The date string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not date_str or not date_str.strip():
        return False, "Date cannot be empty"
    
    date_str = date_str.strip()
    
    # Check format
    if not DATE_PATTERN.match(date_str):
        return False, INVALID_DATE_ERROR
    
    # Check if it's a valid date
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return False, INVALID_DATE_ERROR
    
    return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email format.
    
    Args:
        email: The email string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or not email.strip():
        return True, None  # Email is optional
    
    email = email.strip()
    
    if not EMAIL_PATTERN.match(email):
        return False, INVALID_EMAIL_ERROR
    
    return True, None


def validate_timezone(timezone: str) -> Tuple[bool, Optional[str]]:
    """
    Validate timezone format and support.
    
    Args:
        timezone: The timezone string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not timezone or not timezone.strip():
        return False, "Timezone cannot be empty"
    
    timezone = timezone.strip()
    
    # Check if it's in our supported list
    if timezone not in SUPPORTED_TIMEZONES:
        return False, f"Unsupported timezone. Please choose from: {', '.join(SUPPORTED_TIMEZONES)}"
    
    # Additional pytz validation
    try:
        pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        return False, f"Invalid timezone: {timezone}"
    
    return True, None


def validate_habit_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate habit name.
    
    Args:
        name: The habit name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Habit name cannot be empty"
    
    name = name.strip()
    
    # Check length
    if len(name) < 2:
        return False, "Habit name must be at least 2 characters long"
    
    if len(name) > 50:
        return False, "Habit name must be less than 50 characters"
    
    # Check for invalid characters
    if re.search(r'[<>"\']', name):
        return False, "Habit name contains invalid characters"
    
    return True, None


def validate_habit_goal(goal: Union[str, int]) -> Tuple[bool, Optional[str]]:
    """
    Validate habit goal value.
    
    Args:
        goal: The goal value to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        goal_int = int(goal)
    except (ValueError, TypeError):
        return False, "Goal must be a valid number"
    
    if goal_int < 1:
        return False, "Goal must be at least 1"
    
    if goal_int > 100:
        return False, "Goal cannot exceed 100"
    
    return True, None


def validate_habit_category(category: str) -> Tuple[bool, Optional[str]]:
    """
    Validate habit category.
    
    Args:
        category: The category to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not category or not category.strip():
        return False, "Category cannot be empty"
    
    category = category.strip()
    
    if category not in HABIT_CATEGORIES:
        return False, f"Invalid category. Please choose from: {', '.join(HABIT_CATEGORIES)}"
    
    return True, None


def validate_nickname(nickname: str) -> Tuple[bool, Optional[str]]:
    """
    Validate user nickname.
    
    Args:
        nickname: The nickname to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not nickname or not nickname.strip():
        return False, "Nickname cannot be empty"
    
    nickname = nickname.strip()
    
    # Check length
    if len(nickname) < 1:
        return False, "Nickname must be at least 1 character long"
    
    if len(nickname) > 20:
        return False, "Nickname must be less than 20 characters"
    
    # Check for invalid characters
    if re.search(r'[<>"\']', nickname):
        return False, "Nickname contains invalid characters"
    
    return True, None


def validate_user_id(user_id: Union[str, int]) -> Tuple[bool, Optional[str]]:
    """
    Validate Telegram user ID.
    
    Args:
        user_id: The user ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        return False, "User ID must be a valid number"
    
    if user_id_int <= 0:
        return False, "User ID must be a positive number"
    
    return True, None


def validate_sheet_data(data: dict, required_fields: list) -> Tuple[bool, Optional[str]]:
    """
    Validate Google Sheets data structure.
    
    Args:
        data: The data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Data must be a dictionary"
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
        
        if data[field] is None:
            return False, f"Field {field} cannot be None"
    
    return True, None


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: The text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', text.strip())
    
    # Limit length
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
    
    return sanitized


def validate_callback_data(callback_data: str, expected_prefix: str) -> Tuple[bool, Optional[str]]:
    """
    Validate callback data format.
    
    Args:
        callback_data: The callback data to validate
        expected_prefix: The expected prefix for this callback
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not callback_data:
        return False, "Callback data cannot be empty"
    
    if not callback_data.startswith(expected_prefix):
        return False, f"Invalid callback data format. Expected prefix: {expected_prefix}"
    
    return True, None 