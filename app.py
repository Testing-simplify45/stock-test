import os
import streamlit as st
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel
import data

load_dotenv()
st.set_page_config(page_title="NSE vs BSE", layout="wide")
st.title("NSE vs BSE - Live Price Comparison")

CLIENT_ID = os.getenv("FYERS_CLIENT_ID", "")
TOKEN = ""
if os.path.exists("token.txt"):
    TOKEN = open("token.txt").read().strip()
if not CLIENT_ID or not TOKEN:
    st.error("Not logged in yet. Run login.py first (see README).")
    st.stop()

with open("stocks.txt") as f:
    STOCKS = [x.strip().upper() for x in f if x.strip() and not x.startswith("#")]


@st.cache_data(ttl=6 * 3600, show_spinner="Loading Fyers symbol lists...")
def load_symbols(stocks, day):
    eq = data.build_equity_map(list(stocks), data.load_master("NSE_CM"), data.load_master("BSE_CM"))
    nse_fut = data.build_futures_map(data.load_master("NSE_FO"), "NSE", day)
    bse_fut = data.build_futures_map(data.load_master("BSE_FO"), "BSE", day)
    return eq, nse_fut, bse_fut


today = data.today_ist()
eq_map, nse_fut, bse_fut = load_symbols(tuple(STOCKS), today)
fyers = fyersModel.FyersModel(client_id=CLIENT_ID, token=TOKEN, is_async=False, log_path="")

refresh = st.sidebar.number_input("Refresh every (seconds)", min_value=2, max_value=60, value=5)


@st.fragment(run_every=refresh)
def live_table():
    symbols = []
    for s in STOCKS:
        symbols += list(eq_map[s])
        symbols += [nse_fut.get(s, (None,))[0], bse_fut.get(s, (None,))[0]]
    try:
        quotes = data.get_quotes(fyers, symbols)
    except Exception as e:
        st.error(f"Fyers error: {e}. If it says token/expired, run login.py again (needed once every day).")
        return
    df = data.build_table(STOCKS, quotes, eq_map, nse_fut, bse_fut, today)
    st.dataframe(df, use_container_width=True, hide_index=True, height=600)
    st.caption("Last updated: " + data.dt.datetime.now(data.IST).strftime("%H:%M:%S"))


live_table()
