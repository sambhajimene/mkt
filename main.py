# main.py
import streamlit as st
from datetime import datetime
import pandas as pd

from config import FNO_SYMBOLS
from option_chain import get_option_chain, test_nse_connectivity
from seller_logic import analyze_option_chain
from confidence import confidence_score
from alerts import send_email, should_alert

# -------------------
# Streamlit Page Setup
# -------------------
st.set_page_config(page_title="🚀 Dashboard", layout="wide")
st.title("🚀 Dashboard (High-Confidence Alerts)")

# -------------------
# System Health Buttons
# -------------------
st.subheader("🔌 System Health Checks")
col1, col2 = st.columns(2)

with col1:
    if st.button("📧 Test Email"):
        try:
            send_email("TEST EMAIL", "Email system working ✅")
            st.success("Email sent successfully")
        except Exception as e:
            st.error(f"❌ Email failed: {e}")

with col2:
    if st.button("📡 Test NSE Connectivity"):
        ok, msg = test_nse_connectivity()
        if ok:
            st.success(msg)
        else:
            st.error(f"NSE issue: {msg}")

# -------------------
# Live Option Chain Tab
# -------------------
st.sidebar.markdown("## 🟢 Live Option Chain (LOC)")
if st.sidebar.checkbox("Show LOC"):
    symbol = st.sidebar.selectbox("Select Symbol", FNO_SYMBOLS)
    refresh_minutes = st.sidebar.number_input("Refresh interval (minutes)", 1, 30, 5)
    st.info(f"Fetching live option chain for {symbol}... ⏳")

    try:
        df = get_option_chain(symbol)
        if df.empty:
            st.warning("⚠ No data returned from NSE for this symbol")
        else:
            atm = df['strike'].iloc[len(df)//2] if 'strike' in df.columns else None
            st.write(f"ATM strike ~ {atm}")
            st.dataframe(
                df.style.apply(
                    lambda x: ['background-color: yellow' if atm-2 <= s <= atm+2 else '' for s in x['strike']], axis=1
                )
            )
    except Exception as e:
        st.error(f"❌ Error fetching option chain: {e}")

# -------------------
# High-Confidence Alerts
# -------------------
st.subheader("🔥 Latest High-Confidence Alerts")
alerts_df = pd.DataFrame(columns=["Time", "Symbol", "ATM", "Strike", "Side", "Confidence"])

for symbol in FNO_SYMBOLS:
    try:
        df = get_option_chain(symbol)
        alerts = analyze_option_chain(df)
        bias_list = [a["bias"] for a in alerts]
        confidence = confidence_score(bias_list)

        for a in alerts:
            if confidence >= 60 and should_alert(symbol, a["strike"], a["bias"]):
                alert_row = {
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Symbol": symbol,
                    "ATM": a["atm"],
                    "Strike": a["strike"],
                    "Side": a["bias"],
                    "Confidence": confidence
                }
                alerts_df = pd.concat([alerts_df, pd.DataFrame([alert_row])], ignore_index=True)
                send_email(
                    f"High-Confidence Alert: {symbol} {a['bias']}",
                    f"{symbol} {a['bias']} strike {a['strike']} ATM {a['atm']} CONFIDENCE {confidence}%"
                )
    except Exception as e:
        st.error(f"⚠ Error processing {symbol}: {e}")

# Display alert dataframe with color meter for confidence
if not alerts_df.empty:
    def color_confidence(val):
        if val >= 80:
            return 'background-color: green; color:white'
        elif val >= 60:
            return 'background-color: yellow'
        else:
            return ''

    st.dataframe(alerts_df.style.applymap(color_confidence, subset=['Confidence']))
else:
    st.info("✅ No high-confidence alerts currently")
