from kiteconnect import KiteConnect
from config import ZERODHA_API_KEY, ZERODHA_API_SECRET, ZERODHA_REDIRECT_URI

def generate_access_token(request_token):
    kite = KiteConnect(api_key=ZERODHA_API_KEY)
    data = kite.generate_session(request_token, api_secret=ZERODHA_API_SECRET)
    access_token = data.get("access_token")
    if not access_token:
        raise Exception("Zerodha token generation failed")
    return access_token
