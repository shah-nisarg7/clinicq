import streamlit as st
import database as db
from datetime import datetime

#Title and layout of page
st.set_page_config(
    page_title="Clinic Queue Manager",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #0f2940;
        color: #ffffff;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    
    /* ── Metric cards (added for Phase 2) ── */
    .metric-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 14px 18px;
        text-align: center;
    }
    .metric-box .val { font-size: 28px; font-weight: 700; color: #0f2940; }
    .metric-box .lbl { font-size: 12px; color: #94a3b8; margin-top: 2px; }
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

with st.sidebar:
    st.markdown("## 🏥 Clinic Queue Manager")
    st.markdown("---")

    if not st.session_state.authenticated:
        st.markdown("### Log In")
        clinic_input = st.text_input(
            "Clinic ID",                            #currently no actual auth is there, just typing clinic name would login (can be interpreted as a secret code)
            placeholder="e.g. CLINIC_001",
            help="Each physical clinic has a unique ID."
        )
        login_btn = st.button("🔓 Connect to Queue", use_container_width=True)

        if login_btn:
            if clinic_input.strip():
                st.session_state.clinic_id = clinic_input.strip().upper()
                try:
                    client = db.get_gspread_client()
                    ws = db.get_or_create_clinic_worksheet(client, st.session_state.clinic_id)
                    st.session_state.gs_client = client
                    st.session_state.worksheet = ws                     
                    st.session_state.authenticated = True
                    st.rerun()                  
                except Exception as e:
                    st.error(f"Connection failed: {e}")
            else:
                st.warning("Please enter a Clinic ID.")
#if clinic name is new / secret key, itll automatically create a new sheet in the google sheet with same headers and append patients as we add them later on .
    else:
        st.markdown(f"### ✅ {st.session_state.clinic_id}")
        st.caption(f"Logged in as front-desk user")

        if st.button("🚪 Log Out", use_container_width=True):
            for key in ["clinic_id", "authenticated", "gs_client", "worksheet"]:
                st.session_state[key] = None if key != "authenticated" else False
            st.rerun()
            
        st.markdown("---")
        if st.button("🔄 Refresh Queue", use_container_width=True):
            st.rerun()

if not st.session_state.authenticated:
    st.markdown("""
    <div style="text-align:center; padding:80px 0 40px 0;">
        <span style="font-size:64px;">🏥</span>
        <h1 style="color:#0f2940; margin-top:16px;">Multi-Clinic Queue Manager</h1>
        <p style="color:#64748b; font-size:16px; max-width:480px; margin:0 auto;">
            Log in with your Clinic ID in the sidebar to access your queue dashboard.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


if st.session_state.worksheet is None:
    st.error("Session lost connection to the worksheet. Please log out and reconnect in the sidebar.")
    st.stop()
#to check the count of patients in different queue categories...
patients = db.fetch_all_patients(st.session_state.worksheet)
active   = [p for p in patients if p["Status"] not in ("Completed",)]
waiting  = [p for p in active if p["Status"] == "Waiting"]
in_con   = [p for p in active if p["Status"] == "In Consult"]
skipped  = [p for p in active if p["Status"] == "Skipped"]
done     = [p for p in patients if p["Status"] == "Completed"]

st.markdown(f"## 🏥 {st.session_state.clinic_id} — Live Queue")

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.markdown(f'<div class="metric-box"><div class="val">{len(active)}</div><div class="lbl">Active in Queue</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-box"><div class="val">{len(in_con)}</div><div class="lbl">In Consult</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-box"><div class="val">{len(waiting)}</div><div class="lbl">Waiting in Lobby</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-box"><div class="val">{len(skipped)}</div><div class="lbl">Skipped</div></div>', unsafe_allow_html=True)
with m5:
    st.markdown(f'<div class="metric-box"><div class="val">{len(done)}</div><div class="lbl">Completed Today</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# flash msg defined after calling init_state()
if st.session_state.status_message:
    
    msg = st.session_state.status_message
    mtyp = st.session_state.status_type

    if mtyp == "success": st.success(msg)
    elif mtyp =="error": st.error(msg)
    elif mtyp =="warning": st.warning(msg)
    else:
        st.sesion_state.status_message = ""


#split view dashboard

left_col,right_col = st.columns([1,1],gap = "large")

with left_col:
    with st.expander("➕ Add appointment", expanded = True):
        with st.form("add_patient_form",clear_on_submit=True):
            p_name = st.text_input("Patient Name *")
            p_phone = st.text_input("Whatsapp Number *")
            p_time = st.time_input("Scheduled Time",value = datetime.now().replace(second =0,microsecond=0).time())
            submit_btn = st.form_submit_button("Add to Queue",use_container_width=True,type ="primary")

            if submit_btn:
                if not p_name.strip():
                    st.error("Patient name is required.")
                else:
                    try:
                        db.add_patient(st.session_state.worksheet,p_name.strip(),p_phone.strip(),p_time.strftime("%H:%M"))
                        flash(f"✅ {p_name} added to queue.", "success")
                        st.rerun()
                    except Exception as e:
                        flash(f"Failed to add patient: {e}", "error")
                        st.rerun()

    st.markdown('<div class="section-header">📋 Expected — Not Yet Arrived</div>', unsafe_allow_html=True)
    scheduled_patients = [p for p in patients if p["Status"] == "Scheduled"]
    
    for p in scheduled_patients:
        st.write(f"#{p['ID']} - {p['Patient_Name']} @ {p['Scheduled_Time']}")

with right_col:
    st.markdown('<div class="section-header">🟢 All Patients (Raw Data View)</div>', unsafe_allow_html=True)
    st.dataframe(patients) 
