from zerodha_client import ZerodhaClient

def get_option_chain(client: ZerodhaClient, symbol):
    quote = client.get_quotes([f"NSE:{symbol}"])
    if not quote or f"NSE:{symbol}" not in quote:
        return []

    spot_price = quote[f"NSE:{symbol}"].get("last_price", 0)
    if not spot_price:
        return []

    atm_strike = round(spot_price / 50) * 50
    strikes_range = [atm_strike + i*50 for i in range(-5, 6)]

    ce_symbols = [f"NSE:{symbol}{strike}CE" for strike in strikes_range]
    pe_symbols = [f"NSE:{symbol}{strike}PE" for strike in strikes_range]

    data = client.get_quotes(ce_symbols + pe_symbols)
    if not data:
        return []

    chain = []
    for ce_sym, pe_sym, strike in zip(ce_symbols, pe_symbols, strikes_range):
        ce = data.get(ce_sym, {})
        pe = data.get(pe_sym, {})
        chain.append({
            "strike": strike,
            "CE": {
                "ltp": ce.get("last_price", 0),
                "oi": ce.get("open_interest", 0),
                "changeinOpenInterest": ce.get("change_in_oi", 0)
            },
            "PE": {
                "ltp": pe.get("last_price", 0),
                "oi": pe.get("open_interest", 0),
                "changeinOpenInterest": pe.get("change_in_oi", 0)
            }
        })
    return chain
