# ================== ZERODHA CONFIG ==================
ZERODHA_API_KEY = "z9rful06a9890v8m"
ZERODHA_API_SECRET = "z96wwv8htnih8n792673jj5trqc4hutm"
ZERODHA_REDIRECT_URI = "http://127.0.0.1:5009"

# Paste your Zerodha access token here (from first-time manual login)
# This token will be used in headless mode
ZERODHA_ACCESS_TOKEN = "ZW6Hm3GgtPwe5qU39DPBzMWT8XGb2xeM"

# ================== MARKET CONFIG ==================
REFRESH_MINUTES = 5
TIMEZONE = "Asia/Kolkata"

# ================== SYMBOLS ==================
import pandas as pd
import os
import requests

INSTRUMENTS_CSV = "instruments.csv"  # Local path for instruments file

def download_instruments():
    """Download instruments.csv from Zerodha Kite"""
    print("Downloading instruments.csv from Zerodha...")
    url = "https://api.kite.trade/instruments"
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(INSTRUMENTS_CSV, "wb") as f:
            f.write(response.content)
        print("instruments.csv downloaded successfully!")
    except Exception as e:
        raise Exception(f"Failed to download instruments.csv: {e}")

# Automatically download if not exists
if not os.path.exists(INSTRUMENTS_CSV):
    download_instruments()

# Load instruments CSV
df = pd.read_csv(INSTRUMENTS_CSV)

# Filter for NSE Futures & Options (stocks + indices)
fno_stocks = df[(df["segment"] == "NSE") & (df["instrument_type"].isin(["FUT", "OPT"]))]

# Extract unique tradingsymbols
FNO_SYMBOLS = sorted(fno_stocks["tradingsymbol"].unique())
print(f"Total NSE F&O symbols loaded: {len(FNO_SYMBOLS)}")

# ================== Email Config ==================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_FROM = "sambhajimene@gmail.com"
EMAIL_PASSWORD = "jgebigpsoeqqwrfa"
EMAIL_TO = ["sambhajimene@gmail.com"]

# ================== Alerts Config ==================
MIN_CONFIDENCE = 60  # %
