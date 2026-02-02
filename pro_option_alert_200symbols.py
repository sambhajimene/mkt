# ====================== IMPORTS ======================
from nsepython import nse_optionchain_scrapper, nse_get_index_quote
import schedule, time, threading
from flask import Flask, render_template_string
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# ====================== EMAIL CONFIG ======================
EMAIL_FROM = "your_email@gmail.com"
EMAIL_PASS = "your_16_char_app_password"
EMAIL_TO   = "your_email@gmail.com"

# ====================== SYMBOL CONFIG ======================
SYMBOLS = {
    "NIFTY":50,"BANKNIFTY":100,"FINNIFTY":50,
    "RELIANCE":10,"TCS":10,"HDFCBANK":10,"ICICIBANK":10,"INFY":10,
    # add more symbols as needed
}

# ====================== SETTINGS ======================
MIN_OI = 10000
CONFIRM = 2
SL_PERCENT = 30
TARGET_RATIO = 1

signal_counter = {}
dashboard_data = {}

# ====================== EMAIL ======================
def send_mail(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    try:
        server = smtplib.SMTP("smtp.gmail.com",587)
        server.starttls()
        server.login(EMAIL_FROM,EMAIL_PASS)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Email error: {e}")

# ====================== VWAP ======================
def get_vwap(symbol):
    try:
        if "NIFTY" in symbol or "BANK" in symbol or "FIN" in symbol:
            data = nse_get_index_quote(symbol)
            return data["lastPrice"]
        else:
            data = nse_optionchain_scrapper(symbol)
            prices, volumes = [], []
            for d in data["records"]["data"]:
                if "CE" in d: prices.append(d["CE"]["lastPrice"]); volumes.append(d["CE"]["totalTradedVolume"])
                if "PE" in d: prices.append(d["PE"]["lastPrice"]); volumes.append(d["PE"]["totalTradedVolume"])
            if not volumes or sum(volumes) == 0: return None
            return sum(p*v for p,v in zip(prices,volumes))/sum(volumes)
    except:
        return None

# ====================== ANALYSIS ======================
def analyze_symbol(symbol, gap):
    global signal_counter, dashboard_data
    try:
        data = nse_optionchain_scrapper(symbol)
        spot = data["records"]["underlyingValue"]
        atm = round(spot / gap) * gap
        vwap = get_vwap(symbol)
        if not vwap: return
    except:
        return

    call_sc = put_sc = True
    call_bu = put_bu = True
    strikes_info = []
    active_strikes = []

    for d in data["records"]["data"]:
        sp = d["strikePrice"]
        ce = d.get("CE")
        pe = d.get("PE")

        # CALL side (above ATM)
        if atm < sp <= atm + 4*gap and ce:
            if ce["changeinOpenInterest"] > -MIN_OI: call_sc = False
            if ce["changeinOpenInterest"] < MIN_OI: call_bu = False
            strikes_info.append({"strike": sp, "CE": ce["lastPrice"], "PE": pe["lastPrice"] if pe else 0})
            if abs(ce["changeinOpenInterest"]) > MIN_OI: active_strikes.append(sp)

        # PUT side (below ATM)
        if atm - 4*gap <= sp < atm and pe:
            if pe["changeinOpenInterest"] > -MIN_OI: put_sc = False
            if pe["changeinOpenInterest"] < MIN_OI: put_bu = False
            if not any(s["strike"] == sp for s in strikes_info):
                strikes_info.append({"strike": sp, "CE": ce["lastPrice"] if ce else 0, "PE": pe["lastPrice"]})
            if abs(pe["changeinOpenInterest"]) > MIN_OI: active_strikes.append(sp)

    total_vol = sum([d["CE"]["totalTradedVolume"] if "CE" in d else 0 for d in data["records"]["data"]])
    if total_vol < 5000: return
    if abs(spot - vwap)/spot < 0.002: return

    # CALL BUY ALERT
    if call_sc and put_bu and spot > vwap:
        signal_counter[symbol] = signal_counter.get(symbol, 0) + 1
        if signal_counter[symbol] >= CONFIRM:
            sl = round(spot * SL_PERCENT / 100, 2)
            target = round(sl * TARGET_RATIO, 2)
            dashboard_data[symbol] = {
                "side": "CALL",
                "atm": atm,
                "strikes": strikes_info,
                "active_strikes": active_strikes,
                "spot": spot,
                "sl": sl,
                "target": target
            }
            send_mail(f"📈 CALL BUY ALERT – {symbol}",
                      f"Spot:{spot}\nATM:{atm}\nVWAP:{vwap:.2f}\nSL:{sl}\nTarget:{target}")
            signal_counter[symbol] = 0
        return

    # PUT BUY ALERT
    if put_sc and call_bu and spot < vwap:
        signal_counter[symbol] = signal_counter.get(symbol, 0) + 1
        if signal_counter[symbol] >= CONFIRM:
            sl = round(spot * SL_PERCENT / 100, 2)
            target = round(sl * TARGET_RATIO, 2)
            dashboard_data[symbol] = {
                "side": "PUT",
                "atm": atm,
                "strikes": strikes_info,
                "active_strikes": active_strikes,
                "spot": spot,
                "sl": sl,
                "target": target
            }
            send_mail(f"📉 PUT BUY ALERT – {symbol}",
                      f"Spot:{spot}\nATM:{atm}\nVWAP:{vwap:.2f}\nSL:{sl}\nTarget:{target}")
            signal_counter[symbol] = 0
        return

# ====================== DASHBOARD ======================
app = Flask(__name__)

TEMPLATE = """
<html>
<head>
<title>📊 Multi-Strike Option Alerts</title>
<meta http-equiv="refresh" content="60">
<style>
body{font-family:Arial;background:#f5f5f5;}
table{border-collapse:collapse;width:90%;margin:auto;}
th,td{border:1px solid #888;padding:5px;text-align:center;}
th{background:#333;color:#fff;}
.call{background:#b6fcb6;}   /* CALL side */
.put{background:#fcb6b6;}    /* PUT side */
.atm{background:#ffff99;}     /* ATM strike */
.active{font-weight:bold;color:#0000ff;}
</style>
</head>
<body>
<h1 style="text-align:center;">📊 Multi-Strike Option Alerts</h1>
{% if dashboard_data %}
<table>
<tr><th>Symbol</th><th>Side</th><th>Spot</th><th>SL</th><th>Target</th><th>Strike</th><th>CE</th><th>PE</th></tr>
{% for sym,data in dashboard_data.items() %}
    {% for s in data.strikes %}
    <tr class="{% if data.side=='CALL' %}call{% elif data.side=='PUT' %}put{% endif %}">
        <td>{{sym}}</td>
        <td>{{data.side}}</td>
        <td>{{data.spot}}</td>
        <td>{{data.sl}}</td>
        <td>{{data.target}}</td>
        <td {% if s.strike==data.atm %}class="atm"{% elif s.strike in data.active_strikes %}class="active"{% endif %}>{{s.strike}}</td>
        <td>{{s.CE}}</td>
        <td>{{s.PE}}</td>
    </tr>
    {% endfor %}
{% endfor %}
</table>
{% else %}
<p style="text-align:center;">No active alerts currently.</p>
{% endif %}
<p style="text-align:center;">Last Update: {{last_update}}</p>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(TEMPLATE,
                                  last_update=datetime.now().strftime("%H:%M:%S"),
                                  dashboard_data=dashboard_data)

def run_flask():
    app.run(host="0.0.0.0", port=5009)

# ====================== MASTER ENGINE ======================
def run_engine():
    for sym, gap in SYMBOLS.items():
        analyze_symbol(sym, gap)
        time.sleep(1.2)

schedule.every(1).minutes.do(run_engine)

# ====================== THREADING ======================
threading.Thread(target=run_flask).start()
print("🚀 LIVE Multi-Strike Option Dashboard + Email Alerts Started")

while True:
    schedule.run_pending()
    time.sleep(1)
