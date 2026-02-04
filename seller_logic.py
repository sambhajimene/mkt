# # seller_logic.py

# def classify_strike(prev_oi, curr_oi):
#     if curr_oi > prev_oi:
#         return "WRITING"
#     elif curr_oi < prev_oi:
#         return "UNWINDING"
#     else:
#         return "NEUTRAL"


# def seller_bias(call_status, put_status):
#     if call_status == "WRITING" and put_status == "UNWINDING":
#         return "MARKET DOWN (PUT BUY)"
#     if call_status == "UNWINDING" and put_status == "WRITING":
#         return "MARKET UP (CALL BUY)"
#     if call_status == "WRITING" and put_status == "WRITING":
#         return "RANGE / TRAP"
#     if call_status == "UNWINDING" and put_status == "UNWINDING":
#         return "BREAKOUT / VOLATILITY"
#     return "NO TRADE"
######===========================================
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
