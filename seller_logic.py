# seller_logic.py

def analyze_option_chain(df):
    alerts = []

    if df.empty:
        return alerts

    atm_index = len(df) // 2
    atm_strike = df.iloc[atm_index]["strike"]

    for _, r in df.iterrows():
        ce = r["ce_chg_oi"]
        pe = r["pe_chg_oi"]

        if ce > 0 and pe < 0:
            bias = "MARKET DOWN (PUT BUY)"
        elif ce < 0 and pe > 0:
            bias = "MARKET UP (CALL BUY)"
        elif ce > 0 and pe > 0:
            bias = "RANGE / TRAP"
        elif ce < 0 and pe < 0:
            bias = "BREAKOUT / VOLATILITY"
        else:
            continue

        alerts.append({
            "strike": r["strike"],
            "atm": atm_strike,
            "bias": bias
        })

    return alerts
