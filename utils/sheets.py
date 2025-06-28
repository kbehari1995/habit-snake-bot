# utils/sheets.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import SHEET_ID, HABITS_SHEET_NAME

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(HABITS_SHEET_NAME)

def add_habits(username, year_month, core_habits, bonus_habits):
    row = [username, year_month] + core_habits + [""] * (4 - len(core_habits)) + bonus_habits + [""] * (5 - len(bonus_habits))
    sheet.append_row(row)
