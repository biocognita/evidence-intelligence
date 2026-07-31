import pandas as pd
from config import SPREADSHEET_ID, CLAIM_DATABASE_GID

def load_claim_database():
    csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={CLAIM_DATABASE_GID}"
    data = pd.read_csv(csv_url)
    data.columns = data.columns.str.strip()
    return data