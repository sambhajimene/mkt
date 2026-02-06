import json
from kiteconnect import KiteConnect
from config import (
    ZERODHA_API_KEY,
    ZERODHA_API_SECRET,
    ZERODHA_ACCESS_TOKEN,
    ZERODHA_REDIRECT_URI,
)

class ZerodhaClient:
    def __init__(self):
        self.api_key = ZERODHA_API_KEY
        self.api_secret = ZERODHA_API_SECRET
        self.redirect_uri = ZERODHA_REDIRECT_URI

        # Load access token from JSON file if available
        self.access_token = self._load_access_token()

        # Initialize KiteConnect client
        self.kite = KiteConnect(api_key=self.api_key)
        self.kite.set_access_token(self.access_token)
        print("Kite Client ready ✅")

    def _load_access_token(self):
        """
        Read access token from zerodha_token.json or fallback to config
        """
        try:
            with open("zerodha_token.json") as f:
                data = json.load(f)
                token = data.get("access_token")
                if token:
                    print("✅ Access token loaded from zerodha_token.json")
                    return token
        except FileNotFoundError:
            pass

        print("⚠ Using access token from config.py")
        return ZERODHA_ACCESS_TOKEN

    def get_profile(self):
        """
        Returns profile dict if successful
        """
        try:
            profile = self.kite.profile()
            return profile
        except Exception as e:
            print(f"❌ Failed to fetch profile: {e}")
            return None

    def get_quotes(self, symbols):
        """
        Fetch live quotes for list of symbols
        """
        try:
            data = self.kite.ltp(symbols)
            return data
        except Exception as e:
            print(f"❌ Failed to fetch quotes: {e}")
            return None
