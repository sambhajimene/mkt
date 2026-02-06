# fyers_token.py
from fyers_apiv3.session import SessionModel

def generate_access_token(auth_code):
    CLIENT_ID = "UEYCB0VJMM-100"
    SECRET_KEY = "FNC70J694G"
    REDIRECT_URI = "https://mk-menesambhaji-dev.apps.rm1.0a51.p1.openshiftapps.com/"

    session = SessionModel(
        client_id=CLIENT_ID,
        secret_key=SECRET_KEY,
        redirect_uri=REDIRECT_URI,
        response_type="code",
        grant_type="authorization_code"
    )

    session.set_token(auth_code)
    response = session.generate_token()

    if response.get("s") != "ok":
        raise Exception(f"Token generation failed: {response}")

    return response["access_token"]
