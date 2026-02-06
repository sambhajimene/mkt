# main.py

import streamlit as st
from datetime import datetime
import pandas as pd

from config import FNO_SYMBOLS, FYERS_CLIENT_ID, REFRESH_MINUTES
from fyers_client import FyersClient
from option_chain import get_option_chain
from seller_logic import analyze_strike
from confidence import confidence_score
from alerts import send_email, should_alert


st.set_page_config(page_title="High-Confidence Alerts", layout="wide")
st.title("🚀 High-Confidence Alerts")

# ----------------- FYERS TOKEN -----------------
st.markdown("### 🔑 FYERS Access Token")
access_token = st.text_input(
    "Paste token in format: APP_ID:ACCESS_TOKEN",
    type="password"
)

if not access_token:
    st.warning("⚠️ Paste FYERS access token to continue")
    st.stop()

# ✅ create client
fyers_client = FyersClient(FYERS_CLIENT_ID, access_token)

# ----------------- Sidebar -----------------
st.sidebar.header("⚙ Controls")
symbol = st.sidebar.selectbox("Select Symbol", FNO_SYMBOLS)
refresh_minutes = st.sidebar.number_input(
    "Refresh interval (minutes)", 1, 30, REFRESH_MINUTES
)
show_loc = st.sidebar.checkbox("Show Live Option Chain (LOC)", True)

# ----------------- Mail Test -----------------
st.sidebar.markdown("## 📧 Test Email")
if st.sidebar.button("Send Test Email"):
    try:
        send_email("TEST EMAIL", "Email system working ✅")
        st.success("✅ Test Email sent")
    except Exception as e:
        st.error(f"❌ Email failed: {e}")

# ----------------- Health Check -----------------
st.subheader("🔌 System Health Check")
if st.button("Check FYERS Connectivity"):
    try:
        profile = fyers_client.get_profile()
        if profile.get("s") == "ok":
            st.success("FYERS Connected ✅")
            st.json(profile["data"])
        else:
            st.error("FYERS connection failed")
    except Exception as e:
        st.error(f"Error: {e}")

# ----------------- Alerts -----------------
alerts_df = []

oc = get_option_chain(fyers_client, symbol)
if oc:
    df_oc = pd.DataFrame(oc)
    atm = df_oc['strike'].iloc[len(df_oc)//2]

    if show_loc:
        def highlight_atm(s):
            return [
                'background-color: yellow'
                if atm - 100 <= v <= atm + 100 else ''
                for v in s
            ]

        st.dataframe(
            df_oc.style.apply(highlight_atm, subset=['strike'])
        )

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
                    f"{symbol} {bias} {strike['strike']} | Confidence {score}%"
                )

if alerts_df:
    df_alerts = pd.DataFrame(alerts_df)

    def color_confidence(val):
        if val >= 80:
            return 'background-color: green; color:white'
        elif val >= 60:
            return 'background-color: yellow'
        return ''

    st.dataframe(
        df_alerts.style.applymap(
            color_confidence, subset=['Confidence']
        )
    )
else:
    st.info("✅ No high-confidence alerts currently")
