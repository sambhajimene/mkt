# NSE_client.py
import requests

class NSEClient:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/",
            "Connection": "keep-alive",
        }
        self._init_session()

    def _init_session(self):
        self.session.get(
            "https://www.nseindia.com",
            headers=self.headers,
            timeout=5
        )

    def get_json(self, url):
        r = self.session.get(url, headers=self.headers, timeout=10)
        if r.status_code != 200:
            raise Exception(f"NSE HTTP {r.status_code}")
        try:
            return r.json()
        except Exception:
            raise Exception("NSE returned non-JSON (blocked)")
