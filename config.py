# ================== ZERODHA CONFIG ==================
ZERODHA_API_KEY = "your_api_key_here"
ZERODHA_API_SECRET = "your_api_secret_here"
ZERODHA_REDIRECT_URI = "https://your_redirect_uri_here"

# Paste your Zerodha access token here (from first-time manual login)
# This token will be used in headless mode
ZERODHA_ACCESS_TOKEN = "paste_your_access_token_here"

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
EMAIL_FROM = "yourmail@gmail.com"
EMAIL_PASSWORD = "your_app_password"
EMAIL_TO = ["yourmail@gmail.com"]

# ================== Alerts Config ==================
MIN_CONFIDENCE = 60  # %
