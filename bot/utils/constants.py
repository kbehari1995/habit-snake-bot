"""
Constants used throughout the Telegram bot project.
Centralized location for all application constants.
"""
import re

# =============================================================================
# CONVERSATION STATES
# =============================================================================

# Registration conversation states
NAME, USERMOJI, DOB, TIMEZONE, EMAIL, CONFIRM = range(6)

# Habit setting conversation states
HABIT_SELECTION, HABIT_NAME, HABIT_GOAL, HABIT_CONFIRM = range(4)

# Check-in conversation states
CHECKIN_SELECTION, CHECKIN_CONFIRM = range(2)

# DND conversation states
DND_START, DND_END, DND_CONFIRM = range(3)

# =============================================================================
# VALIDATION PATTERNS
# =============================================================================

# Emoji pattern for validation
EMOJI_PATTERN = re.compile(
    r'[\U0001F1E6-\U0001F1FF'   # flags
    r'\U0001F300-\U0001F5FF'   # symbols & pictographs
    r'\U0001F600-\U0001F64F'   # emoticons
    r'\U0001F680-\U0001F6FF'   # transport & map symbols
    r'\U0001F700-\U0001F77F'   # alchemical symbols
    r'\U00002300-\U000023FF'   # misc technical (includes ⏰)
    r'\U00002600-\U000026FF'   # dingbats/sun/moon/weather
    r'\U00002700-\U000027BF'   # additional dingbats
    r'\U0001F900-\U0001F9FF'   # supplemental symbols
    r'\U0001FA70-\U0001FAFF'   # symbols & pictographs extended-A
    r'] ?$',
    flags=re.UNICODE
)

# Date format pattern
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')

# Email pattern
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# =============================================================================
# SUPPORTED VALUES
# =============================================================================

# Supported timezones
SUPPORTED_TIMEZONES = [
    "Asia/Kolkata",
    "Asia/Dubai", 
    "Asia/Singapore"
]

# Supported habit categories
HABIT_CATEGORIES = [
    "Health & Fitness",
    "Productivity",
    "Learning",
    "Mindfulness",
    "Social",
    "Other"
]

# =============================================================================
# MESSAGE TEMPLATES
# =============================================================================

# Welcome and registration messages
WELCOME_MESSAGE = "👋 Welcome! What are your initials/shortest nickname? This will be used in displaying scores."
EMOJI_PROMPT = "🧡 What emoji would you like to represent you? (Only one emoji)"
DOB_PROMPT = "🗓️ What's your Date of Birth? Please enter in YYYY-MM-DD format"
TIMEZONE_PROMPT = "⏰ Finally, what's your timezone?"
EMAIL_PROMPT = "📧 Enter your email address (optional):"

# Error messages
INVALID_EMOJI_ERROR = "❗ Please enter a single valid emoji."
INVALID_DATE_ERROR = "❗ Invalid format. Please enter your DOB as YYYY-MM-DD (e.g., 1990-12-31)"
INVALID_EMAIL_ERROR = "❗ Please enter a valid email address."
GENERIC_ERROR = "❌ Sorry, something went wrong. Please try again later."

# Success messages
REGISTRATION_SUCCESS = "✅ Registration successful! Use /sethabits to set your habits"
PROFILE_UPDATE_SUCCESS = "✅ Your details were updated successfully. Use /sethabits to set your habits"

# =============================================================================
# CALLBACK DATA PREFIXES
# =============================================================================

# Registration callbacks
REG_CALLBACK_PREFIX = "rr|"
TIMEZONE_CALLBACK_PREFIX = "tz|"
EDIT_CALLBACK_PREFIX = "go|"

# Habit callbacks
HABIT_CALLBACK_PREFIX = "habit|"
CATEGORY_CALLBACK_PREFIX = "cat|"

# Check-in callbacks
CHECKIN_CALLBACK_PREFIX = "checkin|"

# DND callbacks
DND_CALLBACK_PREFIX = "dnd|"

# =============================================================================
# SHEET COLUMN INDICES
# =============================================================================

# User sheet columns
USER_ID_COL = 0
USERNAME_COL = 1
FIRST_NAME_COL = 2
NICKNAME_COL = 3
USERMOJI_COL = 4
DOB_COL = 5
TIMEZONE_COL = 6
EMAIL_COL = 7
REGISTRATION_DATE_COL = 8
LAST_CHECKIN_COL = 9

# =============================================================================
# DEFAULT VALUES
# =============================================================================

# Default habit settings
DEFAULT_HABIT_GOAL = 1
MAX_HABITS_PER_USER = 5
DEFAULT_STREAK_COUNT = 0

# Default timeouts (in seconds)
DEFAULT_TIMEOUT = 30
DEFAULT_POLLING_TIMEOUT = 30

# =============================================================================
# LOGGING CONSTANTS
# =============================================================================

# Log levels
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"

# Log file patterns
LOG_FILE_PATTERN = "{name}_{date}.log"
LOG_DATE_FORMAT = "%Y-%m-%d"

# =============================================================================
# SCHEDULER CONSTANTS
# =============================================================================

# Default scheduler times
DEFAULT_SCHEDULER_START = "0900"
DEFAULT_SCHEDULER_INTERVAL = "0030000"
DEFAULT_AUTOMARK_TIME = "1200"
DEFAULT_UPDATE_TIME = "1400"

# Scheduler intervals (in minutes)
DEFAULT_RECHECK_INTERVAL = 60
MIN_RECHECK_INTERVAL = 5
MAX_RECHECK_INTERVAL = 1440  # 24 hours 