# fyers_token.py

from fyers_apiv3 import fyersModel
from config import FYERS_CLIENT_ID, FYERS_SECRET_ID, REDIRECT_URI


def generate_access_token(auth_code: str) -> str:
    """
    Converts auth_code → access_token
    """

    session = fyersModel.SessionModel(
        client_id=FYERS_CLIENT_ID,
        secret_key=FYERS_SECRET_ID,
        redirect_uri=REDIRECT_URI,
        response_type="code",
        grant_type="authorization_code"
    )

    session.set_token(auth_code)
    response = session.generate_token()

    if response.get("s") != "ok":
        raise Exception(f"Token generation failed: {response}")

    return response["access_token"]
