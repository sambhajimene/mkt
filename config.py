# ================== ZERODHA CONFIG ==================
ZERODHA_API_KEY = "z9rful06a9890v8m"
ZERODHA_API_SECRET = "z96wwv8htnih8n792673jj5trqc4hutm"
ZERODHA_REDIRECT_URI = "http://127.0.0.1:5009"
ZERODHA_ACCESS_TOKEN = "ZW6Hm3GgtPwe5qU39DPBzMWT8XGb2xeM"

# ================== MARKET CONFIG ==================
REFRESH_MINUTES = 5
TIMEZONE = "Asia/Kolkata"

# ================== SYMBOLS ==================
import pandas as pd
import requests
from io import StringIO

# In-memory download of instruments.csv from Zerodha
INSTRUMENTS_URL = "https://api.kite.trade/instruments"

try:
    response = requests.get(INSTRUMENTS_URL)
    response.raise_for_status()
    csv_data = StringIO(response.text)  # Load CSV into memory
    df = pd.read_csv(csv_data)
except Exception as e:
    raise Exception(f"Failed to load instruments CSV: {e}")

# Filter NSE F&O (Futures + Options)
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
