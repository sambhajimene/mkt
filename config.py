# ================== ZERODHA CONFIG ==================
ZERODHA_API_KEY = "z9rful06a9890v8m"
ZERODHA_API_SECRET = "z96wwv8htnih8n792673jj5trqc4hutm"
ZERODHA_REDIRECT_URI = "http://127.0.0.1:5009"

# Paste your Zerodha access token here (from first-time manual login)
# This token will be used in headless mode
ZERODHA_ACCESS_TOKEN = "qXtcvJ2Cr7jjdHTkDUv6RMl4xM9LnsqC"

# ================== MARKET CONFIG ==================
REFRESH_MINUTES = 5
TIMEZONE = "Asia/Kolkata"

# ================== SYMBOLS ==================
FNO_SYMBOLS = [
    "NIFTY",
    "BANKNIFTY",
    "RELIANCE",
    "TCS",
    "HDFCBANK",
    "ICICIBANK",
    "INFY",
    "SBIN"
]

# ================== Email Config ==================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_FROM = "sambhajimene@gmail.com"
EMAIL_PASSWORD = "jgebigpsoeqqwrfa"
EMAIL_TO = ["sambhajimene@gmail.com"]

# ================== Alerts Config ==================
MIN_CONFIDENCE = 60  # %
