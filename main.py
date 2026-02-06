# main.py
import streamlit as st
import pandas as pd
from datetime import datetime

from config import FNO_SYMBOLS, FYERS_CLIENT_ID, REFRESH_MINUTES
from fyers_token import generate_access_token
from fyers_client import FyersClient
from option_chain import get_option_chain
from seller_logic import analyze_strike
from confidence import confidence_score
from alerts import send_email, should_alert


st.set_page_config(page_title="Seller Advisor Dashboard", layout="wide")
st.title("High-Confidence Alerts")

# ----------------- Fyers Token -----------------
st.subheader("🔐 FYERS Access Token (Manual Mode)")
access_token = st.text_input(
    "Paste FYERS access_token here",
    type="password"
)

if not access_token:
    st.warning("⚠ Please paste FYERS access_token to continue")
    st.stop()

fyers_client = FyersClient(FYERS_CLIENT_ID, access_token)


# =========================================================
# 🔝 TOP DASHBOARD BUTTONS
# =========================================================
st.markdown("### 🔌 System Health & Tests")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔌 Check FYERS Connectivity"):
        try:
            profile = fyers_client.get_profile()
            if profile.get("s") == "ok":
                st.success("FYERS Connected ✅")
                st.json(profile["data"])
            else:
                st.error(profile)
        except Exception as e:
            st.error(f"FYERS error: {e}")

with col2:
    if st.button("📧 Send Test Email"):
        try:
            send_email("TEST EMAIL", "Email system working ✅")
            st.success("Test email sent successfully ✅")
        except Exception as e:
            st.error(f"Email failed: {e}")

st.divider()

# =========================================================
# ⚙ CONTROLS
# =========================================================
st.subheader("⚙ Controls")
symbol = st.selectbox("Select Symbol", FNO_SYMBOLS)
refresh_minutes = st.number_input(
    "Refresh interval (minutes)",
    1, 30, REFRESH_MINUTES
)

# =========================================================
# 📊 OPTION CHAIN & ALERTS
# =========================================================
alerts_df = []

oc = get_option_chain(fyers_client, symbol)

if oc:
    df_oc = pd.DataFrame(oc)
    st.subheader("📈 Live Option Chain")
    st.dataframe(df_oc, use_container_width=True)

    for strike in oc:
        bias = analyze_strike(strike)
        if bias != "NO TRADE":
            score = confidence_score([bias])
            if score >= 60 and should_alert(symbol, strike["strike"], bias):
                alerts_df.append({
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Symbol": symbol,
                    "Strike": strike["strike"],
                    "Side": bias,
                    "Confidence": score
                })
                send_email(
                    f"High-Confidence Alert: {symbol}",
                    f"{symbol} {bias} Strike {strike['strike']} Confidence {score}%"
                )

# =========================================================
# 🔥 ALERT TABLE
# =========================================================
st.subheader("🔥 Latest High-Confidence Alerts")

if alerts_df:
    df_alerts = pd.DataFrame(alerts_df)

    def color_conf(val):
        if val >= 80:
            return "background-color: green; color: white"
        elif val >= 60:
            return "background-color: yellow"
        return ""

    st.dataframe(
        df_alerts.style.applymap(color_conf, subset=["Confidence"]),
        use_container_width=True
    )
else:
    st.info("✅ No high-confidence alerts currently")
