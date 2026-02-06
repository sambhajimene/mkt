# fyers_client.py

from fyers_apiv3 import fyersModel
import tempfile
import os


class FyersClient:
    def __init__(self, client_id: str, access_token: str):
        """
        access_token format:
        APP_ID:ACCESS_TOKEN
        """

        # ✅ writable log path (important for Docker/OpenShift)
        log_path = tempfile.gettempdir() + "/fyers/"
        os.makedirs(log_path, exist_ok=True)

        self.fyers = fyersModel.FyersModel(
            client_id=client_id,
            token=access_token,
            log_path=log_path
        )

    def get_profile(self):
        return self.fyers.get_profile()

    def get_quotes(self, symbols):
        data = {"symbols": ",".join(symbols)}
        return self.fyers.quotes(data)

    def get_market_depth(self, symbol):
        data = {"symbol": symbol, "ohlcv_flag": "1"}
        return self.fyers.depth(data)
