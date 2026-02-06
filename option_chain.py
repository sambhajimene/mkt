from zerodha_client import ZerodhaClient
from datetime import datetime, timedelta
import math
import calendar

def get_nearest_expiry(symbol: str):
    """
    Returns the nearest expiry date string in Zerodha format: DDMMM (e.g., 13FEB)
    - For NIFTY/BANKNIFTY: nearest Thursday (weekly expiry)
    - For stocks: nearest monthly expiry (last Thursday of month)
    """
    today = datetime.today()
    
    if symbol in ["NIFTY", "BANKNIFTY"]:
        # Weekly expiry: nearest Thursday
        offset = (3 - today.weekday()) % 7  # Thursday = weekday 3
        if offset == 0 and today.hour >= 15:  # if today is Thursday after market
            offset = 7
        expiry = today + timedelta(days=offset)
    else:
        # Stock monthly expiry: last Thursday of current or next month
        year = today.year
        month = today.month
        last_day = calendar.monthrange(year, month)[1]
        last_thursday = max([day for day in range(1, last_day+1)
                             if datetime(year, month, day).weekday() == 3])
        expiry = datetime(year, month, last_thursday)
        if expiry < today:  # move to next month if already passed
            month += 1
            if month > 12:
                month = 1
                year += 1
            last_day = calendar.monthrange(year, month)[1]
            last_thursday = max([day for day in range(1, last_day+1)
                                 if datetime(year, month, day).weekday() == 3])
            expiry = datetime(year, month, last_thursday)

    return expiry.strftime("%d%b").upper()  # e.g., 13FEB

def get_option_chain(client: ZerodhaClient, symbol: str):
    """
    Fetch dynamic option chain for a given symbol using Zerodha.
    Returns a list of dicts with strike, CE, PE data
    """
    # Step 1: Get spot price
    spot_data = client.get_quotes([f"NSE:{symbol}"])
    if not spot_data or f"NSE:{symbol}" not in spot_data:
        return []

    spot_price = spot_data[f"NSE:{symbol}"].get("last_price", 0)
    if not spot_price:
        return []

    # Step 2: Compute ATM ±5 strikes (round to nearest 50)
    atm_strike = round(spot_price / 50) * 50
    strikes_range = [atm_strike + i*50 for i in range(-5, 6)]

    # Step 3: Get nearest expiry string
    expiry_str = get_nearest_expiry(symbol)

    # Step 4: Generate CE/PE symbols dynamically
    ce_symbols = [f"NSE:{symbol}{expiry_str}{strike}CE" for strike in strikes_range]
    pe_symbols = [f"NSE:{symbol}{expiry_str}{strike}PE" for strike in strikes_range]

    # Step 5: Fetch all quotes
    all_symbols = ce_symbols + pe_symbols
    data = client.get_quotes(all_symbols)
    if not data:
        return []

    # Step 6: Build option chain
    chain = []
    for ce_sym, pe_sym, strike in zip(ce_symbols, pe_symbols, strikes_range):
        ce = data.get(ce_sym, {})
        pe = data.get(pe_sym, {})
        chain.append({
            "strike": strike,
            "CE": {
                "ltp": ce.get("last_price", 0),
                "oi": ce.get("oi", 0),
                "changeinOpenInterest": ce.get("change_in_oi", 0)
            },
            "PE": {
                "ltp": pe.get("last_price", 0),
                "oi": pe.get("oi", 0),
                "changeinOpenInterest": pe.get("change_in_oi", 0)
            }
        })

    return chain
