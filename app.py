import streamlit as st
import database as db
from datetime import datetime
import os

#Title and layout of page
st.set_page_config(
    page_title="ClinicQ",
    layout="wide",
    initial_sidebar_state="expanded",
)
#
st.markdown("""
<style>
    html, body, p, div, span, label, h1, h2, h3 {
        font-family: 'Courier New', Courier, monospace !important;
    }
    .material-icons, .material-symbols-rounded {
        font-family: 'Material Symbols Rounded' !important;
    }
    #refering to kaban board style (visually better for updating queues)
    .kanban-col-header {
        font-weight: bold;
        text-transform: uppercase;
        background-color: #0e1117;
        border: 1px solid #222;
        border-top: 3px solid #33ff00;
        padding: 10px;
        margin-bottom: 15px;
        letter-spacing: 1px;
        color: #e0e0e0;
        text-align: center;
    }

    
    .metric-box {
        background-color: #0e1117;
        border: 1px solid #222;
        border-radius: 0px;
        padding: 10px;
        text-align: center;
        margin-bottom: 20px;
        border-top: 2px solid #33ff00;
    }
    .metric-box .val { font-size: 24px; font-weight: bold; color: #33ff00; } 
    .metric-box .lbl { font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; }

    
    .patient-card {
        background-color: #161a22;
        border: 1px solid #333;
        border-left: 3px solid #33ff00;
        padding: 12px;        
        margin-bottom: 10px;
        box-shadow: 2px 2px 0px #000;
    }
    .patient-card.in-consult { border-left-color: #ffaa00; background-color: #1f1a0d; }
    .patient-card.skipped { border-left-color: #ff3333; }    

    
    .badge { padding: 2px 6px; font-size: 9px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; border-radius: 2px; }
    .badge-scheduled { background: #222; color: #aaa; border: 1px solid #444; }
    .badge-waiting { background: #332200; color: #ffcc00; border: 1px solid #aa8800; }
    .badge-in-consult { background: #002200; color: #33ff00; border: 1px solid #007700; }
    
    
    .block-container {
        padding-top: 3rem !important;
    }
    
    
    .stButton > button {
        border-radius: 2px !important;
        font-family: 'Courier New', Courier, monospace !important;
        font-weight: bold !important;   
        border: 1px solid #444 !important;
    }
            
   
</style>
""", unsafe_allow_html=True)

def init_state():
    defaults = {
        "clinic_id":             None,
        "authenticated":         False,
        "gs_client":             None,
        "worksheet":             None,
        "status_message":        "",
        "status_type":           "info",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

def flash(message: str,msg_type: str="info"):
    st.session_state.status_message = message
    st.session_state.status_type = msg_type 

def status_badge(status:str)-> str:
    cls_map = {
        "Scheduled": "badge-scheduled",
        "Waiting" : "badge-waiting",
        "In Consult" : "badge-in-consult",
        "Skipped": "badge-skipped",
        "Completed": "badge-completed",
    }
    cls = cls_map.get(status,"badge-scheduled")
    return f'<span class="badge {cls}">{status}</span>'


with st.sidebar:
    st.markdown("## CLINICQ MANAGER")
    st.markdown("---")

    if not st.session_state.authenticated:
        tab_login, tab_register = st.tabs(["LOGIN", "REGISTER"])
        
        with tab_login:
            clinic_input = st.text_input(
                "Clinic ID",                            
                placeholder="e.g. CLINIC_001",
                help="Each physical clinic has a unique ID."
            )
            password_input = st.text_input("Password", type="password")
            
            login_btn = st.button("CONNECT TO QUEUE", use_container_width=True)

            if login_btn:
                if clinic_input.strip() and password_input.strip():
                    st.session_state.clinic_id = clinic_input.strip().upper()
                    try:
                        client = db.get_gspread_client()
                        if db.authenticate_clinic(client, st.session_state.clinic_id, password_input.strip()):
                            ws = db.get_or_create_clinic_worksheet(client, st.session_state.clinic_id)
                            st.session_state.gs_client = client
                            st.session_state.worksheet = ws                     
                            st.session_state.authenticated = True
                            st.rerun()                  
                        else:
                            st.error("Access Denied. Invalid Credentials.")
                    except Exception as e:
                        st.error(f"Connection failed: {e}")
                else:
                    st.warning("Please enter both Clinic ID and Password.")
        
        with tab_register:
            st.caption("Requires Admin Invite Code to prevent spam.")
            new_cid = st.text_input("New Clinic ID (e.g. CLINIC_002)")
            new_pw = st.text_input("Create Password", type="password")
            invite_code = st.text_input("Admin Invite Code")
            if st.button("CREATE ACCOUNT", use_container_width=True):
                if invite_code.strip() == os.environ.get("ADMIN_INVITE_CODE", "HACKCLUB_2026"):
                    try:
                        client = db.get_gspread_client()
                        db.register_new_clinic(client, new_cid.strip().upper(), new_pw.strip())
                        st.success(f"{new_cid} registered! You can now log in.")
                    except Exception as e:
                        st.error(f"Registration failed: {e}")
                else:
                    st.error("Invalid Invite Code.")
    else:
        st.markdown(f"### ✅ {st.session_state.clinic_id}")
        st.caption(f"Logged in as front-desk user")

    
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### ➕ REGISTER PATIENT")
        with st.form("add_patient_form",clear_on_submit=True):
            p_name = st.text_input("Patient Name *")
            p_phone = st.text_input("Whatsapp Number *")
            p_date = st.date_input("Scheduled Date", value=datetime.now())
            p_time = st.time_input("Scheduled Time",value = datetime.now().replace(second =0,microsecond=0).time())
            submit_btn = st.form_submit_button("Add to Queue",use_container_width=True,type ="primary")

            if submit_btn:
                if not p_name.strip():
                    st.error("Patient name is required.")
                else:
                    try:
                        db.add_patient(st.session_state.worksheet,p_name.strip(),p_phone.strip(), p_date.strftime("%Y-%m-%d"), p_time.strftime("%H:%M"))
                        flash(f"✅ {p_name} added to queue.", "success")
                        st.rerun()
                    except Exception as e:
                        flash(f"Failed to add patient: {e}", "error")
                        st.rerun()

        st.markdown("---")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("REFRESH", use_container_width=True):
                st.rerun()
        with col_btn2:
            if st.button("LOG OUT", use_container_width=True):
                for key in ["clinic_id", "authenticated", "gs_client", "worksheet"]:
                    st.session_state[key] = None if key != "authenticated" else False
                st.rerun()

if not st.session_state.authenticated:
    st.markdown("""
    <div style="text-align:center; padding:80px 0 40px 0;">
        <span style="font-size:64px;">🏥</span>
        <h1 style="color:#e0e0e0; margin-top:16px;">Multi-Clinic Queue Manager</h1>
        <p style="color:#888; font-size:16px; max-width:480px; margin:0 auto;">
            Log in or register in the sidebar to access your queue dashboard.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


if st.session_state.worksheet is None:
    st.error("Session lost connection to the worksheet. Please log out and reconnect in the sidebar.")
    st.stop()

#to check the count of patients in different queue categories...
patients = db.fetch_all_patients(st.session_state.worksheet)
today_str = datetime.now().strftime("%Y-%m-%d")
today_patients = [p for p in patients if p.get("Scheduled_Date") == today_str]

active   = [p for p in today_patients if p["Status"] not in ("Completed", "Skipped")]
waiting  = [p for p in active if p["Status"] == "Waiting"]
in_con   = [p for p in active if p["Status"] == "In Consult"]
done     = [p for p in today_patients if p["Status"] == "Completed"]

st.markdown(f"## LIVE QUEUE:  {st.session_state.clinic_id}")

if st.session_state.status_message:
    msg = st.session_state.status_message
    mtyp = st.session_state.status_type

    if mtyp == "success": 
        st.markdown(f"<div style='color:#33ff00; padding-bottom: 10px;'>&gt; SUCCESS: {msg}</div>", unsafe_allow_html=True)
    elif mtyp =="error": 
        st.markdown(f"<div style='color:#ff3333; padding-bottom: 10px;'>&gt; ERR: {msg}</div>", unsafe_allow_html=True)
    elif mtyp =="warning": 
        st.markdown(f"<div style='color:#ffaa00; padding-bottom: 10px;'>&gt; WRN: {msg}</div>", unsafe_allow_html=True)
    else:
        st.session_state.status_message = ""

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f'<div class="metric-box"><div class="val">{len(active)}</div><div class="lbl">Active Total</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-box"><div class="val">{len(in_con)}</div><div class="lbl">In Consult</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-box"><div class="val">{len(waiting)}</div><div class="lbl">In Lobby</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-box"><div class="val">{len(done)}</div><div class="lbl">Completed Today</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


k_col1, k_col2, k_col3 = st.columns(3, gap="large")

with k_col1:
    st.markdown('<div class="kanban-col-header">📅 Expected</div>', unsafe_allow_html=True)
    expected = sorted([p for p in today_patients if p["Status"] == "Scheduled"], key=lambda p: int(p["ID"]))
    
    if not expected:
        st.caption("No patients expected.")
    else:
        for p in expected:
            with st.container():
                st.markdown(
                    f'<div class="patient-card"><strong>#{p["ID"]} — {p["Patient_Name"]}</strong><br>'
                    f'<span style="color:#888; font-size:12px;">⏰ {p["Scheduled_Time"]} | 📞 {p["Phone"]}</span></div>', 
                    unsafe_allow_html=True
                )
                btn_cols = st.columns([1, 1])
                with btn_cols[0]:
                    if st.button("ARRIVED", key=f"arrive_{p['ID']}", use_container_width=True):
                        try:
                            db.update_patient_status(st.session_state.worksheet, p, "Waiting")
                            flash(f"{p['Patient_Name']} marked as Waiting.", "success")
                            st.rerun()
                        except Exception as e:
                            flash(f"Error: {e}", "error")
                with btn_cols[1]:
                    if st.button("SKIP", key=f"skip_sched_{p['ID']}", use_container_width=True):
                        try:
                            db.update_patient_status(st.session_state.worksheet, p, "Skipped")
                            flash(f"{p['Patient_Name']} marked as Skipped.", "warning")
                            st.rerun()
                        except Exception as e:
                            flash(f"Error: {e}", "error")

with k_col2:
    st.markdown('<div class="kanban-col-header">🛋️ Waiting Lobby</div>', unsafe_allow_html=True)
    lobby = sorted([p for p in today_patients if p["Status"] == "Waiting"], key=lambda p: int(p["ID"]))
    
    if not lobby:
        st.caption("Lobby is empty.")
    else:
        for p in lobby:
            st.markdown(
                f'<div class="patient-card"><strong>#{p["ID"]} — {p["Patient_Name"]}</strong><br>'
                f'<span style="color:#888; font-size:12px;">⏰ {p["Scheduled_Time"]} | 📞 {p["Phone"]}</span></div>', 
                unsafe_allow_html=True
            )
            if st.button("CALL TO ROOM ➔", key=f"call_{p['ID']}", use_container_width=True):
                db.update_patient_status(st.session_state.worksheet, p, "In Consult", {"Consult_Start_Time": datetime.now().strftime("%H:%M")})
                flash(f"{p['Patient_Name']} called to room.", "success")
                st.rerun()

with k_col3:
    st.markdown('<div class="kanban-col-header">🩺 In Consult</div>', unsafe_allow_html=True)
    consulting = sorted([p for p in today_patients if p["Status"] == "In Consult"], key=lambda p: int(p["ID"]))
    
    if not consulting:
        st.caption("No active consultations.")
    else:
        for p in consulting:
            st.markdown(
                f'<div class="patient-card in-consult"><strong>#{p["ID"]} — {p["Patient_Name"]}</strong><br>'
                f'<span style="color:#888; font-size:12px;">Started: {p["Consult_Start_Time"]}</span></div>', 
                unsafe_allow_html=True
            )
            if st.button("MARK COMPLETE ✔", key=f"complete_{p['ID']}", use_container_width=True):
                db.update_patient_status(st.session_state.worksheet, p, "Completed")
                flash(f"{p['Patient_Name']} consultation completed.", "success")
                st.rerun()                      