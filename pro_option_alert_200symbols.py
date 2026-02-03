# ====================== IMPORTS ======================
from nsepython import nse_optionchain_scrapper, nse_get_index_quote
import schedule, time, threading
from flask import Flask, render_template_string
from datetime import datetime, time as dt_time
import smtplib
from email.mime.text import MIMEText

# ====================== EMAIL CONFIG ======================
import os
EMAIL_FROM = os.getenv("EMAIL_FROM")  # set via GitLab secret/env
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO   = os.getenv("EMAIL_TO")

# ====================== SYMBOL CONFIG ======================
# Example of 200+ symbols
SYMBOLS = {
    "NIFTY":50,"BANKNIFTY":100,"FINNIFTY":50,
    "RELIANCE":10,"TCS":10,"HDFCBANK":10,"ICICIBANK":10,"INFY":10,"SBIN":10,"HCLTECH":10,
    "KOTAKBANK":10,"LT":10,"AXISBANK":10,"MARUTI":10,"TITAN":10,"TECHM":10,"BHARTIARTL":10,
    "ITC":10,"WIPRO":10,"JSWSTEEL":10,"HINDUNILVR":10,"ULTRACEMCO":10,"ONGC":10,"BPCL":10,
    "TATASTEEL":10,"M&M":10,"COALINDIA":10,"GRASIM":10,"ADANIENT":10,"ADANIPORTS":10,"HINDALCO":10,
    "EICHERMOT":10,"SUNPHARMA":10,"DRREDDY":10,"DIVISLAB":10,"BAJFINANCE":10,"BAJAJFINSV":10,
    "SBILIFE":10,"HDFCLIFE":10,"ICICIPRULI":10,"INDUSINDBK":10,"CIPLA":10,"TATAMOTORS":10,"VEDL":10,
    "GAIL":10,"HEROMOTOCO":10,"BRITANNIA":10,"HDFCAMC":10,"ADANIGREEN":10,"TATAELXSI":10,
    "APOLLOHOSP":10,"RECLTD":10,"MUTHOOTFIN":10,"ICICIGI":10,"SBICARD":10,"HAVELLS":10,
    "TORNTPHARM":10,"BIOCON":10,"LUPIN":10,"PEL":10,"NAUKRI":10,"DMART":10,"LICHSGFIN":10,
    "INDIGO":10,"BAJAJ-AUTO":10,"HINDPETRO":10,"SHREECEM":10,"ADANITRANS":10,"BANDHANBNK":10,
    "YESBANK":10,"RBLBANK":10,"PNB":10,"FEDERALBNK":10,"AUROPHARMA":10,"CROMPTON":10,"PAGEIND":10,
    "SRF":10,"COLPAL":10,"TATACONSUM":10,"PIDILITIND":10,"AMBUJACEM":10,"INDUSTOWER":10,
    "BOSCHLTD":10,"JUBLFOOD":10,"ASHOKLEY":10,"BPCL":10,"CGPOWER":10,"CANBK":10,"DLF":10,
    "EXIDEIND":10,"GMRINFRA":10,"HINDCOPPER":10,"IBULHSGFIN":10,"IDEA":10,"INFIBEAM":10,
    "JINDALSTEL":10,"JUSTDIAL":10,"L&TFH":10,"LALPATHLAB":10,"MANAPPURAM":10,"M&MFIN":10,
    "MFSL":10,"MINDTREE":10,"MPHASIS":10,"NAVINFLUOR":10,"NIITTECH":10,"NMDC":10,"OBEROIRLTY":10,
    "OFSS":10,"PETRONET":10,"PFC":10,"PGHH":10,"POWERGRID":10,"RAYMOND":10,"RELAXO":10,
    "REPCOHOME":10,"RNAM":10,"SRTRANSFIN":10,"SUNTV":10,"SYNDIBANK":10,"TVSMOTOR":10,"UBL":10,
    "VOLTAS":10,"WELCORP":10,"ZEEL":10
}

# ====================== SETTINGS ======================
MIN_OI = 10000
CONFIRM = 2
SL_PERCENT = 30
TARGET_RATIO = 1
MARKET_START = dt_time(9,15)   # 9:15 AM
MARKET_END   = dt_time(15,30)  # 3:30 PM

signal_counter = {}
dashboard_data = {}

# ====================== EMAIL ======================
def send_mail(subject, body):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
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
            prices,volumes=[],[]
            for d in data["records"]["data"]:
                if "CE" in d: prices.append(d["CE"]["lastPrice"]); volumes.append(d["CE"]["totalTradedVolume"])
                if "PE" in d: prices.append(d["PE"]["lastPrice"]); volumes.append(d["PE"]["totalTradedVolume"])
            if not volumes or sum(volumes)==0: return None
            return sum(p*v for p,v in zip(prices,volumes))/sum(volumes)
    except: return None

# ====================== ANALYSIS ======================
def analyze_symbol(symbol,gap):
    global signal_counter,dashboard_data
    now_time = datetime.now().time()
    if not (MARKET_START <= now_time <= MARKET_END):
        dashboard_data[symbol] = {"status":"Market Closed","strikes":[],"active_strikes":[],"atm":0}
        return

    try:
        data=nse_optionchain_scrapper(symbol)
        spot=data["records"]["underlyingValue"]
        atm=round(spot/gap)*gap
        vwap=get_vwap(symbol)
        if not vwap: dashboard_data[symbol]={"status":"VWAP NA","strikes":[],"active_strikes":[],"atm":atm}; return
    except: dashboard_data[symbol]={"status":"Data NA","strikes":[],"active_strikes":[],"atm":0}; return

    call_sc=put_sc=True
    call_bu=put_bu=True
    strikes_info=[]
    active_strikes=[]

    for d in data["records"]["data"]:
        sp=d["strikePrice"]
        ce=d.get("CE")
        pe=d.get("PE")
        # CALL short covering + PUT buildup
        if atm<sp<=atm+4*gap and ce:
            if ce["changeinOpenInterest"]>-MIN_OI: call_sc=False
            if ce["changeinOpenInterest"]<MIN_OI: call_bu=False
            strikes_info.append({"strike":sp,"CE":ce["lastPrice"],"PE":pe["lastPrice"] if pe else 0})
            if abs(ce["changeinOpenInterest"])>MIN_OI: active_strikes.append(sp)
        # PUT short covering + CALL buildup
        if atm-4*gap<=sp<atm and pe:
            if pe["changeinOpenInterest"]>-MIN_OI: put_sc=False
            if pe["changeinOpenInterest"]<MIN_OI: put_bu=False
            if not any(s["strike"]==sp for s in strikes_info):
                strikes_info.append({"strike":sp,"CE":ce["lastPrice"] if ce else 0,"PE":pe["lastPrice"]})
            if abs(pe["changeinOpenInterest"])>MIN_OI: active_strikes.append(sp)

    total_vol=sum([d["CE"]["totalTradedVolume"] if "CE" in d else 0 for d in data["records"]["data"]])
    if total_vol<5000: dashboard_data[symbol]={"status":"Low Volume","strikes":strikes_info,"active_strikes":active_strikes,"atm":atm}; return
    if abs(spot-vwap)/spot<0.002: dashboard_data[symbol]={"status":"Sideways","strikes":strikes_info,"active_strikes":active_strikes,"atm":atm}; return

    # CALL BUY signal (example)
    if call_sc and put_bu and spot>vwap:
        signal_counter[symbol]=signal_counter.get(symbol,0)+1
        if signal_counter[symbol]>=CONFIRM:
            sl=round(spot*SL_PERCENT/100,2)
            target=round(sl*TARGET_RATIO,2)
            dashboard_data[symbol]={"status":f"CALL BUY | SL:{sl} | Target:{target}",
                                     "strikes":strikes_info,"active_strikes":active_strikes,"atm":atm}
            send_mail(f"📈 CALL BUY ALERT – {symbol}",f"Spot:{spot}\nATM:{atm}\nVWAP:{vwap:.2f}\nSL:{sl}\nTarget:{target}")
            signal_counter[symbol]=0
        else:
            dashboard_data[symbol]={"status":"CALL BUY (1st candle)","strikes":strikes_info,"active_strikes":active_strikes,"atm":atm}
        return

    # PUT BUY signal (example)
    if put_sc and call_bu and spot<vwap:
        signal_counter[symbol]=signal_counter.get(symbol,0)+1
        if signal_counter[symbol]>=CONFIRM:
            sl=round(spot*SL_PERCENT/100,2)
            target=round(sl*TARGET_RATIO,2)
            dashboard_data[symbol]={"status":f"PUT BUY | SL:{sl} | Target:{target}",
                                     "strikes":strikes_info,"active_strikes":active_strikes,"atm":atm}
            send_mail(f"📉 PUT BUY ALERT – {symbol}",f"Spot:{spot}\nATM:{atm}\nVWAP:{vwap:.2f}\nSL:{sl}\nTarget:{target}")
            signal_counter[symbol]=0
        else:
            dashboard_data[symbol]={"status":"PUT BUY (1st candle)","strikes":strikes_info,"active_strikes":active_strikes,"atm":atm}
        return

    dashboard_data[symbol]={"status":"No Trade","strikes":strikes_info,"active_strikes":active_strikes,"atm":atm}

# ====================== DASHBOARD ======================
app = Flask(__name__)

TEMPLATE = """
<html>
<head>
<title>📊 Multi-Strike Option Dashboard (200+ Symbols)</title>
<meta http-equiv="refresh" content="15">
<style>
body{font-family:Arial;background:#f5f5f5;}
table{border-collapse:collapse;width:95%;margin:auto;}
th,td{border:1px solid #888;padding:5px;text-align:center;}
th{background:#333;color:#fff;}
tr:nth-child(even){background:#eee;}
.call{background:#b6fcb6;}    /* Above ATM */
.put{background:#fcb6b6;}     /* Below ATM */
.side{background:#ccc;}        /* Sideways / no trade */
.active{font-weight:bold;color:#0000ff;}
</style>
</head>
<body>
<h1 style="text-align:center;">📊 Multi-Strike Option Dashboard (200+ Symbols)</h1>
<table>
<tr><th>Symbol</th><th>Status</th><th>Strike</th><th>CE</th><th>PE</th></tr>
{% for sym,data in dashboard_data.items() %}
    {% if data.strikes %}
        {% for s in data.strikes %}
            <tr class="{% if s.strike >= data.atm %}call{% elif s.strike < data.atm %}put{% else %}side{% endif %}">
                <td>{{sym}}</td>
                <td>{{data.status}}</td>
                <td {% if s.strike in data.active_strikes %}class="active"{% endif %}>{{s.strike}}</td>
                <td>{{s.CE}}</td>
                <td>{{s.PE}}</td>
            </tr>
        {% endfor %}
    {% else %}
        <tr class="side">
            <td>{{sym}}</td>
            <td>{{data.status}}</td>
            <td>-</td>
            <td>-</td>
            <td>-</td>
        </tr>
    {% endif %}
{% endfor %}
</table>
<p style="text-align:center;">Last Update: {{last_update}}</p>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(TEMPLATE,last_update=datetime.now().strftime("%H:%M:%S"),
                                  dashboard_data=dashboard_data)

def run_flask():
    app.run(host="0.0.0.0", port=5009)

# ====================== ENGINE ======================
def run_engine():
    print(f"\n🔍 Scan @ {datetime.now().strftime('%H:%M:%S')}")
    for sym,gap in SYMBOLS.items():
        analyze_symbol(sym,gap)
        time.sleep(1)  # rate-limit API calls

schedule.every(1).minutes.do(run_engine)

# ====================== THREADING ======================
threading.Thread(target=run_flask).start()
print("🚀 LIVE Multi-Strike Option Dashboard + Email Alerts Started")

while True:
    schedule.run_pending()
    time.sleep(1)
