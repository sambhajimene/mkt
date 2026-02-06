# fyers_client.py
from fyers_apiv3 import fyersModel

class FyersClient:
    def __init__(self, client_id, access_token):
        self.client_id = client_id
        self.access_token = access_token

        # IMPORTANT: log_path writable hona chahiye
        self.fyers = fyersModel.FyersModel(
            client_id=client_id,
            token=access_token,
            log_path="/tmp/"   # 🔥 permission error fix
        )

    def get_quotes(self, symbols):
        try:
            data = self.fyers.quotes({"symbols": ",".join(symbols)})
            return data
        except Exception as e:
            print("Fyers quote error:", e)
            return None
