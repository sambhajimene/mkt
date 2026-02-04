# config.py

# -----------------------------
# MARKET SETTINGS
# -----------------------------
TIMEZONE = "Asia/Kolkata"

MARKET_OPEN = (9, 15)
MARKET_CLOSE = (15, 30)

REFRESH_MINUTES = 10

# -----------------------------
# OPTION SETTINGS
# -----------------------------
ATM_RANGE = 2          # ATM ±2
MIN_CONFIDENCE = 60    # % to show / alert

# -----------------------------
# SYMBOL LIST (START SMALL)
# -----------------------------
INDEX_SYMBOLS = [
    "NIFTY",
    "BANKNIFTY",
    "FINNIFTY"
]

STOCK_SYMBOLS = [
    "RELIANCE",
    "TCS",
    "INFY",
    "HDFCBANK",
    "ICICIBANK",
    "SBIN",
    "LT",
    "HCLTECH"
]

ALL_SYMBOLS = INDEX_SYMBOLS + STOCK_SYMBOLS
