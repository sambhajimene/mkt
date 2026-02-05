# NSE_client.py
import requests
import time

class NSEClient:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com",
            "Connection": "keep-alive",
        }
        self._init_session()

    def _init_session(self):
        """Initial request to get cookies"""
        try:
            self.session.get("https://www.nseindia.com", headers=self.headers, timeout=5)
        except Exception as e:
            raise Exception(f"NSE session init failed: {e}")

    def get_json(self, url, retries=3, sleep_sec=2):
        """GET JSON with retries and NSE-safe headers"""
        for attempt in range(1, retries+1):
            try:
                r = self.session.get(url, headers=self.headers, timeout=10)
                if r.status_code != 200:
                    raise Exception(f"NSE HTTP {r.status_code}")

                data = r.json()
                if "records" not in data:
                    raise Exception("Option chain blocked (records missing)")
                return data

            except Exception as e:
                if attempt < retries:
                    time.sleep(sleep_sec)
                else:
                    raise Exception(f"NSE GET failed after {retries} attempts: {e}")
