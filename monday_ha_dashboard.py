import streamlit as st
import pandas as pd
import datetime
import time
import smtplib
from email.mime.text import MIMEText
from kiteconnect import KiteConnect

# ================= CONFIG =================

API_KEY = "z9rful06a9890v8m"
ACCESS_TOKEN = "1Ga0wgJD3kdHtD6eTCQCVaqNL2z7QEor"

# ================== Email Config ==================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_FROM = "sambhajimene@gmail.com"
EMAIL_PASSWORD = "jgebigpsoeqqwrfa"
EMAIL_TO = ["sambhajimene@gmail.com"]

TOL = 0.0001
SLEEP_INTERVAL = 0.25
BACKTEST_YEARS = 2
# ==========================================

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

st.set_page_config(layout="wide")
st.title("🏦 Institutional Monday HA System")

# ================= HA FUNCTION =================
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

# ================= EMAIL =================
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

# ================= LOAD NSE500 =================
@st.cache_data
def load_nse500():
    return pd.read_csv(
        "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    )["Symbol"].tolist()

# =================================================

# ================= AUTO MONDAY SCAN =================
def run_live_scan():

    now = datetime.datetime.now()

    if now.weekday() != 0 or now.time() < datetime.time(10, 20):
        st.info("Waiting for Monday 10:20 AM...")
        return

    st.success("🚀 Running Live Monday Scan")

    instruments = kite.instruments("NSE")
    df_inst = pd.DataFrame(instruments)
    nse500 = load_nse500()

    df_stocks = df_inst[
        (df_inst["segment"] == "NSE") &
        (df_inst["instrument_type"] == "EQ") &
        (df_inst["tradingsymbol"].isin(nse500))
    ]

    bullish, bearish = [], []

    for _, row in df_stocks.iterrows():

        symbol = row["tradingsymbol"]
        token = row["instrument_token"]

        try:
            weekly = kite.historical_data(
                token,
                now.date() - datetime.timedelta(days=365),
                now.date(),
                "week"
            )

            if len(weekly) < 20:
                continue

            df_week = pd.DataFrame(weekly)
            ha_week = calculate_heikin_ashi(df_week)

            last_w = ha_week.iloc[-2]
            prev_w = ha_week.iloc[-3]

            weekly_bull = (
                prev_w['HA_Close'] > prev_w['HA_Open'] and
                last_w['HA_Close'] > last_w['HA_Open'] and
                abs(last_w['HA_Open'] - last_w['HA_Low']) < TOL
            )

            weekly_bear = (
                prev_w['HA_Close'] < prev_w['HA_Open'] and
                last_w['HA_Close'] < last_w['HA_Open'] and
                abs(last_w['HA_Open'] - last_w['HA_High']) < TOL
            )

            if not weekly_bull and not weekly_bear:
                continue

            hourly = kite.historical_data(
                token,
                now.date(),
                now.date(),
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

    st.subheader("🟢 BUY")
    st.write(bullish)

    st.subheader("🔴 SELL")
    st.write(bearish)

    if bullish or bearish:
        body = f"BUY:\n{bullish}\n\nSELL:\n{bearish}"
        send_email("Live Monday HA Signals", body)

# =================================================

# ================= BACKTEST MODULE =================
def run_backtest():

    st.subheader("📊 Backtest Results")

    instruments = kite.instruments("NSE")
    df_inst = pd.DataFrame(instruments)
    nse500 = load_nse500()

    df_stocks = df_inst[
        (df_inst["segment"] == "NSE") &
        (df_inst["instrument_type"] == "EQ") &
        (df_inst["tradingsymbol"].isin(nse500))
    ]

    results = []

    for _, row in df_stocks.head(50).iterrows():  # limit for speed

        symbol = row["tradingsymbol"]
        token = row["instrument_token"]

        try:
            data = kite.historical_data(
                token,
                datetime.date.today() - datetime.timedelta(days=365*BACKTEST_YEARS),
                datetime.date.today(),
                "day"
            )

            df = pd.DataFrame(data)

            if len(df) < 200:
                continue

            weekly = df.resample("W", on="date").agg({
                "open":"first",
                "high":"max",
                "low":"min",
                "close":"last"
            }).dropna()

            ha_week = calculate_heikin_ashi(weekly)

            total_return = (
                df["close"].iloc[-1] / df["close"].iloc[0] - 1
            ) * 100

            results.append([symbol, round(total_return,2)])

        except:
            continue

    result_df = pd.DataFrame(results, columns=["Stock", "Return %"])
    st.dataframe(result_df.sort_values("Return %", ascending=False))

# =================================================

# ================= MAIN =================
run_live_scan()

st.divider()

if st.button("Run Backtest"):
    run_backtest()
