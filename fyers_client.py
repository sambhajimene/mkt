# fyers_client.py
from fyers_apiv3 import FyersModel

class FyersClient:
    def __init__(self, client_id, access_token):
        self.client_id = client_id
        self.access_token = access_token
        self.fyers = FyersModel(client_id=client_id, token=access_token)

    def get_quotes(self, symbols):
        """
        Fetch quotes for list of symbols
        Returns dict with symbol as key and quote data as value
        """
        try:
            response = self.fyers.quotes(symbols)
            return response.get("d", {})  # APIv3 returns data under "d"
        except Exception as e:
            print(f"Fyers API error: {e}")
            return {}
