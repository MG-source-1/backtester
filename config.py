"""
Shared configuration — dates, capital, and absolute paths.
All strategies import from here for common parameters.
"""
import os

# Project root (absolute — works regardless of where scripts are run from)
ROOT_DIR       = os.path.dirname(os.path.abspath(__file__))
DATA_CACHE_DIR = os.path.join(ROOT_DIR, "data_cache")
OUTPUT_DIR     = os.path.join(ROOT_DIR, "outputs")

# ── Backtest window ───────────────────────────────────────────
START_DATE      = "2020-01-01"
END_DATE        = "2024-12-31"
INITIAL_CAPITAL = 100_000

# ── Benchmark tickers ─────────────────────────────────────────
TBILL_TICKER = "^IRX"
SPY_TICKER   = "SPY"
VIX_TICKER   = "^VIX"
