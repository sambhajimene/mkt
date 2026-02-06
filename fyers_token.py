from fyers_apiv3 import SessionModel

CLIENT_ID = "UEYCB0VJMM-100"
SECRET_KEY = "FNC70J694G"
REDIRECT_URI = "https://mk-menesambhaji-dev.apps.rm1.0a51.p1.openshiftapps.com/"

# 🔴 YAHAN CHANGE KARNA HAI
AUTH_CODE = "PASTE_AUTH_CODE_HERE"

session = SessionModel(
    client_id=CLIENT_ID,
    secret_key=SECRET_KEY,
    redirect_uri=REDIRECT_URI,
    response_type="code",
    grant_type="authorization_code"
)

session.set_token(AUTH_CODE)
response = session.generate_token()

print("TOKEN RESPONSE 👉", response)
