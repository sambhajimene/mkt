import os
import time
import pytz
import smtplib
import yfinance as yf
import pandas as pd
from datetime import datetime, time as dtime
from email.mime.text import MIMEText
from flask import Flask, render_template_string
from ta.momentum import RSIIndicator
from ta.trend import MACD

# ================= TIME CONFIG =================
IST = pytz.timezone("Asia/Kolkata")

def market_is_open():
    now = datetime.now(IST).time()
    return dtime(9, 15) <= now <= dtime(15, 30)

# ================= EMAIL CONFIG =================
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO   = os.getenv("EMAIL_TO")

def send_email(subject, body):
    if not market_is_open():
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASS)
        server.send_message(msg)

# ================= SYMBOL LIST =================
SYMBOLS = ["^NSEI", "^NSEBANK"]  # expand later safely

# ================= STRATEGY CORE =================
def check_signal(symbol):
    if not market_is_open():
        return None

    df = yf.download(symbol, interval="15m", period="5d", progress=False)
    if df.empty or len(df) < 50:
        return None

    close = df["Close"]

    # RSI
    rsi = RSIIndicator(close, window=14).rsi()

    # MACD (15m)
    macd = MACD(close)
    macd_hist = macd.macd_diff()

    # Hourly MACD
    df_h = yf.download(symbol, interval="60m", period="10d", progress=False)
    macd_h = MACD(df_h["Close"]).macd_diff()

    # Daily MACD
    df_d = yf.download(symbol, interval="1d", period="3mo", progress=False)
    macd_d = MACD(df_d["Close"]).macd_diff()

    # Latest values
    rsi_prev, rsi_now = rsi.iloc[-2], rsi.iloc[-1]

    # CALL BUY CONDITION
    if (
        rsi_prev < 60 and rsi_now > 60 and
        macd_hist.iloc[-1] > 0 and
        macd_h.iloc[-1] > 0 and
        macd_d.iloc[-1] > 0
    ):
        return {
            "symbol": symbol,
            "side": "CALL BUY",
            "time": datetime.now(IST).strftime("%H:%M:%S"),
            "rsi": round(rsi_now, 2)
        }

    # PUT BUY CONDITION
    if (
        rsi_prev > 40 and rsi_now < 40 and
        macd_hist.iloc[-1] < 0 and
        macd_h.iloc[-1] < 0 and
        macd_d.iloc[-1] < 0
    ):
        return {
            "symbol": symbol,
            "side": "PUT BUY",
            "time": datetime.now(IST).strftime("%H:%M:%S"),
            "rsi": round(rsi_now, 2)
        }

    return None

# ================= RUN LOOP =================
alerts = []

def run_engine():
    while True:
        if not market_is_open():
            print("🔒 Market CLOSED — engine idle")
            time.sleep(300)
            continue

        for sym in SYMBOLS:
            signal = check_signal(sym)
            if signal:
                alerts.append(signal)

                mail_body = f"""
🟢 AUTO TRADE SIGNAL CONFIRMED

Symbol : {signal['symbol']}
Action : {signal['side']}
RSI    : {signal['rsi']}
Time   : {signal['time']}

All filters matched:
✔ RSI
✔ 15m candle
✔ Hourly MACD
✔ Daily MACD
✔ Market Open
"""
                send_email(
                    f"🟢 {signal['side']} | {signal['symbol']}",
                    mail_body
                )

        time.sleep(900)  # 15 min

# ================= DASHBOARD =================
app = Flask(__name__)

HTML = """
<h2>Live Confirmed Option Alerts (15-Min)</h2>
<table border=1 cellpadding=6>
<tr><th>Time</th><th>Symbol</th><th>Action</th><th>RSI</th></tr>
{% for a in alerts %}
<tr>
<td>{{a.time}}</td>
<td>{{a.symbol}}</td>
<td><b>{{a.side}}</b></td>
<td>{{a.rsi}}</td>
</tr>
{% endfor %}
</table>
"""

@app.route("/")
def index():
    return render_template_string(HTML, alerts=alerts[-20:])

# ================= START =================
if __name__ == "__main__":
    import threading
    threading.Thread(target=run_engine, daemon=True).start()
    app.run(host="0.0.0.0", port=5009)
