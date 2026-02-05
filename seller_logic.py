# seller_logic.py
def analyze_strike(strike):
    ce = strike["CE"]
    pe = strike["PE"]

    ce_change = ce["changeinOpenInterest"]
    pe_change = pe["changeinOpenInterest"]

    if ce_change > 0 and pe_change < 0:
        return "MARKET DOWN (PUT BUY)"
    if ce_change < 0 and pe_change > 0:
        return "MARKET UP (CALL BUY)"
    if ce_change > 0 and pe_change > 0:
        return "RANGE / TRAP"
    if ce_change < 0 and pe_change < 0:
        return "BREAKOUT / VOLATILITY"

    return "NO TRADE"
