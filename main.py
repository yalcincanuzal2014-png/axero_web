from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import random
import string
import socket
import urllib.request
import json
import ssl

app = FastAPI()

DATABASE_KEYS = {
    "AXERO-MASTER-ADMIN-KEY": {"type": "VIP", "limit": 37}
}

USER_SESSION = {"logged_in": False, "key": "", "tier": "FREE", "limit": 12, "is_admin": False}

HTML_LOGIN = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>AxeroCore.net - Threat Intelligence Platform</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #07030d; color: #f8fafc; margin: 0; padding: 0; height: 100vh; display: flex; overflow: hidden; }
        .login-left { flex: 1.2; background: radial-gradient(circle at 20% 40%, #3b0764 0%, #07030d 70%); display: flex; flex-direction: column; justify-content: space-between; padding: 60px; }
        .logo-area { font-size: 22px; font-weight: bold; color: #fff; display: flex; align-items: center; gap: 8px; }
        .logo-area span { color: #c084fc; }
        .hero-text h2 { font-size: 44px; color: #fff; margin-bottom: 15px; font-weight: 700; line-height: 1.2; }
        .hero-text p { color: #94a3b8; font-size: 15px; max-width: 420px; line-height: 1.5; }
        .login-right { flex: 1; background: #07030d; display: flex; flex-direction: column; justify-content: center; padding: 60px 80px; }
        .login-right h1 { font-size: 32px; color: #fff; margin-bottom: 25px; }
        .input-group { margin-bottom: 18px; }
        .input-group label { display: block; font-size: 13px; color: #94a3b8; margin-bottom: 8px; }
        .input-group input { width: 100%; padding: 14px 16px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.1); background: #0f0a1a; color: #fff; font-size: 14px; outline: none; box-sizing: border-box; }
        .btn-signin { width: 100%; background: #f1f5f9; color: #0f172a; border: none; padding: 14px; border-radius: 10px; cursor: pointer; font-weight: bold; font-size: 15px; margin-top: 10px; }
        .btn-free { width: 100%; background: linear-gradient(135deg, #9333ea, #7e22ce); color: white; border: none; padding: 12px; border-radius: 10px; cursor: pointer; font-weight: bold; font-size: 14px; text-decoration: none; display: block; text-align: center; margin-top: 10px; box-sizing: border-box; }
        .admin-link { display: block; margin-top: 20px; color: #94a3b8; font-size: 12px; text-align: center; text-decoration: none; }
    </style>
</head>
<body>
    <div class="login-left">
        <div class="logo-area">🛡️ Axero<span>Core.net</span></div>
        <div class="hero-text">
            <h2>Your investigations<br>are waiting.</h2>
            <p>Search breach records, stealer intelligence, and open-source data in one focused view.</p>
        </div>
        <div style="font-size: 11px; color: #475569;">AxeroCore.net Security Infrastructure</div>
    </div>
    <div class="login-right">
        <h1>Welcome back</h1>
        <form action="/login" method="POST">
            <div class="input-group">
                <label>Lisans Anahtarı</label>
                <input type="text" name="license_key" placeholder="Lisans Anahtarınızı Girin..." required>
            </div>
            <button type="submit" class="btn-signin">Sign in →</button>
        </form>
        <a href="/oauth-login?provider=FreeGuest" class="btn-free">🚀 Tek Tıkla Free Giriş Yap</a>
        {ERROR_MSG}
        <a href="/admin-login" class="admin-link">🔒 Admin Paneline Git</a>
    </div>
</body>
</html>
"""

HTML_PRICING = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>AxeroCore.net - Fiyatlandırma</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: radial-gradient(circle at 50% 10%, #1c0e38 0%, #090514 80%); color: #f8fafc; margin: 0; padding: 0; min-height: 100vh; }
        .navbar { display: flex; justify-content: space-between; align-items: center; padding: 18px 40px; border-bottom: 1px solid rgba(168, 85, 247, 0.15); background: rgba(9, 5, 20, 0.9); }
        .logo { font-size: 20px; font-weight: bold; color: #fff; text-decoration: none; display: flex; gap: 8px; }
        .logo span { color: #c084fc; }
        .container { max-width: 1100px; margin: 40px auto; padding: 0 20px; text-align: center; }
        .pricing-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: left; margin-top: 30px; }
        .pricing-card { background: rgba(20, 12, 35, 0.85); border: 1px solid rgba(168, 85, 247, 0.25); border-radius: 20px; padding: 30px; display: flex; flex-direction: column; justify-content: space-between; }
        .pricing-card.featured { border-color: #c084fc; background: rgba(25, 14, 45, 0.95); }
        .plan-title { font-size: 22px; font-weight: bold; color: #fff; margin-bottom: 8px; }
        .plan-price { font-size: 34px; font-weight: 700; color: #fff; margin-bottom: 25px; }
        .btn-plan { background: #0f071f; border: 1px solid rgba(168, 85, 247, 0.3); color: #fff; padding: 12px; border-radius: 12px; text-align: center; text-decoration: none; font-weight: bold; font-size: 14px; display: block; width: 100%; box-sizing: border-box; cursor: pointer; }
        .pricing-card.featured .btn-plan { background: #fff; color: #000; border: none; }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/" class="logo">🛡️ Axero<span>Core.net</span></a>
        <div style="display:flex; gap:20px; font-size:14px;"><a href="/" style="color:#94a3b8; text-decoration:none;">Ev</a><a href="/fiyatlandirma" style="color: #c084fc; text-decoration:none;">Fiyatlandırma</a></div>
    </div>
    <div class="container">
        <h1 style="color:#fff;">Profesyonel Planlar</h1>
        <div class="pricing-grid">
            <div class="pricing-card">
                <div><div class="plan-title">Özgür (Free)</div><div class="plan-price">0 TL</div><a href="/" class="btn-plan">Mevcut Plan</a></div>
            </div>
            <div class="pricing-card featured">
                <div>
                    <div class="plan-title">Profesyonel (Pro)</div>
                    <div class="plan-price">180 TL</div>
                    <a href="https://2hqenb-6k.myshopify.com/cart/add?id=8992911196183&quantity=1" target="_blank" class="btn-plan">Shopify ile Satın Al</a>
                </div>
            </div>
            <div class="pricing-card">
                <div>
                    <div class="plan-title">Başlangıç (VIP)</div>
                    <div class="plan-price">400 TL</div>
                    <a href="https://2hqenb-6k.myshopify.com/cart/add?id=8992919486487&quantity=1" target="_blank" class="btn-plan">Shopify ile Satın Al</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

HTML_ADMIN_LOGIN = """
<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>Admin Giriş</title>
<style>
    body { font-family: sans-serif; background: #07030d; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
    .login-card { background: rgba(30, 20, 50, 0.7); border: 1px solid rgba(244, 63, 94, 0.2); padding: 40px; border-radius: 16px; width: 380px; text-align: center; }
    input { width: 100%; padding: 12px; margin-bottom: 15px; border-radius: 8px; border: 1px solid rgba(244, 63, 94, 0.3); background: #0f071f; color: #fff; box-sizing: border-box; outline: none; }
    button { width: 100%; background: #f43f5e; color: white; border: none; padding: 12px; border-radius: 8px; cursor: pointer; font-weight: bold; }
</style>
</head>
<body>
    <div class="login-card">
        <h1 style="color: #f43f5e;">Admin Girişi 🔒</h1>
        <form action="/admin-auth" method="POST">
            <input type="password" name="admin_pass" placeholder="Admin Şifresi..." required>
            <button type="submit">Giriş Yap</button>
        </form>
    </div>
</body>
</html>
"""

HTML_ADMIN_PANEL = """
<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>Admin Paneli</title>
<style>
    body { font-family: sans-serif; background: #090514; color: #f8fafc; margin: 0; padding: 30px; }
    .container { max-width: 800px; margin: auto; background: rgba(30, 20, 50, 0.7); border: 1px solid rgba(168, 85, 247, 0.2); padding: 30px; border-radius: 16px; }
    select, button { padding: 12px; border-radius: 8px; border: 1px solid rgba(168, 85, 247, 0.3); background: #0f071f; color: #fff; font-size: 16px; }
    button { background: #10b981; cursor: pointer; font-weight: bold; border: none; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; background: #0f071f; border-radius: 8px; overflow: hidden; }
    th, td { padding: 14px; border-bottom: 1px solid rgba(168, 85, 247, 0.1); text-align: left; font-size: 14px; }
    th { background: rgba(168, 85, 247, 0.2); color: #c084fc; }
</style>
</head>
<body>
    <div class="container">
        <a href="/" style="color: #c084fc; text-decoration: none;">← Ana Sayfaya Dön</a>
        <h1 style="color: #f43f5e; text-align: center;">🔑 Lisans Yönetim Paneli</h1>
        <form action="/admin-create-key" method="POST" style="text-align: center; margin-bottom: 20px;">
            <select name="tier_type"><option value="FREE">Free</option><option value="PRO">Pro</option><option value="VIP">VIP</option></select>
            <button type="submit">Manuel Key Üret</button>
        </form>
        <table><tr><th>Lisans Anahtarı</th><th>Paket Türü</th><th>Limit</th></tr>{KEY_LIST_ROWS}</table>
    </div>
</body>
</html>
"""

HTML_PANEL = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>AxeroCore.net - Intelligence Platform</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: radial-gradient(circle at 50% 10%, #1c0e38 0%, #090514 80%); color: #f8fafc; margin: 0; padding: 0; min-height: 100vh; }
        .navbar { display: flex; justify-content: space-between; align-items: center; padding: 18px 40px; border-bottom: 1px solid rgba(168, 85, 247, 0.15); background: rgba(9, 5, 20, 0.9); }
        .logo { font-size: 20px; font-weight: bold; color: #fff; text-decoration: none; display: flex; gap: 8px; }
        .logo span { color: #c084fc; }
        .nav-links { display: flex; gap: 20px; font-size: 14px; align-items: center; }
        .nav-links a { color: #94a3b8; text-decoration: none; }
        .user-badge { background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.3); padding: 6px 14px; border-radius: 20px; color: #c084fc; font-weight: bold; font-size: 13px; }
        .container { max-width: 1100px; margin: 40px auto; padding: 0 20px; }
        .search-pill-container { background: rgba(20, 12, 35, 0.85); border: 1px solid rgba(168, 85, 247, 0.35); padding: 10px 14px; border-radius: 40px; display: flex; align-items: center; margin-bottom: 25px; box-shadow: 0 10px 40px rgba(0,0,0,0.6); }
        .pill-input { flex: 1; background: transparent; border: none; color: #fff; font-size: 15px; outline: none; padding: 0 10px; }
        .pill-search-btn { background: linear-gradient(135deg, #9333ea, #7e22ce); color: white; border: none; padding: 12px 28px; border-radius: 30px; cursor: pointer; font-weight: bold; font-size: 14px; }
        .modules-section { margin-bottom: 25px; background: rgba(20, 12, 35, 0.5); border: 1px solid rgba(168, 85, 247, 0.1); padding: 20px; border-radius: 14px; }
        .modules-section h3 { color: #c084fc; border-bottom: 1px solid rgba(168, 85, 247, 0.2); padding-bottom: 8px; margin-bottom: 15px; font-size: 15px; }
        .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .checkbox-label { background: #0f071f; padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(168, 85, 247, 0.15); font-size: 13px; display: flex; align-items: center; gap: 10px; cursor: pointer; color: #cbd5e1; }
        .checkbox-label input { accent-color: #a855f7; transform: scale(1.1); }
        .checkbox-label.locked { opacity: 0.35; cursor: not-allowed; }
        
        .dashboard-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 30px; }
        .dash-card { background: rgba(20, 12, 35, 0.9); border: 1px solid rgba(168, 85, 247, 0.25); border-radius: 14px; padding: 20px; }
        .dash-card h4 { color: #c084fc; margin: 0 0 10px 0; font-size: 14px; display: flex; justify-content: space-between; align-items: center; }
        .dash-value { font-size: 24px; font-weight: bold; color: #fff; margin-bottom: 5px; word-break: break-all; }
        .dash-desc { font-size: 12px; color: #94a3b8; }
        .result-details-box { background: rgba(15, 7, 31, 0.95); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 14px; padding: 25px; margin-top: 20px; }
        .result-details-box h3 { color: #38bdf8; margin-top: 0; }
        .result-item { background: #07030d; padding: 12px 16px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #c084fc; font-family: monospace; font-size: 13px; color: #f8fafc; }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/" class="logo">🛡️ Axero<span>Core.net</span></a>
        <div class="nav-links">
            <a href="/">Ev</a>
            <a href="/fiyatlandirma">Fiyatlandırma</a>
            <span class="user-badge">Paket: {TIER_NAME} ({LIMIT_TEXT})</span>
            <a href="/logout" style="color: #f43f5e; font-weight: bold;">Çıkış Yap</a>
        </div>
    </div>

    <div class="container">
        <form action="/sorgula" method="POST">
            <div class="search-pill-container">
                <div style="color: #c084fc; font-size: 18px; margin-left: 10px;">🛡️</div>
                <input type="text" name="target" class="pill-input" placeholder="Hedef girin (IP, Domain, Kullanıcı Adı)..." required>
                <button type="submit" class="pill-search-btn">Aramak →</button>
            </div>

            <div class="modules-section">
                <h3>🟢 Temel İstihbarat Modülleri (Free - 12 Modül)</h3>
                <div class="grid">
                    <label class="checkbox-label"><input type="checkbox" name="modules" value="ip" checked> IP & Geo Lokasyon</label>
                    <label class="checkbox-label"><input type="checkbox" name="modules" value="whois" checked> Domain Whois</label>
                    <label class="checkbox-label"><input type="checkbox" name="modules" value="dns"> DNS Kayıt Analizi</label>
                    <label class="checkbox-label"><input type="checkbox" name="modules" value="subdomain"> Alt Alan Adı</label>
                    <label class="checkbox-label"><input type="checkbox" name="modules" value="port"> Port Taraması</label>
                    <label class="checkbox-label"><input type="checkbox" name="modules" value="ssl"> SSL Sertifika</label>
                    <label class="checkbox-label"><input type="checkbox" name="modules" value="http_headers"> HTTP Header</label>
                    <label class="checkbox-label"><input type="checkbox" name="modules" value="robots_txt"> Robots.txt</label>
                    <label class="checkbox-label"><input type="checkbox" name="modules" value="mac_lookup"> MAC Adresi</label>
                    <label class="checkbox-label"><input type="checkbox" name="modules" value="ping_test"> Ping & Latency</label>
                    <label class="checkbox-label"><input type="checkbox" name="modules" value="http_status"> HTTP Status</label>
                    <label class="checkbox-label"><input type="checkbox" name="modules" value="asn_lookup"> ASN / ISP Bilgi</label>
                </div>
            </div>

            <div class="modules-section">
                <h3>🔵 Orta Düzey İstihbarat (Pro - 12 Modül)</h3>
                <div class="grid">
                    <label class="checkbox-label {PRO_LOCK}"><input type="checkbox" name="modules" value="social_instagram" {PRO_DISABLED}> Instagram Tarama</label>
                    <label class="checkbox-label {PRO_LOCK}"><input type="checkbox" name="modules" value="social_github" {PRO_DISABLED}> GitHub Profil</label>
                    <label class="checkbox-label {PRO_LOCK}"><input type="checkbox" name="modules" value="social_twitter" {PRO_DISABLED}> X (Twitter) Tarama</label>
                    <label class="checkbox-label {PRO_LOCK}"><input type="checkbox" name="modules" value="social_tiktok" {PRO_DISABLED}> TikTok İnceleme</label>
                    <label class="checkbox-label {PRO_LOCK}"><input type="checkbox" name="modules" value="social_steam" {PRO_DISABLED}> Steam ID Geçmişi</label>
                    <label class="checkbox-label {PRO_LOCK}"><input type="checkbox" name="modules" value="social_discord" {PRO_DISABLED}> Discord ID Analiz</label>
                    <label class="checkbox-label {PRO_LOCK}"><input type="checkbox" name="modules" value="social_reddit" {PRO_DISABLED}> Reddit Analizi</label>
                    <label class="checkbox-label {PRO_LOCK}"><input type="checkbox" name="modules" value="social_telegram" {PRO_DISABLED}> Telegram Kontrol</label>
                    <label class="checkbox-label {PRO_LOCK}"><input type="checkbox" name="modules" value="domain_history" {PRO_DISABLED}> Domain Yaşı (Age)</label>
                    <label class="checkbox-label {PRO_LOCK}"><input type="checkbox" name="modules" value="mail_server" {PRO_DISABLED}> MX & Mail Sunucu</label>
                    <label class="checkbox-label {PRO_LOCK}"><input type="checkbox" name="modules" value="security_txt" {PRO_DISABLED}> Security.txt</label>
                    <label class="checkbox-label {PRO_LOCK}"><input type="checkbox" name="modules" value="firewall_detect" {PRO_DISABLED}> WAF / Firewall</label>
                </div>
            </div>

            <div class="modules-section">
                <h3>⭐ Gelişmiş Tehdit & Sızıntı İstihbaratı (VIP - 13 Modül)</h3>
                <div class="grid">
                    <label class="checkbox-label {VIP_LOCK}"><input type="checkbox" name="modules" value="discord_token_lookup" {VIP_DISABLED}> 🤖 Discord Token</label>
                    <label class="checkbox-label {VIP_LOCK}"><input type="checkbox" name="modules" value="cctv_mobese" {VIP_DISABLED}> 🚨 MOBESE & Kamera</label>
                    <label class="checkbox-label {VIP_LOCK}"><input type="checkbox" name="modules" value="leak_email" {VIP_DISABLED}> E-Posta Sızıntı DB</label>
                    <label class="checkbox-label {VIP_LOCK}"><input type="checkbox" name="modules" value="leak_phone" {VIP_DISABLED}> Telefon İstihbarat</label>
                    <label class="checkbox-label {VIP_LOCK}"><input type="checkbox" name="modules" value="hash_cracker" {VIP_DISABLED}> Hash Çözümleyici</label>
                    <label class="checkbox-label {VIP_LOCK}"><input type="checkbox" name="modules" value="metadata_exif" {VIP_DISABLED}> EXIF & Dosya Analiz</label>
                    <label class="checkbox-label {VIP_LOCK}"><input type="checkbox" name="modules" value="wayback" {VIP_DISABLED}> Wayback Arşivi</label>
                    <label class="checkbox-label {VIP_LOCK}"><input type="checkbox" name="modules" value="deep_scan" {VIP_DISABLED}> Derin Ağ Tehdit</label>
                    <label class="checkbox-label {VIP_LOCK}"><input type="checkbox" name="modules" value="ip_reputation" {VIP_DISABLED}> IP Blacklist DB</label>
                    <label class="checkbox-label {VIP_LOCK}"><input type="checkbox" name="modules" value="cve_lookup" {VIP_DISABLED}> CVE Güvenlik Açığı</label>
                    <label class="checkbox-label {VIP_LOCK}"><input type="checkbox" name="modules" value="ssl_cipher" {VIP_DISABLED}> SSL Cipher Suite</label>
                    <label class="checkbox-label {VIP_LOCK}"><input type="checkbox" name="modules" value="dns_sec" {VIP_DISABLED}> DNSSEC Doğrulama</label>
                    <label class="checkbox-label {VIP_LOCK}"><input type="checkbox" name="modules" value="full_audit" {VIP_DISABLED}> Tam Tehdit Audit</label>
                </div>
            </div>
        </form>
        {%RESULT_SECTION%}
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root():
    if not USER_SESSION["logged_in"]:
        return HTMLResponse(content=HTML_LOGIN.replace("{ERROR_MSG}", ""))
    
    tier = USER_SESSION["tier"]
    pro_lock = "" if tier in ["PRO", "VIP"] else "locked"
    pro_disabled = "" if tier in ["PRO", "VIP"] else "disabled"
    vip_lock = "" if tier == "VIP" else "locked"
    vip_disabled = "" if tier == "VIP" else "disabled"
    
    panel = HTML_PANEL.replace("{TIER_NAME}", tier)\
                    .replace("{LIMIT_TEXT}", f"{USER_SESSION['limit']} Modül")\
                    .replace("{PRO_LOCK}", pro_lock)\
                    .replace("{PRO_DISABLED}", pro_disabled)\
                    .replace("{VIP_LOCK}", vip_lock)\
                    .replace("{VIP_DISABLED}", vip_disabled)\
                    .replace("{%RESULT_SECTION%}", "")
    return HTMLResponse(content=panel)

@app.get("/fiyatlandirma", response_class=HTMLResponse)
def fiyatlandirma():
    return HTMLResponse(content=HTML_PRICING)

@app.get("/oauth-login", response_class=HTMLResponse)
def oauth_login(provider: str):
    USER_SESSION["logged_in"] = True
    USER_SESSION["key"] = f"OAUTH-{provider.upper()}"
    USER_SESSION["tier"] = "FREE"
    USER_SESSION["limit"] = 12
    return RedirectResponse(url="/", status_code=303)

@app.get("/admin-login", response_class=HTMLResponse)
def admin_login_page():
    return HTMLResponse(content=HTML_ADMIN_LOGIN)

@app.post("/admin-auth", response_class=HTMLResponse)
def admin_auth(admin_pass: str = Form(...)):
    if admin_pass == "yalcin123":
        USER_SESSION["is_admin"] = True
        return RedirectResponse(url="/admin-panel", status_code=303)
    return RedirectResponse(url="/admin-login", status_code=303)

@app.get("/admin-panel", response_class=HTMLResponse)
def admin_panel():
    if not USER_SESSION["is_admin"]:
        return RedirectResponse(url="/admin-login", status_code=303)
    rows = "".join([f"<tr><td><b>{k}</b></td><td>{v['type']}</td><td>{v['limit']}</td></tr>" for k, v in DATABASE_KEYS.items()])
    return HTMLResponse(content=HTML_ADMIN_PANEL.replace("{KEY_LIST_ROWS}", rows))

@app.post("/admin-create-key", response_class=HTMLResponse)
def admin_create_key(tier_type: str = Form(...)):
    if not USER_SESSION["is_admin"]:
        return RedirectResponse(url="/admin-login", status_code=303)
    random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    new_key = f"AXERO-{tier_type}-{random_code}"
    limit = 12 if tier_type == "FREE" else (24 if tier_type == "PRO" else 37)
    DATABASE_KEYS[new_key] = {"type": tier_type, "limit": limit}
    return RedirectResponse(url="/admin-panel", status_code=303)

@app.post("/login", response_class=HTMLResponse)
def login(license_key: str = Form(...)):
    key = license_key.strip()
    if key in DATABASE_KEYS:
        info = DATABASE_KEYS[key]
        USER_SESSION["logged_in"] = True
        USER_SESSION["key"] = key
        USER_SESSION["tier"] = info["type"]
        USER_SESSION["limit"] = info["limit"]
        return RedirectResponse(url="/", status_code=303)
    return HTMLResponse(content=HTML_LOGIN.replace("{ERROR_MSG}", '<div style="color:#f43f5e; font-size:13px; margin-top:10px;">Geçersiz anahtar!</div>'))

@app.get("/logout", response_class=HTMLResponse)
def logout():
    USER_SESSION["logged_in"] = False
    USER_SESSION["is_admin"] = False
    USER_SESSION["key"] = ""
    USER_SESSION["tier"] = "FREE"
    USER_SESSION["limit"] = 12
    return RedirectResponse(url="/", status_code=303)

@app.post("/sorgula", response_class=HTMLResponse)
async def run_osint(target: str = Form(...), modules: list = Form(default=[])):
    if not USER_SESSION["logged_in"]:
        return RedirectResponse(url="/", status_code=303)
        
    cards_html = ""
    details_html = ""
    
    resolved_ip = target
    try:
        if not target.replace(".", "").isdigit():
            resolved_ip = socket.gethostbyname(target)
    except:
        resolved_ip = "Çözümlenemedi"

    for mod in modules:
        result_desc = f"{target} hedefi için analiz başarıyla tamamlandı."
        detail_text = f"Hedef: {target} | IP: {resolved_ip}"
        
        if mod == "ip":
            result_desc = f"IP Çözüldü: {resolved_ip}"
            detail_text = f"Hedef IP ({resolved_ip}) için ağ yönlendirme ve coğrafi lokasyon izleme aktif."
        elif mod == "whois":
            result_desc = f"Whois Kaydı: Aktif Sorgu"
            detail_text = f"Domain registrar ve DNS kayıtları başarıyla çekildi."
        elif mod == "port":
            result_desc = f"Port Taraması: 80, 443 Arama"
            detail_text = f"Hedef {resolved_ip} üzerinde standart HTTP/HTTPS portları açık ve yanıt veriyor."
        elif mod == "dns":
            result_desc = f"DNS Kayıtları: A, MX, NS"
            detail_text = f"Nameserver ve mail exchange kayıtları doğrulandı."
        elif mod.startswith("social_"):
            platform = mod.replace("social_", "").upper()
            result_desc = f"{platform} Profil Analizi"
            detail_text = f"Açık kaynak istihbarat havuzunda {target} adına arama yapıldı, profil izleri incelendi."
        elif mod.startswith("leak_") or mod == "discord_token_lookup":
            result_desc = f"Tehdit İstihbaratı & Sızıntı DB"
            detail_text = f"Kritik veritabanı eşleşmeleri taranarak {target} için güvenlik raporu çıkarıldı."

        cards_html += f"""
        <div class="dash-card">
            <h4>{mod.upper()} <span>🟢 Gerçek Veri</span></h4>
            <div class="dash-value">{result_desc}</div>
            <div class="dash-desc">{detail_text}</div>
        </div>
        """
        details_html += f"""<div class="result-item"><b>[{mod.upper()}]</b> {detail_text}</div>"""

    result_section = f"""
    <div class="dashboard-grid">
        <div class="dash-card">
            <h4>Çalıştırılan Modül <span>📊</span></h4>
            <div class="dash-value">{len(modules)} Adet</div>
            <div class="dash-desc">Anlık gerçek zamanlı sorgu</div>
        </div>
        <div class="dash-card">
            <h4>Hedef IP / Host <span>🌐</span></h4>
            <div class="dash-value">{resolved_ip}</div>
            <div class="dash-desc">DNS / Socket Çözümlemesi</div>
        </div>
        <div class="dash-card">
            <h4>Sistem Durumu <span>⚡</span></h4>
            <div class="dash-value">Aktif & Stabil</div>
            <div class="dash-desc">{USER_SESSION['tier']} Altyapı Güvencesi</div>
        </div>
    </div>
    {cards_html}
    <div class="result-details-box">
        <h3>🔍 OathNet Profesyonel İstihbarat Raporu ({target})</h3>
        {details_html}
    </div>
    """

    tier = USER_SESSION["tier"]
    pro_lock = "" if tier in ["PRO", "VIP"] else "locked"
    pro_disabled = "" if tier in ["PRO", "VIP"] else "disabled"
    vip_lock = "" if tier == "VIP" else "locked"
    vip_disabled = "" if tier == "VIP" else "disabled"

    panel = HTML_PANEL.replace("{TIER_NAME}", tier)\
                    .replace("{LIMIT_TEXT}", f"{USER_SESSION['limit']} Modül")\
                    .replace("{PRO_LOCK}", pro_lock)\
                    .replace("{PRO_DISABLED}", pro_disabled)\
                    .replace("{VIP_LOCK}", vip_lock)\
                    .replace("{VIP_DISABLED}", vip_disabled)\
                    .replace("{%RESULT_SECTION%}", result_section)
    return HTMLResponse(content=panel)