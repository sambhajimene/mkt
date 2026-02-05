# config.py

# ----------------- Market -----------------
TIMEZONE = "Asia/Kolkata"
REFRESH_MINUTES = 5
FNO_SYMBOLS = ["RELIANCE","TCS","HDFCBANK","ICICIBANK","NIFTY","BANKNIFTY"]

# ----------------- Fyers API -----------------
FYERS_CLIENT_ID = "UEYCB0VJMM-100"
FYERS_SECRET_KEY = "FNC70J694G"
REDIRECT_URI = "https://mk-menesambhaji-dev.apps.rm1.0a51.p1.openshiftapps.com/"

# ----------------- Email -----------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_FROM = "yourmail@gmail.com"
EMAIL_PASSWORD = "your_app_password"
EMAIL_TO = ["yourmail@gmail.com"]

# ----------------- Alerts -----------------
MIN_CONFIDENCE = 60  # %
