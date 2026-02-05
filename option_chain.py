# option_chain.py
from fyers_client import FyersClient

def get_option_chain(fyers_client, symbol):
    """
    Dynamic option chain fetch for given symbol
    Returns list of dicts: strike, CE {ltp, oi, changeinOI}, PE {ltp, oi, changeinOI}
    """

    # Step 1: Get spot price
    spot_data = fyers_client.get_quotes([f"NSE:{symbol}"])
    if not spot_data or f"NSE:{symbol}" not in spot_data:
        return []

    spot_price = spot_data[f"NSE:{symbol}"].get("lastPrice", 0)
    if not spot_price:
        return []

    # Step 2: Compute ATM and ±5 strikes
    atm_strike = round(spot_price / 50) * 50
    strikes_range = [atm_strike + i*50 for i in range(-5, 6)]

    # Step 3: Generate CE and PE symbols
    ce_symbols = [f"NSE:{symbol}21APR{strike}CE" for strike in strikes_range]
    pe_symbols = [f"NSE:{symbol}21APR{strike}PE" for strike in strikes_range]

    # Step 4: Fetch all quotes
    data = fyers_client.get_quotes(ce_symbols + pe_symbols)
    if not data:
        return []

    # Step 5: Build chain
    chain = []
    for ce_sym, pe_sym, strike in zip(ce_symbols, pe_symbols, strikes_range):
        ce = data.get(ce_sym, {})
        pe = data.get(pe_sym, {})
        chain.append({
            "strike": strike,
            "CE": {
                "ltp": ce.get("lastPrice", 0),
                "oi": ce.get("openInterest", 0),
                "changeinOpenInterest": ce.get("changeInOpenInterest", 0)
            },
            "PE": {
                "ltp": pe.get("lastPrice", 0),
                "oi": pe.get("openInterest", 0),
                "changeinOpenInterest": pe.get("changeInOpenInterest", 0)
            }
        })
    return chain
