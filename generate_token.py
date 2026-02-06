# generate_token.py
from kiteconnect import KiteConnect
from config import ZERODHA_API_KEY, ZERODHA_API_SECRET

def main():
    print("🔑 Zerodha Access Token Generator\n")
    
    # Step 1: Paste your request_token from URL
    request_token = input("Paste request_token from URL: ").strip()
    if not request_token:
        print("❌ request_token is required!")
        return
    
    try:
        kite = KiteConnect(api_key=ZERODHA_API_KEY)
        data = kite.generate_session(request_token, api_secret=ZERODHA_API_SECRET)
        access_token = data.get("access_token")
        if access_token:
            print("\n✅ Access Token generated successfully!")
            print("Copy this value into config.py -> ZERODHA_ACCESS_TOKEN\n")
            print(f"ACCESS_TOKEN = '{access_token}'\n")
        else:
            print("❌ Failed to get access_token, response:", data)
    except Exception as e:
        print(f"❌ Error generating token: {e}")

if __name__ == "__main__":
    main()
