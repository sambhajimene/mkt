# nse_data.py
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.nseindia.com"
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)
SESSION.get("https://www.nseindia.com")

def get_option_chain(symbol):
    if symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY"]:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    else:
        url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"

    r = SESSION.get(url, timeout=10)
    r.raise_for_status()
    return r.json()
