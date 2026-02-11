import yfinance as yf
import pandas as pd

# =========================
# Heikin Ashi Functions
# =========================

def heikin_ashi(df):
    ha_df = df.copy()
    ha_df['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    ha_df['HA_Open'] = (df['Open'].shift(1) + df['Close'].shift(1)) / 2
    ha_df['HA_High'] = ha_df[['HA_Open', 'HA_Close', 'High']].max(axis=1)
    ha_df['HA_Low'] = ha_df[['HA_Open', 'HA_Close', 'Low']].min(axis=1)
    return ha_df

def is_strong_ha(df):
    return abs(df['HA_Open'].iloc[-1] - df['HA_Low'].iloc[-1]) < 0.01 and df['HA_Close'].iloc[-1] > df['HA_Open'].iloc[-1]

# =========================
# Get NSE 500 List
# =========================

def get_nse500_list():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    df = pd.read_csv(url)
    symbols = df['Symbol'].tolist()
    symbols = [s + ".NS" for s in symbols]
    return symbols

# =========================
# Scanner Logic
# =========================

print("Fetching NSE 500 list...")
nse500 = get_nse500_list()
print(f"Total stocks fetched: {len(nse500)}")

results = []

for stock in nse500:
    try:
        print(f"Checking {stock}...")

        # Fetch weekly, daily, and hourly data
        weekly = yf.download(stock, period="1y", interval="1wk", progress=False)
        daily = yf.download(stock, period="6mo", interval="1d", progress=False)
        hourly = yf.download(stock, period="1mo", interval="1h", progress=False)

        if weekly.empty or daily.empty or hourly.empty:
            continue

        weekly_ha = heikin_ashi(weekly)
        daily_ha = heikin_ashi(daily)
        hourly_ha = heikin_ashi(hourly)

        weekly_strong = is_strong_ha(weekly_ha)
        daily_strong = is_strong_ha(daily_ha)
        hourly_strong = is_strong_ha(hourly_ha)

        # Scanner Logic: Weekly + Daily + Hourly strong HA
        if weekly_strong and daily_strong and hourly_strong:
            results.append(stock)

    except Exception as e:
        continue

# =========================
# Output
# =========================

print("\n===== WEEKLY + DAILY + HOURLY STRONG HA STOCKS =====")
for r in results:
    print(r)

if not results:
    print("No stocks matched across all 3 timeframes.")

(venv) root@root:/HA# cat scanner.py
import yfinance as yf
import pandas as pd

# =========================
# Heikin Ashi Functions
# =========================

def heikin_ashi(df):
    ha_df = df.copy()
    ha_df['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    ha_df['HA_Open'] = (df['Open'].shift(1) + df['Close'].shift(1)) / 2
    ha_df['HA_High'] = ha_df[['HA_Open', 'HA_Close', 'High']].max(axis=1)
    ha_df['HA_Low'] = ha_df[['HA_Open', 'HA_Close', 'Low']].min(axis=1)
    return ha_df

def is_strong_ha(df):
    return abs(df['HA_Open'].iloc[-1] - df['HA_Low'].iloc[-1]) < 0.01 and df['HA_Close'].iloc[-1] > df['HA_Open'].iloc[-1]

# =========================
# Get NSE 500 List
# =========================

def get_nse500_list():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    df = pd.read_csv(url)
    symbols = df['Symbol'].tolist()
    symbols = [s + ".NS" for s in symbols]
    return symbols

# =========================
# Scanner Logic
# =========================

print("Fetching NSE 500 list...")
nse500 = get_nse500_list()
print(f"Total stocks fetched: {len(nse500)}")

results = []

for stock in nse500:
    try:
        print(f"Checking {stock}...")

        # Fetch weekly, daily, and hourly data
        weekly = yf.download(stock, period="1y", interval="1wk", progress=False)
        daily = yf.download(stock, period="6mo", interval="1d", progress=False)
        hourly = yf.download(stock, period="1mo", interval="1h", progress=False)

        if weekly.empty or daily.empty or hourly.empty:
            continue

        weekly_ha = heikin_ashi(weekly)
        daily_ha = heikin_ashi(daily)
        hourly_ha = heikin_ashi(hourly)

        weekly_strong = is_strong_ha(weekly_ha)
        daily_strong = is_strong_ha(daily_ha)
        hourly_strong = is_strong_ha(hourly_ha)

        # Scanner Logic: Weekly + Daily + Hourly strong HA
        if weekly_strong and daily_strong and hourly_strong:
            results.append(stock)

    except Exception as e:
        continue

# =========================
# Output
# =========================

print("\n===== WEEKLY + DAILY + HOURLY STRONG HA STOCKS =====")
for r in results:
    print(r)

if not results:
    print("No stocks matched across all 3 timeframes.")
