from kiteconnect import KiteConnect
from config import (
    ZERODHA_API_KEY,
    ZERODHA_API_SECRET,
    ZERODHA_REDIRECT_URI,
    ZERODHA_ACCESS_TOKEN
)
import json
import os

class ZerodhaClient:
    def __init__(self):
        self.api_key = ZERODHA_API_KEY
        self.api_secret = ZERODHA_API_SECRET
        self.redirect_uri = ZERODHA_REDIRECT_URI
        self.access_token = ZERODHA_ACCESS_TOKEN
        self.token_file = "zerodha_token.json"

        self.kite = KiteConnect(api_key=self.api_key)

        # Headless: Use access token from config or saved file
        if self.access_token:
            self.kite.set_access_token(self.access_token)
        elif os.path.exists(self.token_file):
            with open(self.token_file, "r") as f:
                data = json.load(f)
                self.access_token = data.get("access_token")
                self.kite.set_access_token(self.access_token)
        else:
            raise Exception(
                "No Zerodha access token provided. "
                "Please generate manually and set ZERODHA_ACCESS_TOKEN in config.py"
            )

    def get_profile(self):
        """Fetch user profile to test connectivity"""
        try:
            return self.kite.profile()
        except Exception as e:
            print("Zerodha profile error:", e)
            return None

    def get_quotes(self, symbols):
        """Fetch live quotes"""
        try:
            data = self.kite.quote(symbols)
            return data
        except Exception as e:
            print("Zerodha quote error:", e)
            return None
