# 🏗️ Project Organization Guide

This document outlines the organizational improvements made to the Habit Snake Bot project.

## 📁 Improved Project Structure

```
telegram_bot_project/
├── bot/                           # Main bot code
│   ├── handlers/                  # Bot command handlers
│   │   ├── __init__.py           # Handler initialization
│   │   ├── register.py           # User registration and profile management
│   │   ├── checkin.py            # Daily check-in functionality
│   │   ├── sethabits.py          # Habit configuration
│   │   └── dnd.py                # Do Not Disturb management
│   ├── utils/                     # Utility modules
│   │   ├── __init__.py           # Utils initialization
│   │   ├── config.py             # Configuration management
│   │   ├── constants.py          # Centralized constants
│   │   ├── validation.py         # Input validation utilities
│   │   ├── helpers.py            # Common helper functions
│   │   ├── logger.py             # Logging system
│   │   ├── exceptions.py         # Custom exceptions
│   │   ├── sheets.py             # Google Sheets integration
│   │   ├── sheets_schema.py      # Schema management
│   │   └── streaks.py            # Streak calculation logic
│   ├── main.py                   # Bot initialization and main loop
│   └── scheduler.py              # Task scheduling
├── schemas/                       # JSON schema files
│   ├── sheets.json               # Google Sheets schema
│   └── validation_rules.json     # Validation rules
├── logs/                         # Application logs
├── run_bot.py                    # Entry point script
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
├── PROJECT_ORGANIZATION.md       # This file
└── .env                         # Environment variables (not in repo)
```

## 🔧 Code Organization Improvements

### 1. Import Organization

**Before:**
```python
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="telegram.ext._conversationhandler")
import os
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram.error import NetworkError, TimedOut, RetryAfter
from telegram import BotCommand
from handlers.sethabits import set_habits_handler
from handlers.register import register_handler
from handlers.checkin import checkin_handler
from handlers.dnd import dnd_handler
from scheduler import launch_scheduler
from utils.logger import get_logger
```

**After:**
```python
# Standard library imports
import os
import asyncio
import warnings
import traceback

# Third-party imports
import nest_asyncio
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler
)
from telegram.error import NetworkError, TimedOut, RetryAfter
from telegram import BotCommand

# Local imports
from handlers.sethabits import set_habits_handler
from handlers.register import register_handler
from handlers.checkin import checkin_handler
from handlers.dnd import dnd_handler
from scheduler import launch_scheduler
from utils.logger import get_logger

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="telegram.ext._conversationhandler")
warnings.filterwarnings("ignore", message="If 'per_message=False', 'CallbackQueryHandler' will not be tracked")
```

### 2. Centralized Constants

**New File: `bot/utils/constants.py`**
- All conversation states
- Validation patterns
- Supported values (timezones, categories)
- Message templates
- Callback data prefixes
- Sheet column indices
- Default values
- Logging constants
- Scheduler constants

### 3. Validation Utilities

**New File: `bot/utils/validation.py`**
- Input validation functions
- Consistent error messages
- Type hints for better IDE support
- Centralized validation logic

### 4. Helper Functions

**New File: `bot/utils/helpers.py`**
- Common utility functions
- Data formatting helpers
- Keyboard creation utilities
- Timezone handling
- Data sanitization

## 📋 Coding Standards

### 1. File Headers

Every Python file should start with:
```python
"""
Brief description of the module.

Longer description if needed.
"""
```

### 2. Function Documentation

Use consistent docstring format:
```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of what the function does.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When and why this exception is raised
    """
```

### 3. Import Organization

Follow this order:
1. Standard library imports
2. Third-party imports
3. Local imports
4. Import-related configurations (warnings, etc.)

### 4. Error Handling

Use consistent error handling patterns:
```python
try:
    # Operation that might fail
    result = some_operation()
except SpecificException as e:
    logger.error(f"Specific error occurred: {e}")
    # Handle specific error
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle general error
```

### 5. Logging

Use the centralized logger:
```python
from utils.logger import get_logger

logger = get_logger("module_name")

# Use appropriate log levels
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error")
```

## 🚀 Configuration Management

### Environment Variables

All configuration should be in `.env` file:
```env
# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here

# Google Sheets Configuration
SHEET_ID=your_google_spreadsheet_id_here
HABITS_SHEET_NAME=Habits
CREDS_JSON=your_credentials_json_here

# Scheduler Configuration
SCHEDULER_START_HHMM=0900
SCHEDULER_INTERVAL_HHMMSSS=0030000
SCHEDULER_RECHECK_MIN=60
SCHEDULER_AUTOMARK_HHMM=1200
TIME_FOR_UPDATE=1400

# Telegram Configuration
TELEGRAM_CHANNEL_ID=0

# Habits Configuration
COLLECT_HABITS_YYYYMM=

# Schema Configuration
SHEETS_SCHEMA_FILE=schemas/sheets.json
VALIDATION_RULES_FILE=schemas/validation_rules.json
```

### Configuration Validation

The `config.py` module validates all environment variables on startup and provides meaningful error messages.

## 🔍 Validation Standards

### Input Validation

Use the centralized validation functions:
```python
from utils.validation import validate_emoji, validate_date_format

# Validate user input
is_valid, error_msg = validate_emoji(user_input)
if not is_valid:
    await update.message.reply_text(error_msg)
    return CURRENT_STATE
```

### Data Sanitization

Always sanitize user input:
```python
from utils.validation import sanitize_input

clean_input = sanitize_input(user_input)
```

## 📝 Message Templates

Use constants for consistent messaging:
```python
from utils.constants import (
    WELCOME_MESSAGE, INVALID_EMOJI_ERROR, REGISTRATION_SUCCESS
)

await update.message.reply_text(WELCOME_MESSAGE)
```

## 🎯 Best Practices

### 1. Separation of Concerns
- Keep handlers focused on user interaction
- Move business logic to utility functions
- Use separate modules for different functionalities

### 2. Error Handling
- Always handle exceptions gracefully
- Provide meaningful error messages to users
- Log errors for debugging

### 3. Code Reusability
- Extract common functionality into utility functions
- Use constants for repeated values
- Create helper functions for common operations

### 4. Type Hints
- Use type hints for better IDE support
- Document parameter and return types
- Use `Optional` and `Union` where appropriate

### 5. Testing
- Write unit tests for utility functions
- Test validation functions thoroughly
- Mock external dependencies

## 🔄 Migration Guide

### For Existing Code

1. **Update Imports**: Reorganize imports according to the new standard
2. **Use Constants**: Replace hardcoded values with constants from `constants.py`
3. **Add Validation**: Use validation functions from `validation.py`
4. **Improve Logging**: Use the centralized logger
5. **Add Type Hints**: Add type annotations to function signatures

### Example Migration

**Before:**
```python
async def get_usermoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emoji_input = update.message.text.strip()
    if not emoji_lib.is_emoji(emoji_input):
        await update.message.reply_text("❗ Please enter a single valid emoji.")
        return USERMOJI
```

**After:**
```python
from utils.validation import validate_emoji
from utils.constants import INVALID_EMOJI_ERROR

async def get_usermoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emoji_input = update.message.text.strip()
    is_valid, error_msg = validate_emoji(emoji_input)
    if not is_valid:
        await update.message.reply_text(error_msg)
        return USERMOJI
```

## 📊 Benefits of Organization

1. **Maintainability**: Easier to find and modify code
2. **Consistency**: Uniform patterns across the codebase
3. **Reusability**: Common functions can be shared
4. **Testing**: Better structure for unit tests
5. **Documentation**: Clear organization makes code self-documenting
6. **Scalability**: Easier to add new features
7. **Debugging**: Better error handling and logging

## 🎯 Next Steps

1. Apply these standards to all existing files
2. Add comprehensive unit tests
3. Create API documentation
4. Set up automated code quality checks
5. Implement continuous integration 