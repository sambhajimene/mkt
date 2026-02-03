import os
import time
import threading
from datetime import datetime, time as dtime
import pytz
import smtplib
from email.mime.text import MIMEText
from flask import Flask, render_template_string

# ======================
# CONFIG
# ======================
IST = pytz.timezone("Asia/Kolkata")

CHECK_INTERVAL_SECONDS = 60        # background loop
DASHBOARD_REFRESH_SEC = 30

FLASK_PORT = 5009

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO   = os.getenv("EMAIL_TO")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# ======================
# SYMBOL LIST (sample – extend safely)
# ======================
SYMBOLS = [
    # =====================
    # INDEX OPTIONS
    # =====================
    "NIFTY", "BANKNIFTY", "FINNIFTY",

    # =====================
    # BANKING & FINANCE
    # =====================
    "HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK",
    "BANKBARODA","PNB","IDFCFIRSTB","FEDERALBNK",
    "INDUSINDBK","AUBANK","CANBK",
    "BAJFINANCE","BAJAJFINSV","SBILIFE","HDFCLIFE",
    "ICICIPRULI","CHOLAFIN","MUTHOOTFIN","LICHSGFIN",
    "PFC","RECLTD","IRFC","MANAPPURAM",

    # =====================
    # IT
    # =====================
    "TCS","INFY","WIPRO","HCLTECH","TECHM","LTIM",
    "MPHASIS","COFORGE","PERSISTENT","LTTS",

    # =====================
    # FMCG & CONSUMER
    # =====================
    "HINDUNILVR","ITC","NESTLEIND","BRITANNIA",
    "DABUR","GODREJCP","TATACONSUM","MARICO",
    "COLPAL","UBL",

    # =====================
    # METALS
    # =====================
    "TATASTEEL","JSWSTEEL","HINDALCO","VEDL",
    "SAIL","NMDC","JINDALSTEL","ADANIENT","ADANIGREEN",

    # =====================
    # ENERGY & PSU
    # =====================
    "RELIANCE","ONGC","BPCL","IOC","GAIL","POWERGRID",
    "NTPC","COALINDIA","ADANIPORTS","ADANIPOWER",
    "TATAPOWER",

    # =====================
    # AUTO
    # =====================
    "MARUTI","TATAMOTORS","M&M","BAJAJ-AUTO",
    "EICHERMOT","HEROMOTOCO","TVSMOTOR",
    "ASHOKLEY","BALKRISIND","MRF",

    # =====================
    # PHARMA & HEALTHCARE
    # =====================
    "SUNPHARMA","DRREDDY","CIPLA","DIVISLAB",
    "APOLLOHOSP","LUPIN","BIOCON","AUROPHARMA",
    "ALKEM","TORNTPHARM","GLENMARK","GRANULES",

    # =====================
    # CEMENT & INFRA
    # =====================
    "ULTRACEMCO","ACC","AMBUJACEM","SHREECEM",
    "RAMCOCEM","DLF","LODHA","OBEROIRLTY",

    # =====================
    # CAPITAL GOODS
    # =====================
    "LT","SIEMENS","ABB","BEL","HAL","BHEL",
    "CUMMINSIND","THERMAX","APLAPOLLO",

    # =====================
    # OTHERS (HIGH LIQUIDITY OPTIONS)
    # =====================
    "DMART","NAUKRI","IRCTC","ZOMATO","PAYTM",
    "INDIGO","TRENT","PAGEIND","HAVELLS",
    "PIDILITIND","ASIANPAINT","BERGEPAINT",
    "POLYCAB","VOLTAS","ESCORTS",
    "SRF","DEEPAKNTR","ATUL","PIIND",
    "BANDHANBNK","RBLBANK","YESBANK"
]


# You can later extend this to 200 safely

# ======================
# GLOBAL STATE
# ======================
dashboard_rows = []
last_alerts = []

# ======================
# MARKET TIME CHECK (IST)
# ======================
def market_is_open():
    now = datetime.now(IST).time()
    return dtime(9, 15) <= now <= dtime(15, 30)

# ======================
# EMAIL
# ======================
def should_send_alert(symbol, strike, side):
    """
    Returns True ONLY if strike or side changed
    """
    key = f"{strike}_{side}"

    if LAST_ALERT.get(symbol) == key:
        return False  # ❌ same strike + same side → ignore

    LAST_ALERT[symbol] = key
    return True


    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASS)
            server.send_message(msg)
        print("📧 Email sent:", subject)
    except Exception as e:
        print("❌ Email error:", e)

# ======================
# MOCK SIGNAL ENGINE
# (Replace later with NSE logic)
# ======================
def generate_signals():
    global dashboard_rows, last_alerts

    dashboard_rows = []

    if not market_is_open():
        for sym in SYMBOLS:
            dashboard_rows.append({
                "symbol": sym,
                "status": "Market Closed",
                "strike": "-",
                "ce": "-",
                "pe": "-"
            })
        return

    # Example logic (safe placeholder)
    for sym in SYMBOLS:
        dashboard_rows.append({
            "symbol": sym,
            "status": "Watching",
            "strike": "ATM",
            "ce": "-",
            "pe": "-"
        })

    # Example alert (only for demo)
    alert = {
        "time": datetime.now(IST).strftime("%H:%M:%S"),
        "symbol": "NIFTY",
        "atm": "22500",
        "strike": "22550",
        "side": "CALL"
    }

    last_alerts.append(alert)

    send_mail(
        "🟢 CALL BUY CONFIRMED – NIFTY",
        f"""
Time: {alert['time']}
Symbol: {alert['symbol']}
ATM: {alert['atm']}
Strike: {alert['strike']}
Side: CALL BUY

Rule:
• Seller trap detected
• Confirmation candle logic
• SL = signal candle low (closing basis)
"""
    )

# ======================
# BACKGROUND LOOP
# ======================
def engine_loop():
    print("🧠 Engine loop started")
    while True:
        try:
            generate_signals()
        except Exception as e:
            print("Engine error:", e)
        time.sleep(CHECK_INTERVAL_SECONDS)

# ======================
# FLASK DASHBOARD
# ======================
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Option Dashboard</title>
    <meta http-equiv="refresh" content="{{ refresh }}">
    <style>
        body { font-family: Arial; background:#111; color:#eee; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #444; padding: 8px; text-align:center; }
        th { background:#222; }
        .call { color: #00ff99; font-weight: bold; }
        .put  { color: #ff6666; font-weight: bold; }
    </style>
</head>
<body>

<h2>📊 Multi-Strike Option Dashboard</h2>

<table>
<tr>
<th>Symbol</th><th>Status</th><th>Strike</th><th>CE</th><th>PE</th>
</tr>
{% for r in rows %}
<tr>
<td>{{ r.symbol }}</td>
<td>{{ r.status }}</td>
<td>{{ r.strike }}</td>
<td class="call">{{ r.ce }}</td>
<td class="put">{{ r.pe }}</td>
</tr>
{% endfor %}
</table>

<h3>🔔 Latest Alerts</h3>
<table>
<tr><th>Time</th><th>Symbol</th><th>ATM</th><th>Strike</th><th>Side</th></tr>
{% for a in alerts[-10:] %}
<tr>
<td>{{ a.time }}</td>
<td>{{ a.symbol }}</td>
<td>{{ a.atm }}</td>
<td>{{ a.strike }}</td>
<td class="{{ 'call' if a.side == 'CALL' else 'put' }}">{{ a.side }}</td>
</tr>
{% endfor %}
</table>

</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(
        HTML,
        rows=dashboard_rows,
        alerts=last_alerts,
        refresh=DASHBOARD_REFRESH_SEC
    )

def run_flask():
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)

# ======================
# ENTRY POINT (CRITICAL FIX)
# ======================
def start_app():
    print("🚀 LIVE Multi-Strike Option Dashboard + Email Alerts Started")
    threading.Thread(target=engine_loop, daemon=True).start()
    run_flask()

if __name__ == "__main__":
    start_app()
