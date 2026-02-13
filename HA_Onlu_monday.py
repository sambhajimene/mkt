import pandas as pd
import datetime
import time
from kiteconnect import KiteConnect

# ================= CONFIG =================

API_KEY = "z9rful06a9890v8m"
ACCESS_TOKEN = "Rylci23jGBJE6J636yAxoZCeUct0EEiX"

TOL = 0.0001
SLEEP_INTERVAL = 0.25
# ==========================================

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

now = datetime.datetime.now()
today = now.date()

# ===== Only Run Monday after 10:20 =====
if now.weekday() != 0 or now.time() < datetime.time(10, 20):
    print("⏳ This scanner runs only Monday after 10:20 AM")
    exit()

print("🚀 Running Monday Weekly + Hourly HA Scanner...\n")

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

# ===== Load NSE500 =====
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

for _, row in df_stocks.iterrows():

    symbol = row["tradingsymbol"]
    token = row["instrument_token"]

    try:
        # ================= WEEKLY =================
        weekly_data = kite.historical_data(
            token,
            today - datetime.timedelta(days=365),
            today,
            "week"
        )

        if len(weekly_data) < 20:
            continue

        df_weekly = pd.DataFrame(weekly_data)
        ha_weekly = calculate_heikin_ashi(df_weekly)

        last_w = ha_weekly.iloc[-2]   # closed week
        prev_w = ha_weekly.iloc[-3]

        last_w_body = last_w['HA_Close'] - last_w['HA_Open']
        prev_w_body = prev_w['HA_Close'] - prev_w['HA_Open']

        weekly_bullish = (
            prev_w_body > 0 and
            last_w_body > 0 and
            abs(last_w['HA_Open'] - last_w['HA_Low']) < TOL
        )

        weekly_bearish = (
            prev_w_body < 0 and
            last_w_body < 0 and
            abs(last_w['HA_Open'] - last_w['HA_High']) < TOL
        )

        if not weekly_bullish and not weekly_bearish:
            continue

        # ================= MONDAY HOURLY =================
        hourly_data = kite.historical_data(
            token,
            today,
            today,
            "60minute"
        )

        if len(hourly_data) < 1:
            continue

        df_hourly = pd.DataFrame(hourly_data)
        ha_hourly = calculate_heikin_ashi(df_hourly)

        first_hour = ha_hourly.iloc[0]
        first_body = first_hour['HA_Close'] - first_hour['HA_Open']

        hourly_bullish = (
            first_body > 0 and
            abs(first_hour['HA_Open'] - first_hour['HA_Low']) < TOL
        )

        hourly_bearish = (
            first_body < 0 and
            abs(first_hour['HA_Open'] - first_hour['HA_High']) < TOL
        )

        # ================= FINAL =================
        if weekly_bullish and hourly_bullish:
            print(f"🟢 BUY: {symbol}")
            bullish.append(symbol)

        if weekly_bearish and hourly_bearish:
            print(f"🔴 SELL: {symbol}")
            bearish.append(symbol)

        time.sleep(SLEEP_INTERVAL)

    except Exception:
        continue

# ================= RESULT =================
print("\n==============================")
print(f"🟢 BUY Signals: {len(bullish)}")
print(bullish)

print(f"\n🔴 SELL Signals: {len(bearish)}")
print(bearish)
