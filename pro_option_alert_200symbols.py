# ====================== IMPORTS ======================
from nsepython import nse_optionchain_scrapper, nse_get_index_quote
import schedule, time, threading
from flask import Flask, render_template_string
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os, pandas as pd
import yfinance as yf

# ====================== EMAIL CONFIG ======================
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
EMAIL_TO   = os.environ.get("EMAIL_TO") or EMAIL_FROM

# ====================== SYMBOL CONFIG ======================
SYMBOLS = {
    "NIFTY":50,"BANKNIFTY":100,"FINNIFTY":50,
    # Add more symbols as before
}

MIN_OI = 10000
CONFIRM = 2
SL_PERCENT = 30
TARGET_RATIO = 1

signal_counter = {}
dashboard_data = {}
alerts_history = []

# ====================== EMAIL FUNCTION ======================
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
        print(f"📧 Mail sent: {subject}")
    except Exception as e:
        print(f"Email error: {e}")

# ====================== TECHNICAL INDICATORS ======================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain/loss
    return 100 - (100/(1+rs))

def macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

def check_tech(symbol):
    """Returns True if RSI+MACD conditions met for CALL/PUT"""
    ticker = symbol if symbol.isalpha() else "^"+symbol
    df_15 = yf.download(ticker, period="2d", interval="15m", progress=False)
    df_1h = yf.download(ticker, period="5d", interval="1h", progress=False)
    df_1d = yf.download(ticker, period="1mo", interval="1d", progress=False)
    if df_15.empty or df_1h.empty or df_1d.empty:
        return None, None

    # Latest RSI 15-min
    rsi_15 = rsi(df_15['Close']).iloc[-1]
    macd_15, sig_15 = macd(df_15['Close'])
    macd_1h, sig_1h = macd(df_1h['Close'])
    macd_1d, sig_1d = macd(df_1d['Close'])

    # Conditions
    call_cond = (rsi_15>60) and (macd_15.iloc[-1]>sig_15.iloc[-1]) and \
                (macd_1h.iloc[-1]>sig_1h.iloc[-1]) and (macd_1d.iloc[-1]>sig_1d.iloc[-1])
    put_cond  = (rsi_15<40) and (macd_15.iloc[-1]<sig_15.iloc[-1]) and \
                (macd_1h.iloc[-1]<sig_1h.iloc[-1]) and (macd_1d.iloc[-1]<sig_1d.iloc[-1])

    return call_cond, put_cond

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
            if not volumes or sum(volumes)==0: return None
            return sum(p*v for p,v in zip(prices,volumes))/sum(volumes)
    except:
        return None

# ====================== ANALYSIS ======================
def analyze_symbol(symbol, gap):
    global signal_counter, dashboard_data, alerts_history
    try:
        data = nse_optionchain_scrapper(symbol)
        spot = data["records"]["underlyingValue"]
        atm = round(spot/gap)*gap
        vwap = get_vwap(symbol)
        if not vwap:
            dashboard_data[symbol] = {"status":"VWAP NA"}
            return
    except:
        dashboard_data[symbol] = {"status":"Data NA"}
        return

    # Active strike info
    strikes_info = []
    active_strikes = []
    for d in data["records"]["data"]:
        sp = d["strikePrice"]
        ce = d.get("CE")
        pe = d.get("PE")
        if atm-4*gap<=sp<=atm+4*gap:
            strikes_info.append({"strike":sp,
                                 "CE":ce["lastPrice"] if ce else 0,
                                 "PE":pe["lastPrice"] if pe else 0})
            if (ce and abs(ce["changeinOpenInterest"])>MIN_OI) or \
               (pe and abs(pe["changeinOpenInterest"])>MIN_OI):
                active_strikes.append(sp)

    # Volume + Sideways Filter
    total_vol = sum([d.get("CE",{}).get("totalTradedVolume",0) for d in data["records"]["data"]])
    if total_vol < 5000 or abs(spot-vwap)/spot < 0.002:
        dashboard_data[symbol] = {"status":"No Trade / Sideways","strikes":strikes_info,"active_strikes":active_strikes}
        return

    # ====== Technical Filters ======
    call_tech, put_tech = check_tech(symbol)
    if call_tech: signal="CALL BUY"
    elif put_tech: signal="PUT BUY"
    else: signal=None

    if signal:
        signal_counter[symbol] = signal_counter.get(symbol,0)+1
        if signal_counter[symbol]>=CONFIRM:
            sl = round(spot*SL_PERCENT/100,2)
            target = round(sl*TARGET_RATIO,2)
            dashboard_data[symbol] = {"status":f"{signal} | SL:{sl} | Target:{target}",
                                     "strikes":strikes_info,"active_strikes":active_strikes}
            # ====== Mail ======
            mail_body = f"""
Time: {datetime.now().strftime("%H:%M:%S")}
Symbol: {symbol}
Signal: {signal}
Spot: {spot}
ATM: {atm}
VWAP: {vwap:.2f}
Stoploss: {sl}
Target: {target}
Active Strikes: {active_strikes}
"""
            send_mail(f"📈 {signal} ALERT – {symbol}", mail_body)
            alerts_history.append(mail_body)
            signal_counter[symbol]=0
        else:
            dashboard_data[symbol] = {"status":f"{signal} (1st candle)","strikes":strikes_info,"active_strikes":active_strikes}
    else:
        dashboard_data[symbol] = {"status":"No Trade","strikes":strikes_info,"active_strikes":active_strikes}

# ====================== DASHBOARD ======================
app=Flask(__name__)
TEMPLATE="""
<html>
<head><title>📊 Live Option Alerts (15-Min Candle)</title>
<meta http-equiv="refresh" content="10">
<style>
body{font-family:Arial;background:#f5f5f5;}
table{border-collapse:collapse;width:95%;margin:auto;}
th,td{border:1px solid #888;padding:5px;text-align:center;}
th{background:#333;color:#fff;}
.call{background:#b6fcb6;}
.put{background:#fcb6b6;}
.side{background:#ccc;}
.active{font-weight:bold;color:#0000ff;}
</style></head>
<body>
<h1 style="text-align:center;">📊 Live Option Alerts (15-Min Candle)</h1>
<table>
<tr><th>Time</th><th>Symbol</th><th>ATM</th><th>Strike</th><th>Side</th></tr>
{% for alert in alerts %}
<tr class="{% if 'CALL' in alert %}call{% elif 'PUT' in alert %}put{% else %}side{% endif %}">
<td>{{alert.time}}</td>
<td>{{alert.symbol}}</td>
<td>{{alert.atm}}</td>
<td>{{alert.strike}}</td>
<td>{{alert.side}}</td>
</tr>
{% endfor %}
</table>
<p style="text-align:center;">Last Update: {{last_update}}</p>
</body></html>
"""

@app.route("/")
def dashboard():
    display_alerts=[]
    for a in alerts_history[-50:]:
        lines = a.strip().split("\n")
        display_alerts.append({
            "time": lines[1].split(":")[1].strip(),
            "symbol": lines[2].split(":")[1].strip(),
            "atm": lines[5].split(":")[1].strip(),
            "strike": lines[4].split(":")[1].strip(),
            "side": lines[3].split(":")[1].strip()
        })
    return render_template_string(TEMPLATE,last_update=datetime.now().strftime("%H:%M:%S"),alerts=display_alerts)

# ====================== MASTER ENGINE ======================
def run_engine():
    print(f"\n🔍 Scan @ {datetime.now().strftime('%H:%M:%S')}")
    for sym,gap in SYMBOLS.items():
        analyze_symbol(sym,gap)
        time.sleep(1.2)

schedule.every(15).minutes.do(run_engine) # 15-min candle

# ====================== THREADING ======================
threading.Thread(target=lambda: app.run(host="0.0.0.0",port=5009)).start()
print("🚀 LIVE Option Alert Dashboard Started")

while True:
    schedule.run_pending()
    time.sleep(1)
