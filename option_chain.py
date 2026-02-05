# option_chain.py
import pandas as pd
from NSE_client import NSEClient

nse = NSEClient()

# Common NSE index symbols
INDEX_SYMBOLS = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]

def test_nse_connectivity(symbol="NIFTY"):
    """Test NSE connectivity & option chain availability"""
    try:
        df = get_option_chain(symbol)
        if df.empty:
            return False, "Connected but option chain empty"
        return True, f"NSE Connected ✅ | {symbol} | Rows: {len(df)}"
    except Exception as e:
        return False, str(e)


def get_option_chain(symbol):
    """Fetch option chain and return as pandas DataFrame"""
    if symbol in INDEX_SYMBOLS:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    else:
        url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"

    data = nse.get_json(url)

    rows = []
    for row in data["records"].get("data", []):
        ce = row.get("CE")
        pe = row.get("PE")
        if not ce or not pe:
            continue  # skip incomplete strikes

        rows.append({
            "strike": row["strikePrice"],
            "ce_oi": ce.get("openInterest", 0),
            "ce_chg_oi": ce.get("changeinOpenInterest", 0),
            "pe_oi": pe.get("openInterest", 0),
            "pe_chg_oi": pe.get("changeinOpenInterest", 0),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        raise Exception("Option chain returned empty data")
    return df
