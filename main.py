# ==============================
# main.py
# Seller Advisor – REAL NSE DATA
# ==============================

import streamlit as st
import pandas as pd
import pytz
from datetime import datetime, time
from nsepython import nse_optionchain_scrapper

# ==============================
# CONFIG
# ==============================

TIMEZONE = pytz.timezone("Asia/Kolkata")

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)

REFRESH_SECONDS = 600  # 10 min

SYMBOLS = [
    "NIFTY","BANKNIFTY","FINNIFTY","RELIANCE","TCS","HDFCBANK","ICICIBANK",
    "INFY","SBIN","HCLTECH","KOTAKBANK","LT","ITC","HINDUNILVR","AXISBANK",
    "MARUTI","TECHM","ASIANPAINT","WIPRO","BAJAJ-AUTO","BHARTIARTL","DRREDDY",
    "TITAN","ULTRACEMCO","HDFCLIFE","DIVISLAB","ADANIPORTS","INDUSINDBK","JSWSTEEL",
    "ONGC","GRASIM","COALINDIA","BPCL","SHREECEM","HDFCBANK","LTIM","SUNPHARMA",
    "EICHERMOT","TATAMOTORS","HCLTECH","UPL","ICICIPRULI","BAJFINANCE","CIPLA",
    "BRITANNIA","POWERGRID","NTPC","TATACONSUM","VEDL","SBILIFE","TECHM","GAIL",
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","AXISBANK","KOTAKBANK","LT",
    "ITC","HINDUNILVR","SBIN","HCLTECH","MARUTI","BAJAJFINSV","ADANIENT","ADANIGREEN",
    "BAJAJ-AUTO","BHARTIARTL","DRREDDY","TITAN","ULTRACEMCO","DIVISLAB","ASIANPAINT",
    "ONGC","GRASIM","COALINDIA","BPCL","SHREECEM","LTIM","SUNPHARMA","EICHERMOT",
    "TATAMOTORS","UPL","ICICIPRULI","BAJFINANCE","CIPLA","BRITANNIA","POWERGRID",
    "NTPC","TATACONSUM","VEDL","SBILIFE","GAIL","RELIANCE","TCS","INFY","HDFCBANK",
    "ICICIBANK","AXISBANK","KOTAKBANK","LT","ITC","HINDUNILVR","SBIN","HCLTECH",
    "MARUTI","TECHM","ASIANPAINT","WIPRO","BAJAJ-AUTO","BHARTIARTL","DRREDDY",
    "TITAN","ULTRACEMCO","HDFCLIFE","DIVISLAB","ADANIPORTS","INDUSINDBK","JSWSTEEL",
    "ONGC","GRASIM","COALINDIA","BPCL","SHREECEM","HDFCBANK","LTIM","SUNPHARMA",
    "EICHERMOT","TATAMOTORS","HCLTECH","UPL","ICICIPRULI","BAJFINANCE","CIPLA",
    "BRITANNIA","POWERGRID","NTPC","TATACONSUM","VEDL","SBILIFE","TECHM","GAIL"
]

# ==============================
# TIME FUNCTIONS
# ==============================

def ist_now():
    return datetime.now(TIMEZONE)

def is_market_open():
    now = ist_now().time()
    return MARKET_OPEN <= now <= MARKET_CLOSE

# ==============================
# NSE OPTION DATA (REAL)
# ==============================

def get_option_data(symbol):
    """
    Fetch ATM strike + OI change for CE & PE
    """
    try:
        data = nse_optionchain_scrapper(symbol)

        spot = data["records"]["underlyingValue"]

        strikes = sorted(
            set(item["strikePrice"] for item in data["records"]["data"])
        )

        atm = min(strikes, key=lambda x: abs(x - spot))

        ce_oi = pe_oi = 0

        for item in data["records"]["data"]:
            if item["strikePrice"] == atm:
                if "CE" in item:
                    ce_oi = item["CE"]["changeinOpenInterest"]
                if "PE" in item:
                    pe_oi = item["PE"]["changeinOpenInterest"]

        return atm, ce_oi, pe_oi

    except Exception as e:
        return None, None, None

# ==============================
# SELLER LOGIC (GOLD)
# ==============================

def seller_bias(ce_oi, pe_oi):
    if ce_oi is None or pe_oi is None:
        return None, None

    # CALL Writing + PUT Unwinding
    if ce_oi > 0 and pe_oi < 0:
        return "MARKET DOWN (PUT BUY bias)", "🔴"

    # CALL Unwinding + PUT Writing
    if ce_oi < 0 and pe_oi > 0:
        return "MARKET UP (CALL BUY bias)", "🟢"

    # Both Writing
    if ce_oi > 0 and pe_oi > 0:
        return "RANGE / TRAP – NO TRADE", "🟠"

    # Both Unwinding
    if ce_oi < 0 and pe_oi < 0:
        return "BREAKOUT / VOLATILITY", "🟣"

    return "NO CLEAR EDGE", "⚪"

# ==============================
# STREAMLIT UI
# ==============================

st.set_page_config("Seller Advisor – NSE Options", layout="wide")

st.title("📊 Seller Advisor – REAL NSE Option Chain")

st.caption(f"🕒 IST Time: {ist_now().strftime('%d-%b-%Y %H:%M:%S')}")

if not is_market_open():
    st.warning("🚫 Market Closed (IST)")
    st.stop()

st.success("✅ Market Live")

st.caption("🔄 Auto refresh every 10 minutes")

# ==============================
# DASHBOARD TABLE
# ==============================

rows = []

for symbol in SYMBOLS:
    atm, ce_oi, pe_oi = get_option_data(symbol)

    signal, emoji = seller_bias(ce_oi, pe_oi)

    if signal is None:
        continue  # NSE data not available

    rows.append({
        "Symbol": symbol,
        "ATM Strike": atm,
        "CALL OI Δ": ce_oi,
        "PUT OI Δ": pe_oi,
        "Signal": f"{emoji} {signal}"
    })

df = pd.DataFrame(rows)

if df.empty:
    st.error("❌ NSE data not available right now")
else:
    st.dataframe(df, use_container_width=True)

# ==============================
# CONFIDENCE SCORE
# ==============================

if not df.empty:
    signals = df["Signal"].tolist()
    dominant = max(set(signals), key=signals.count)
    score = int((signals.count(dominant) / len(signals)) * 100)

    st.subheader("📈 Confidence Meter")
    st.progress(score)

    if score >= 60:
        st.success(f"🔥 HIGH CONFIDENCE: {score}%")
    else:
        st.info(f"⚠️ LOW CONFIDENCE: {score}% – WAIT")

# ==============================
# FOOTER
# ==============================

st.caption("Seller logic based on REAL OI change | ATM focused")
