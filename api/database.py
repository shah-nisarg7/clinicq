import gspread
import os
from datetime import datetime 
import hashlib 
import json
SERVICE_ACCOUNT_FILE = os.environ.get("GSHEET_SERVICE_ACCOUNT_JSON", "service_account.json") #getting google cloud service account details
SPREADSHEET_NAME = os.environ.get("GSHEET_SPREADSHEET_NAME", "Clinic_Queue_MVP")#locating the google sheet (shared to that service account)

GSPREAD_SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
    
#column indexes 
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
    "ID", 
    "Patient_Name", 
    "Phone", 
    "Scheduled_Date", 
    "Scheduled_Time", 
    "Status", 
    "Consult_Start_Time", 
    "Last_ETA",   
    "Is_Walk_In",      
    "Notification_Status"
]    
    
VALID_STATUSES = {"Scheduled", "Waiting", "In Consult", "Completed", "Skipped"}
 #which status change acc makes sense in a real clinic (not really imp here its only if someone calls api directly..)
 #but still adding it (bcs atleast im testing thru calling api directly in powershell)
VALID_TRANSITIONS = {
    "Scheduled" : {"Waiting":"Skipped"},
    "Waiting": {"In Consult","Skipped"},
    "In Consult": {"Completed"},
    "Completed":set(),#after this evenn in terminal it wont let u switch directly from scheduled to completed etc
    "Skipped":set(),
}

VALID_DOCTOR_STATUSES = {"Arrived","Not Arrived"}
               
def is_valid_phone(phone:str)-> bool:
    #not adding strict rules bcs there are various formats of numbers
    #with + , brackets, spaces etc       
    #mostly digits is a resasonable check...
    digits_only = "".join(c for c in phone if c.isdigit())
    return len(digits_only) >= 7 and len(digits_only) <= 15    
        
def get_gspread_client():
    #on vercel theres no actual file , so the whole service account
    #json gets pasted into an env var .. locally we just use the file
    #like before since thats easier for  me while building...
    service_account_env = os.environ.get("GSHEET_SERVICE_ACCOUNT_JSON_CONTENT")
           
    if service_account_env:
        creds_dict = json.loads(service_account_env)
        return gspread.service_account_from_dict(creds_dict)      

    return gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
def get_or_create_clinic_worksheet(client, clinic_id):     
    # each clinic gets its own worksheet tab ,named after their clinic id 

    try:          
        ws = client.open("Clinic_Queue_MVP").worksheet(clinic_id)      
        return ws   
    except gspread.exceptions.WorksheetNotFound:
        ws = client.open("Clinic_Queue_MVP").add_worksheet(title=clinic_id, rows="1000", cols="20")
        headers = ["ID", "Patient_Name", "Phone", "Scheduled_Date", "Scheduled_Time", "Status", "Consult_Start_Time", "Last_ETA", "Is_Walk_In", "Notification_Status"]
        ws.append_row(headers)
        return ws

     
def fetch_all_patients(worksheet) -> list[dict]:
    #reads all the new patient rows and returns them as dicts, skips the header row (bcs its not to be counted)
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
    #returns the active queue patients only
    all_p = fetch_all_patients(worksheet)
    active = [p for p in all_p if p["Status"] not in ("Completed",)]
    active.sort(key=lambda p: int(p["ID"]))
    return active
    

def get_next_patient_id(worksheet) -> int:
    #to determine the auto incrementing token (ID) assigned to everypatient row                    
    #just doing max + 1 instead len+1 so gaps from deleted rows dont cause dupes
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
    is_walk_in: bool = False
) -> dict:


    if not is_valid_phone(phone):
        raise ValueError(f"{phone} doesnt look like a valid phone no.")
    new_id = get_next_patient_id(worksheet)
    
    new_patient_row=[   
        str(new_id),            
        name,     
        phone,
        scheduled_date,    
        scheduled_time,
        "Scheduled",
        "", # consult start time placeholder
        "", # last msgd ETA placeholder
        str(is_walk_in), # Walk in flag
        "Pending"        # Notification status
    ]
         
    worksheet.append_row(new_patient_row, value_input_option="USER_ENTERED")
    print(f"[DB] Added patient {name} (ID ={new_id}) at slot {scheduled_time}")
    
    new_patient = {field: new_patient_row[i] for i, field in enumerate(HEADER_ROW)}
    return new_patient

#changing patient status based on their current state (like in consult , waiting etc...)
def update_patient_status(
        worksheet,
        patient: dict,
        new_status: str,    
        extra_fields: dict = None
):          
    if new_status not in VALID_STATUSES:    
        raise ValueError(f"Invalid status '{new_status}' . Must be one of {VALID_STATUSES}")    
        
    current_status = patient["Status"]       
    allowed_next = VALID_TRANSITIONS.get(current_status, set())
    #ig this can only happen if someone changes the google sheet directly (or some glitch ig) but just added it for prevention
    if new_status not in allowed_next:
        raise ValueError(f"Cant go from '{current_status}' to '{new_status}', thats not a real transition")
     
    row_idx  = patient["_row_index"]
    #only touching the status cell here, extra_fields (below) handles the rest 
    worksheet.update_cell(row_idx,COL_STATUS +1,new_status)

    if extra_fields:
        header_to_col = {h: i+1 for i, h in enumerate(HEADER_ROW)}
        for field, value in extra_fields.items():
            if field in header_to_col:
                worksheet.update_cell(row_idx,header_to_col[field],str(value))

    print(f"[DB] PATIENT ID = {patient['ID']} status -> {new_status}")

         
def hash_password(password:str)-> str:
    #simple hash    
    #adding this bcs rn passwords are saved raw in public google sheet (if ever leaked it could cause problem..)
    return hashlib.sha256(password.encode()).hexdigest()



#new login/register logic to create new spreadsheet, also added a test login with name CLINIC_001 
def _get_auth_sheet(spreadsheet):
    # shared by login + register so neither one crashes on a brand new spreadsheet
    try:
        return spreadsheet.worksheet("System_Auth"), False
    except gspread.exceptions.WorksheetNotFound:
        auth_sheet = spreadsheet.add_worksheet("System_Auth", rows="100", cols="2")
        auth_sheet.append_row(["Clinic_ID", "Password"])
        auth_sheet.append_row(["CLINIC_001", hash_password("admin123")])
        print("[DB] Created System_Auth tab with default credentials.")
        return auth_sheet, True
    #returning just_created so authentication knows to check 
    #against the hardcoded default set instead of the sheet (which is emptyy)

def _get_settings_sheet(spreadsheet):
    #seperate tab that tracks doctor status + delay per clinic , same idea as system_auth (passwords and all) 
    try:
        return spreadsheet.worksheet("Clinic_Settings")
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet("Clinic_Settings", rows = "100",cols = "3")
        sheet.append_row(["Clinic_ID", "Doctor_Status", "Delay_Minutes"])
        return sheet 


def get_clinic_settings(client,clinic_id:str)-> dict:
    spreadsheet = client.open(SPREADSHEET_NAME)
    sheet = _get_settings_sheet(spreadsheet)
    records = sheet.get_all_records()        

    for row in records:
        if str(row.get("Clinic_ID", "")).strip().upper() == clinic_id:
            return{
                "doctor_status" : row.get("Doctor_Status","Not Arrived"),
                "delay_minutes" : row.get("Delay_Minutes",0)
            }
    
    #no row for a clinic yet, so creating one with defaults
    sheet.append_row([clinic_id,"Not Arrived","0"])   
    return { "doctor_status": "Not Arrived", "delay_minutes" : 0}
   
                 
def update_clinic_settings (client,clinic_id:str,doctor_status:str = None, delay_minutes = None):
    if doctor_status is not None and doctor_status not in VALID_DOCTOR_STATUSES:
        raise ValueError(f"Invalid doctor_status '{doctor_status}'. Must be one of {VALID_DOCTOR_STATUSES}")

    if delay_minutes is not None:
        try:
            delay_minutes = int(delay_minutes)
        except (ValueError, TypeError):    
            raise ValueError("delay_minutes must be a number")
        if delay_minutes < 0:    
            raise ValueError("delay_minutes cant be negative")

    spreadsheet = client.open(SPREADSHEET_NAME)
    sheet = _get_settings_sheet(spreadsheet)
    records = sheet.get_all_records()

    row_idx = None
    for i, row in enumerate(records,start = 2): #starting w 2 bcs first row is headers
        if str(row.get("Clinic_ID","")).strip().upper() == clinic_id:
            row_idx = i
            break        
         
    if row_idx is None:
        sheet.append_row([clinic_id,"Not Arrived","0"])
        row_idx = len(records) + 2

    if doctor_status is not None:
        sheet.update_cell(row_idx,2,doctor_status)

    if delay_minutes is not None:
        sheet.update_cell(row_idx,3,str(delay_minutes))
    
                
def find_patient_by_id(worksheet,patient_id:str):         
    #need this for the queue actions (call to room, mark done etc)
    #since frontend only sends us the patient id not their row number in the sheet
    all_p = fetch_all_patients(worksheet)
    for p in all_p:     
        if str(p["ID"]) == str(patient_id):    
            return p       
    return None     
     
def _get_notification_log_sheet(spreadsheet):            
    #logs what msgs wouldve gone out, but doesnt acc send anything    
    try:
        return spreadsheet.worksheet("Notification_Log")
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet("Notification_Log",rows = "1000",cols = "6")
        sheet.append_row(["Clinic_ID", "Patient_Name", "Phone","Message", "Trigger", "Timestamp"])
        return sheet     
     

def log_notification(client,clinic_id,patient_name,phone,message,trigger):
    spreadsheet = client.open(SPREADSHEET_NAME)
    sheet = _get_notification_log_sheet(spreadsheet)   
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([clinic_id, patient_name, phone, message, trigger, timestamp], value_input_option="USER_ENTERED")
      

def get_recent_notifications(client,clinic_id,limit = 20):
    spreadsheet = client.open(SPREADSHEET_NAME)               
    sheet = _get_notification_log_sheet(spreadsheet)    
    records = sheet.get_all_records()
    clinic_logs = [r for r in records if str(r.get("Clinic_ID","")).strip().upper()== clinic_id]
    clinic_logs.reverse() #puttingi the neweset one first
    return clinic_logs[:limit]
  
def build_booking_message(clinic_id, patient_name, scheduled_time, is_walk_in):
    if is_walk_in:
        return (f"Hi {patient_name}, you've been added to the queue at {clinic_id} as a walk-in. "
                f"We'll message you with updates as your turn gets closer.")
    return (f"Hi {patient_name}, your appointment at {clinic_id} is confirmed for {scheduled_time}. "
            f"We'll message you with updates as your turn gets closer.")
                            


def build_queue_update_message(clinic_id, patient_name, people_ahead):
    if people_ahead <= 3:
        return (f"Hi {patient_name}, only {people_ahead} people are ahead of you at {clinic_id}. "
                f"Please start heading back to the clinic, you'll be seen soon.")
    return (f"Hi {patient_name}, you're {people_ahead} people away from your turn at {clinic_id}. "
            f"You still have some time, feel free to step out and come back.")
              
def check_queue_notifications(client, clinic_id, worksheet):
    #after any status change, see if anyone crossed the 5-ahead or 3-ahead
    #mark and log what wouldve been sent to them. reuses Notification_Status
    #so we dont log the same threshold twice for the same patient
    patients = fetch_active_queue(worksheet)   
    #indx here doubles as people_head since waiting list is already in queue order 
    waiting = [p for p in patients if p["Status"] == "Waiting"]

    for idx, p in enumerate(waiting):                      
        people_ahead = idx     
        notif_status = p.get("Notification_Status", "Pending")        

        if people_ahead <= 3 and notif_status != "3_ahead_sent":
            msg = build_queue_update_message(clinic_id, p["Patient_Name"], people_ahead)
            log_notification(client, clinic_id, p["Patient_Name"], p["Phone"], msg, "3_people_ahead")
            _set_notification_flag(worksheet, p, "3_ahead_sent")

        elif people_ahead <= 5 and notif_status == "Pending":
            msg = build_queue_update_message(clinic_id, p["Patient_Name"], people_ahead)
            log_notification(client, clinic_id, p["Patient_Name"], p["Phone"], msg, "5_people_ahead")
            _set_notification_flag(worksheet, p, "5_ahead_sent")
            
             
def _set_notification_flag(worksheet, patient, value):
    row_idx = patient["_row_index"]
    header_to_col = {h: i + 1 for i, h in enumerate(HEADER_ROW)}
    worksheet.update_cell(row_idx, header_to_col["Notification_Status"], value)                
      
def authenticate_clinic(client, clinic_id: str, password: str) -> bool:
    spreadsheet = client.open(SPREADSHEET_NAME)
    auth_sheet, just_created = _get_auth_sheet(spreadsheet)        
    if just_created:    
        return clinic_id == "CLINIC_001" and password == "admin123"

    hashed_input = hash_password(password)
    records = auth_sheet.get_all_records()    
    for row in records:    
        if str(row.get("Clinic_ID", "")).strip().upper() == clinic_id:
            if str(row.get("Password", "")).strip() == hashed_input:
                return True
    return False
              
     
def register_new_clinic(client, clinic_id: str, password: str):
    spreadsheet = client.open(SPREADSHEET_NAME)    
    auth_sheet, _ = _get_auth_sheet(spreadsheet)

    # Check if clinic ID already exists             
    records = auth_sheet.get_all_records()
    if any(str(row.get("Clinic_ID", "")).strip().upper() == clinic_id for row in records):
        raise ValueError("Clinic ID already exists.")            

    auth_sheet.append_row([clinic_id, hash_password(password)]) 

