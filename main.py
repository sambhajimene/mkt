# main.py
import streamlit as st
from datetime import datetime
import pandas as pd
from config import FNO_SYMBOLS, FYERS_CLIENT_ID
from fyers_client import FyersClient
from option_chain import get_option_chain
from seller_logic import analyze_strike
from confidence import confidence_score
from alerts import send_email, should_alert
import time

st.set_page_config(page_title="Seller Advisor Dashboard", layout="wide")
st.title("🚀 Seller Advisor Dashboard (High-Confidence Alerts)")

# ----------------- Fyers Access Token -----------------
access_token = st.text_input("Enter Fyers Access Token", type="password")
if not access_token:
    st.warning("Please enter your Fyers access token to continue.")
    st.stop()

fyers_client = FyersClient(FYERS_CLIENT_ID, access_token)

# ----------------- Sidebar -----------------
st.sidebar.header("⚙ Controls")
symbol = st.sidebar.selectbox("Select Symbol", FNO_SYMBOLS)
refresh_minutes = st.sidebar.number_input("Refresh interval (minutes)", 1, 30, 5)
show_loc = st.sidebar.checkbox("Show Live Option Chain (LOC)", True)

# ----------------- Health Check -----------------
st.subheader("🔌 System Health Check")
if st.button("Check Fyers Connectivity"):
    try:
        test = fyers_client.get_quotes([f"NSE:{symbol}"])
        if test:
            st.success("Fyers Connected ✅")
        else:
            st.error("Failed to fetch data from Fyers")
    except Exception as e:
        st.error(f"Error: {e}")

# ----------------- Main Dashboard Loop -----------------
alerts_df = []

while True:
    st.subheader(f"🟢 Live Option Chain & Alerts: {symbol}")
    try:
        oc = get_option_chain(fyers_client, symbol)
        if not oc:
            st.warning("⚠ No data returned from Fyers for this symbol")
        else:
            df_oc = pd.DataFrame(oc)
            atm = df_oc['strike'].iloc[len(df_oc)//2]

            # Highlight ATM ±2 strikes
            def highlight_atm(s):
                return ['background-color: yellow' if atm-2*50 <= v <= atm+2*50 else '' for v in s]

            if show_loc:
                st.dataframe(df_oc.style.apply(highlight_atm, subset=['strike']))

            # Seller bias + alerts
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

            # Display alerts
            if alerts_df:
                df_alerts = pd.DataFrame(alerts_df)
                def color_confidence(val):
                    if val >= 80: return 'background-color: green; color:white'
                    elif val >= 60: return 'background-color: yellow'
                    else: return ''
                st.dataframe(df_alerts.style.applymap(color_confidence, subset=['Confidence']))
            else:
                st.info("✅ No high-confidence alerts currently")

    except Exception as e:
        st.error(f"Error processing {symbol}: {e}")

    st.info(f"Next refresh in {refresh_minutes} minutes ⏳")
    time.sleep(refresh_minutes*60)
