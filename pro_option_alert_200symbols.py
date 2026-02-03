# ====================== IMPORTS ======================
import os
import time
import threading
from datetime import datetime, time as dtime
import schedule
import smtplib
from email.mime.text import MIMEText

from flask import Flask, render_template_string
import pytz

from nsepython import nse_optionchain_scrapper, nse_get_index_quote

# ====================== EMAIL CONFIG ======================
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
EMAIL_TO   = os.environ.get("EMAIL_TO")

# ====================== NSE SYMBOLS ======================
SYMBOLS = {
    "NIFTY":50,"BANKNIFTY":100,"FINNIFTY":50,
    "RELIANCE":10,"TCS":10,"HDFCBANK":10,"ICICIBANK":10,"INFY":10,
    "SBIN":10,"HCLTECH":10,"KOTAKBANK":10,"LT":10,"AXISBANK":10,
    "MARUTI":10,"TITAN":10,"TECHM":10,"BHARTIARTL":10,"ITC":10,
    "WIPRO":10,"JSWSTEEL":10,"HINDUNILVR":10,"ULTRACEMCO":10,
    "ONGC":10,"BPCL":10,"TATASTEEL":10,"M&M":10,"COALINDIA":10,
    "GRASIM":10,"ADANIENT":10,"ADANIPORTS":10,"HINDALCO":10,
    "EICHERMOT":10,"SUNPHARMA":10,"DRREDDY":10,"DIVISLAB":10,
    "BAJFINANCE":10,"BAJAJFINSV":10,"SBILIFE":10,"HDFCLIFE":10,
    "ICICIPRULI":10,"INDUSINDBK":10,"CIPLA":10,"TATAMOTORS":10,
    "VEDL":10,"GAIL":10,"HEROMOTOCO":10,"BRITANNIA":10,
    "HDFCAMC":10,"ADANIGREEN":10,"TATAELXSI":10,"APOLLOHOSP":10
}
# You can expand up to 200 symbols

# ====================== SETTINGS ======================
MIN_OI = 10000
CONFIRM = 2
SL_PERCENT = 30
TARGET_RATIO = 1

signal_counter = {}
dashboard_data = {}

INDIA_TZ = pytz.timezone("Asia/Kolkata")

# ====================== EMAIL FUNCTION ======================
def send_mail(subject, body):
    if not EMAIL_FROM or not EMAIL_PASS or not EMAIL_TO:
        print("⚠️ Email not configured")
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print(f"📧 Alert sent: {subject}")
    except Exception as e:
        print(f"Email error: {e}")

# ====================== MARKET HOURS CHECK ======================
def is_market_open():
    now = datetime.now(INDIA_TZ).time()
    return dtime(9,15) <= now <= dtime(15,30)

# ====================== VWAP FUNCTION ======================
def get_vwap(symbol):
    try:
        if "NIFTY" in symbol or "BANK" in symbol or "FIN" in symbol:
            data = nse_get_index_quote(symbol)
            return data["lastPrice"]
        else:
            data = nse_optionchain_scrapper(symbol)
            prices, volumes = [], []
            for d in data["records"]["data"]:
                if "CE" in d:
                    prices.append(d["CE"]["lastPrice"])
                    volumes.append(d["CE"]["totalTradedVolume"])
                if "PE" in d:
                    prices.append(d["PE"]["lastPrice"])
                    volumes.append(d["PE"]["totalTradedVolume"])
            if not volumes or sum(volumes) == 0:
                return None
            return sum(p*v for p,v in zip(prices, volumes))/sum(volumes)
    except:
        return None

# ====================== ANALYSIS FUNCTION ======================
def analyze_symbol(symbol, gap):
    global signal_counter, dashboard_data

    if not is_market_open():
        dashboard_data[symbol] = {"status":"Market Closed", "strikes":[],"active_strikes":[]}
        return

    try:
        data = nse_optionchain_scrapper(symbol)
        spot = data["records"]["underlyingValue"]
        atm = round(spot/gap)*gap
        vwap = get_vwap(symbol)
        if not vwap:
            dashboard_data[symbol] = {"status":"VWAP NA","strikes":[],"active_strikes":[]}
            return
    except:
        dashboard_data[symbol] = {"status":"Data NA","strikes":[],"active_strikes":[]}
        return

    strikes_info = []
    active_strikes = []
    call_signal = put_signal = False

    for d in data["records"]["data"]:
        sp = d["strikePrice"]
        ce = d.get("CE")
        pe = d.get("PE")

        # CALL SIDE
        if atm < sp <= atm+4*gap and ce:
            if ce["changeinOpenInterest"] > MIN_OI:
                call_signal = True
            strikes_info.append({"strike":sp,"CE":ce["lastPrice"],"PE":pe["lastPrice"] if pe else 0})
            if abs(ce["changeinOpenInterest"]) > MIN_OI: active_strikes.append(sp)

        # PUT SIDE
        if atm-4*gap <= sp < atm and pe:
            if pe["changeinOpenInterest"] > MIN_OI:
                put_signal = True
            if not any(s["strike"]==sp for s in strikes_info):
                strikes_info.append({"strike":sp,"CE":ce["lastPrice"] if ce else 0,"PE":pe["lastPrice"]})
            if abs(pe["changeinOpenInterest"]) > MIN_OI: active_strikes.append(sp)

    # Decide signal
    status_text = "No Trade"
    if call_signal:
        status_text = "CALL BUY"
        send_mail(f"📈 CALL BUY ALERT – {symbol}", f"Spot:{spot}\nATM:{atm}\nVWAP:{vwap:.2f}")

    if put_signal:
        status_text = "PUT BUY"
        send_mail(f"📉 PUT BUY ALERT – {symbol}", f"Spot:{spot}\nATM:{atm}\nVWAP:{vwap:.2f}")

    dashboard_data[symbol] = {"status":status_text,"strikes":strikes_info,"active_strikes":active_strikes}

# ====================== DASHBOARD ======================
app = Flask(__name__)

TEMPLATE = """
<html>
<head>
<title>📊 Live Option Alerts</title>
<meta http-equiv="refresh" content="30">
<style>
body{font-family:Arial;background:#f5f5f5;}
table{border-collapse:collapse;width:95%;margin:auto;}
th,td{border:1px solid #888;padding:5px;text-align:center;}
th{background:#333;color:#fff;}
tr:nth-child(even){background:#eee;}
.call{background:#b6fcb6;}
.put{background:#fcb6b6;}
.side{background:#ccc;}
.active{font-weight:bold;color:#0000ff;}
</style>
</head>
<body>
<h1 style="text-align:center;">📊 Live Option Alerts (15-Min Candle)</h1>
<table>
<tr><th>Symbol</th><th>Status</th><th>Strike</th><th>CE</th><th>PE</th></tr>
{% for sym,data in dashboard_data.items() %}
    {% for s in data.get('strikes',[{}]) %}
    <tr class="{% if 'CALL' in data.status %}call{% elif 'PUT' in data.status %}put{% else %}side{% endif %}">
        <td>{{sym}}</td>
        <td>{{data.status}}</td>
        <td {% if s.strike in data.active_strikes %}class="active"{% endif %}>{{s.get('strike','-')}}</td>
        <td>{{s.get('CE','-')}}</td>
        <td>{{s.get('PE','-')}}</td>
    </tr>
    {% endfor %}
{% endfor %}
</table>
<p style="text-align:center;">Last Update: {{last_update}}</p>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(TEMPLATE, last_update=datetime.now(INDIA_TZ).strftime("%H:%M:%S"), dashboard_data=dashboard_data)

def run_flask():
    app.run(host="0.0.0.0", port=5009)

# ====================== MASTER ENGINE ======================
def run_engine():
    print(f"\n🔍 Scan @ {datetime.now(INDIA_TZ).strftime('%H:%M:%S')}")
    for sym, gap in SYMBOLS.items():
        analyze_symbol(sym, gap)
        time.sleep(1.0)  # To avoid NSE throttling

schedule.every(1).minutes.do(run_engine)

# ====================== THREADING ======================
threading.Thread(target=run_flask).start()
print("🚀 Live Option Dashboard Started")

while True:
    schedule.run_pending()
    time.sleep(1)
