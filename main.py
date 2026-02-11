# main.py
import streamlit as st
import pandas as pd
from datetime import datetime

from config import FNO_SYMBOLS, MIN_CONFIDENCE
from zerodha_client import ZerodhaClient
from option_chain import get_option_chain
from seller_logic import analyze_strike
from confidence import confidence_score
from alerts import send_email, should_alert

st.set_page_config(page_title="Seller Advisor", layout="wide")
st.title("📊 Seller Logic – Live Alerts")

client = ZerodhaClient()
symbol = st.selectbox("Select Symbol", FNO_SYMBOLS)

alerts = []

oc = get_option_chain(client, symbol)

if oc:
    df = pd.DataFrame(oc)
    st.dataframe(df, use_container_width=True)

    biases = []

    for strike in oc:
        bias = analyze_strike(strike)
        if bias != "NO TRADE":
            biases.append(bias)

    score = confidence_score(biases)

    # 🔍 LIVE DEBUG (abhi ke liye rakho)
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
                f"{symbol} SELLER ALERT",
                f"""Symbol: {symbol}
Signal: {final_bias}
Confidence: {score}%"""
            )

st.subheader("🔥 Latest Alerts")

if alerts:
    st.dataframe(pd.DataFrame(alerts), use_container_width=True)
else:
    st.info("No high-confidence signal right now")
