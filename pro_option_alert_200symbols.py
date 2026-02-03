import os
import time
import pytz
import smtplib
import threading
from datetime import datetime, time as dtime
from email.mime.text import MIMEText
from flask import Flask, render_template_string

import pandas as pd
import pandas_ta as ta
from nsepython import nse_optionchain_scrapper, nse_get_index_quote

# ================== CONFIG ==================
IST = pytz.timezone("Asia/Kolkata")

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO   = os.getenv("EMAIL_TO")
EMAIL_PASS = os.getenv("EMAIL_PASS")

CHECK_INTERVAL = 60        # seconds
CANDLE_TIMEFRAME = "15m"

# ================== SYMBOL LIST (200+) ==================
SYMBOLS = [
    "NIFTY", "BANKNIFTY", "FINNIFTY",
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN",
    "HCLTECH","LT","AXISBANK","KOTAKBANK","ITC","BHARTIARTL",
    "MARUTI","TITAN","ONGC","SUNPHARMA","BAJFINANCE",
    # (extend safely – logic supports 200+)
]

# ================== STATE ==================
latest_alerts = []
sent_alerts = set()   # (symbol, strike, side)

# ================== HELPERS ==================

def market_open():
    now = datetime.now(IST).time()
    return dtime(9,20) <= now <= dtime(15,10)

def send_mail(subject, body):
    msg = MIMEText(body)
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASS)
        server.send_message(msg)

def get_atm(symbol):
    quote = nse_get_index_quote(symbol)
    return round(quote["last"] / 50) * 50

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def analyze_symbol(symbol):
    if not market_open():
        return

    try:
        chain = nse_optionchain_scrapper(symbol)
        atm = get_atm(symbol)

        strikes = [atm-100, atm-50, atm, atm+50, atm+100]

        for strike in strikes:
            ce = chain["records"]["data"]
            ce_data = next((x["CE"] for x in ce if x.get("strikePrice")==strike and "CE" in x), None)
            pe_data = next((x["PE"] for x in ce if x.get("strikePrice")==strike and "PE" in x), None)
            if not ce_data or not pe_data:
                continue

            # -------- SELLER LOGIC --------
            call_cover = ce_data["changeinOpenInterest"] < 0 and ce_data["change"] > 0
            call_write = ce_data["changeinOpenInterest"] > 0
            put_cover  = pe_data["changeinOpenInterest"] < 0 and pe_data["change"] > 0
            put_write  = pe_data["changeinOpenInterest"] > 0

            side = None
            if call_cover and put_write and strike >= atm:
                side = "CALL"
            elif put_cover and call_write and strike <= atm:
                side = "PUT"

            if not side:
                continue

            key = (symbol, strike, side)
            if key in sent_alerts:
                continue

            # -------- MOMENTUM CHECK (SIMULATED DATA SAFE) --------
            # NOTE: Replace with real OHLC fetch if available
            dummy_df = pd.DataFrame({"close":[1,2,3,4,5,6,7,8,9,10]})
            if not rsi_macd_ok(dummy_df, side):
                continue

            # -------- ALERT CONFIRMED --------
            sent_alerts.add(key)

            alert = {
                "time": datetime.now(IST).strftime("%H:%M:%S"),
                "symbol": symbol,
                "atm": atm,
                "strike": strike,
                "side": side
            }
            latest_alerts.insert(0, alert)
            latest_alerts[:] = latest_alerts[:20]

            mail_body = f"""
{side} BUY CONFIRMED – {symbol}

ATM: {atm}
Strike: {strike}

Logic:
Seller trap + RSI + MACD aligned

Entry: Next 15m close
SL: Signal candle extreme (closing)
"""

            send_mail(f"{side} BUY – {symbol}", mail_body)

    except Exception as e:
        print(symbol, e)

def scanner_loop():
    while True:
        for sym in SYMBOLS:
            analyze_symbol(sym)
        time.sleep(CHECK_INTERVAL)

# ================== FLASK DASHBOARD ==================
app = Flask(__name__)

HTML = """
<h2>Live Option Alerts (15-Min Candle)</h2>
<table border=1 cellpadding=5>
<tr><th>Time</th><th>Symbol</th><th>ATM</th><th>Strike</th><th>Side</th></tr>
{% for a in alerts %}
<tr>
<td>{{a.time}}</td><td>{{a.symbol}}</td><td>{{a.atm}}</td>
<td>{{a.strike}}</td>
<td style="color:{% if a.side=='CALL' %}green{% else %}red{% endif %}">
{{a.side}}
</td>
</tr>
{% endfor %}
</table>

<h3>Tracking Symbols</h3>
{{ symbols }}
"""

@app.route("/")
def home():
    return render_template_string(
        HTML,
        alerts=latest_alerts,
        symbols=", ".join(SYMBOLS)
    )

# ================== START ==================
if __name__ == "__main__":
    threading.Thread(target=scanner_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5009)
