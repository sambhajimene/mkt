import pandas as pd
import numpy as np
from kiteconnect import KiteConnect
import datetime
import time

# ================= CONFIG =================
API_KEY = "z9rful06a9890v8m"
ACCESS_TOKEN = "Rylci23jGBJE6J636yAxoZCeUct0EEiX"

START_DATE = datetime.date.today() - datetime.timedelta(days=60)
END_DATE = datetime.date.today()

BODY_THRESHOLD = 0.2   # smaller = stricter (0.2 = 20% of candle range)
SLEEP_INTERVAL = 0.25  # prevent rate limit
# ==========================================

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

print("🔄 Fetching instruments...")
instruments = kite.instruments("NSE")
df_instruments = pd.DataFrame(instruments)

# ✅ NSE 500 list fetch (direct Zerodha tag method)
nse500_symbols = pd.read_csv(
    "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
)["Symbol"].tolist()

df_nse500 = df_instruments[
    (df_instruments["segment"] == "NSE") &
    (df_instruments["instrument_type"] == "EQ") &
    (df_instruments["tradingsymbol"].isin(nse500_symbols))
]

print(f"✅ NSE500 Stocks Found: {len(df_nse500)}")
print("🚀 Starting strict scan...\n")

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

for index, row in df_nse500.iterrows():
    symbol = row["tradingsymbol"]
    token = row["instrument_token"]

    try:
        data = kite.historical_data(
            token,
            START_DATE,
            END_DATE,
            "day"
        )

        if len(data) < 10:
            continue

        df = pd.DataFrame(data)
        ha = calculate_heikin_ashi(df)

        last = ha.iloc[-1]

        body = abs(last['HA_Close'] - last['HA_Open'])
        full_range = last['HA_High'] - last['HA_Low']

        if full_range == 0:
            continue

        body_ratio = body / full_range

        upper_wick = last['HA_High'] - max(last['HA_Open'], last['HA_Close'])
        lower_wick = min(last['HA_Open'], last['HA_Close']) - last['HA_Low']

        # 🔥 STRICT NEUTRAL CONDITIONS
        if (
            body_ratio < BODY_THRESHOLD and
            upper_wick > 0 and
            lower_wick > 0
        ):
            print(f"🔥 Neutral HA: {symbol}")
            signals.append(symbol)

        time.sleep(SLEEP_INTERVAL)

    except Exception as e:
        print(f"Error in {symbol}")

print("\n==============================")
print(f"🎯 Total Strict Neutral Signals: {len(signals)}")
print(signals)
