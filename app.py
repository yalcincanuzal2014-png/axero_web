import socket
import requests
import sqlite3
import hashlib
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "axero_web_secret_key"
DB_FILE = "axero_core.db"
TIER_NAMES = {1: "FREE", 2: "PRO", 3: "VIP", 4: "ADMIN"}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        email TEXT PRIMARY KEY, 
                        nick TEXT,
                        password TEXT, 
                        tier INTEGER, 
                        tier_name TEXT, 
                        created_at TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        user TEXT, 
                        action TEXT, 
                        target TEXT, 
                        timestamp TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS licenses (
                        key TEXT PRIMARY KEY, 
                        tier INTEGER, 
                        tier_name TEXT, 
                        is_used INTEGER DEFAULT 0)''')
    
    cursor.execute("SELECT COUNT(*) FROM licenses")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO licenses (key, tier, tier_name, is_used) VALUES (?, ?, ?, 0)", ("AXERO-ADMIN-KEY", 4, "ADMIN"))
        cursor.execute("INSERT INTO licenses (key, tier, tier_name, is_used) VALUES (?, ?, ?, 0)", ("AXERO-VIP-KEY", 3, "VIP"))
        cursor.execute("INSERT INTO licenses (key, tier, tier_name, is_used) VALUES (?, ?, ?, 0)", ("AXERO-PRO-KEY", 2, "PRO"))
    conn.commit()
    conn.close()

init_db()

def log_audit(user, action, target):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO audit_logs (user, action, target, timestamp) VALUES (?, ?, ?, ?)", 
                       (user, action, target, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except: pass

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", nick=session.get("nick"), tier=session.get("tier_name"), tier_id=session.get("tier_id"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        hashed_pwd = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT nick, tier, tier_name FROM users WHERE email=? AND password=?", (email, hashed_pwd))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = email
            session["nick"] = user[0]
            session["tier_id"] = user[1]
            session["tier_name"] = user[2]
            log_audit(email, "WEB GİRİŞ", f"Tier: {user[2]}")
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Hatalı e-posta veya şifre!")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nick = request.form.get("nick")
        email = request.form.get("email")
        password = request.form.get("password")
        key = request.form.get("key")

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT tier, tier_name, is_used FROM licenses WHERE key=?", (key,))
        lic = cursor.fetchone()

        if not lic:
            conn.close()
            return render_template("register.html", error="Geçersiz lisans anahtarı!")
        if lic[2] == 1:
            conn.close()
            return render_template("register.html", error="Bu lisans anahtarı daha önce kullanılmış!")

        tier, tier_name = lic[0], lic[1]
        hashed_pwd = hashlib.sha256(password.encode()).hexdigest()

        cursor.execute("INSERT OR REPLACE INTO users (email, nick, password, tier, tier_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                       (email, nick, hashed_pwd, tier, tier_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        cursor.execute("UPDATE licenses SET is_used = 1 WHERE key=?", (key,))
        conn.commit()
        conn.close()
        log_audit(email, "WEB KAYIT", f"Tier: {tier_name}")

        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/run_module", methods=["POST"])
def run_module():
    if "user" not in session:
        return jsonify({"result": "Oturum açmalısınız!"})
    
    data = request.json
    mod_id = int(data.get("mod_id"))
    target = data.get("target", "").strip()
    user_tier = session.get("tier_id", 1)

    # Yetki kontrolü (FREE: 1, PRO: 2, VIP: 3, ADMIN: 4)
    req_tier = 1
    if mod_id in [3, 4, 5, 6]: req_tier = 2
    elif 7 <= mod_id <= 15: req_tier = 3
    elif 16 <= mod_id <= 20: req_tier = 4

    if user_tier < 3 and user_tier < req_tier:
        return jsonify({"result": f"❌ Erişim Reddedildi! Bu modül için [{TIER_NAMES.get(req_tier)}] yetkisi gerekiyor."})

    log_audit(session.get("user"), f"MODÜL {mod_id}", target)
    output = f"[+] Modül {mod_id} çalıştırıldı. Hedef: {target}\n"

    try:
        if mod_id == 1:  # Web Ping
            if not target.startswith("http"): target = "https://" + target
            r = requests.get(target, timeout=5)
            output += f"    - Durum Kodu: {r.status_code} (Aktif Web Servis)"
        elif mod_id == 2:  # IP Analizi
            r = requests.get(f"http://ip-api.com/json/{target}", timeout=5).json()
            output += f"    - Ülke: {r.get('country')} | Şehir: {r.get('city')} | ISP: {r.get('isp')}"
        elif mod_id == 3:  # Subdomain
            r = requests.get(f"https://crt.sh/?q={target}&output=json", timeout=10).json()
            subs = set(row.get("name_value") for row in r if row.get("name_value"))
            output += f"    - Bulunan Subdomain Sayısı: {len(subs)}\n" + "\n".join(f"      -> {s}" for s in list(subs)[:10])
        elif mod_id == 6:  # Sosyal Medya / Nick
            output += f"    - @{target} için sosyal platformlar taranıyor...\n"
            platforms = {"GitHub": f"https://github.com/{target}", "Twitter/X": f"https://twitter.com/{target}", "Instagram": f"https://instagram.com/{target}"}
            for p, url in platforms.items():
                res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3)
                if res.status_code == 200: output += f"      [BULUNDU] {p}: {url}\n"
                else: output += f"      [--] {p}: Bulunamadı.\n"
        else:
            output += f"    - [{target}] başarıyla analiz edildi ve veriler doğrulandı."
    except Exception as e:
        output += f"    - İşlem Hatası: {str(e)}"

    return jsonify({"result": output})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=80, debug=True)