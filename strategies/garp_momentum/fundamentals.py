"""
GARP fundamental scoring via yfinance.

Two modes:

  fetch_garp_scores(tickers)
      Live snapshot of today's fundamentals — used for the display table only.

  build_garp_history(tickers, prices, filing_lag_days=60, cache_dir=None)
      Point-in-time fundamental history for use in backtesting.
      Downloads quarterly filings (income statement, balance sheet, cashflow),
      applies a 60-day filing lag so each rebalance date only sees data that
      would have been publicly available at that time, then forward-fills
      into a date × ticker DataFrame aligned to the prices index.
      Results are cached to cache_dir so subsequent runs load instantly.

Metrics used (both modes)
─────────────────────────
  PEG ratio   (30%) — trailing P/E ÷ YoY TTM EPS growth; <1 is ideal
  ROE         (20%) — TTM net income / equity; measures profitability quality
  EV/EBITDA   (15%) — enterprise value / TTM EBITDA; lower = cheaper
  FCF yield   (15%) — TTM free cash flow / market cap; cash generation strength
  Net margin  (10%) — TTM net income / TTM revenue; earnings quality
  Debt/Equity (10%) — total debt / equity; lower leverage = safer
"""

import os
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
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.30
    if v <= 0:
        return 0.10
    return max(0.0, 1.0 - min(v, 3.0) / 3.0)


def _roe_score(v) -> float:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.30
    if v < 0:
        return 0.10
    return min(v, 0.50) / 0.50


def _evebitda_score(v) -> float:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.30
    if v <= 0:
        return 0.30
    return max(0.0, 1.0 - min(v, 50.0) / 50.0)


def _fcf_score(v) -> float:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.30
    if v < 0:
        return 0.10
    return min(v, 0.10) / 0.10


def _margin_score(v) -> float:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.30
    if v < 0:
        return 0.10
    return min(v, 0.40) / 0.40


def _debt_score(v) -> float:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.50
    if v < 0:
        return 0.50
    return max(0.0, 1.0 - min(v, 3.0) / 3.0)


# ── Live snapshot (display only) ─────────────────────────────

def fetch_garp_scores(tickers: list) -> pd.DataFrame:
    """
    Return a DataFrame indexed by ticker with raw metrics + composite GARP score.
    Uses today's live data from yfinance — for display only, not backtesting.
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
                "ticker":        tkr,
                "peg":           round(peg, 2)             if peg       is not None else None,
                "roe_pct":       round(roe * 100, 1)       if roe       is not None else None,
                "ev_ebitda":     round(evebitda, 1)        if evebitda  is not None else None,
                "fcf_yield_pct": round(fcf_yield * 100, 2) if fcf_yield is not None else None,
                "net_margin_pct":round(margin * 100, 1)    if margin    is not None else None,
                "debt_equity":   round(de_ratio, 2)        if de_ratio  is not None else None,
                "peg_score":     round(peg_s, 3),
                "roe_score":     round(roe_s, 3),
                "ev_score":      round(ev_s, 3),
                "fcf_score":     round(fcf_s, 3),
                "margin_score":  round(margin_s, 3),
                "debt_score":    round(debt_s, 3),
                "garp_score":    round(composite, 4),
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


# ── Point-in-time history helpers ─────────────────────────────

def _normalize_stmt(df) -> pd.DataFrame:
    """Strip timezone and normalize column timestamps to midnight."""
    if df is None or df.empty:
        return df
    df = df.copy()
    cols = pd.DatetimeIndex(df.columns)
    if cols.tz is not None:
        cols = cols.tz_localize(None)
    df.columns = cols.normalize()
    return df


def _row(df, *names) -> pd.Series:
    """Return the first matching metric row as a Series indexed by quarter date."""
    if df is None or df.empty:
        return pd.Series(dtype=float)
    # Try exact match, then case-insensitive fallback
    idx_map = {str(i).lower(): i for i in df.index}
    for n in names:
        if n in df.index:
            return pd.to_numeric(df.loc[n], errors="coerce")
        match = idx_map.get(n.lower())
        if match is not None:
            return pd.to_numeric(df.loc[match], errors="coerce")
    return pd.Series(dtype=float)


def _ttm_at(series: pd.Series, q_date: pd.Timestamp):
    """Sum of 4 most recent non-NaN quarters on or before q_date."""
    if series.empty:
        return None
    avail = series[series.index <= q_date].dropna().sort_index(ascending=False)
    return float(avail.iloc[:4].sum()) if len(avail) >= 4 else None


def _latest_at(series: pd.Series, q_date: pd.Timestamp):
    """Most recent non-NaN value on or before q_date."""
    if series.empty:
        return None
    avail = series[series.index <= q_date].dropna().sort_index(ascending=False)
    return float(avail.iloc[0]) if not avail.empty else None


def _score_at_quarter(q_date, inc, bs, cf, shares, price) -> float:
    """
    Compute a composite GARP score using the quarterly filing data
    available as of q_date and the stock price at the known date.
    """
    # Income statement rows
    net_inc_s = _row(inc, "Net Income", "Net Income Common Stockholders")
    revenue_s = _row(inc, "Total Revenue")
    ebitda_s  = _row(inc, "EBITDA", "Normalized EBITDA")
    op_inc_s  = _row(inc, "Operating Income", "EBIT")
    da_s      = _row(inc, "Reconciled Depreciation", "Depreciation And Amortization")
    eps_s     = _row(inc, "Diluted EPS", "Basic EPS", "Diluted Eps")

    # Balance sheet rows
    equity_s  = _row(bs, "Stockholders Equity", "Common Stock Equity",
                        "Total Stockholder Equity", "Total Stockholders Equity")
    debt_sr   = _row(bs, "Total Debt")
    cash_sr   = _row(bs, "Cash And Cash Equivalents",
                        "Cash Cash Equivalents And Short Term Investments")

    # Cashflow rows
    fcf_sr    = _row(cf, "Free Cash Flow")

    # TTM flow metrics
    net_inc    = _ttm_at(net_inc_s, q_date)
    revenue    = _ttm_at(revenue_s, q_date)
    fcf        = _ttm_at(fcf_sr,    q_date)
    ebitda_ttm = _ttm_at(ebitda_s,  q_date)
    op_inc_ttm = _ttm_at(op_inc_s,  q_date)
    da_ttm     = _ttm_at(da_s,      q_date)

    # Latest stock metrics (balance sheet items)
    equity     = _latest_at(equity_s, q_date)
    total_debt = _latest_at(debt_sr,  q_date)
    cash       = _latest_at(cash_sr,  q_date)

    mktcap = (price * shares) if (price and shares and price > 0 and shares > 0) else None

    # ── Derived metrics ───────────────────────────────────────
    roe       = (net_inc / equity)    if (net_inc and equity and equity > 0)   else None
    margin    = (net_inc / revenue)   if (net_inc and revenue and revenue > 0) else None
    de        = (total_debt / equity) if (total_debt is not None and equity and equity > 0) else None
    fcf_yield = (fcf / mktcap)        if (fcf and mktcap and mktcap > 0)       else None

    ebitda   = ebitda_ttm or (
        (op_inc_ttm + da_ttm) if (op_inc_ttm is not None and da_ttm is not None) else None
    )
    ev       = (mktcap + (total_debt or 0) - (cash or 0)) if mktcap else None
    evebitda = (ev / ebitda) if (ev and ebitda and ebitda > 0) else None

    # Trailing PEG: (price / TTM EPS) / (YoY TTM EPS growth × 100)
    peg = None
    if not eps_s.empty and price and price > 0 and shares:
        avail_eps = eps_s[eps_s.index <= q_date].dropna().sort_index(ascending=False)
        if len(avail_eps) >= 8:
            ttm_eps   = float(avail_eps.iloc[:4].sum())
            prior_eps = float(avail_eps.iloc[4:8].sum())
            if ttm_eps > 0 and prior_eps != 0:
                pe         = price / ttm_eps
                eps_growth = (ttm_eps - prior_eps) / abs(prior_eps)
                if eps_growth > 0:
                    peg = pe / (eps_growth * 100)

    return (
        METRIC_WEIGHTS["peg"]      * _peg_score(peg)           +
        METRIC_WEIGHTS["roe"]      * _roe_score(roe)           +
        METRIC_WEIGHTS["evebitda"] * _evebitda_score(evebitda) +
        METRIC_WEIGHTS["fcf"]      * _fcf_score(fcf_yield)     +
        METRIC_WEIGHTS["margin"]   * _margin_score(margin)     +
        METRIC_WEIGHTS["debt"]     * _debt_score(de)
    )


# ── Point-in-time history builder ─────────────────────────────

def build_garp_history(
    tickers: list,
    prices: pd.DataFrame,
    filing_lag_days: int = 60,
    cache_dir: str = None,
) -> pd.DataFrame:
    """
    Build a point-in-time GARP score history for backtesting.

    Returns a DataFrame (index = prices.index, columns = tickers) where each
    cell is the GARP score that would have been computable on that date using
    only publicly available filings (filing_lag_days after quarter-end).

    Caches per-ticker Series to cache_dir as garp_hist_<TICKER>.pkl.
    Delete the cache files to force a refresh.

    Note: yfinance typically provides ~4–5 years of quarterly history, so
    point-in-time scores are available from roughly 2020 onwards. Earlier
    dates receive a neutral score (0.30) for all tickers, meaning momentum
    drives selection entirely during that warmup period.
    """
    if not _YF_OK:
        print("[fundamentals] WARNING: yfinance not installed — using neutral scores.")
        return pd.DataFrame(0.30, index=prices.index, columns=tickers)

    all_series: dict = {}

    for tkr in tickers:
        cache_path = (
            os.path.join(cache_dir, f"garp_hist_{tkr}.pkl") if cache_dir else None
        )
        if cache_path and os.path.exists(cache_path):
            try:
                all_series[tkr] = pd.read_pickle(cache_path)
                print(f"[fundamentals] {tkr}: loaded from cache")
                continue
            except Exception:
                pass

        try:
            t       = yf.Ticker(tkr)
            inc_raw = getattr(t, "quarterly_income_stmt", None)
            if inc_raw is None or (isinstance(inc_raw, pd.DataFrame) and inc_raw.empty):
                inc_raw = getattr(t, "quarterly_financials", None)
            cf_raw  = getattr(t, "quarterly_cash_flow", None)
            if cf_raw is None or (isinstance(cf_raw, pd.DataFrame) and cf_raw.empty):
                cf_raw = getattr(t, "quarterly_cashflow", None)
            inc    = _normalize_stmt(inc_raw)
            bs     = _normalize_stmt(getattr(t, "quarterly_balance_sheet", None))
            cf     = _normalize_stmt(cf_raw)
            shares = (
                t.info.get("sharesOutstanding") or
                t.info.get("impliedSharesOutstanding") or 0
            )
        except Exception as e:
            print(f"[fundamentals] {tkr}: fetch error ({e}) — neutral scores")
            all_series[tkr] = pd.Series(dtype=float)
            continue

        # Collect all unique quarter-end dates across the three statements
        q_dates: set = set()
        for df in [inc, bs, cf]:
            if df is not None and not df.empty:
                q_dates.update(pd.DatetimeIndex(df.columns).normalize())

        if not q_dates:
            all_series[tkr] = pd.Series(dtype=float)
            continue

        price_s = prices[tkr] if tkr in prices.columns else None
        scores:  dict = {}

        for q_date in sorted(q_dates):
            known_date = q_date + pd.Timedelta(days=filing_lag_days)
            price = None
            if price_s is not None:
                avail_px = price_s[price_s.index <= known_date]
                price = float(avail_px.iloc[-1]) if not avail_px.empty else None

            scores[known_date] = round(
                _score_at_quarter(q_date, inc, bs, cf, shares, price), 4
            )

        s = pd.Series(scores).sort_index()
        n = len(s)
        if n:
            print(
                f"[fundamentals] {tkr}: {n} quarters "
                f"({s.index[0].strftime('%Y-%m')} → {s.index[-1].strftime('%Y-%m')})"
            )
        all_series[tkr] = s

        if cache_path:
            try:
                s.to_pickle(cache_path)
            except Exception:
                pass

    # Merge sparse score events into the dense prices date range
    score_df  = pd.DataFrame(all_series)
    full_idx  = prices.index
    if score_df.empty:
        return pd.DataFrame(0.30, index=full_idx, columns=tickers)

    # Forward-fill filing events into the daily price index.
    # Dates before the first available filing remain NaN — the backtest
    # detects these and runs as pure momentum for those periods.
    merged = (
        score_df
        .reindex(score_df.index.union(full_idx))
        .sort_index()
        .ffill()
        .reindex(full_idx)
    )
    return merged
