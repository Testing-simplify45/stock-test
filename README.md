# NSE vs BSE Live Comparison (Fyers)

Shows live NSE and BSE prices side by side for the stocks in `stocks.txt`: spot price, change, % change, futures price, futures change, differences, and days to expiry (DTE).

## One-time setup
1. Create an app at https://myapi.fyers.in (you get an App ID and a Secret). Set the Redirect URL to `https://trade.fyers.in/api-login/redirect-uri/index.html`.
2. Copy `.env.example` to a new file named `.env` and fill in your App ID and Secret.
3. Open a terminal in this folder and run: `pip install -r requirements.txt`

## Every day
1. `python login.py`  (follow the 3 steps it prints; Fyers needs a fresh login daily)
2. `streamlit run app.py`

## Change stocks
Edit `stocks.txt`, one NSE symbol per line.

## Notes
- Difference = NSE minus BSE.
- Futures are the nearest expiry on each exchange. A blank means that stock has no futures on that exchange.
- Never upload `.env` or `token.txt` to GitHub (the `.gitignore` already blocks them).
