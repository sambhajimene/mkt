import streamlit as st
import pandas as pd
import datetime
import smtplib
from email.mime.text import MIMEText
from kiteconnect import KiteConnect
from streamlit_autorefresh import st_autorefresh
import os
import json

# ================= CONFIG =================
API_KEY = "z9rful06a9890v8m"
ACCESS_TOKEN = "Rylci23jGBJE6J636yAxoZCeUct0EEiX"

# ================== Email Config ==================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_FROM = "sambhajimene@gmail.com"
EMAIL_PASSWORD = "jgebigpsoeqqwrfa"
EMAIL_TO = ["sambhajimene@gmail.com"]

BODY_THRESHOLD = 0.2
SLEEP_INTERVAL = 0.2

START_DAILY = datetime.date.today() - datetime.timedelta(days=120)
START_WEEKLY = datetime.date.today() - datetime.timedelta(days=365)
START_HOURLY = datetime.date.today() - datetime.timedelta(days=10)
END_DATE = datetime.date.today()

SIGNAL_STORE_FILE = "last_signals.json"

# Ensure signal store file exists and has write permissions
if not os.path.exists(SIGNAL_STORE_FILE):
    with open(SIGNAL_STORE_FILE, "w") as f:
        json.dump({"bullish": [], "bearish": []}, f)
os.chmod(SIGNAL_STORE_FILE, 0o666)

# ==========================================
kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

# ================= HA FUNCTION =================
def calculate_heikin_ashi(df):
    ha_df = df.copy()
    ha_df['HA_Close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    ha_open = [(df['open'][0] + df['close'][0]) / 2]
    for i in range(1, len(df)):
        ha_open.append((ha_open[i-1] + ha_df['HA_Close'][i-1]) / 2)
    ha_df['HA_Open'] = ha_open
    ha_df['HA_High'] = ha_df[['high', 'HA_Open', 'HA_Close']].max(axis=1)
    ha_df['HA_Low'] = ha_df[['low', 'HA_Open', 'HA_Close']].min(axis=1)
    return ha_df

# ================= EMAIL FUNCTION =================
def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = ",".join(EMAIL_TO)
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        return str(e)

# ================= SCANNER FUNCTIONS =================
def scan_bullish():
    instruments = kite.instruments("NSE")
    df_instruments = pd.DataFrame(instruments)
    nse500_symbols = pd.read_csv(
        "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    )["Symbol"].tolist()

    df_nse500 = df_instruments[
        (df_instruments["segment"] == "NSE") &
        (df_instruments["instrument_type"] == "EQ") &
        (df_instruments["tradingsymbol"].isin(nse500_symbols))
    ]

    results = []

    for _, row in df_nse500.iterrows():
        symbol = row["tradingsymbol"]
        token = row["instrument_token"]

        try:
            # DAILY
            daily_data = kite.historical_data(token, START_DAILY, END_DATE, "day")
            if len(daily_data) < 60:
                continue
            df_daily = pd.DataFrame(daily_data)
            df_daily["EMA50"] = df_daily["close"].ewm(span=50).mean()
            ha_daily = calculate_heikin_ashi(df_daily)
            last_daily = ha_daily.iloc[-1]

            body = abs(last_daily['HA_Close'] - last_daily['HA_Open'])
            full_range = last_daily['HA_High'] - last_daily['HA_Low']
            if full_range == 0: continue

            body_ratio = body / full_range
            upper_wick = last_daily['HA_High'] - max(last_daily['HA_Open'], last_daily['HA_Close'])
            lower_wick = min(last_daily['HA_Open'], last_daily['HA_Close']) - last_daily['HA_Low']

            neutral_daily = (body_ratio < BODY_THRESHOLD and upper_wick > 0 and lower_wick > 0 and last_daily["close"] > last_daily["EMA50"])
            strong_daily = (last_daily['HA_Close'] > last_daily['HA_Open'] and last_daily["close"] > last_daily["EMA50"])

            if not (neutral_daily or strong_daily):
                continue

            # WEEKLY
            weekly_data = kite.historical_data(token, START_WEEKLY, END_DATE, "week")
            df_weekly = pd.DataFrame(weekly_data)
            ha_weekly = calculate_heikin_ashi(df_weekly)
            last_weekly = ha_weekly.iloc[-1]

            weekly_body = last_weekly['HA_Close'] - last_weekly['HA_Open']
            weekly_lower_wick = min(last_weekly['HA_Open'], last_weekly['HA_Close']) - last_weekly['HA_Low']

            weekly_strong = (weekly_body > 0 and weekly_lower_wick <= (weekly_body * 0.1))
            if not weekly_strong:
                continue

            # HOURLY
            hourly_data = kite.historical_data(token, START_HOURLY, END_DATE, "60minute")
            df_hourly = pd.DataFrame(hourly_data)
            ha_hourly = calculate_heikin_ashi(df_hourly)
            last_hourly = ha_hourly.iloc[-1]

            hourly_body = last_hourly['HA_Close'] - last_hourly['HA_Open']
            hourly_lower_wick = min(last_hourly['HA_Open'], last_hourly['HA_Close']) - last_hourly['HA_Low']
            hourly_range = last_hourly['HA_High'] - last_hourly['HA_Low']
            if hourly_range == 0: continue

            hourly_body_ratio = hourly_body / hourly_range
            hourly_strong = (hourly_body > 0 and hourly_lower_wick <= (hourly_body * 0.1) and hourly_body_ratio > 0.5)

            if hourly_strong:
                results.append({"Symbol": str(symbol), "CMP": float(last_daily["close"])})

        except:
            continue

    return results


def scan_bearish():
    instruments = kite.instruments("NSE")
    df_instruments = pd.DataFrame(instruments)

    nse500_symbols = pd.read_csv(
        "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    )["Symbol"].tolist()

    df_nse500 = df_instruments[
        (df_instruments["segment"] == "NSE") &
        (df_instruments["instrument_type"] == "EQ") &
        (df_instruments["tradingsymbol"].isin(nse500_symbols))
    ]

    results = []

    for _, row in df_nse500.iterrows():
        symbol = row["tradingsymbol"]
        token = row["instrument_token"]

        try:
            daily_data = kite.historical_data(token, START_DAILY, END_DATE, "day")
            if len(daily_data) < 60:
                continue
            df_daily = pd.DataFrame(daily_data)
            df_daily["EMA50"] = df_daily["close"].ewm(span=50).mean()
            ha_daily = calculate_heikin_ashi(df_daily)
            last_daily = ha_daily.iloc[-1]

            body = abs(last_daily['HA_Close'] - last_daily['HA_Open'])
            full_range = last_daily['HA_High'] - last_daily['HA_Low']
            if full_range == 0: continue

            body_ratio = body / full_range
            upper_wick = last_daily['HA_High'] - max(last_daily['HA_Open'], last_daily['HA_Close'])
            lower_wick = min(last_daily['HA_Open'], last_daily['HA_Close']) - last_daily['HA_Low']

            neutral_daily = (body_ratio < BODY_THRESHOLD and upper_wick > 0 and lower_wick > 0 and last_daily["close"] < last_daily["EMA50"])
            strong_daily = (last_daily['HA_Close'] < last_daily['HA_Open'] and last_daily["close"] < last_daily["EMA50"])

            if neutral_daily or strong_daily:
                results.append({"Symbol": str(symbol), "CMP": float(last_daily["close"])})

        except:
            continue

    return results

# ================= SAVE SIGNALS =================
def save_signals(bullish, bearish):
    cleaned = {
        "bullish": [{"Symbol": s["Symbol"], "CMP": s["CMP"]} for s in bullish],
        "bearish": [{"Symbol": s["Symbol"], "CMP": s["CMP"]} for s in bearish]
    }
    with open(SIGNAL_STORE_FILE, "w") as f:
        json.dump(cleaned, f, indent=2)

# ================= STREAMLIT UI =================
st.set_page_config(layout="wide")
st.title("🔥 Bullish & Bearish NSE500 HA Scanner")

st.sidebar.title("⚙ Settings")
auto_mode = st.sidebar.checkbox("Enable Auto Scan Every Hour")
if auto_mode:
    st_autorefresh(interval=3600000, limit=None, key="hourlyrefresh")

col1, col2 = st.columns(2)
with col1:
    run_scan = st.button("🚀 Run Scan Now")
with col2:
    test_mail = st.button("📧 Send Test Mail")

if test_mail:
    result = send_email("Test Email", "This is a test email from HA Scanner")
    if result == True:
        st.success("Test Email Sent Successfully!")
    else:
        st.error(f"Email Failed: {result}")

if run_scan or auto_mode:
    with st.spinner("Scanning NSE500 Cash Stocks..."):
        bullish_signals = scan_bullish()
        bearish_signals = scan_bearish()

        st.subheader("📈 Bullish Signals")
        if bullish_signals:
            df_bull = pd.DataFrame(bullish_signals)
            st.dataframe(df_bull, width='stretch')
            send_email("Bullish HA Signals", str([s['Symbol'] for s in bullish_signals]))
        else:
            st.write("No Bullish setups found.")

        st.subheader("📉 Bearish Signals")
        if bearish_signals:
            df_bear = pd.DataFrame(bearish_signals)
            st.dataframe(df_bear, width='stretch')
            send_email("Bearish HA Signals", str([s['Symbol'] for s in bearish_signals]))
        else:
            st.write("No Bearish setups found.")

        save_signals(bullish_signals, bearish_signals)
