import os
import json
from kiteconnect import KiteConnect
from config import ZERODHA_API_KEY, ZERODHA_API_SECRET, ZERODHA_REDIRECT_URI

TOKEN_FILE = "zerodha_token.json"

class ZerodhaClient:
    def __init__(self, api_key=ZERODHA_API_KEY, api_secret=ZERODHA_API_SECRET):
        self.api_key = api_key
        self.api_secret = api_secret
        self.kite = KiteConnect(api_key=self.api_key)
        self.access_token = None

        # Load existing token if exists
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                data = json.load(f)
                self.access_token = data.get("access_token")

        if self.access_token:
            self.kite.set_access_token(self.access_token)
        else:
            self.manual_login()

    def manual_login(self):
        """
        Run once: print login URL to generate request token
        """
        login_url = self.kite.login_url()
        print(f"⚡ Login URL: {login_url}")
        print("Open URL, login, copy request_token from redirect URL")

        request_token = input("Paste request_token from URL: ").strip()
        data = self.kite.generate_session(request_token, api_secret=self.api_secret)
        self.access_token = data["access_token"]

        # Save token
        with open(TOKEN_FILE, "w") as f:
            json.dump({"access_token": self.access_token}, f)

        self.kite.set_access_token(self.access_token)

    def get_quotes(self, instruments):
        try:
            return self.kite.quote(instruments)
        except Exception as e:
            print("Kite quote error:", e)
            return None

    def get_profile(self):
        try:
            return self.kite.margins()
        except Exception as e:
            print("Kite profile error:", e)
            return None
