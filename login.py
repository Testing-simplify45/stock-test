"""Run this once every morning. It gets a fresh Fyers access token and saves it in token.txt."""
import os
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel

load_dotenv()
client_id = os.getenv("FYERS_CLIENT_ID")
secret = os.getenv("FYERS_SECRET_KEY")
redirect = os.getenv("FYERS_REDIRECT_URI", "https://trade.fyers.in/api-login/redirect-uri/index.html")

session = fyersModel.SessionModel(
    client_id=client_id, secret_key=secret, redirect_uri=redirect,
    response_type="code", grant_type="authorization_code",
)
print("\n1. Open this link in your browser and log in to Fyers:\n")
print(session.generate_authcode())
print("\n2. After login the browser shows a page (maybe blank/error). Copy the FULL address from the address bar.\n")
url = input("3. Paste that address here and press Enter: ").strip()
code = parse_qs(urlparse(url).query).get("auth_code", [None])[0]
if not code:
    raise SystemExit("Could not find auth_code in that address. Try again.")

session.set_token(code)
resp = session.generate_token()
if "access_token" not in resp:
    raise SystemExit(f"Login failed: {resp}")
with open("token.txt", "w") as f:
    f.write(resp["access_token"])
print("\nDone. token.txt saved. Now run:  streamlit run app.py")
