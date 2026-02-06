#zerodha_token.py
from kiteconnect import KiteConnect
from config import ZERODHA_API_KEY, ZERODHA_API_SECRET, ZERODHA_REDIRECT_URI
import json

def generate_access_token(request_token: str) -> str:
    """
    Exchange Zerodha request_token for an access_token
    """
    kite = KiteConnect(api_key=ZERODHA_API_KEY)
    data = kite.generate_session(request_token, api_secret=ZERODHA_API_SECRET)
    access_token = data.get("access_token")
    if not access_token:
        raise Exception(f"Zerodha token generation failed: {data}")
    return access_token

if __name__ == "__main__":
    request_token = input("Paste request_token from URL: ").strip()
    token = generate_access_token(request_token)
    print("✅ Access token:", token)

    # Optionally save to a JSON file for headless app
    with open("zerodha_token.json", "w") as f:
        json.dump({"access_token": token}, f)
    print("✅ Token saved to zerodha_token.json")

