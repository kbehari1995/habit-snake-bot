import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
from dotenv import load_dotenv

# Load environment variables (skip if already injected by Replit)
if os.path.exists(".env"):
    load_dotenv()

# Load variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
HABITS_SHEET_NAME = os.getenv("HABITS_SHEET_NAME")
CRED_JSON = os.getenv("CRED_JSON")

# Convert the JSON string to a dict and authorize
creds_dict = json.loads(CRED_JSON)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Access the worksheet
sheet = client.open_by_key(SHEET_ID).worksheet(HABITS_SHEET_NAME)

# Test append
sheet.append_row(["2025-07-28", "kunj", "Meditation", "✅"])
