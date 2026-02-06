import streamlit as st
import pandas as pd
from datetime import datetime

from config import FNO_SYMBOLS, REFRESH_MINUTES, MIN_CONFIDENCE
from zerodha_client import ZerodhaClient
from option_chain import get_option_chain
from seller_logic import analyze_strike
from confidence import confidence_score
from alerts import send_email, should_alert

# ----------------- Streamlit Page -----------------
st.set_page_config(page_title="Zerodha Seller Advisor", layout="wide")
st.title("High-Confidence Alerts (Zerodha)")

# ----------------- Initialize Zerodha Client -----------------
st.subheader("🔌 Initializing Zerodha Client...")
client = ZerodhaClient()
st.success("Kite Client ready ✅")

# ----------------- System Health & Tests -----------------
st.markdown("### 🔌 System Health & Tests")
col1, col2 = st.columns(2)

# --- Button: Check Zerodha Connectivity ---
with col1:
    if st.button("🔌 Check Zerodha Connectivity"):
        profile = client.get_profile()
        if profile:
            st.success("Kite Connected ✅")
            st.json(profile)
        else:
            st.error("Failed to fetch profile")

# --- Button: Send Test Email ---
with col2:
    if st.button("📧 Send Test Email"):
        try:
            send_email("TEST EMAIL", "Email system working ✅")
            st.success("Test email sent successfully ✅")
        except Exception as e:
            st.error(f"Email failed: {e}")

st.divider()

# ----------------- Controls -----------------
st.subheader("⚙ Controls")
symbol = st.selectbox("Select Symbol", FNO_SYMBOLS)
refresh_minutes = st.number_input(
    "Refresh interval (minutes)", 1, 30, REFRESH_MINUTES
)

# ----------------- Option Chain & Alerts -----------------
alerts_df = []

oc = get_option_chain(client, symbol)
if oc:
    df_oc = pd.DataFrame(oc)
    st.subheader("📈 Live Option Chain")
    st.dataframe(df_oc, use_container_width=True)

    for strike in oc:
        bias = analyze_strike(strike)
        if bias != "NO TRADE":
            score = confidence_score([bias])
            if score >= MIN_CONFIDENCE and should_alert(symbol, strike["strike"], bias):
                alerts_df.append({
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Symbol": symbol,
                    "Strike": strike["strike"],
                    "Side": bias,
                    "Confidence": score
                })
                # Send Email Alert
                send_email(
                    f"High-Confidence Alert: {symbol}",
                    f"{symbol} {bias} Strike {strike['strike']} Confidence {score}%"
                )

# ----------------- Alerts Table -----------------
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
