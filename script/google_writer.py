import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
from config import SPREADSHEET_ID


# Connect to Google
def connect_sheet():

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    BASE_DIR = Path(__file__).resolve().parent.parent
    KEY_PATH = BASE_DIR / "credentials" / "google_key.json"

    credentials = Credentials.from_service_account_file(
        KEY_PATH,
        scopes=scopes
    )

    client = gspread.authorize(credentials)

    return client


# Open spreadsheet
def open_spreadsheet():

    client = connect_sheet()

    spreadsheet = client.open_by_key(
        SPREADSHEET_ID
    )

    print("Spreadsheet opened successfully")

    return spreadsheet


# Get specific tab
def get_worksheet(sheet_name):

    spreadsheet = open_spreadsheet()

    worksheet = spreadsheet.worksheet(sheet_name)

    return worksheet


# Read data
def read_sheet(sheet_name):

    worksheet = get_worksheet(sheet_name)

    data = worksheet.get_all_records()

    return data


# Test
if __name__ == "__main__":

    print("Connecting...")

    data = read_sheet("Claim Database")

    print(data[:3])