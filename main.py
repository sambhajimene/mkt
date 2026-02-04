# main.py
from datetime import datetime
import streamlit as st
from config import *
from nse_data import get_option_chain
from seller_logic import classify_strike, seller_bias
from confidence import confidence_score
from alert_manager import can_alert, send_mail
from dashboard import render
import pytz

def market_open():
    now = datetime.now(TIMEZONE).time()
    return MARKET_OPEN <= now <= MARKET_CLOSE


results = []

if market_open():
    for symbol in ALL_SYMBOLS:
        try:
            data = get_option_chain(symbol)
            records = data["records"]["data"]

            strikes = records[len(records)//2 - 2 : len(records)//2 + 3]
            bias_list = []

            for s in strikes:
                ce = s.get("CE")
                pe = s.get("PE")
                if not ce or not pe:
                    continue

                call = classify_strike(
                    ce["previousOpenInterest"], ce["openInterest"]
                )
                put = classify_strike(
                    pe["previousOpenInterest"], pe["openInterest"]
                )

                bias_list.append(seller_bias(call, put))

            dominant, score = confidence_score(bias_list)

            threshold = INDEX_CONFIDENCE if symbol in INDEX_SYMBOLS else STOCK_CONFIDENCE
            if score >= threshold:
                results.append({
                    "symbol": symbol,
                    "bias": dominant,
                    "confidence": score
                })

                if can_alert(symbol, "ATM", dominant):
                    send_mail(
                        f"HIGH CONFIDENCE – {dominant}",
                        f"{symbol}\nConfidence: {score}%"
                    )

        except Exception:
            pass

render(results)
