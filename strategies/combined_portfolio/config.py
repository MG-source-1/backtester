"""
Investor Portfolio — capital allocation config.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config import START_DATE, END_DATE, INITIAL_CAPITAL, OUTPUT_DIR, DATA_CACHE_DIR  # noqa: F401

# ── Allocation weights ────────────────────────────────────────
WEIGHT_GARP = 0.45   # GARP Momentum              (individual stock alpha)
WEIGHT_XAT  = 0.45   # Cross-Asset Trend          (SPY · TLT · GLD — bonds/gold ballast)
WEIGHT_SIS  = 0.10   # SPY Intraday Short         (market-neutral alpha; active ~18% of days)

# ── Cross-asset universe ──────────────────────────────────────
XAT_TICKERS = {
    "SPY": "SPDR S&P 500 ETF",
    "TLT": "iShares 20+ Year Treasury Bond",
    "GLD": "SPDR Gold Shares",
}
