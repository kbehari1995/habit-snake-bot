"""
Helper utilities for the Telegram bot.
Common functions used across different modules.
"""
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import pytz

from .constants import (
    SUPPORTED_TIMEZONES, HABIT_CATEGORIES,
    DEFAULT_HABIT_GOAL, MAX_HABITS_PER_USER
)
from .exceptions import ValidationError


def format_user_display_name(user_data: Dict[str, Any]) -> str:
    """
    Format user display name from user data.
    
    Args:
        user_data: Dictionary containing user information
        
    Returns:
        Formatted display name
    """
    nickname = user_data.get('nickname', 'Unknown')
    usermoji = user_data.get('usermoji', '')
    
    if usermoji:
        return f"{nickname} {usermoji}"
    return nickname


def parse_time_string(time_str: str) -> Optional[Any]:
    """
    Parse time string in HHMM format to datetime.time object.
    
    Args:
        time_str: Time string in HHMM format
        
    Returns:
        datetime.time object or None if invalid
    """
    if not time_str or len(time_str) != 4:
        return None
    
    try:
        hour = int(time_str[:2])
        minute = int(time_str[2:])
        
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None
            
        return datetime.time(hour, minute)
    except ValueError:
        return None


def format_time_for_display(time_obj: Any) -> str:
    """
    Format time object for display.
    
    Args:
        time_obj: datetime.time object
        
    Returns:
        Formatted time string
    """
    return time_obj.strftime("%I:%M %p")


def get_user_timezone(user_data: Dict[str, Any]) -> Optional[Any]:
    """
    Get user's timezone from user data.
    
    Args:
        user_data: Dictionary containing user information
        
    Returns:
        pytz timezone object or None if invalid
    """
    timezone_str = user_data.get('timezone')
    if not timezone_str:
        return None
    
    try:
        return pytz.timezone(timezone_str)
    except pytz.exceptions.UnknownTimeZoneError:
        return None


def convert_to_user_timezone(dt: datetime, user_timezone: Any) -> datetime:
    """
    Convert datetime to user's timezone.
    
    Args:
        dt: datetime object (assumed to be in UTC)
        user_timezone: User's timezone
        
    Returns:
        datetime in user's timezone
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.astimezone(user_timezone)


def format_date_for_display(date_str: str) -> str:
    """
    Format date string for display.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        Formatted date string
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%B %d, %Y")
    except ValueError:
        return date_str


def calculate_age(birth_date: str) -> Optional[int]:
    """
    Calculate age from birth date.
    
    Args:
        birth_date: Birth date in YYYY-MM-DD format
        
    Returns:
        Age in years or None if invalid
    """
    try:
        birth = datetime.strptime(birth_date, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth.year
        
        # Adjust if birthday hasn't occurred this year
        if today.month < birth.month or (today.month == birth.month and today.day < birth.day):
            age -= 1
            
        return age
    except ValueError:
        return None


def validate_habit_data(habit_data: Dict[str, Any]) -> List[str]:
    """
    Validate habit data and return list of errors.
    
    Args:
        habit_data: Dictionary containing habit information
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Check required fields
    required_fields = ['name', 'goal', 'category']
    for field in required_fields:
        if field not in habit_data or not habit_data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate name
    if 'name' in habit_data and habit_data['name']:
        name = habit_data['name'].strip()
        if len(name) < 2:
            errors.append("Habit name must be at least 2 characters long")
        if len(name) > 50:
            errors.append("Habit name must be less than 50 characters")
    
    # Validate goal
    if 'goal' in habit_data and habit_data['goal']:
        try:
            goal = int(habit_data['goal'])
            if goal < 1:
                errors.append("Goal must be at least 1")
            if goal > 100:
                errors.append("Goal cannot exceed 100")
        except (ValueError, TypeError):
            errors.append("Goal must be a valid number")
    
    # Validate category
    if 'category' in habit_data and habit_data['category']:
        if habit_data['category'] not in HABIT_CATEGORIES:
            errors.append(f"Invalid category. Please choose from: {', '.join(HABIT_CATEGORIES)}")
    
    return errors


def format_habit_summary(habit_data: Dict[str, Any]) -> str:
    """
    Format habit data for display.
    
    Args:
        habit_data: Dictionary containing habit information
        
    Returns:
        Formatted habit summary string
    """
    name = habit_data.get('name', 'Unknown')
    goal = habit_data.get('goal', DEFAULT_HABIT_GOAL)
    category = habit_data.get('category', 'Other')
    
    return f"📝 **{name}**\n🎯 Goal: {goal}\n📂 Category: {category}"


def create_inline_keyboard(buttons_data: List[List[Dict[str, str]]]) -> Any:
    """
    Create inline keyboard markup from button data.
    
    Args:
        buttons_data: List of button rows, each containing button dictionaries
        
    Returns:
        InlineKeyboardMarkup object
    """
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = []
        for row in buttons_data:
            keyboard_row = []
            for button in row:
                keyboard_row.append(
                    InlineKeyboardButton(
                        text=button['text'],
                        callback_data=button['callback_data']
                    )
                )
            keyboard.append(keyboard_row)
        
        return InlineKeyboardMarkup(keyboard)
    except ImportError:
        # Fallback if telegram module is not available
        return None


def extract_callback_data(callback_data: str, prefix: str) -> Optional[str]:
    """
    Extract data from callback string after prefix.
    
    Args:
        callback_data: Full callback data string
        prefix: Expected prefix
        
    Returns:
        Data after prefix or None if invalid
    """
    if not callback_data.startswith(prefix):
        return None
    
    return callback_data[len(prefix):]


def sanitize_sheet_value(value: Any) -> str:
    """
    Sanitize value for Google Sheets storage.
    
    Args:
        value: Value to sanitize
        
    Returns:
        Sanitized string value
    """
    if value is None:
        return ""
    
    # Convert to string and remove problematic characters
    str_value = str(value).strip()
    
    # Remove or replace characters that might cause issues in sheets
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str_value)
    
    return sanitized


def format_streak_display(streak_count: int) -> str:
    """
    Format streak count for display.
    
    Args:
        streak_count: Number of consecutive days
        
    Returns:
        Formatted streak string
    """
    if streak_count == 0:
        return "🔥 No streak yet"
    elif streak_count == 1:
        return "🔥 1 day streak"
    else:
        return f"🔥 {streak_count} day streak"


def get_habit_progress_emoji(completed: int, goal: int) -> str:
    """
    Get appropriate emoji for habit progress.
    
    Args:
        completed: Number of completed items
        goal: Goal number
        
    Returns:
        Progress emoji
    """
    if completed == 0:
        return "⚪"
    elif completed < goal:
        return "🟡"
    elif completed == goal:
        return "🟢"
    else:
        return "🟣"  # Bonus completion 