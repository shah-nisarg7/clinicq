import os
os.environ.setdefault("APPDATA", os.path.expanduser("~"))

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
        # clinic id already taken, 
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


