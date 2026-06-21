"""
Multi-Asset Trend Following — strategy-specific parameters.
Shared params (dates, capital, paths) come from the root config.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config import START_DATE, END_DATE, INITIAL_CAPITAL, OUTPUT_DIR  # noqa: F401

TICKERS = {
    "SPY":  "SPDR S&P 500 ETF (US Large Cap Equities)",
    "EFA":  "iShares MSCI EAFE ETF (International Developed)",
    "TLT":  "iShares 20+ Year Treasury Bond (Long Duration)",
    "IEF":  "iShares 7-10 Year Treasury Bond (Medium Duration)",
    "GLD":  "SPDR Gold Shares (Inflation Hedge / Safe Haven)",
    "DBC":  "Invesco DB Commodity Index (Broad Commodities)",
    "VNQ":  "Vanguard Real Estate ETF (US REITs)",
}

LOOKBACK_MONTHS  = [1, 3, 6, 12]
TARGET_VOL       = 0.10
MAX_WEIGHT       = 0.40
MAX_LEVERAGE     = 1.5
VOL_LOOKBACK     = 20
DRAWDOWN_STOP    = 0.08
TRANSACTION_COST = 0.001
