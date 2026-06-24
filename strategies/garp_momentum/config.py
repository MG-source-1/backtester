"""
GARP Momentum — strategy parameters.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config import END_DATE, INITIAL_CAPITAL, OUTPUT_DIR, DATA_CACHE_DIR  # noqa: F401

# GARP runs from 2016 — earlier than the combined portfolio's 2020 start.
# EDGAR fundamental data goes back to ~2009 for most large-cap TMT names,
# and Alpaca daily prices go back to ~2016. SIS (the binding constraint for
# the combined portfolio) needs 5-minute intraday bars which only exist from
# 2020, but GARP only needs daily prices so it can run the longer window.
START_DATE = "2016-01-01"

# ── Universe: large-cap TMT / growth stocks ───────────────────
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "META", "NVDA",
    "AMD",  "AVGO", "QCOM",  "ORCL", "CRM",
    "ADBE", "NFLX", "AMZN",  "TSLA", "INTC",
]

# ── Portfolio construction ────────────────────────────────────
TOP_N            = 5       # max simultaneous holdings
MAX_WEIGHT       = 0.30    # max 30% per stock

# ── Signal weights (composite rank = MOM_WEIGHT * mom + GARP_WEIGHT * garp) ─
MOM_WEIGHT       = 0.65
GARP_WEIGHT      = 0.35

# ── Momentum (Jegadeesh-Titman style with 1-month skip) ───────
LOOKBACK_MONTHS  = [3, 6, 12]
SKIP_MONTHS      = 1

# ── Risk management ───────────────────────────────────────────
TARGET_VOL       = 0.20    # 20% annualised portfolio volatility target
MAX_LEVERAGE     = 1.0     # no leverage
VOL_LOOKBACK     = 20      # days for rolling vol estimate
DRAWDOWN_STOP    = 0.15    # 15% drawdown triggers 21-day cash pause
TRANSACTION_COST = 0.001   # 10 bps per side
