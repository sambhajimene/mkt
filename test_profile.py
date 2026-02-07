#!/usr/bin/env python3
import os
from kiteconnect import KiteConnect

# ================== CONFIG ==================
API_KEY = os.getenv("API_KEY", "z9rful06a9890v8m")  # API key
ACCESS_TOKEN_FILE = "access_token.txt"

# ================== LOAD ACCESS TOKEN ==================
if not os.path.exists(ACCESS_TOKEN_FILE):
    raise Exception(f"{ACCESS_TOKEN_FILE} not found! Run auto_token.py first.")

with open(ACCESS_TOKEN_FILE, "r") as f:
    ACCESS_TOKEN = f.read().strip()

if not ACCESS_TOKEN:
    raise Exception(f"{ACCESS_TOKEN_FILE} is empty!")

# ================== INIT KITECONNECT ==================
kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

# ================== FETCH PROFILE ==================
try:
    profile = kite.profile()
    print("✅ Profile fetched successfully:\n")
    print(profile)
except Exception as e:
    print("❌ Error fetching profile:", e)

