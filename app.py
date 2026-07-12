import streamlit as st
import datetime as datetime
import database as db

st.set_page_config(
    page_title='Clinic Queue Manager',
    page_icon=':hospital:',
    layout='wide',
    initial_sidebar_state='expanded',
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
</style>
""", unsafe_allow_html=True)
     
def init_state():
    defaults={
        "clinic_id" : None,
        "authenticated" : False,
        "gs_client" : None,
        "worksheet" : None,
        "status_message": "",
        "status_type": "info",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()

#sidebar for clinic login page

with st.sidebar:
    st.markdown("## :hospital: Clinic Queue Manager")
    st.markdown("---")

    if not st.session_state.authenticated:
        st.markdown("### Log in")
        clinic_input = st.text_input("Clinic ID",
                                     placeholder= "e.g. CLINIC_001",
                                     help = "Each physical clinic has a unique ID.")
        
        login_btn = st.button("🔓 Connect to Queue", use_container_width = True)

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

else:
     st.markdown(f"### :tick: {st.session_state.clinic_id} ")
     st.caption(f"Logged in as front-desk user")

     if st.button("🔒 Logout", use_container_width = True):
          for key in ["clinic_id", "authenticated", "gs_client", "worksheet"]:
               st.session_state[key] = None if key != "authenticated" else False
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

st.markdown(f" {st.session_state.clinic_id} = Connected Successfully.")
    