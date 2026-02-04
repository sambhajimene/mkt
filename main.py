import streamlit as st
from datetime import datetime
import pytz

from config import *
from option_chain import get_option_chain
from seller_logic import analyze_strike
from confidence import confidence_score
from alerts import send_email, should_alert

tz = pytz.timezone(TIMEZONE)

st.set_page_config(layout="wide")
st.title("📊 NSE Seller Advisor – High Confidence Only")
#============================test button=================================
if st.button("📧 Test Mail"):
    try:
        send_email(
            "TEST EMAIL – Seller Advisor",
            "Email system working ✅"
        )
        st.success("✅ Test mail sent successfully")
    except Exception as e:
        st.error(f"❌ Mail failed: {e}")
#===========================================================================

symbols = INDEX_SYMBOLS + FNO_STOCKS
table = []

for sym in symbols:
    try:
        spot, strikes = get_option_chain(sym, sym in INDEX_SYMBOLS)
        biases = []
        for s in strikes:
            biases.append(analyze_strike(s))

        final_bias, score = confidence_score(biases)

        if score >= MIN_CONFIDENCE:
            atm = strikes[0]["strikePrice"]

            if should_alert(sym, final_bias, atm):
                send_email(
                    f"{sym} | {final_bias} | {score}%",
                    f"{sym}\nSpot: {spot}\nATM: {atm}\nBias: {final_bias}\nConfidence: {score}%"
                )

            table.append([
                sym, spot, atm, final_bias, f"{score}%"
            ])
    except Exception as e:
        continue

st.subheader("🔥 HIGH CONFIDENCE SIGNALS")
st.table(table)

st.caption(f"Last refresh: {datetime.now(tz).strftime('%H:%M:%S')}")
