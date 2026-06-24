"""
Investor Portfolio — capital allocation config.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config import START_DATE, END_DATE, INITIAL_CAPITAL, OUTPUT_DIR, DATA_CACHE_DIR  # noqa: F401

# ── Allocation weights ────────────────────────────────────────
# SIS removed from the live portfolio — it requires 5-min intraday data
# only available from 2020, which would shorten the backtest window by 4 years.
# SIS is retained as a reference strategy.
WEIGHT_GARP = 0.80   # Primary alpha engine
WEIGHT_XAT  = 0.20   # Cross-asset trend — regime diversifier

# ── Cross-asset rotation universe ─────────────────────────────
XAT_TICKERS = {
    "SPY": "SPDR S&P 500 ETF",
    "TLT": "iShares 20+ Year Treasury Bond",
    "GLD": "SPDR Gold Shares",
}
