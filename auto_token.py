#!/usr/bin/env python3
import os
import webbrowser
from flask import Flask, request
from kiteconnect import KiteConnect
from datetime import datetime

# ================== CONFIG ==================
API_KEY = os.getenv("API_KEY")        # your API key
API_SECRET = os.getenv("API_SECRET")  # your API secret
REDIRECT_URI = "http://127.0.0.1:5010"

ACCESS_TOKEN_FILE = "access_token.txt"

# ================== FLASK APP ==================
app = Flask(__name__)

@app.route("/", methods=["GET"])
def login_redirect():
    # Debug: print all query params
    print("ARGS:", request.args)

    # Kite Connect can send either 'request_token' or 'requestToken'
    req_token = request.args.get("request_token") or request.args.get("requestToken")
    status = request.args.get("status")

    print("Got request_token:", req_token)

    if status == "success" and req_token:
        try:
            kite = KiteConnect(api_key=API_KEY)
            data = kite.generate_session(req_token, api_secret=API_SECRET)

            # Convert datetime objects to string for safety
            safe_data = {}
            for k, v in data.items():
                if isinstance(v, datetime):
                    safe_data[k] = v.isoformat()
                else:
                    safe_data[k] = v

            access_token = safe_data.get("access_token")
            if not access_token:
                raise Exception("No access_token returned")

            # Save locally
            with open(ACCESS_TOKEN_FILE, "w") as f:
                f.write(access_token)

            print(f"\n✅ Access Token ready: {access_token}")
            return f"<h2>Login successful! Access token saved to {ACCESS_TOKEN_FILE}.</h2>"

        except Exception as e:
            print("❌ Error generating token:", e)
            return f"<h2>Error generating token: {e}</h2>"

    return "<h2>Waiting for login...</h2>"

# ================== MAIN ==================
if __name__ == "__main__":
    # If token already exists, use it
    if os.path.exists(ACCESS_TOKEN_FILE):
        with open(ACCESS_TOKEN_FILE) as f:
            token = f.read().strip()
        if token:
            print(f"✅ Existing token found: {token}")
            exit(0)

    # Open login URL
    kite = KiteConnect(api_key=API_KEY)
    login_url = kite.login_url()
    print("🔐 Login URL (OPEN THIS IN BROWSER):\n")
    print(login_url)
    webbrowser.open(login_url)

    # Start Flask server to capture redirect
    print("\n* Starting local server at http://127.0.0.1:5009")
    print("After login, the page will show Access Token automatically.\n")
    app.run(port=5009)
