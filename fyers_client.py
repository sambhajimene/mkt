# fyers_client.py

from fyers_apiv3 import fyersModel
import tempfile
import os


class FyersClient:
    def __init__(self, client_id: str, access_token: str):

        # ✅ writable log path (fixes PermissionError)
        log_dir = tempfile.gettempdir() + "/fyers/"
        os.makedirs(log_dir, exist_ok=True)

        self.fyers = fyersModel.FyersModel(
            client_id=client_id,
            token=f"{client_id}:{access_token}",
            log_path=log_dir
        )

    def get_profile(self):
        return self.fyers.get_profile()

    def get_quotes(self, symbols):
        data = {"symbols": ",".join(symbols)}
        return self.fyers.quotes(data)

    def get_depth(self, symbol):
        data = {"symbol": symbol, "ohlcv_flag": "1"}
        return self.fyers.depth(data)
