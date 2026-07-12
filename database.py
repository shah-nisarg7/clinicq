import gspread
from oauth2client.service_account import ServiceAccountCredentials 
import os

#configuring everything

SERVICE_ACCOUNT_FILE = os.environ.get("GSHEET_SERVICE_ACCOUNT_JSON","service_account.json")
SPREADSHEET_NAME = os.environ.get("GSHEET_SPREADSHEET_NAME", "Clinic_Queue_MVP")

GSPREAD_SCOPES = [

    'https://spreadhseets.google.com/feeds'
    'https://www.googleapis.com/auth/drive'
]

#defining colums of spreadsheet

COL_ID = 0
COL_NAME = 1
COL_PHONE = 2
COL_SCHEDULED = 3
COL_STATUS = 4
COL_CONSULT_START = 5
COL_LAST_MSG_ETA = 6

HEADER_ROW = ["ID","Patient_Name", "Phone","Scheduled_Time","Status","Consult_Start_Time", "Last_Messaged_ETA"]


VALID_STATUSES = {"Scheduled","Waiting", "In Consult", "Completed","Skipped"} # What all status a patient meeting can have

# Connecting Google Sheets (using google cloud servcives)

def get_gspread_client():
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_FILE, GSPREAD_SCOPES
    )
    return gspread.authorize(creds)


def get_or_create_clinic_worksheet(client,clinic_id:str):

    spreadsheet = client.open(SPREADSHEET_NAME)

    try:
        worksheet = spreadsheet.worksheet(clinic_id)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title= clinic_id, rows = "500", cols = str(len(HEADER_ROW)))
        worksheet.append_row(HEADER_ROW,value_input_options= "USER_ENTERED")
        print(f"[DB] Created new worksheet for {clinic_id}")

        return worksheet   
