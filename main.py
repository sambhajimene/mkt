# import streamlit as st
# from datetime import datetime
# import pytz

# from config import *
# from option_chain import get_option_chain
# from seller_logic import analyze_strike
# from confidence import confidence_score
# from alerts import send_email, should_alert

# tz = pytz.timezone(TIMEZONE)

# st.set_page_config(layout="wide")
# st.title("High Confidence Only")
# #============================test button=================================
# if st.button("📧 Test Mail"):
#     try:
#         send_email(
#             "TEST EMAIL ",
#             "Email system working ✅"
#         )
#         st.success("✅ Test mail sent successfully")
#     except Exception as e:
#         st.error(f"❌ Mail failed: {e}")
# #===========================================================================
# # -------------------
# # Live Option Chain Tab
# # -------------------
# st.sidebar.markdown("## 🟢 Live Option Chain")
# if st.sidebar.checkbox("Show Live Option Chain"):
#     symbol = st.sidebar.selectbox("Select Symbol", FNO_SYMBOLS)
#     refresh_minutes = st.sidebar.number_input("Refresh interval (minutes)", 1, 30, 5)
#     st.info(f"Fetching live option chain for {symbol}... ⏳")

#     try:
#         df = get_option_chain(symbol)
#         if df.empty:
#             st.warning("⚠ No data returned from NSE for this symbol")
#         else:
#             # Highlight ATM ±2 strikes
#             atm = df['strike'].iloc[len(df)//2] if 'strike' in df.columns else None
#             st.write(f"ATM strike ~ {atm}")
#             st.dataframe(
#                 df.style.apply(
#                     lambda x: ['background-color: yellow' if atm-2 <= s <= atm+2 else '' for s in x['strike']], axis=1
#                 )
#             )
#     except Exception as e:
#         st.error(f"❌ Error fetching option chain: {e}")
# #===========================================================================

# symbols = INDEX_SYMBOLS + FNO_SYMBOLS
# table = []

# for sym in symbols:
#     try:
#         spot, strikes = get_option_chain(sym, sym in INDEX_SYMBOLS)
#         biases = []
#         for s in strikes:
#             biases.append(analyze_strike(s))

#         final_bias, score = confidence_score(biases)

#         if score >= MIN_CONFIDENCE:
#             atm = strikes[0]["strikePrice"]

#             if should_alert(sym, final_bias, atm):
#                 send_email(
#                     f"{sym} | {final_bias} | {score}%",
#                     f"{sym}\nSpot: {spot}\nATM: {atm}\nBias: {final_bias}\nConfidence: {score}%"
#                 )

#             table.append([
#                 sym, spot, atm, final_bias, f"{score}%"
#             ])
#     except Exception as e:
#         continue

# st.subheader("🔥 HIGH CONFIDENCE SIGNALS")
# st.table(table)

# st.caption(f"Last refresh: {datetime.now(tz).strftime('%H:%M:%S')}")
########################################################################

# ########################################################################
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from config import FNO_SYMBOLS, TIMEZONE
from alerts import send_email, should_alert
from option_chain import test_nse_connectivity
from option_chain import get_option_chain
#from seller_logic import evaluate_seller
from seller_logic import analyze_strike
#from confidence import compute_confidence
from confidence import confidence_score

# -------------------
# Streamlit Page Setup
# -------------------
st.set_page_config(page_title=" Dashboard", layout="wide")
st.title("🚀 Dashboard (High-Confidence Alerts)")

# -------------------
# Mail Test Button
# -------------------
# if st.sidebar.button("📧 Test Email"):
#     try:
#         send_email("TEST EMAIL", "Email system working ✅")
#         st.success("✅ Test Email sent successfully")
#     except Exception as e:
#         st.error(f"❌ Email failed: {e}")
#--------------------------
# NSE connectivity Button
#--------------------------
st.subheader("🔌 System Health Checks")

col1, col2 = st.columns(2)

with col1:
    if st.button("📧 Test Email"):
        send_email("TEST EMAIL", "Email system working ✅")
        st.success("Email sent successfully")

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
st.sidebar.markdown("## 🟢 LOC")
if st.sidebar.checkbox("Show LOC"):
    symbol = st.sidebar.selectbox("Select Symbol", FNO_SYMBOLS)
    refresh_minutes = st.sidebar.number_input("Refresh interval (minutes)", 1, 30, 5)
    st.info(f"Fetching live option chain for {symbol}... ⏳")

    try:
        df = get_option_chain(symbol)
        if df.empty:
            st.warning("⚠ No data returned from NSE for this symbol")
        else:
            # Highlight ATM ±2 strikes
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
        oc = get_option_chain(symbol)
        if oc.empty:
            continue

        # Evaluate seller logic per strike
        alerts = analyze_strike(symbol, oc)
        
        for alert in alerts:
            side = alert['side']
            strike = alert['strike']
            atm = alert['atm']
            
            confidence = confidence_score(symbol, strike, side, oc)
            alert_row = {
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Symbol": symbol,
                "ATM": atm,
                "Strike": strike,
                "Side": side,
                "Confidence": confidence
            }

            # Only display + send mail if HIGH confidence & not repeated
            if confidence >= 3 and should_alert(symbol, strike, side):
                alerts_df = pd.concat([alerts_df, pd.DataFrame([alert_row])], ignore_index=True)
                send_email(
                    f"High-Confidence Alert: {symbol} {side}",
                    f"{symbol} {side} strike {strike} ATM {atm} CONFIDENCE {confidence}"
                )
    except Exception as e:
        st.error(f"⚠ Error processing {symbol}: {e}")

# Display alert dataframe with color meter for confidence
if not alerts_df.empty:
    def color_confidence(val):
        if val >= 4:
            return 'background-color: green; color:white'
        elif val == 3:
            return 'background-color: yellow'
        else:
            return ''
    
    st.dataframe(alerts_df.style.applymap(color_confidence, subset=['Confidence']))
else:
    st.info("✅ No high-confidence alerts currently")
