"""
Investor Portfolio — capital allocation config.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config import START_DATE, END_DATE, INITIAL_CAPITAL, OUTPUT_DIR, DATA_CACHE_DIR  # noqa: F401

# ── Allocation weights ────────────────────────────────────────
WEIGHT_GARP = 0.70   # Primary alpha engine — TMT quality-momentum
WEIGHT_XAT  = 0.20   # Cross-asset trend — regime diversifier; holds SPY, TLT, or GLD
WEIGHT_SIS  = 0.10   # SPY Intraday Short — market-neutral, ~18% active days

# ── Cross-asset rotation universe ─────────────────────────────
# SPY is included so XAT can participate in equity upside when momentum favours
# equities, while rotating into TLT or GLD for protection during risk-off regimes.
XAT_TICKERS = {
    "SPY": "SPDR S&P 500 ETF",
    "TLT": "iShares 20+ Year Treasury Bond",
    "GLD": "SPDR Gold Shares",
}
