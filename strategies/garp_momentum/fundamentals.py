"""
GARP fundamental scoring via yfinance.

Fetches a current snapshot of six metrics per stock and collapses them into
a single composite GARP score (0–1, higher = better quality/value).

Metrics used
────────────
  PEG ratio   (30%) — price-to-earnings ÷ EPS growth; <1 is ideal
  ROE         (20%) — return on equity; measures profitability quality
  EV/EBITDA   (15%) — enterprise value efficiency; lower = cheaper
  FCF yield   (15%) — free cash flow / market cap; cash generation strength
  Net margin  (10%) — earnings quality / pricing power
  Debt/Equity (10%) — financial health; lower leverage = safer

Look-ahead note
───────────────
Scores are fetched at runtime (today) and treated as a static quality screen.
The actual buy/sell timing in the backtest is driven by price momentum only.
Quality rankings of large-cap tech have been relatively stable over 2016-2024,
so using a current snapshot as a persistent screen is a reasonable compromise
when historical fundamental time-series data is unavailable.
"""

import numpy as np
import pandas as pd

try:
    import yfinance as yf
    _YF_OK = True
except ImportError:
    _YF_OK = False


METRIC_WEIGHTS = {
    "peg":      0.30,
    "roe":      0.20,
    "evebitda": 0.15,
    "fcf":      0.15,
    "margin":   0.10,
    "debt":     0.10,
}


# ── Individual metric scorers (all return 0–1) ────────────────

def _peg_score(v) -> float:
    """PEG < 1 = excellent growth value.  PEG > 3 = expensive."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.30
    if v <= 0:
        return 0.10   # negative earnings / growth = poor
    return max(0.0, 1.0 - min(v, 3.0) / 3.0)


def _roe_score(v) -> float:
    """ROE as decimal (0.30 = 30%).  Cap benefit at 50%."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.30
    if v < 0:
        return 0.10
    return min(v, 0.50) / 0.50


def _evebitda_score(v) -> float:
    """EV/EBITDA.  < 15 = cheap for tech; > 50 = very expensive."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.30
    if v <= 0:
        return 0.30
    return max(0.0, 1.0 - min(v, 50.0) / 50.0)


def _fcf_score(v) -> float:
    """FCF yield as decimal (0.05 = 5%).  Cap benefit at 10%."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.30
    if v < 0:
        return 0.10
    return min(v, 0.10) / 0.10


def _margin_score(v) -> float:
    """Net profit margin as decimal.  Cap benefit at 40%."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.30
    if v < 0:
        return 0.10
    return min(v, 0.40) / 0.40


def _debt_score(v) -> float:
    """D/E ratio (not percent).  0 = no debt; > 3 = highly levered."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.50   # neutral when unknown
    if v < 0:
        return 0.50
    return max(0.0, 1.0 - min(v, 3.0) / 3.0)


# ── Main fetcher ──────────────────────────────────────────────

def fetch_garp_scores(tickers: list) -> pd.DataFrame:
    """
    Return a DataFrame indexed by ticker with raw metrics + composite GARP score.
    Falls back to neutral scores (0.30) when yfinance is unavailable or a field
    is missing for a specific stock.
    """
    if not _YF_OK:
        print("[fundamentals] WARNING: yfinance not installed — using neutral scores.")
        return pd.DataFrame({"garp_score": 0.30}, index=tickers)

    rows = []
    for tkr in tickers:
        try:
            info = yf.Ticker(tkr).info

            peg     = info.get("pegRatio")
            roe     = info.get("returnOnEquity")
            ebitda  = info.get("ebitda")
            ev      = info.get("enterpriseValue")
            fcf     = info.get("freeCashflow")
            mktcap  = info.get("marketCap") or 1
            margin  = info.get("profitMargins")
            de_pct  = info.get("debtToEquity")   # yfinance returns as percent (150 = 150%)

            evebitda  = (ev / ebitda) if (ev and ebitda and ebitda > 0) else None
            fcf_yield = (fcf / mktcap) if (fcf is not None and mktcap > 0) else None
            de_ratio  = (de_pct / 100.0) if de_pct is not None else None

            peg_s    = _peg_score(peg)
            roe_s    = _roe_score(roe)
            ev_s     = _evebitda_score(evebitda)
            fcf_s    = _fcf_score(fcf_yield)
            margin_s = _margin_score(margin)
            debt_s   = _debt_score(de_ratio)

            composite = (
                METRIC_WEIGHTS["peg"]      * peg_s    +
                METRIC_WEIGHTS["roe"]      * roe_s    +
                METRIC_WEIGHTS["evebitda"] * ev_s     +
                METRIC_WEIGHTS["fcf"]      * fcf_s    +
                METRIC_WEIGHTS["margin"]   * margin_s +
                METRIC_WEIGHTS["debt"]     * debt_s
            )

            rows.append({
                "ticker":       tkr,
                "peg":          round(peg, 2)          if peg      is not None else None,
                "roe_pct":      round(roe * 100, 1)    if roe      is not None else None,
                "ev_ebitda":    round(evebitda, 1)     if evebitda is not None else None,
                "fcf_yield_pct":round(fcf_yield * 100, 2) if fcf_yield is not None else None,
                "net_margin_pct":round(margin * 100, 1) if margin  is not None else None,
                "debt_equity":  round(de_ratio, 2)     if de_ratio is not None else None,
                "peg_score":    round(peg_s, 3),
                "roe_score":    round(roe_s, 3),
                "ev_score":     round(ev_s, 3),
                "fcf_score":    round(fcf_s, 3),
                "margin_score": round(margin_s, 3),
                "debt_score":   round(debt_s, 3),
                "garp_score":   round(composite, 4),
            })

        except Exception as e:
            print(f"[fundamentals] {tkr}: {e} — using neutral score")
            rows.append({
                "ticker": tkr,
                "peg": None, "roe_pct": None, "ev_ebitda": None,
                "fcf_yield_pct": None, "net_margin_pct": None, "debt_equity": None,
                "peg_score": 0.30, "roe_score": 0.30, "ev_score": 0.30,
                "fcf_score": 0.30, "margin_score": 0.30, "debt_score": 0.30,
                "garp_score": 0.30,
            })

    return pd.DataFrame(rows).set_index("ticker")
