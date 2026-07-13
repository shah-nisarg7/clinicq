import gspread
import os

SERVICE_ACCOUNT_FILE = os.environ.get("GSHEET_SERVICE_ACCOUNT_JSON", "service_account.json") #getting google cloud service account details
SPREADSHEET_NAME = os.environ.get("GSHEET_SPREADSHEET_NAME", "Clinic_Queue_MVP")#locating the google sheet (shared to that service account)

GSPREAD_SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


COL_ID              = 0   
COL_NAME            = 1   
COL_PHONE           = 2 
COL_DATE            = 3  
COL_SCHEDULED       = 4   
COL_STATUS          = 5   
COL_CONSULT_START   = 6   
COL_LAST_MSG_ETA    = 7   
#headers will be same for all sheets (different clinics) theyll automatically appear once a new clinic logs in.
HEADER_ROW = [
    "ID", "Patient_Name", "Phone", "Scheduled_Date", "Scheduled_Time",
    "Status", "Consult_Start_Time", "Last_Messaged_ETA"   
]

VALID_STATUSES = {"Scheduled", "Waiting", "In Consult", "Completed", "Skipped"}



def get_gspread_client():

    return gspread.service_account(filename=SERVICE_ACCOUNT_FILE)

def get_or_create_clinic_worksheet(client, clinic_id: str):
    #actually opens and creates the new spreadsheet (or opens if already present..)
    spreadsheet = client.open(SPREADSHEET_NAME)

    try:
        worksheet = spreadsheet.worksheet(clinic_id)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=clinic_id, rows="500", cols=str(len(HEADER_ROW))
        )
        worksheet.append_row(HEADER_ROW, value_input_option="USER_ENTERED")
        print(f"[DB] Created new worksheet for {clinic_id}")

    return worksheet


def fetch_all_patients(worksheet) -> list[dict]:
    #reads all the new patient rows and returns them as dicts, skips the header row (not to be counted)
    all_rows = worksheet.get_all_values()

    if not all_rows or len(all_rows) < 2:
        return []  

    patients = []
    for sheet_row_idx, row in enumerate(all_rows[1:], start=2):  
        while len(row) < len(HEADER_ROW):
            row.append("")

        patient = {field: row[i] for i, field in enumerate(HEADER_ROW)}
        patient["_row_index"] = sheet_row_idx  

        if patient["ID"]:
            patients.append(patient)

    return patients

def fetch_active_queue(worksheet) -> list[dict]:
    #returns the active queue patients only.
    all_p = fetch_all_patients(worksheet)
    active = [p for p in all_p if p["Status"] not in ("Completed",)]
    active.sort(key=lambda p: int(p["ID"]))
    return active


def get_next_patient_id(worksheet) -> int:
    #to determine the auto incrementing token (ID) assigned to everypatient row

    all_p = fetch_all_patients(worksheet)
    if not all_p:
        return 1
    return max(int(p["ID"]) for p in all_p) + 1

def add_patient(
        worksheet,
        name: str,
        phone: str,
        scheduled_date: str, 
        scheduled_time: str,

)-> dict:
    
    new_id = get_next_patient_id(worksheet)

    new_patient_row=[
        str(new_id),
        name,
        phone,
        scheduled_date, 
        scheduled_time,
        "Scheduled",
        "", #consult start time placeholder
        "", # last msgd ETA placeholder
    ]

    worksheet.append_row(new_patient_row,value_input_option="USER_ENTERED")
    print(f"[DB] Added patient {name} (ID ={new_id}) at slot {scheduled_time}")

    new_patient = {field: new_patient_row[i] for i, field in enumerate(HEADER_ROW)}
    return new_patient


def update_patient_status(
        worksheet,
        patient: dict,
        new_status: str,
        extra_fields: dict = None
):
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{new_status}' . Must be one of {VALID_STATUSES}")


    row_idx = patient["_row_index"]

    worksheet.update_cell(row_idx,COL_STATUS +1,new_status)

    if extra_fields:
        header_to_col = {h: i+1 for i, h in enumerate(HEADER_ROW)}
        for field, value in extra_fields.items():
            if field in header_to_col:
                worksheet.update_cell(row_idx,header_to_col[field],str(value))

    print(f"[DB] PATIENT ID = {patient['ID']} status -> {new_status}")

#new login/register logic to create new spreadsheet, also added a test login with name CLINIC_001 
def authenticate_clinic(client, clinic_id: str, password: str) -> bool:
    spreadsheet = client.open(SPREADSHEET_NAME)
    try:
        auth_sheet = spreadsheet.worksheet("System_Auth")
    except gspread.exceptions.WorksheetNotFound:
        # Auto create the auth table if it doesnt exist
        auth_sheet = spreadsheet.add_worksheet("System_Auth", rows="100", cols="2")
        auth_sheet.append_row(["Clinic_ID", "Password"])
        auth_sheet.append_row(["CLINIC_001", "admin123"])
        print("[DB] Created System_Auth tab with default credentials.")
        return clinic_id == "CLINIC_001" and password == "admin123"

    records = auth_sheet.get_all_records()
    for row in records:
        if str(row.get("Clinic_ID", "")).strip().upper() == clinic_id:
            if str(row.get("Password", "")).strip() == password:
                return True
    return False


def register_new_clinic(client, clinic_id: str, password: str):
    spreadsheet = client.open(SPREADSHEET_NAME)
    auth_sheet = spreadsheet.worksheet("System_Auth")
    
    # Check if clinic ID already exists
    records = auth_sheet.get_all_records()
    if any(str(row.get("Clinic_ID", "")).strip().upper() == clinic_id for row in records):
        raise ValueError("Clinic ID already exists.")
        
    auth_sheet.append_row([clinic_id, password])

    