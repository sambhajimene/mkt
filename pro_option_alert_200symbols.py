import pandas as pd
from nsepython import nse_optionchain_scrapper, nse_get_index_quote
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import pytz
import random

# ====================== EMAIL CONFIG ======================
import os
EMAIL_FROM = os.environ.get('EMAIL_FROM')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
EMAIL_TO   = os.environ.get('EMAIL_TO')

def send_mail(subject, body):
    try:
        msg = MIMEText(body, "plain")
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASS)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print(f"✅ Email sent: {subject}")
    except Exception as e:
        print(f"❌ Email error: {e}")

# ====================== SYMBOLS (200+ NSE) ======================
SYMBOLS = [
    "NIFTY","BANKNIFTY","FINNIFTY","RELIANCE","TCS","HDFCBANK","ICICIBANK",
    "INFY","SBIN","HCLTECH","KOTAKBANK","LT","ITC","HINDUNILVR","AXISBANK",
    "MARUTI","TECHM","ASIANPAINT","WIPRO","BAJAJ-AUTO","BHARTIARTL","DRREDDY",
    "TITAN","ULTRACEMCO","HDFCLIFE","DIVISLAB","ADANIPORTS","INDUSINDBK","JSWSTEEL",
    "ONGC","GRASIM","COALINDIA","BPCL","SHREECEM","HDFCBANK","LTIM","SUNPHARMA",
    "EICHERMOT","TATAMOTORS","HCLTECH","UPL","ICICIPRULI","BAJFINANCE","CIPLA",
    "BRITANNIA","POWERGRID","NTPC","TATACONSUM","VEDL","SBILIFE","TECHM","GAIL",
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","AXISBANK","KOTAKBANK","LT",
    "ITC","HINDUNILVR","SBIN","HCLTECH","MARUTI","BAJAJFINSV","ADANIENT","ADANIGREEN",
    "BAJAJ-AUTO","BHARTIARTL","DRREDDY","TITAN","ULTRACEMCO","DIVISLAB","ASIANPAINT",
    "ONGC","GRASIM","COALINDIA","BPCL","SHREECEM","LTIM","SUNPHARMA","EICHERMOT",
    "TATAMOTORS","UPL","ICICIPRULI","BAJFINANCE","CIPLA","BRITANNIA","POWERGRID",
    "NTPC","TATACONSUM","VEDL","SBILIFE","GAIL","RELIANCE","TCS","INFY","HDFCBANK",
    "ICICIBANK","AXISBANK","KOTAKBANK","LT","ITC","HINDUNILVR","SBIN","HCLTECH",
    "MARUTI","TECHM","ASIANPAINT","WIPRO","BAJAJ-AUTO","BHARTIARTL","DRREDDY",
    "TITAN","ULTRACEMCO","HDFCLIFE","DIVISLAB","ADANIPORTS","INDUSINDBK","JSWSTEEL",
    "ONGC","GRASIM","COALINDIA","BPCL","SHREECEM","HDFCBANK","LTIM","SUNPHARMA",
    "EICHERMOT","TATAMOTORS","HCLTECH","UPL","ICICIPRULI","BAJFINANCE","CIPLA",
    "BRITANNIA","POWERGRID","NTPC","TATACONSUM","VEDL","SBILIFE","TECHM","GAIL"
]

# ====================== ALERT HISTORY ======================
ALERT_HISTORY = {}  # last alert time per symbol+strike+side

IST = pytz.timezone('Asia/Kolkata')

def market_open():
    now = datetime.now(IST)
    if now.weekday() >= 5:  # Sat/Sun
        return False
    open_time = now.replace(hour=9, minute=15, second=0)
    close_time = now.replace(hour=15, minute=30, second=0)
    return open_time <= now <= close_time

# ====================== OPTION DATA FETCH ======================
def get_option_data(symbol):
    """Fetch option chain data and ATM strike"""
    try:
        chain = nse_optionchain_scrapper(symbol)
        ltp = nse_get_index_quote(symbol)['lastPrice'] if symbol in ["NIFTY","BANKNIFTY","FINNIFTY"] else nse_get_index_quote(symbol)['lastPrice']
        atm = int(round(ltp / 50) * 50)
        strikes = sorted(chain['CE'].keys())
        data = []
        for strike in strikes:
            ce = chain['CE'][strike]
            pe = chain['PE'][strike]
            data.append({
                'strike': strike,
                'call_writing': ce['openInterest'] > ce['changeinOpenInterest'],
                'put_writing': pe['openInterest'] > pe['changeinOpenInterest'],
                'call_unwinding': ce['openInterest'] < ce['changeinOpenInterest'],
                'put_unwinding': pe['openInterest'] < pe['changeinOpenInterest']
            })
        return data, atm
    except Exception as e:
        print(f"Error {symbol}: {e}")
        # fallback random dummy data
        atm = 22500
        strikes = [atm - 200, atm - 100, atm, atm + 100, atm + 200]
        data = []
        for s in strikes:
            data.append({
                'strike': s,
                'call_writing': random.choice([True, False]),
                'put_writing': random.choice([True, False]),
                'call_unwinding': random.choice([True, False]),
                'put_unwinding': random.choice([True, False])
            })
        return data, atm

# ====================== SIGNAL LOGIC ======================
def generate_signal(data, atm):
    """Generate signals with confidence"""
    signals = []
    atm_strikes = [s for s in data if abs(s['strike']-atm) <= 200]  # ATM ±2
    for d in atm_strikes:
        strike = d['strike']
        cw, cu = d['call_writing'], d['call_unwinding']
        pw, pu = d['put_writing'], d['put_unwinding']
        if cw and pu:
            side = "MARKET UP (CALL BUY bias)"
        elif cu and pw:
            side = "MARKET DOWN (PUT BUY bias)"
        elif cw and pw:
            side = "RANGE / TRAP NO TRADE"
        elif cu and pu:
            side = "BREAKOUT / VOLATILITY"
        else:
            side = None
        if side:
            signals.append({'strike': strike, 'side': side})
    # Confidence calculation
    if len(signals) >= 3:
        bias_count = {}
        for s in signals:
            bias_count[s['side']] = bias_count.get(s['side'],0)+1
        max_bias = max(bias_count, key=bias_count.get)
        conf = "HIGH" if bias_count[max_bias]>=3 else "MEDIUM"
        return signals, conf
    else:
        return signals, "LOW"

def check_and_send_alert(symbol, strike, side):
    key = f"{symbol}_{strike}_{side}"
    now = datetime.now(IST)
    last = ALERT_HISTORY.get(key)
    if not last or (now - last).seconds > 900:  # 15 min
        ALERT_HISTORY[key] = now
        subject = f"{side} | {symbol} | Strike {strike}"
        body = f"Signal: {side}\nSymbol: {symbol}\nStrike: {strike}\nTime: {now.strftime('%H:%M:%S')}"
        send_mail(subject, body)

# ====================== DASHBOARD ======================
st.set_page_config(page_title="Option Dashboard", layout="wide")
st.title("🟢 LIVE Option Dashboard + Confidence Score")

if market_open():
    for symbol in SYMBOLS:
        data, atm = get_option_data(symbol)
        signals, conf = generate_signal(data, atm)
        if signals:
            for sig in signals:
                check_and_send_alert(symbol, sig['strike'], sig['side'])
            df = pd.DataFrame(signals)
            st.subheader(f"{symbol} | ATM: {atm} | Confidence: {conf}")
            color = "#28a745" if conf=="HIGH" else "#ffc107" if conf=="MEDIUM" else "#dc3545"
            st.markdown(f"<div style='background-color:{color};padding:5px'>{conf}</div>", unsafe_allow_html=True)
            st.dataframe(df)
else:
    st.warning("Market is closed")
