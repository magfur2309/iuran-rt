import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

def connect_to_gsheet(spreadsheet_name):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    return client.open(spreadsheet_name)

def load_sheet(sheet):
    records = sheet.get_all_records()
    return pd.DataFrame(records)

def save_sheet(sheet, df):
    sheet.clear()
    if not df.empty:
        df_str = df.astype(str)
        sheet.update([df_str.columns.tolist()] + df_str.values.tolist())
