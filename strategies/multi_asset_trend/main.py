"""
Multi-Asset Trend Following with Risk Parity Sizing — main runner.

Run from the project root:
    python -m strategies.multi_asset_trend.main
Or directly:
    python strategies/multi_asset_trend/main.py
"""

import os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pandas as pd

from core.data import fetch_prices, fetch_tbill, fetch_spy
from core.metrics import compute_metrics, per_ticker_metrics
from strategies.multi_asset_trend.backtest import (
    run_rp_trend_backtest, per_asset_contribution, per_asset_weights,
)
from strategies.multi_asset_trend.plot import plot_results
from strategies.multi_asset_trend.config import (
    TICKERS, START_DATE, END_DATE, INITIAL_CAPITAL, OUTPUT_DIR,
    LOOKBACK_MONTHS, TARGET_VOL, MAX_WEIGHT, MAX_LEVERAGE,
    VOL_LOOKBACK, DRAWDOWN_STOP, TRANSACTION_COST,
)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    tickers = list(TICKERS.keys())
    print(f"\n{'='*60}")
    print("  MULTI-ASSET TREND-FOLLOWING — RISK PARITY SIZING")
    print(f"{'='*60}")
    print(f"  Universe      : {', '.join(tickers)}")
    print(f"  Period        : {START_DATE}  →  {END_DATE}")
    print(f"  Capital       : ${INITIAL_CAPITAL:,.0f}")
    print(f"  Signal        : 3-of-4 composite vote momentum (monthly)")
    print(f"  Sizing        : Inverse-vol risk parity, target {TARGET_VOL:.0%} vol p.a.")
    print(f"  Max leverage  : {MAX_LEVERAGE:.1f}×  |  Max per asset: {MAX_WEIGHT:.0%}")
    print(f"  Drawdown stop : {DRAWDOWN_STOP:.0%} / 21-day cool-down")
    print(f"{'='*60}\n")

    print("[data] Downloading prices …")
    prices = fetch_prices(tickers, START_DATE, END_DATE)

    print("[data] Downloading SPY benchmark …")
    spy_cumulative = fetch_spy(START_DATE, END_DATE, INITIAL_CAPITAL)

    print("[data] Downloading T-bill rates …")
    tbill_rate, tbill_cumulative = fetch_tbill(START_DATE, END_DATE, INITIAL_CAPITAL)

    available = list(prices.columns)
    print(f"[data] Available tickers: {available}\n")

    portfolio = run_rp_trend_backtest(
        prices,
        tbill_daily_rate=tbill_rate,
        initial_capital=INITIAL_CAPITAL,
        lookback_months=LOOKBACK_MONTHS,
        target_vol=TARGET_VOL,
        max_weight=MAX_WEIGHT,
        max_leverage=MAX_LEVERAGE,
        vol_lookback=VOL_LOOKBACK,
        transaction_cost=TRANSACTION_COST,
        drawdown_stop_pct=DRAWDOWN_STOP,
    )

    asset_w   = per_asset_weights(prices, LOOKBACK_MONTHS, TARGET_VOL,
                                  MAX_WEIGHT, MAX_LEVERAGE, VOL_LOOKBACK)
    per_asset = per_asset_contribution(prices, INITIAL_CAPITAL, LOOKBACK_MONTHS,
                                       TARGET_VOL, MAX_WEIGHT, MAX_LEVERAGE, VOL_LOOKBACK)

    metrics     = compute_metrics(portfolio, tbill_rate, INITIAL_CAPITAL)
    spy_aligned = spy_cumulative.reindex(portfolio.index).ffill()
    spy_total   = (spy_aligned.iloc[-1] / spy_aligned.iloc[0]) - 1

    print("Portfolio Summary")
    print("-" * 45)
    for k, v in metrics.items():
        print(f"  {k:<32} {v}")
    print(f"  {'SPY Return (same window)':<32} {spy_total:.2%}")
    print(f"  {'Avg assets held':<32} {portfolio['n_long'].mean():.1f} of {len(available)}")
    print()

    ticker_df = per_ticker_metrics(prices, borrow_rate=0.0, initial_capital=INITIAL_CAPITAL)
    print("Per-Asset Buy-and-Hold Reference")
    print("-" * 45)
    print(ticker_df.to_string())
    print()

    portfolio.to_csv(os.path.join(OUTPUT_DIR, "daily_portfolio.csv"))
    ticker_df.to_csv(os.path.join(OUTPUT_DIR, "daily_per_ticker.csv"))
    print(f"[output] CSVs → {OUTPUT_DIR}/")

    plot_results(
        portfolio=portfolio,
        tbill_cumulative=tbill_cumulative,
        spy_cumulative=spy_cumulative,
        asset_weights=asset_w,
        per_asset=per_asset,
        ticker_labels=TICKERS,
        output_dir=OUTPUT_DIR,
        initial_capital=INITIAL_CAPITAL,
    )
    print("\nDone.")


if __name__ == "__main__":
    main()
