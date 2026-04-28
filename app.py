import imaplib
import email
from email.utils import parsedate_to_datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import os
import json
import hashlib

app = Flask(__name__)
CORS(app)

# --- PERMANENT STORAGE ---
DATA_FILE = "database.json"

def load_db():
    if not os.path.exists(DATA_FILE):
        return {"products": [], "users": {}}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"products": [], "users": {}}

def save_db(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

GMAIL_ID = os.environ.get("GMAIL_ID", "kagarol505@gmail.com")
GMAIL_APP_PASS = os.environ.get("GMAIL_PASS", "nnywmitezfqwqiq")

# --- ALOK BHAI KA CUSTOM GROWTH ALGORITHM ---
def format_num(n):
    if n >= 1000000: return f"{n/1000000:.1f}M"
    if n >= 1000: return f"{n/1000:.1f}k"
    return str(int(n))

def calculate_stats(upload_time_iso, title):
    upload_time = datetime.datetime.fromisoformat(upload_time_iso)
    now = datetime.datetime.now(datetime.timezone.utc)
    delta_hours = (now - upload_time).total_seconds() / 3600.0
    if delta_hours < 0: delta_hours = 0.1

    # VIEWS LOGIC
    if delta_hours <= 1:
        views = delta_hours * 8000
    elif delta_hours <= 5:
        views = 8000 + ((delta_hours - 1) * 11000)
    elif delta_hours <= 24:
        views = 52000 + ((delta_hours - 5) * 3789)
    else:
        views = 124000 + ((delta_hours - 24) * 1500)

    # Variation taaki sab exactly same na lage
    seed = int(hashlib.md5(title.encode()).hexdigest(), 16) % 100
    variation = (seed / 100.0) * 0.2  
    views = views * (0.9 + variation)
    views = int(views)
    if views < 1: views = 1

    # LIKES & BUYS LOGIC (TERE CUSTOM NUMBERS)
    if delta_hours <= 1:
        likes = (views / 8000.0) * 1783
        buys = (views / 8000.0) * 2364
    elif delta_hours <= 5:
        # Pata nahi 5 ghante me likes/buys kyu kam ho rahe hain tere hisaab se, par ye lo
        likes = 1783 + ((delta_hours - 1) * (1274 - 1783) / 4) 
        buys = 2364 + ((delta_hours - 1) * (1893 - 2364) / 4)
    elif delta_hours <= 24:
        likes = 1274 + ((delta_hours - 5) * (74936 - 1274) / 19)
        buys = 1893 + ((delta_hours - 5) * (83635 - 1893) / 19)
    else:
        # 24 ghante ke baad slow steady growth
        likes = 74936 + ((delta_hours - 24) * 500)
        buys = 83635 + ((delta_hours - 24) * 600)

    likes = int(likes * (0.9 + variation))
    buys = int(buys * (0.9 + variation))

    return format_num(views), format_num(likes), format_num(buys)

@app.route('/')
def home():
    return "<h1>ProStore Dynamic API is Live Alok Bhai! 🚀</h1>"

# --- USER AUTHENTICATION & DATA SAVE ---
@app.route('/api/auth', methods=['POST'])
def handle_auth():
    db = load_db()
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    if username in db["users"]:
        if db["users"][username]["password"] == password:
            return jsonify({"success": True, "user": db["users"][username]})
        else:
            return jsonify({"success": False, "message": "Galat Password!"})
    else:
        db["users"][username] = {"username": username, "password": password, "files": []}
        save_db(db)
        return jsonify({"success": True, "user": db["users"][username]})

@app.route('/api/save-file', methods=['POST'])
def save_file():
    db = load_db()
    data = request.json
    username = data.get("username")
    file_data = {"title": data.get("title"), "link": data.get("link")}
    
    if username in db["users"]:
        existing_titles = [f["title"] for f in db["users"][username]["files"]]
        if file_data["title"] not in existing_titles:
            db["users"][username]["files"].append(file_data)
            save_db(db)
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "User not found"})

# --- PRODUCTS (WITH LIVE STATS) ---
@app.route('/api/products', methods=['GET', 'POST'])
def handle_products():
    db = load_db()
    if request.method == 'POST':
        new_p = request.json
        new_p["id"] = str(len(db["products"]) + int(datetime.datetime.now().timestamp()))
        new_p["upload_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        db["products"].append(new_p)
        save_db(db)
        return jsonify({"success": True})
    
    response_products = []
    for p in db["products"]:
        if "upload_time" not in p:
            p["upload_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        v, l, b = calculate_stats(p["upload_time"], p["title"])
        p_copy = p.copy()
        p_copy["views"] = v
        p_copy["likes"] = l
        p_copy["buys"] = b  
        response_products.append(p_copy)
    
    save_db(db)
    return jsonify(response_products)

@app.route('/api/products/<id>', methods=['DELETE'])
def delete_product(id):
    db = load_db()
    db["products"] = [p for p in db["products"] if str(p.get("id")) != str(id)]
    save_db(db)
    return jsonify({"success": True})

# --- VIP FAST PAYMENT CHECK (10 MIN LOGIC) ---
@app.route('/check-payment', methods=['GET'])
def check_payment():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_ID, GMAIL_APP_PASS)
        mail.select('"[Gmail]/All Mail"')
        
        search_query = '(OR FROM "no-reply@famapp.in" FROM "kagarol505@gmail.com")'
        status, messages = mail.search(None, search_query)
        
        email_ids = messages[0].split()
        if not email_ids:
            mail.logout()
            return jsonify({"success": False, "message": "No emails found"}), 200

        latest_emails = email_ids[-5:]
        recent_email_found = False
        now = datetime.datetime.now(datetime.timezone.utc)

        for e_id in reversed(latest_emails):
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    try:
                        msg_date = parsedate_to_datetime(msg["Date"])
                        time_diff = (now - msg_date).total_seconds()
                        if 0 <= time_diff <= 600:
                            recent_email_found = True
                            break
                    except Exception:
                        pass
            if recent_email_found: break

        mail.logout()
        if recent_email_found:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
      
