# 🐍 Habit Snake Bot

A gamified Telegram bot for habit tracking, streak protection, bonus tasks, and community accountability.

## 🚀 Features

- ✅ **Daily Habit Check-ins**: Track your daily habits with a simple check-in system
- ⭐ **Bonus Habit Logging**: Log additional habits beyond your daily goals
- 🛡️ **Streak Protection**: Use shields, freeze days, and gifting to protect your streaks
- 📊 **Leaderboard Tracking**: Real-time leaderboards via Google Sheets integration
- 💬 **Mood Journaling**: Daily prompts for mood tracking and reflection
- 🧾 **Admin Dashboard**: Comprehensive admin tools through Google Sheets
- 🔄 **Profile Management**: Edit your profile and habits anytime

## 🛠 Tech Stack

- **Python 3.11+**
- **python-telegram-bot** (v20.6) - Telegram Bot API wrapper
- **Google Sheets API** - Data storage and leaderboards
- **APScheduler** - Task scheduling for daily reminders
- **Replit** - Hosting and deployment platform

## 📋 Prerequisites

Before setting up the bot, you'll need:

1. **Telegram Bot Token**: Create a bot via [@BotFather](https://t.me/botfather)
2. **Google Sheets API**: Set up Google Cloud Project and enable Sheets API
3. **Service Account**: Create a service account with Sheets API access
4. **Python 3.11+**: Ensure Python is installed on your system

## 🧪 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/kbehari1995/habit-snake-bot.git
cd habit-snake-bot
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv env311

# Activate virtual environment
# On Windows:
env311\Scripts\activate
# On macOS/Linux:
source env311/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the root directory:

```env
# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_FILE=path/to/your/service-account-key.json
SPREADSHEET_ID=your_google_spreadsheet_id_here

# Bot Settings
ADMIN_USER_ID=your_telegram_user_id_here
```

### 5. Google Sheets Setup

1. Create a new Google Spreadsheet
2. Share it with your service account email (with edit permissions)
3. Copy the spreadsheet ID from the URL
4. Update your `.env` file with the spreadsheet ID

### 6. Run the Bot

```bash
python run_bot.py
```

## 📁 Project Structure

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
├── PROJECT_ORGANIZATION.md       # Organization guide
└── .env                         # Environment variables (not in repo)
```

## 🎮 Usage

### For Users

1. **Start the bot**: Send `/start` to begin
2. **Register**: Use `/register` to create your profile
3. **Set habits**: Use `/sethabits` to configure your daily habits
4. **Daily check-in**: Use `/checkin` to log your daily progress
5. **Edit profile**: Use the edit button in your profile to modify settings

### For Admins

- Access the Google Sheets dashboard for user management
- Monitor leaderboards and user statistics
- Manage bot settings through the spreadsheet

## 🔧 Configuration

### Environment Variables

This project uses environment variables for configuration. **Never commit your `.env` file or secrets to the repository.**

Set these variables in a `.env` file (for local use) or in Replit's Secrets UI (for Replit deployment):

| Variable                       | Description                                 | Required | Example/Default                |
|--------------------------------|---------------------------------------------|----------|-------------------------------|
| `BOT_TOKEN`                    | Telegram bot token from @BotFather          | Yes      | `123456:ABC-DEF...`           |
| `GOOGLE_SHEETS_CREDENTIALS_FILE` | Path to Google service account JSON         | Yes      | `creds.json`                  |
| `SPREADSHEET_ID`               | Google Sheets spreadsheet ID                 | Yes      | `1A2B3C4D5E6F...`             |
| `ADMIN_USER_ID`                | Your Telegram user ID (for admin access)     | Yes      | `123456789`                   |
| ...                            | ... (add any other variables you use)        |          |                               |

- For local development, create a `.env` file in the project root with the above variables.
- For Replit, use the Secrets UI to add each variable (no `.env` file needed).
- `.env` is already in `.gitignore` and will not be committed.

### Google Sheets Structure

The bot expects the following columns in your spreadsheet:
- User ID, Username, First Name, Last Name
- Registration Date, Last Check-in
- Habit 1-5 names and completion status
- Streak counts and protection items

## 🚀 Deployment

### Replit Deployment

1. Fork this repository to your GitHub account
2. Create a new Replit project
3. Connect your GitHub repository
4. Set environment variables in Replit secrets
5. Run the bot using `python run_bot.py`

### Local Deployment

1. Follow the setup instructions above
2. Use a process manager like `pm2` or `systemd`
3. Set up a reverse proxy if needed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues:

1. Check the [Issues](https://github.com/kbehari1995/habit-snake-bot/issues) page
2. Create a new issue with detailed information
3. Include error logs and steps to reproduce

## 🔄 Changelog

### Recent Updates
- **Code Organization**: Reorganized imports and improved file structure
- **Centralized Constants**: Created `constants.py` for all application constants
- **Validation Utilities**: Added `validation.py` for centralized input validation
- **Helper Functions**: Created `helpers.py` for common utility functions
- **Package Structure**: Added proper `__init__.py` files for Python packages
- **Documentation**: Created comprehensive organization guide
- **Configuration**: Enhanced environment variable management with validation
- **Error Handling**: Improved exception handling and logging consistency

### Technical Improvements
- Standardized import organization (stdlib → third-party → local)
- Added type hints throughout the codebase
- Centralized message templates and error messages
- Improved code reusability and maintainability
- Enhanced configuration validation and error reporting


