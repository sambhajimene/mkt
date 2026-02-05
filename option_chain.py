# option_chain.py using nsepython
from nsepython import nse_optionchain_scrapper
import pandas as pd

def get_option_chain(symbol):
    data = nse_optionchain_scrapper(symbol)
    rows = []
    for r in data["records"]["data"]:
        ce = r.get("CE")
        pe = r.get("PE")
        if ce and pe:
            rows.append({
                "strike": r["strikePrice"],
                "ce_oi": ce["openInterest"],
                "ce_chg_oi": ce["changeinOpenInterest"],
                "pe_oi": pe["openInterest"],
                "pe_chg_oi": pe["changeinOpenInterest"]
            })
    return pd.DataFrame(rows)
