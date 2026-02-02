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

# ====================== SYMBOL CONFIG (200+ symbols) ======================
SYMBOLS = {
    "NIFTY":50,"BANKNIFTY":100,"FINNIFTY":50,
    "RELIANCE":10,"TCS":10,"HDFCBANK":10,"ICICIBANK":10,"INFY":10,"SBIN":10,"HCLTECH":10,
    "KOTAKBANK":10,"LT":10,"AXISBANK":10,"MARUTI":10,"TITAN":10,"TECHM":10,"BHARTIARTL":10,
    "ITC":10,"WIPRO":10,"JSWSTEEL":10,"HINDUNILVR":10,"ULTRACEMCO":10,"ONGC":10,"BPCL":10,
    "TATASTEEL":10,"M&M":10,"COALINDIA":10,"GRASIM":10,"ADANIENT":10,"ADANIPORTS":10,"HINDALCO":10,
    "EICHERMOT":10,"SUNPHARMA":10,"DRREDDY":10,"DIVISLAB":10,"BAJFINANCE":10,"BAJAJFINSV":10,
    "SBILIFE":10,"HDFCLIFE":10,"ICICIPRULI":10,"INDUSINDBK":10,"CIPLA":10,"TATAMOTORS":10,"VEDL":10,
    "GAIL":10,"HEROMOTOCO":10,"BRITANNIA":10,"HDFCAMC":10,"ADANIGREEN":10,"TATAELXSI":10,"APOLLOHOSP":10,
    "RECLTD":10,"MUTHOOTFIN":10,"ICICIGI":10,"SBICARD":10,"HAVELLS":10,"TORNTPHARM":10,"BIOCON":10,
    "LUPIN":10,"PEL":10,"NAUKRI":10,"DMART":10,"LICHSGFIN":10,"INDIGO":10,"BAJAJ-AUTO":10,"HINDPETRO":10,
    "SHREECEM":10,"ADANITRANS":10,"BANDHANBNK":10,"YESBANK":10,"RBLBANK":10,"PNB":10,"FEDERALBNK":10,
    "AUROPHARMA":10,"CROMPTON":10,"PAGEIND":10,"SRF":10,"COLPAL":10,"TATACONSUM":10,"PIDILITIND":10,
    "AMBUJACEM":10,"INDUSTOWER":10,"BOSCHLTD":10,"JUBLFOOD":10,"ASHOKLEY":10,"BPCL":10,"CGPOWER":10,
    "CANBK":10,"DLF":10,"EXIDEIND":10,"GMRINFRA":10,"HINDCOPPER":10,"IBULHSGFIN":10,"IDEA":10,
    "INFIBEAM":10,"JINDALSTEL":10,"JUSTDIAL":10,"L&TFH":10,"LALPATHLAB":10,"MANAPPURAM":10,"M&MFIN":10,
    "MFSL":10,"MINDTREE":10,"MPHASIS":10,"NAVINFLUOR":10,"NIITTECH":10,"NMDC":10,"OBEROIRLTY":10,
    "OFSS":10,"PETRONET":10,"PFC":10,"PGHH":10,"POWERGRID":10,"RAYMOND":10,"RELAXO":10,"REPCOHOME":10,
    "RNAM":10,"SRTRANSFIN":10,"SUNTV":10,"SYNDIBANK":10,"TVSMOTOR":10,"UBL":10,"VOLTAS":10,
    "WELCORP":10,"ZEEL":10
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
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASS)
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
            return sum(p*v for p,v in zip(prices,volumes)) / sum(volumes)
    except:
        return None

# ====================== ANALYSIS ======================
def analyze_symbol(symbol, gap):
    global signal_counter, dashboard_data
    try:
        data = nse_optionchain_scrapper(symbol)
        spot = data["records"]["underlyingValue"]
        atm = round(spot/gap)*gap
        vwap = get_vwap(symbol)
        if not vwap: dashboard_data[symbol] = {"status":"VWAP NA"}; return
    except: 
        dashboard_data[symbol] = {"status":"Data NA"}; return

    call_sc = put_sc = True
    call_bu = put_bu = True
    strikes_info = []
    active_strikes = []

    for d in data["records"]["data"]:
        sp = d["strikePrice"]
        ce = d.get("CE")
        pe = d.get("PE")

        if atm < sp <= atm+4*gap and ce:
            if ce["changeinOpenInterest"] > -MIN_OI: call_sc = False
            if ce["changeinOpenInterest"] < MIN_OI: call_bu = False
            strikes_info.append({"strike": sp, "CE": ce["lastPrice"], "PE": pe["lastPrice"] if pe else 0})
            if abs(ce["changeinOpenInterest"]) > MIN_OI: active_strikes.append(sp)

        if atm-4*gap <= sp < atm and pe:
            if pe["changeinOpenInterest"] > -MIN_OI: put_sc = False
            if pe["changeinOpenInterest"] < MIN_OI: put_bu = False
            if not any(s["strike"]==sp for s in strikes_info):
                strikes_info.append({"strike": sp, "CE": ce["lastPrice"] if ce else 0, "PE": pe["lastPrice"]})
            if abs(pe["changeinOpenInterest"]) > MIN_OI: active_strikes.append(sp)

    total_vol = sum([d["CE"]["totalTradedVolume"] if "CE" in d else 0 for d in data["records"]["data"]])
    if total_vol < 5000: signal_counter[symbol]=0; dashboard_data[symbol] = {"status":"Low Volume","strikes":strikes_info,"active_strikes":active_strikes}; return
    if abs(spot-vwap)/spot < 0.002: signal_counter[symbol]=0; dashboard_data[symbol] = {"status":"Sideways","strikes":strikes_info,"active_strikes":active_strikes}; return

    # CALL BUY
    if call_sc and put_bu and spot > vwap:
        signal_counter[symbol] = signal_counter.get(symbol,0)+1
        if signal_counter[symbol] >= CONFIRM:
            sl = round(spot*SL_PERCENT/100,2)
            target = round(sl*TARGET_RATIO,2)
            dashboard_data[symbol] = {"status":f"CALL BUY | SL:{sl} | Target:{target}","strikes":strikes_info,"active_strikes":active_strikes}
            send_mail(f"📈 CALL BUY ALERT – {symbol}", f"Spot:{spot}\nATM:{atm}\nVWAP:{vwap:.2f}\nSL:{sl}\nTarget:{target}")
            signal_counter[symbol] = 0
        else:
            dashboard_data[symbol] = {"status":"CALL BUY (1st candle)","strikes":strikes_info,"active_strikes":active_strikes}
        return

    # PUT BUY
    if put_sc and call_bu and spot < vwap:
        signal_counter[symbol] = signal_counter.get(symbol,0)+1
        if signal_counter[symbol] >= CONFIRM:
            sl = round(spot*SL_PERCENT/100,2)
            target = round(sl*TARGET_RATIO,2)
            dashboard_data[symbol] = {"status":f"PUT BUY | SL:{sl} | Target:{target}","strikes":strikes_info,"active_strikes":active_strikes}
            send_mail(f"📉 PUT BUY ALERT – {symbol}", f"Spot:{spot}\nATM:{atm}\nVWAP:{vwap:.2f}\nSL:{sl}\nTarget:{target}")
            signal_counter[symbol] = 0
        else:
            dashboard_data[symbol] = {"status":"PUT BUY (1st candle)","strikes":strikes_info,"active_strikes":active_strikes}
        return

    # Mark symbols with no active trade as inactive (won't show)
    dashboard_data[symbol] = {"status":"No Trade","strikes":strikes_info,"active_strikes":active_strikes}

# ====================== DASHBOARD ======================
app = Flask(__name__)

TEMPLATE = """
<html>
<head>
<title>📊 Active Option Alerts</title>
<meta http-equiv="refresh" content="10">
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>
body{font-family:Arial;background:#f5f5f5;}
table{border-collapse:collapse;width:95%;margin:auto;}
th,td{border:1px solid #888;padding:5px;text-align:center;}
th{background:#333;color:#fff;}
tr:nth-child(even){background:#eee;}
.call{background:#b6fcb6;}
.put{background:#fcb6b6;}
.active{font-weight:bold;color:#0000ff;}
</style>
</head>
<body>
<h1 style="text-align:center;">📊 Active Option Alerts Dashboard</h1>
{% if dashboard_data %}
<table>
<tr><th>Symbol</th><th>Status</th><th>Strike</th><th>CE</th><th>PE</th></tr>
{% for sym,data in dashboard_data.items() %}
    {% if "CALL BUY" in data.status or "PUT BUY" in data.status %}
        {% for s in data.get('strikes',[]) %}
        <tr class="{% if 'CALL' in data.status %}call{% elif 'PUT' in data.status %}put{% endif %}">
            <td>{{sym}}</td>
            <td>{{data.status}}</td>
            <td {% if s.strike in data.active_strikes %}class="active"{% endif %}>{{s.get('strike','-')}}</td>
            <td>{{s.get('CE','-')}}</td>
            <td>{{s.get('PE','-')}}</td>
        </tr>
        {% endfor %}
    {% endif %}
{% endfor %}
</table>

<h2 style="text-align:center;">Live Option Premium Chart (ATM ±4 Strikes)</h2>
<div id="chart" style="width:95%;height:400px;margin:auto;"></div>
<script>
var symbols={{dashboard_data|tojson}};
var data=[];

for(var sym in symbols){
    var s = symbols[sym];
    if (!("CALL BUY" in s.status || "PUT BUY" in s.status)) continue;
    var ce_x=[],ce_y=[],pe_x=[],pe_y=[];
    for(var i=0;i<s.strikes.length;i++){
        ce_x.push(s.strikes[i].strike);
        ce_y.push(s.strikes[i].CE);
        pe_x.push(s.strikes[i].strike);
        pe_y.push(s.strikes[i].PE);
    }
    data.push({x:ce_x,y:ce_y,type:'scatter',mode:'lines+markers',name:sym+' CE'});
    data.push({x:pe_x,y:pe_y,type:'scatter',mode:'lines+markers',name:sym+' PE'});
}

Plotly.newPlot('chart',data,{margin:{t:0}});
</script>
<p style="text-align:center;">Last Update: {{last_update}}</p>
{% else %}
<p style="text-align:center;font-size:18px;">No active alerts currently.</p>
{% endif %}
</body>
</html>
"""

@app.route("/")
def dashboard():
    # Only show active alerts
    active_symbols = {sym:data for sym,data in dashboard_data.items()
                      if "CALL BUY" in data["status"] or "PUT BUY" in data["status"]}
    return render_template_string(TEMPLATE,
                                  last_update=datetime.now().strftime("%H:%M:%S"),
                                  dashboard_data=active_symbols)

# ====================== MASTER ENGINE ======================
def run_engine():
    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n🔍 Scan @ {now}")
    for sym, gap in SYMBOLS.items():
        analyze_symbol(sym, gap)
        time.sleep(1.2)

schedule.every(1).minutes.do(run_engine)

# ====================== THREADING ======================
threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5009)).start()
print("🚀 LIVE Multi-Strike Option Dashboard + Email Alerts Started (Active Symbols Only)")

while True:
    schedule.run_pending()
    time.sleep(1)
