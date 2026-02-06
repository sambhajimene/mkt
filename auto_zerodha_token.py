import os
from kiteconnect import KiteConnect
from flask import Flask, request
import webbrowser
import threading
import time
import json

API_KEY = "z9rful06a9890v8m"
API_SECRET = "z96wwv8htnih8n792673jj5trqc4hutm"
REDIRECT_URI = "http://127.0.0.1:5009"
TOKEN_FILE = "access_token.json"

kite = KiteConnect(api_key=API_KEY)
app = Flask(__name__)
access_token_value = None

def save_token(token):
    with open(TOKEN_FILE, "w") as f:
        json.dump({"access_token": token}, f)

def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return json.load(f).get("access_token")
    return None

@app.route("/")
def login_redirect():
    global access_token_value
    request_token = request.args.get("request_token")
    status = request.args.get("status")
    if status == "success" and request_token:
        try:
            data = kite.generate_session(request_token, api_secret=API_SECRET)
            access_token_value = data["access_token"]
            kite.set_access_token(access_token_value)
            save_token(access_token_value)
            return f"Login successful! Access token saved. You can close this window."
        except Exception as e:
            return f"Error generating access token: {e}"
    else:
        return "Login failed or cancelled."

def run_flask():
    app.run(port=5009)

# Step 1: Try loading previous token
access_token_value = load_token()
if access_token_value:
    print("Loaded access token from file.")
    kite.set_access_token(access_token_value)
else:
    print("No valid token found, opening browser to login...")
    threading.Thread(target=run_flask).start()
    time.sleep(1)
    webbrowser.open(kite.login_url())
    while access_token_value is None:
        time.sleep(0.5)

print("Access Token ready:", access_token_value)
