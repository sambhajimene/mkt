# main.py
import streamlit as st
import pandas as pd
from datetime import datetime

from config import FNO_SYMBOLS, REFRESH_MINUTES, MIN_CONFIDENCE
from zerodha_client import ZerodhaClient
from option_chain import get_option_chain
from seller_logic import analyze_strike
from confidence import confidence_score
from alerts import send_email, should_alert

st.set_page_config(page_title="Advisor Dashboard", layout="wide")
st.title("Live Alerts")

# =========================================================
# 🔌 SYSTEM HEALTH TABS (RESTORED)
# =========================================================
st.subheader("🔌 System Health & Tests")

client = ZerodhaClient()

col1, col2 = st.columns(2)

with col1:
    if st.button("🔌 Check Zerodha Connectivity"):
        profile = client.get_profile()
        if profile:
            st.success("Zerodha Connected ✅")
            st.json(profile)
        else:
            st.error("❌ Zerodha connection failed")

with col2:
    if st.button("📧 Send Test Email"):
        ok = send_email("TEST EMAIL", "Email system working ✅")
        if ok:
            st.success("Test email sent successfully ✅")
        else:
            st.error("Email failed ❌")

st.divider()

# =========================================================
# ⚙ CONTROLS
# =========================================================
st.subheader("⚙ Controls")

symbol = st.selectbox("Select Symbol", FNO_SYMBOLS)
refresh_minutes = st.number_input(
    "Refresh interval (minutes)", 1, 30, REFRESH_MINUTES
)

# =========================================================
# 📊 OPTION CHAIN & ALERT LOGIC
# =========================================================
alerts = []

oc = get_option_chain(client, symbol)

if oc:
    df_oc = pd.DataFrame(oc)
    st.subheader("📈 Live Option Chain")
    st.dataframe(df_oc, use_container_width=True)

    biases = []

    for strike in oc:
        bias = analyze_strike(strike)
        if bias != "NO TRADE":
            biases.append(bias)

    score = confidence_score(biases)

    # 🔍 LIVE DEBUG (market time me useful)
    st.write("Biases:", biases)
    st.write("Confidence:", score)

    if score >= MIN_CONFIDENCE and biases:
        final_bias = max(set(biases), key=biases.count)

        if should_alert(symbol, final_bias):
            alerts.append({
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Symbol": symbol,
                "Signal": final_bias,
                "Confidence": score
            })

            send_email(
                f"High-Confidence Alert: {symbol}",
                f"""Symbol: {symbol}
Signal: {final_bias}
Confidence: {score}%"""
            )

# =========================================================
# 🔥 ALERT TABLE
# =========================================================
st.subheader("🔥 Latest High-Confidence Alerts")

if alerts:
    df_alerts = pd.DataFrame(alerts)

    def color_conf(val):
        if val >= 80:
            return "background-color: green; color: white"
        elif val >= MIN_CONFIDENCE:
            return "background-color: yellow"
        return ""

    st.dataframe(
        df_alerts.style.applymap(color_conf, subset=["Confidence"]),
        use_container_width=True
    )
else:
    st.info("No high-confidence alerts right now")
