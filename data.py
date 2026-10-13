"""All the data work: reading Fyers symbol lists, fetching prices, building the table."""
import re
import datetime as dt
import pandas as pd

BASE = "https://public.fyers.in/sym_details/"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def today_ist():
    return dt.datetime.now(IST).date()


def load_master(name):
    """Download one of Fyers' symbol lists (NSE_CM, BSE_CM, NSE_FO, BSE_FO)."""
    return pd.read_csv(BASE + name + ".csv", header=None, dtype=str, on_bad_lines="skip")


def find_col(df, pattern):
    """Find the column whose values look like `pattern` (so we don't depend on column numbers)."""
    for c in df.columns:
        s = df[c].dropna().astype(str).head(300)
        if len(s) and s.str.match(pattern).mean() > 0.9:
            return c
    raise ValueError("Could not find a column matching " + pattern)


def build_equity_map(stocks, nse_cm, bse_cm):
    """stock name -> (NSE symbol, BSE symbol). BSE symbol is matched through the ISIN code."""
    isin_pat = r"^IN[A-Z0-9]{10}$"
    n_t, n_i = find_col(nse_cm, r"^NSE:"), find_col(nse_cm, isin_pat)
    b_t, b_i = find_col(bse_cm, r"^BSE:"), find_col(bse_cm, isin_pat)

    nse_isin = {}
    for tk, isin in zip(nse_cm[n_t], nse_cm[n_i]):
        if isinstance(tk, str) and tk.endswith("-EQ"):
            nse_isin[tk] = isin
    bse_by_isin = {}
    for tk, isin in zip(bse_cm[b_t], bse_cm[b_i]):
        if isinstance(isin, str) and isin not in bse_by_isin:
            bse_by_isin[isin] = tk

    out = {}
    for s in stocks:
        nse_sym = f"NSE:{s}-EQ"
        out[s] = (nse_sym if nse_sym in nse_isin else None,
                  bse_by_isin.get(nse_isin.get(nse_sym)))
    return out


def build_futures_map(fo_df, exch, today):
    """underlying -> (nearest futures symbol, expiry date) for one exchange."""
    t = find_col(fo_df, rf"^{exch}:")
    e = t - 1  # expiry (epoch seconds) sits right before the symbol column
    pat = re.compile(rf"^{exch}:(.+?)\d{{2}}[A-Z]{{3}}FUT$")
    best = {}
    for tk, ex in zip(fo_df[t], fo_df[e]):
        m = pat.match(str(tk))
        if not m:
            continue
        try:
            expiry = dt.datetime.fromtimestamp(int(float(ex)), IST).date()
        except (ValueError, TypeError):
            continue
        if expiry < today:
            continue
        u = m.group(1)
        if u not in best or expiry < best[u][1]:
            best[u] = (tk, expiry)
    return best


def get_quotes(fyers, symbols):
    """Ask Fyers for live prices (max 50 symbols per request)."""
    out = {}
    symbols = [s for s in symbols if s]
    for i in range(0, len(symbols), 50):
        r = fyers.quotes({"symbols": ",".join(symbols[i:i + 50])})
        if r.get("s") != "ok":
            raise RuntimeError(r.get("message", str(r)))
        for item in r.get("d", []):
            v = item.get("v", {})
            if item.get("s") == "ok" and "lp" in v:
                out[item["n"]] = v
    return out


def _diff(a, b):
    return None if a is None or b is None else round(a - b, 2)


def _get(q, sym, key):
    v = q.get(sym) if sym else None
    return None if v is None else v.get(key)


def build_table(stocks, quotes, eq_map, nse_fut, bse_fut, today):
    rows = []
    for s in stocks:
        n_sym, b_sym = eq_map.get(s, (None, None))
        nf, nf_exp = nse_fut.get(s, (None, None))
        bf, bf_exp = bse_fut.get(s, (None, None))

        n_p, b_p = _get(quotes, n_sym, "lp"), _get(quotes, b_sym, "lp")
        n_c, b_c = _get(quotes, n_sym, "ch"), _get(quotes, b_sym, "ch")
        n_cp, b_cp = _get(quotes, n_sym, "chp"), _get(quotes, b_sym, "chp")
        nf_p, bf_p = _get(quotes, nf, "lp"), _get(quotes, bf, "lp")
        nf_c, bf_c = _get(quotes, nf, "ch"), _get(quotes, bf, "ch")
        nf_cp, bf_cp = _get(quotes, nf, "chp"), _get(quotes, bf, "chp")

        rows.append({
            "Stock": s,
            "NSE Price": n_p, "BSE Price": b_p, "Price Diff (NSE-BSE)": _diff(n_p, b_p),
            "NSE Chg": n_c, "NSE Chg %": n_cp,
            "BSE Chg": b_c, "BSE Chg %": b_cp,
            "Chg Diff": _diff(n_c, b_c), "Chg % Diff": _diff(n_cp, b_cp),
            "NSE Fut": nf_p, "BSE Fut": bf_p, "Fut Diff (NSE-BSE)": _diff(nf_p, bf_p),
            "NSE Fut Chg": nf_c, "NSE Fut Chg %": nf_cp,
            "BSE Fut Chg": bf_c, "BSE Fut Chg %": bf_cp,
            "Fut Chg Diff": _diff(nf_c, bf_c), "Fut Chg % Diff": _diff(nf_cp, bf_cp),
            "NSE DTE": (nf_exp - today).days if nf_exp else None,
            "BSE DTE": (bf_exp - today).days if bf_exp else None,
        })
    return pd.DataFrame(rows)
