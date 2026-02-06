# config.py

# ===== FYERS CONFIG =====

FYERS_CLIENT_ID = "UEYCB0VJMM-100"      # App ID
FYERS_SECRET_ID = "FNC70J694G"         # Secret ID
REDIRECT_URI = "https://mk-menesambhaji-dev.apps.rm1.0a51.p1.openshiftapps.com/"

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