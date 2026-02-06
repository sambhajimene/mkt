# fyers_client.py
from fyers_apiv3 import fyersModel

class FyersClient:
    def __init__(self, client_id, access_token):
        self.fyers = fyersModel.FyersModel(
            client_id=client_id,
            token=access_token,
            log_path=""
        )

    def get_quotes(self, symbols):
        """
        symbols: ["NSE:RELIANCE-EQ"]
        """
        try:
            response = self.fyers.quotes({
                "symbols": ",".join(symbols)
            })
            return response.get("d", {})
        except Exception as e:
            print("Fyers API error:", e)
            return {}
