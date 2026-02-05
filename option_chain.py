# option_chain.py
import pandas as pd
from NSE_client import NSEClient

nse = NSEClient()

INDEX_SYMBOLS = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]

def test_nse_connectivity(symbol="NIFTY"):
    try:
        _ = get_option_chain(symbol)
        return True, f"NSE Connected ✅ | {symbol}"
    except Exception as e:
        return False, str(e)


def get_option_chain(symbol):
    if symbol in INDEX_SYMBOLS:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    else:
        url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"

    data = nse.get_json(url)

    if "records" not in data or "data" not in data["records"]:
        raise Exception("Option chain blocked (records missing)")

    rows = []
    for row in data["records"]["data"]:
        if "CE" in row and "PE" in row:
            rows.append({
                "strike": row["strikePrice"],
                "ce_oi": row["CE"]["openInterest"],
                "ce_chg_oi": row["CE"]["changeinOpenInterest"],
                "pe_oi": row["PE"]["openInterest"],
                "pe_chg_oi": row["PE"]["changeinOpenInterest"],
            })

    return pd.DataFrame(rows)
