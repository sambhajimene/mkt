import os
import time
import pytz
import smtplib
import threading
from datetime import datetime
from email.mime.text import MIMEText
from flask import Flask, render_template_string

# ================= IST TIME =================
IST = pytz.timezone("Asia/Kolkata")

def ist_now():
    return datetime.now(IST)

# ================= MARKET TIME CHECK =================
def is_market_open():
    now = ist_now().time()
    return now >= datetime.strptime("09:15", "%H:%M").time() and \
           now <= datetime.strptime("15:30", "%H:%M").time()

# ================= EMAIL CONFIG (FROM ENV) =================
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO   = os.getenv("EMAIL_TO")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def send_mail(subject, body):
    if not all([EMAIL_FROM, EMAIL_TO, EMAIL_PASS]):
        print("❌ Email env missing")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_FROM, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("📧 Email sent:", subject)
    except Exception as e:
        print("❌ Email error:", e)

# ================= SYMBOL LIST (SAMPLE – EXTEND TO 200) =================
SYMBOLS = [
    "NIFTY", "BANKNIFTY", "FINNIFTY",
    "RELIANCE", "TCS", "INFY", "HDFCBANK",
    "ICICIBANK", "SBIN", "LT", "HCLTECH"
]
# 👉 You can safely extend this list to 200 NSE symbols

# ================= ALERT MEMORY =================
LAST_ALERT = {}  # symbol -> "strike_side"

# ================= DASHBOARD STORAGE =================
LATEST_ALERTS = []

# ================= CORE LOGIC (SIMULATED DATA PLACEHOLDER) =================
def generate_signal(symbol):
    """
    Replace this block with NSE live option-chain logic.
    This structure is FINAL & STABLE.
    """

    # ---- Dummy example values (structure only) ----
    atm = 22500
    strike = atm + 50
    side = "CALL"   # or PUT

    rsi_15m = 62 if side == "CALL" else 38
    macd_15m = True
    macd_1h = True
    macd_1d = True

    seller_trap = True  # placeholder

    # ================= FILTERS =================
    if side == "CALL" and rsi_15m <= 60:
        return None
    if side == "PUT" and rsi_15m >= 40:
        return None
    if not (macd_15m and macd_1h and macd_1d):
        return None
    if not seller_trap:
        return None

    return atm, strike, side

# ================= ALERT DEDUP LOGIC =================
def should_send_alert(symbol, strike, side):
    key = f"{strike}_{side}"
    if LAST_ALERT.get(symbol) == key:
        return False
    LAST_ALERT[symbol] = key
    return True

# ================= MAIN SCANNER LOOP =================
def scanner():
    print("🚀 Scanner started")
    while True:
        if not is_market_open():
            time.sleep(30)
            continue

        for symbol in SYMBOLS:
            result = generate_signal(symbol)
            if not result:
                continue

            atm, strike, side = result

            if should_send_alert(symbol, strike, side):
                t = ist_now().strftime("%H:%M:%S")

                alert = {
                    "time": t,
                    "symbol": symbol,
                    "atm": atm,
                    "strike": strike,
                    "side": side
                }

                LATEST_ALERTS.insert(0, alert)
                LATEST_ALERTS[:] = LATEST_ALERTS[:20]

                subject = f"{symbol} {side} BUY CONFIRMED"
                body = f"""
Time: {t}
Symbol: {symbol}
ATM: {atm}
Strike: {strike}
Side: {side}

All filters matched:
✔ Seller trap
✔ RSI
✔ MACD (15m/1h/1d)
"""

                send_mail(subject, body)

        time.sleep(60)

# ================= FLASK DASHBOARD =================
app = Flask(__name__)

HTML = """
<!doctype html>
<html>
<head>
<title>Live Option Alerts</title>
<meta http-equiv="refresh" content="30">
<style>
body { font-family: Arial; background:#0f172a; color:#e5e7eb }
table { border-collapse: collapse; width: 100% }
th, td { padding: 8px; border: 1px solid #334155; text-align:center }
th { background:#1e293b }
.call { color:#22c55e; font-weight:bold }
.put { color:#ef4444; font-weight:bold }
</style>
</head>
<body>
<h2>📊 Latest Alerts (15-Min Candle)</h2>
<table>
<tr><th>Time</th><th>Symbol</th><th>ATM</th><th>Strike</th><th>Side</th></tr>
{% for a in alerts %}
<tr>
<td>{{a.time}}</td>
<td>{{a.symbol}}</td>
<td>{{a.atm}}</td>
<td>{{a.strike}}</td>
<td class="{{'call' if a.side=='CALL' else 'put'}}">{{a.side}}</td>
</tr>
{% endfor %}
</table>

<h3>📌 Tracking Symbols ({{symbols|length}})</h3>
<p>{{ symbols|join(", ") }}</p>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(
        HTML,
        alerts=LATEST_ALERTS,
        symbols=SYMBOLS
    )

# ================= START =================
if __name__ == "__main__":
    threading.Thread(target=scanner, daemon=True).start()
    app.run(host="0.0.0.0", port=5009)
