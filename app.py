import imaplib
import email
from email.utils import parsedate_to_datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import os
import json
import random
import string

app = Flask(__name__)
CORS(app)

DATA_FILE = "database.json"

def load_db():
    if not os.path.exists(DATA_FILE): return {"products": [], "subscriptions": []}
    try:
        with open(DATA_FILE, "r") as f: return json.load(f)
    except: return {"products": [], "subscriptions": []}

def save_db(data):
    try:
        with open(DATA_FILE, "w") as f: json.dump(data, f, indent=4)
    except Exception as e: print(e)

GMAIL_ID = os.environ.get("GMAIL_ID", "kagarol505@gmail.com")
GMAIL_APP_PASS = os.environ.get("GMAIL_PASS", "nnywmitezfqwqiq")

# --- CUSTOM TIMER LOGIC (Fixed for Admin Inputs) ---
def parse_num(val):
    val = str(val).lower().replace(' ', '')
    if 'k' in val: return float(val.replace('k', '')) * 1000
    if 'm' in val: return float(val.replace('m', '')) * 1000000
    try: return float(val)
    except: return 0

def format_num(n):
    if n >= 1000000: return f"{n/1000000:.1f}M"
    if n >= 1000: return f"{n/1000:.1f}k"
    return str(int(n))

def calc_stats(iso_time, duration_hrs, tv, tl, tb):
    try: up_time = datetime.datetime.fromisoformat(iso_time)
    except: up_time = datetime.datetime.now(datetime.timezone.utc)
    
    now = datetime.datetime.now(datetime.timezone.utc)
    hrs_passed = (now - up_time).total_seconds() / 3600.0
    if hrs_passed < 0: hrs_passed = 0.01
    
    try: dur = float(duration_hrs)
    except: dur = 24.0
    if dur <= 0: dur = 1.0

    ratio = hrs_passed / dur
    if ratio > 1.0: ratio = 1.0 

    # Exact numbers based on admin input
    v = int(parse_num(tv) * ratio)
    l = int(parse_num(tl) * ratio)
    b = int(parse_num(tb) * ratio)

    if v < 1 and parse_num(tv) > 0: v = 1
    return format_num(v), format_num(l), format_num(b)

@app.route('/')
def home():
    return "<h1>API Live! (Subscriptions & Custom Timer Logic Active) 🚀</h1>"

# --- SUBSCRIPTION SYSTEM ---
def generate_sub_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/api/verify-sub', methods=['POST', 'OPTIONS'])
def verify_sub():
    if request.method == 'OPTIONS': return jsonify({"success": True}), 200
    db = load_db()
    code = request.json.get("code", "").upper()
    
    # Check if code exists and is valid
    for sub in db.get("subscriptions", []):
        if sub["code"] == code:
            exp_date = datetime.datetime.fromisoformat(sub["expires"])
            if datetime.datetime.now(datetime.timezone.utc) < exp_date:
                return jsonify({"success": True, "plan": sub["plan"]})
            else:
                return jsonify({"success": False, "message": "Subscription Expired!"})
    
    return jsonify({"success": False, "message": "Invalid Code!"})

@app.route('/api/create-sub', methods=['POST', 'OPTIONS'])
def create_sub():
    if request.method == 'OPTIONS': return jsonify({"success": True}), 200
    db = load_db()
    data = request.json
    plan = data.get("plan")
    
    days = 30 if plan == "1M" else 180 if plan == "6M" else 365
    exp_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)
    
    new_code = generate_sub_code()
    if "subscriptions" not in db: db["subscriptions"] = []
    db["subscriptions"].append({"code": new_code, "plan": plan, "expires": exp_date.isoformat()})
    save_db(db)
    
    return jsonify({"success": True, "code": new_code})

# --- PRODUCTS SYSTEM ---
@app.route('/api/products', methods=['GET', 'POST'])
def products():
    db = load_db()
    if request.method == 'POST':
        data = request.json
        data["id"] = str(len(db["products"]) + int(datetime.datetime.now().timestamp()))
        data["upload_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        db["products"].append(data)
        save_db(db)
        return jsonify({"success": True})
    
    res = []
    for p in db["products"]:
        v, l, b = calc_stats(p.get("upload_time", datetime.datetime.now(datetime.timezone.utc).isoformat()), 
                             p.get("duration", 24), p.get("t_views", "10k"), p.get("t_likes", "1k"), p.get("t_buys", "500"))
        pc = p.copy()
        pc["views"], pc["likes"], pc["buys"] = v, l, b
        res.append(pc)
    return jsonify(res)

@app.route('/api/products/<id>', methods=['DELETE', 'OPTIONS'])
def del_p(id):
    if request.method == 'OPTIONS': return jsonify({"success": True}), 200
    db = load_db()
    db["products"] = [p for p in db["products"] if str(p.get("id")) != str(id)]
    save_db(db)
    return jsonify({"success": True})

@app.route('/check-payment', methods=['GET'])
def check_payment():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_ID, GMAIL_APP_PASS)
        mail.select('"[Gmail]/All Mail"')
        _, messages = mail.search(None, '(OR FROM "no-reply@famapp.in" FROM "kagarol505@gmail.com")')
        ids = messages[0].split()
        if not ids:
            mail.logout()
            return jsonify({"success": False})
        
        latest = ids[-5:]
        found = False
        now = datetime.datetime.now(datetime.timezone.utc)
        for e_id in reversed(latest):
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            for r in msg_data:
                if isinstance(r, tuple):
                    msg = email.message_from_bytes(r[1])
                    try:
                        m_date = parsedate_to_datetime(msg["Date"])
                        if 0 <= (now - m_date).total_seconds() <= 600:
                            found = True
                            break
                    except: pass
            if found: break
        mail.logout()
        return jsonify({"success": found})
    except: return jsonify({"success": False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
                
