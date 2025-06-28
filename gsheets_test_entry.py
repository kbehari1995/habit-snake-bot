import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1pShshf-q3D329ObcSOIRHiLxpO2VPKwEHzjnUj0mxy8").sheet1
sheet.append_row(["2025-06-28", "kunj", "Meditation", "✅"])

