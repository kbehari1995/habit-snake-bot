# utils/sheets.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from dotenv import load_dotenv

# Load .env only if running locally
if os.path.exists(".env"):
    load_dotenv()

# Environment variables
SHEET_ID = os.getenv("SHEET_ID")
HABITS_SHEET_NAME = os.getenv("HABITS_SHEET_NAME")
CREDS_JSON = os.getenv("CREDS_JSON")

# Set up credentials using dict (from Replit secret or .env)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(CREDS_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Target sheet
sheet = client.open_by_key(SHEET_ID).worksheet(HABITS_SHEET_NAME)

def add_habits(username, year_month, core_habits, bonus_habits):
    row = [username, year_month] + core_habits + [""] * (4 - len(core_habits)) + bonus_habits + [""] * (5 - len(bonus_habits))
    sheet.append_row(row)
