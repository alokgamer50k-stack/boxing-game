import imaplib
import email
from email.utils import parsedate_to_datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import os
import json
import hashlib
import random
import string
import requests

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
    except Exception as e: print("DB Save Error:", e)

GMAIL_ID = os.environ.get("GMAIL_ID", "kagarol505@gmail.com")
GMAIL_APP_PASS = os.environ.get("GMAIL_PASS", "nnywmitezfqwqiq")

# TERI GEMINI API KEY YAHAN FIX KAR DI HAI
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyAJmTzQ2XJn6mDbtldBcAdZ4Er2RQJIDvA")

def format_num(n):
    if n >= 1000000: return f"{n/1000000:.1f}M"
    if n >= 1000: return f"{n/1000:.1f}k"
    return str(int(n))

def calc_stats(iso_time, title):
    try: up_time = datetime.datetime.fromisoformat(iso_time)
    except: up_time = datetime.datetime.now(datetime.timezone.utc)
    now = datetime.datetime.now(datetime.timezone.utc)
    minutes = (now - up_time).total_seconds() / 60.0
    if minutes < 0: minutes = 0

    views = int(minutes * 40) + 45
    likes = int(minutes * 10) + 12
    buys = int(minutes * 5) + 2

    seed = int(hashlib.md5(title.encode()).hexdigest(), 16) % 100
    var = (seed / 100.0) * 0.1 
    
    return format_num(views * (1+var)), format_num(likes * (1+var)), format_num(buys * (1+var))

@app.route('/')
def home():
    return "<h1>ProStore API Live! (AI Chat Active) 🚀</h1>"

# --- REAL AI CHATBOT ROUTE ---
@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS': return jsonify({"success": True}), 200
    user_msg = request.json.get("message", "")
    
    system_prompt = f"You are a helpful, professional AI assistant for 'ProStore', a VIP digital asset marketplace. Keep answers short, crisp (1-2 sentences), and use emojis. The user says: {user_msg}"
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": system_prompt}]}]}
        response = requests.post(url, json=payload).json()
        
        reply_text = response['candidates'][0]['content']['parts'][0]['text']
        return jsonify({"success": True, "reply": reply_text})
    except Exception as e:
        print("AI Error:", e)
        return jsonify({"success": False, "reply": "AI Network Error. Re-connecting..."})

@app.route('/api/verify-sub', methods=['POST', 'OPTIONS'])
def verify_sub():
    if request.method == 'OPTIONS': return jsonify({"success": True}), 200
    db = load_db()
    code = request.json.get("code", "").upper()
    for sub in db.get("subscriptions", []):
        if sub["code"] == code:
            exp = datetime.datetime.fromisoformat(sub["expires"])
            if datetime.datetime.now(datetime.timezone.utc) < exp:
                return jsonify({"success": True, "plan": sub["plan"]})
    return jsonify({"success": False, "message": "Invalid or Expired Code!"})

@app.route('/api/create-sub', methods=['POST', 'OPTIONS'])
def create_sub():
    if request.method == 'OPTIONS': return jsonify({"success": True}), 200
    db = load_db()
    plan = request.json.get("plan")
    days = 30 if plan == "1M" else 180 if plan == "6M" else 365
    exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    if "subscriptions" not in db: db["subscriptions"] = []
    db["subscriptions"].append({"code": code, "plan": plan, "expires": exp.isoformat()})
    save_db(db)
    return jsonify({"success": True, "code": code})

@app.route('/api/products', methods=['GET', 'POST'])
def products():
    db = load_db()
    if request.method == 'POST':
        data = request.json
        data["id"] = str(int(datetime.datetime.now().timestamp()))
        data["upload_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        db["products"].append(data)
        save_db(db)
        return jsonify({"success": True})
    
    res = []
    for p in db["products"]:
        v, l, b = calc_stats(p.get("upload_time", ""), p.get("title", ""))
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

        found = False
        now = datetime.datetime.now(datetime.timezone.utc)
        for e_id in reversed(ids[-5:]):
            _, data = mail.fetch(e_id, "(RFC822)")
            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    m_date = parsedate_to_datetime(msg["Date"])
                    if 0 <= (now - m_date).total_seconds() <= 600:
                        found = True
                        break
            if found: break
            
        mail.logout()
        return jsonify({"success": found})
    except Exception as e:
        return jsonify({"success": False}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
        
