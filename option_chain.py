from nse_client import NSEClient

client = NSEClient()

def get_option_chain(symbol, is_index=False):
    if is_index:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    else:
        url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"

    data = client.get(url)
    records = data["records"]
    spot = records["underlyingValue"]

    strikes = records["data"]
    strikes = [s for s in strikes if s.get("CE") and s.get("PE")]

    strikes.sort(key=lambda x: abs(x["strikePrice"] - spot))
    atm_block = strikes[:5]   # ATM ±2

    return spot, atm_block
#===================================================================================================
def test_nse_connectivity():
    """
    Test NSE connectivity + option chain availability
    """
    try:
        session = init_nse_session()

        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        r = session.get(url, headers=HEADERS, timeout=5)

        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"

        data = r.json()

        if "records" not in data:
            return False, "Connected but option chain blocked (no records)"

        rows = len(data["records"].get("data", []))
        return True, f"Connected ✅ | Rows: {rows}"

    except Exception as e:
        return False, str(e)
