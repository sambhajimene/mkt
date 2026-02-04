import requests

class NSEClient:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": "https://www.nseindia.com"
        }
        self._init_session()

    def _init_session(self):
        self.session.get("https://www.nseindia.com", headers=self.headers, timeout=5)

    def get(self, url):
        return self.session.get(url, headers=self.headers, timeout=10).json()
