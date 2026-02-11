# seller_logic.py

# Noise filter for Zerodha OI
OI_THRESHOLD = 500

def analyze_strike(strike):
    ce = strike["CE"]
    pe = strike["PE"]

    ce_change = ce.get("changeinOpenInterest", 0)
    pe_change = pe.get("changeinOpenInterest", 0)

    if ce_change > OI_THRESHOLD and pe_change < -OI_THRESHOLD:
        return "MARKET DOWN (PUT BUY)"

    if ce_change < -OI_THRESHOLD and pe_change > OI_THRESHOLD:
        return "MARKET UP (CALL BUY)"

    if ce_change > OI_THRESHOLD and pe_change > OI_THRESHOLD:
        return "RANGE / TRAP"

    if ce_change < -OI_THRESHOLD and pe_change < -OI_THRESHOLD:
        return "BREAKOUT / VOLATILITY"

    return "NO TRADE"
