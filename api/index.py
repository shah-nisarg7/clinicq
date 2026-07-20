import os
os.environ.setdefault("APPDATA", os.path.expanduser("~"))
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify
import database as db
import traceback

app = Flask(__name__)

_client = None

def get_client():
    #cache the gspread client so we're not re authenticating with google on
    #every single request.. that was slowing things down when i tested it
    global _client
    if _client is None:
        _client = db.get_gspread_client()

    return _client         
              

@app.route("/api/login",methods=["POST"])
def login():
    data = request.get_json(force = True)           
    clinic_id = (data.get("clinic_id") or "").strip().upper()
    password = (data.get("password") or "").strip()        


    if not clinic_id or not password:
        return jsonify({"success": False, "error": "missing clinic ID or Pass"}),400
    

    try:
        client = get_client()
        ok = db.authenticate_clinic(client,clinic_id,password)

    except Exception as e:    
        print("[API] login error",e)
        traceback.print_exc()
        return jsonify({"success":False, "error": "server error, try again "}),500
    
    if not ok:
        return jsonify({"success": False, "error": "wrong clinic id or password"}), 401
    

    return jsonify({"success":True,"clinic_id":clinic_id})


@app.route("/api/register",methods=["POST"])
def register():
    data = request.get_json(force=True)
    clinic_id = (data.get("clinic_id") or "").strip().upper()
    password = (data.get("password") or "").strip()
    invite_code = (data.get("invite_code") or "").strip()

    #same fallback code mentioned in readme for reviewers..
    admin_invite_code = os.environ.get("ADMIN_INVITE_CODE","HACKCLUB_2026")
    if invite_code != admin_invite_code:
        return jsonify({"success": False, "error": "invalid invite code"}), 403
    if not clinic_id or not password:
        return jsonify({"success": False, "error": "missing clinic id or password"}), 400


    try:
        client = get_client()
        db.register_new_clinic(client,clinic_id,password)     
       
    except ValueError as e:
        # clinic id already taken    
        return jsonify({"success":False,"error":str(e)}),409
    
    except Exception as e:
        print("[API] register error",e)
        return jsonify({"success": False,"error": "server error, try again"}),500
    
    return jsonify({"success": True,"clinic_id":clinic_id})


@app.route("/api/queue",methods=["GET"])
def get_queue():
    clinic_id = (request.args.get("clinic_id") or "").strip().upper()
    if not clinic_id:
        return jsonify({"success":False,"error": "missing clinic_id"}),400
    

    try:
        client = get_client()
        worksheet = db.get_or_create_clinic_worksheet(client,clinic_id)
        patients = db.fetch_active_queue(worksheet)
        
    except Exception as e:
        print("[API] queue fetching error",e)
        return jsonify({"success": False,"error": "couldnt load queue"}),500
    

    return jsonify({"success": True,"patients":patients})


@app.route("/api/patients",methods=["POST"])
def add_patient():
    data = request.get_json(force = True)
    clinic_id = (data.get("clinic_id") or "").strip().upper()
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    scheduled_date = (data.get("scheduled_date") or "").strip()
    scheduled_time = (data.get("scheduled_time")or "").strip()
    is_walk_in = bool(data.get("is_walk_in",False))

    if not clinic_id or not name or not phone:
        return jsonify({"success": False, "error": "missing name, phone, or clinic id"}),400
    

    try:
        client = get_client()
        worksheet = db.get_or_create_clinic_worksheet(client,clinic_id)
        new_patient = db.add_patient(worksheet,name,phone,scheduled_date,scheduled_time,is_walk_in)

    except Exception as e:
        print("[API add patient error",e)
        traceback.print_exc()
        return jsonify({"success":False,"error": "couldnt add patient"}),500
    
    return jsonify({"success": True, "patient": new_patient})


@app.route("/api/patients/status",methods=["POST"])
def udpate_status():
    #handles call to room/mark completed/skip patient all through here
    #since its just changing status field 
    data = request.get_json(force=True)
    clinic_id = (data.get("clinic_id") or "").strip().upper()
    patient_id = data.get("patient_id")
    new_status = (data.get("new_status") or "").strip()

    if not clinic_id or not patient_id or not new_status:
        return jsonify({"success": False, "error": "missing clinic id , patient id or new status"}),400
    

    try:
        client = get_client()
        worksheet = db.get_or_create_clinic_worksheet(client,clinic_id)
        patient = db.find_patient_by_id(worksheet,patient_id)

        if patient is None:     
           return jsonify({"success": False, "error": "patient not found"}), 404

        extra_fields = {}    
        if new_status == "In Consult":
            extra_fields["Consult_Start_Time"] = data.get("consult_start_time","")


        db.update_patient_status(worksheet,patient,new_status,extra_fields)

    except ValueError as e:     
        #invalid status string from our own VALID_STATUSES check
         return jsonify({"success": False, "error": str(e)}), 400
    
    except Exception as e:
        print('[API] update status error',e)
        traceback.print_exc()
        return jsonify({"success":False,"error":"couldnt update patient "}),500
    
    return jsonify({"success":True})

