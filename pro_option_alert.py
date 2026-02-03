#
import yfinance as yf
import pandas as pd
import numpy as np
import smtplib
import ssl
from email.mime.text import MIMEText
from datetime import datetime, time
import pytz
import os

# ====================== EMAIL CONFIG (ENV FROM GITLAB SECRET) ======================
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO   = os.getenv("EMAIL_TO")

# ====================== SETTINGS ======================
TIMEFRAME = "15m"
RSI_CALL = 60
RSI_PUT  = 40
INDIA_TZ = pytz.timezone("Asia/Kolkata")

# ====================== MARKET TIME CHECK ======================
def is_market_open():
    now = datetime.now(INDIA_TZ).time()
    return time(9, 15) <= now <= time(15, 30)

# ====================== LOAD SYMBOLS ======================
def load_symbols():
    with open("symbols.txt") as f:
        return [x.strip() for x in f if x.strip()]

# ====================== INDICATORS ======================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def macd(series):
    ema12 = series.ewm(span=12).mean()
    ema26 = series.ewm(span=26).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9).mean()
    return macd_line, signal

# ====================== EMAIL ======================
def send_email(subject, body):
    msg = MIMEText(body)
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_FROM, EMAIL_PASS)
        server.send_message(msg)

# ====================== CORE LOGIC ======================
def analyze_symbol(symbol):
    data = yf.download(symbol + ".NS", interval=TIMEFRAME, period="5d", progress=False)

    if len(data) < 50:
        return None

    close = data["Close"]
    rsi_val = rsi(close).iloc[-1]

    macd_15, sig_15 = macd(close)
    macd_1h, sig_1h = macd(close.resample("1H").last().dropna())
    macd_d, sig_d = macd(close.resample("1D").last().dropna())

    macd_ok = (
        macd_15.iloc[-1] > sig_15.iloc[-1] and
        macd_1h.iloc[-1] > sig_1h.iloc[-1] and
        macd_d.iloc[-1] > sig_d.iloc[-1]
    )

    last_candle = data.iloc[-1]
    prev_candle = data.iloc[-2]

    # ====================== SELLER MOVEMENT (SIMULATED VIA PRICE + VOL) ======================
    seller_activity = last_candle["Volume"] > data["Volume"].rolling(20).mean().iloc[-1]

    # ====================== CALL BUY ======================
    if (
        rsi_val > RSI_CALL and
        macd_ok and
        seller_activity and
        last_candle["Close"] > last_candle["Open"]
    ):
        return {
            "symbol": symbol,
            "side": "CALL BUY",
            "price": round(last_candle["Close"], 2),
            "sl": round(last_candle["Low"], 2)
        }

    # ====================== PUT BUY ======================
    if (
        rsi_val < RSI_PUT and
        macd_ok and
        seller_activity and
        last_candle["Close"] < last_candle["Open"]
    ):
        return {
            "symbol": symbol,
            "side": "PUT BUY",
            "price": round(last_candle["Close"], 2),
            "sl": round(last_candle["High"], 2)
        }

    return None

# ====================== MAIN ======================
def main():
    if not is_market_open():
        print("❌ Market Closed – No alerts")
        return

    symbols = load_symbols()
    alerts = []

    for sym in symbols:
        try:
            result = analyze_symbol(sym)
            if result:
                alerts.append(result)
        except Exception as e:
            print(f"Error {sym}: {e}")

    if alerts:
        body = "🟢 CONFIRMED OPTION BUY SIGNAL (ALL FILTERS MATCHED)\n\n"
        for a in alerts:
            body += (
                f"Symbol: {a['symbol']}\n"
                f"Signal: {a['side']}\n"
                f"Entry: {a['price']}\n"
                f"SL (Candle Basis): {a['sl']}\n"
                f"Timeframe: 15 MIN\n"
                "--------------------------\n"
            )

        send_email("🔥 CONFIRMED OPTION BUY ALERT", body)
        print("✅ Email Sent")
    else:
        print("ℹ️ No valid setup")

if __name__ == "__main__":
    main()
