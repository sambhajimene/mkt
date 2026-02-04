# dashboard.py
import streamlit as st

def render(rows):
    st.title("SELLER ADVISOR – HIGH CONFIDENCE ONLY")

    for r in rows:
        color = "green" if r["confidence"] >= 80 else "orange"
        st.markdown(
            f"""
            <div style="border-left:6px solid {color};padding:10px;margin:8px;">
            <b>{r['symbol']}</b><br>
            Bias: {r['bias']}<br>
            Confidence: {r['confidence']}%
            </div>
            """,
            unsafe_allow_html=True
        )
