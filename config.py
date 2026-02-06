# ===== ZERODHA CONFIG =====
ZERODHA_API_KEY = "your_api_key"
ZERODHA_API_SECRET = "your_api_secret"
ZERODHA_REDIRECT_URI = "http://127.0.0.1:5009"  # Local for manual login

# ===== MARKET CONFIG =====
REFRESH_MINUTES = 5
TIMEZONE = "Asia/Kolkata"

# ===== SYMBOLS =====
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

# ----------------- Email -----------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_FROM = "yourmail@gmail.com"
EMAIL_PASSWORD = "your_app_password"
EMAIL_TO = ["yourmail@gmail.com"]

# ----------------- Alerts -----------------
MIN_CONFIDENCE = 60  # %
