# ===== MARKET CONFIG =====
TIMEZONE = "Asia/Kolkata"
REFRESH_MINUTES = 10

# ===== INDICES =====
INDEX_SYMBOLS = ["NIFTY", "BANKNIFTY"]

# ===== F&O STOCKS (NSE official list – expandable) =====
FNO_STOCKS = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","LT","HCLTECH",
    "KOTAKBANK","AXISBANK","ITC","MARUTI","ONGC","POWERGRID","BHARTIARTL"
]

# ===== EMAIL CONFIG =====
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = "yourmail@gmail.com"
EMAIL_PASSWORD = "your_app_password"
EMAIL_TO = ["yourmail@gmail.com"]

# ===== ALERT CONTROL =====
MIN_CONFIDENCE = 60   # %
