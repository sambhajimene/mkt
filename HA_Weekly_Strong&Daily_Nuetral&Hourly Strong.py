import pandas as pd
import numpy as np
from kiteconnect import KiteConnect
import datetime
import time

# ================= CONFIG =================
API_KEY = "z9rful06a9890v8m"
ACCESS_TOKEN = "Rylci23jGBJE6J636yAxoZCeUct0EEiX"

START_DATE = datetime.date.today() - datetime.timedelta(days=120)
END_DATE = datetime.date.today()

BODY_THRESHOLD = 0.2
SLEEP_INTERVAL = 0.2
# ==========================================

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

print("🔄 Fetching instruments...")
instruments = kite.instruments("NSE")
df_instruments = pd.DataFrame(instruments)

# NSE500 list
nse500_symbols = pd.read_csv(
    "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
)["Symbol"].tolist()

df_nse500 = df_instruments[
    (df_instruments["segment"] == "NSE") &
    (df_instruments["instrument_type"] == "EQ") &
    (df_instruments["tradingsymbol"].isin(nse500_symbols))
]

print(f"✅ NSE500 Stocks Found: {len(df_nse500)}")
print("🚀 Starting Multi-Timeframe Scan...\n")

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
# =================================================

signals = []

for _, row in df_nse500.iterrows():
    symbol = row["tradingsymbol"]
    token = row["instrument_token"]

    try:
        # ================= DAILY =================
        daily_data = kite.historical_data(token, START_DATE, END_DATE, "day")
        if len(daily_data) < 60:
            continue

        df_daily = pd.DataFrame(daily_data)
        df_daily["EMA50"] = df_daily["close"].ewm(span=50).mean()

        ha_daily = calculate_heikin_ashi(df_daily)
        last_daily = ha_daily.iloc[-1]

        body = abs(last_daily['HA_Close'] - last_daily['HA_Open'])
        full_range = last_daily['HA_High'] - last_daily['HA_Low']
        if full_range == 0:
            continue

        body_ratio = body / full_range
        upper_wick = last_daily['HA_High'] - max(last_daily['HA_Open'], last_daily['HA_Close'])
        lower_wick = min(last_daily['HA_Open'], last_daily['HA_Close']) - last_daily['HA_Low']

        neutral_daily = (
            body_ratio < BODY_THRESHOLD and
            upper_wick > 0 and
            lower_wick > 0 and
            last_daily["close"] > last_daily["EMA50"]
        )

        if not neutral_daily:
            continue

        # ================= WEEKLY =================
        weekly_data = kite.historical_data(
            token,
            datetime.date.today() - datetime.timedelta(days=365),
            END_DATE,
            "week"
        )

        if len(weekly_data) < 10:
            continue

        df_weekly = pd.DataFrame(weekly_data)
        ha_weekly = calculate_heikin_ashi(df_weekly)
        last_weekly = ha_weekly.iloc[-1]

        weekly_body = last_weekly['HA_Close'] - last_weekly['HA_Open']
        weekly_lower_wick = min(last_weekly['HA_Open'], last_weekly['HA_Close']) - last_weekly['HA_Low']

        weekly_strong = (
            weekly_body > 0 and
            weekly_lower_wick <= (weekly_body * 0.1)
        )

        if not weekly_strong:
            continue

        # ================= HOURLY =================
        hourly_data = kite.historical_data(
            token,
            datetime.date.today() - datetime.timedelta(days=10),
            END_DATE,
            "60minute"
        )

        if len(hourly_data) < 20:
            continue

        df_hourly = pd.DataFrame(hourly_data)
        ha_hourly = calculate_heikin_ashi(df_hourly)
        last_hourly = ha_hourly.iloc[-1]

        hourly_body = last_hourly['HA_Close'] - last_hourly['HA_Open']
        hourly_lower_wick = min(last_hourly['HA_Open'], last_hourly['HA_Close']) - last_hourly['HA_Low']
        hourly_range = last_hourly['HA_High'] - last_hourly['HA_Low']

        if hourly_range == 0:
            continue

        hourly_body_ratio = hourly_body / hourly_range

        hourly_strong = (
            hourly_body > 0 and
            hourly_lower_wick <= (hourly_body * 0.1) and
            hourly_body_ratio > 0.5
        )

        if hourly_strong:
            print(f"🔥 HIGH PROBABILITY SETUP: {symbol}")
            signals.append(symbol)

        time.sleep(SLEEP_INTERVAL)

    except Exception:
        continue

print("\n==============================")
print(f"🎯 Total High Probability Signals: {len(signals)}")
print(signals)
