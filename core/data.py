"""
Core data fetching — 100% Alpaca, zero yfinance.

T-bill proxy:
  BIL (SPDR Bloomberg 1-3 Month T-Bill ETF) replaces ^IRX.
  BIL tracks the 1-3 month US T-bill yield with an expense ratio of 0.135%/yr —
  a negligibly conservative proxy for the risk-free rate.

VIX:
  ^VIX is a CBOE index not available on Alpaca. fetch_vix() is removed.
  The intraday strategy's VIX filter was also removed (did not improve Sharpe).
"""

import sys
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pandas as pd
from core.alpaca import fetch_bars
from config import DATA_CACHE_DIR


def fetch_prices(tickers: list, start: str, end: str) -> pd.DataFrame:
    """Daily closing prices for a list of ETF/stock tickers from Alpaca."""
    closes = {}
    for ticker in tickers:
        try:
            df = fetch_bars(ticker, start, end, "1Day",
                            cache_dir=DATA_CACHE_DIR, verbose=False)
            if not df.empty:
                closes[ticker] = df["close"]
        except Exception as e:
            print(f"[data] WARNING: could not fetch {ticker} — {e}")

    result  = pd.DataFrame(closes).dropna(how="all")
    missing = [t for t in tickers if t not in result.columns]
    if missing:
        print(f"[data] WARNING: no data for {missing}, dropping them.")
    return result[[t for t in tickers if t in result.columns]]


def fetch_spy(start: str, end: str, initial_capital: float) -> pd.Series:
    """SPY cumulative value series starting at initial_capital (equity benchmark)."""
    df  = fetch_bars("SPY", start, end, "1Day", cache_dir=DATA_CACHE_DIR)
    ret = df["close"].pct_change().fillna(0)
    cumulative      = (1 + ret).cumprod() * initial_capital
    cumulative.name = "SPY"
    return cumulative


def fetch_tbill(start: str, end: str, initial_capital: float) -> tuple:
    """
    Risk-free rate using BIL (SPDR Bloomberg 1-3 Month T-Bill ETF).

    Returns
    -------
    daily_rate : pd.Series — daily return of BIL (≈ daily T-bill rate)
    cumulative : pd.Series — BIL value index starting at initial_capital
    """
    df         = fetch_bars("BIL", start, end, "1Day", cache_dir=DATA_CACHE_DIR)
    daily_rate = df["close"].pct_change().fillna(0)
    daily_rate.name = "BIL"

    cumulative      = (1 + daily_rate).cumprod() * initial_capital
    cumulative.name = "T-bill (BIL)"

    return daily_rate, cumulative
