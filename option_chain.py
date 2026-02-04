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
