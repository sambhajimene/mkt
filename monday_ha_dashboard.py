import streamlit as st
import pandas as pd
import datetime
import time
import smtplib
from email.mime.text import MIMEText
from kiteconnect import KiteConnect

# ================= CONFIG =================

API_KEY = "z9rful06a9890v8m"
ACCESS_TOKEN = "IInPxgBD32aAoK3WdfiWXipAyXZzhjYJ"

# ================== Email Config ==================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_FROM = "sambhajimene@gmail.com"
EMAIL_PASSWORD = "jgebigpsoeqqwrfa"
EMAIL_TO = ["sambhajimene@gmail.com"]


TOL = 0.0001
SLEEP_INTERVAL = 0.25
# ==========================================

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

st.set_page_config(page_title="Monday HA Institutional Panel", layout="wide")

st.title("📊 Monday Weekly + Hourly HA Control Panel")

# ================= HEIKIN ASHI =================
def calculate_heikin_ashi(df):
    ha = df.copy()

    ha['HA_Close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    ha_open = [(df['open'].iloc[0] + df['close'].iloc[0]) / 2]

    for i in range(1, len(df)):
        ha_open.append((ha_open[i-1] + ha['HA_Close'].iloc[i-1]) / 2)

    ha['HA_Open'] = ha_open
    ha['HA_High'] = ha[['high', 'HA_Open', 'HA_Close']].max(axis=1)
    ha['HA_Low'] = ha[['low', 'HA_Open', 'HA_Close']].min(axis=1)

    return ha
# =================================================

# ================= EMAIL FUNCTION =================
def send_email(subject, body):

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL_SENDER, EMAIL_PASSWORD)
    server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
    server.quit()
# =================================================

if st.button("🚀 Run Monday Scanner"):

    now = datetime.datetime.now()

    if now.weekday() != 0 or now.time() < datetime.time(10, 20):
        st.warning("Scanner works only Monday after 10:20 AM")
        st.stop()

    today = now.date()

    st.info("Scanning NSE500 Stocks...")

    instruments = kite.instruments("NSE")
    df_inst = pd.DataFrame(instruments)

    nse500 = pd.read_csv(
        "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    )["Symbol"].tolist()

    df_stocks = df_inst[
        (df_inst["segment"] == "NSE") &
        (df_inst["instrument_type"] == "EQ") &
        (df_inst["tradingsymbol"].isin(nse500))
    ]

    bullish = []
    bearish = []

    progress = st.progress(0)

    for i, (_, row) in enumerate(df_stocks.iterrows()):

        symbol = row["tradingsymbol"]
        token = row["instrument_token"]

        try:
            # ===== WEEKLY =====
            weekly = kite.historical_data(
                token,
                today - datetime.timedelta(days=365),
                today,
                "week"
            )

            if len(weekly) < 20:
                continue

            df_week = pd.DataFrame(weekly)
            ha_week = calculate_heikin_ashi(df_week)

            last_w = ha_week.iloc[-2]
            prev_w = ha_week.iloc[-3]

            weekly_bull = (
                (prev_w['HA_Close'] > prev_w['HA_Open']) and
                (last_w['HA_Close'] > last_w['HA_Open']) and
                abs(last_w['HA_Open'] - last_w['HA_Low']) < TOL
            )

            weekly_bear = (
                (prev_w['HA_Close'] < prev_w['HA_Open']) and
                (last_w['HA_Close'] < last_w['HA_Open']) and
                abs(last_w['HA_Open'] - last_w['HA_High']) < TOL
            )

            if not weekly_bull and not weekly_bear:
                continue

            # ===== MONDAY FIRST HOURLY =====
            hourly = kite.historical_data(
                token,
                today,
                today,
                "60minute"
            )

            if len(hourly) < 1:
                continue

            df_hour = pd.DataFrame(hourly)
            ha_hour = calculate_heikin_ashi(df_hour)

            first = ha_hour.iloc[0]

            hourly_bull = (
                first['HA_Close'] > first['HA_Open'] and
                abs(first['HA_Open'] - first['HA_Low']) < TOL
            )

            hourly_bear = (
                first['HA_Close'] < first['HA_Open'] and
                abs(first['HA_Open'] - first['HA_High']) < TOL
            )

            if weekly_bull and hourly_bull:
                bullish.append(symbol)

            if weekly_bear and hourly_bear:
                bearish.append(symbol)

            time.sleep(SLEEP_INTERVAL)

        except:
            continue

        progress.progress((i + 1) / len(df_stocks))

    # ================= DASHBOARD OUTPUT =================

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🟢 BUY Signals")
        st.write(bullish)

    with col2:
        st.subheader("🔴 SELL Signals")
        st.write(bearish)

    # ================= EMAIL ALERT =================

    if bullish or bearish:

        body = f"""
Monday HA Signals:

BUY:
{bullish}

SELL:
{bearish}
"""

        send_email("Monday HA Scanner Signals", body)
        st.success("📧 Email Alert Sent!")

    else:
        st.info("No Signals Found Today.")
