"""
Investor Portfolio — three uncorrelated return engines sharing capital.

Why GARP replaces AFP here
──────────────────────────
AFP (equity factor ETFs) and GARP (individual stock GARP + momentum) are both
long-equity strategies.  Running both just doubles equity exposure without real
diversification.  GARP is strictly better as the equity engine (Sharpe 1.23 vs
0.97; +531% vs +130% over 2016-2024) so AFP is retired from this portfolio.

The genuine diversification comes from XAT and SIS, which are structurally
uncorrelated with equity:
  • XAT holds TLT (bonds) and GLD (gold) alongside SPY — these go up when stocks
    fall in crises, acting as a natural hedge.
  • SIS is intraday and market-neutral — it earns on a different clock entirely.

Allocation (40 / 40 / 20):
  40%  GARP  — Growth-at-Reasonable-Price + Momentum (individual stock alpha)
               TMT universe: AAPL · MSFT · GOOGL · META · NVDA · AMD · AVGO …
               Sharpe 1.23 · Return +531% · Max DD −21%
  40%  XAT   — Cross-Asset Trend (SPY · TLT · GLD momentum)
               Higher weight than before — more bond/gold ballast needed since
               individual stocks are more volatile than factor ETFs.
               Genuine drawdown protection in rate shocks and risk-off episodes.
  20%  SIS   — SPY Intraday Afternoon Short (market-neutral alpha)
               Earns on a different clock; partially negative equity correlation.

Run from project root:
    python -m strategies.combined_portfolio.main
"""

import os, sys
from pathlib import Path

try:
    _ROOT = str(Path(__file__).resolve().parent.parent.parent)
except (PermissionError, OSError):
    _raw  = __file__.replace("\\", "/")
    _ROOT = _raw.split("/strategies/")[0] if "/strategies/" in _raw else ""

if _ROOT and _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
sys.path[:] = [p for p in sys.path if p and p not in ('.', '')]

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from core.data import fetch_prices, fetch_tbill, fetch_spy
from core.metrics import compute_metrics

from strategies.garp_momentum.fundamentals import fetch_garp_scores
from strategies.garp_momentum.backtest import run_garp_backtest
from strategies.garp_momentum.config import (
    TICKERS as GARP_TICKERS,
    TOP_N, MAX_WEIGHT as GARP_MAX_WEIGHT,
    MOM_WEIGHT, GARP_WEIGHT as GARP_SCORE_WEIGHT,
    LOOKBACK_MONTHS, SKIP_MONTHS,
    TARGET_VOL, MAX_LEVERAGE, VOL_LOOKBACK,
    DRAWDOWN_STOP, TRANSACTION_COST,
)

from strategies.equity_factor_rotation.backtest import run_factor_backtest
from strategies.equity_factor_rotation.config import (
    LOOKBACK_MONTHS as AFP_LB, RANK_TILT,
    CORR_WINDOW, CORR_HIGH, CORR_MID,
    TARGET_VOL as AFP_VOL, MAX_WEIGHT as AFP_MAX_W,
    MAX_LEVERAGE as AFP_LEV, VOL_LOOKBACK as AFP_VOLLB,
    TRANSACTION_COST as AFP_TC, DRAWDOWN_STOP as AFP_DD,
)

from strategies.spy_intraday_short.data_intraday import fetch_bars as fetch_intraday
from strategies.spy_intraday_short.strategy import compute_daily_signals, run_intraday_backtest
from strategies.spy_intraday_short.config import (
    MIN_MORNING_MOVE, MIN_OVERNIGHT_GAP,
    TC as SIS_TC, DD_STOP as SIS_STOP,
)

from strategies.combined_portfolio.config import (
    START_DATE, END_DATE, INITIAL_CAPITAL, OUTPUT_DIR, DATA_CACHE_DIR,
    WEIGHT_GARP, WEIGHT_XAT, WEIGHT_SIS,
    XAT_TICKERS,
)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    cap_garp = INITIAL_CAPITAL * WEIGHT_GARP
    cap_xat  = INITIAL_CAPITAL * WEIGHT_XAT
    cap_sis  = INITIAL_CAPITAL * WEIGHT_SIS

    print(f"\n{'='*68}")
    print("  INVESTOR PORTFOLIO  (40 / 40 / 20)")
    print(f"{'='*68}")
    print(f"  Period        : {START_DATE}  →  {END_DATE}")
    print(f"  Total capital : ${INITIAL_CAPITAL:,.0f}")
    print(f"  GARP  40%  = ${cap_garp:,.0f}  GARP Momentum (individual stocks)")
    print(f"  XAT   40%  = ${cap_xat:,.0f}  Cross-Asset Trend (SPY · TLT · GLD)")
    print(f"  SIS   20%  = ${cap_sis:,.0f}  SPY Intraday Short")
    print(f"  Design goal   : Sharpe > 1.0  |  Max DD < 20%")
    print(f"{'='*68}\n")

    # ── Fetch shared data ─────────────────────────────────────
    print("[data] Downloading stock prices for GARP universe …")
    garp_all_px = fetch_prices(GARP_TICKERS + ["SPY"], START_DATE, END_DATE)
    spy_prices  = garp_all_px["SPY"] if "SPY" in garp_all_px.columns else None
    garp_prices = garp_all_px[[t for t in GARP_TICKERS if t in garp_all_px.columns]]

    print("[data] Downloading cross-asset prices …")
    xat_prices = fetch_prices(list(XAT_TICKERS.keys()), START_DATE, END_DATE)

    print("[data] Downloading T-bill / BIL …")
    tbill_rate, tbill_cumulative = fetch_tbill(START_DATE, END_DATE, INITIAL_CAPITAL)

    print("[data] Downloading SPY benchmark …")
    spy_cumulative = fetch_spy(START_DATE, END_DATE, INITIAL_CAPITAL)

    print("[fundamentals] Fetching GARP scores from yfinance …")
    garp_df = fetch_garp_scores(list(garp_prices.columns))

    # ── Run GARP ──────────────────────────────────────────────
    print("\n[GARP] Running GARP momentum portfolio …")
    garp_portfolio = run_garp_backtest(
        prices           = garp_prices,
        garp_scores      = garp_df["garp_score"],
        spy_prices       = spy_prices,
        tbill_daily_rate = tbill_rate,
        initial_capital  = cap_garp,
        top_n            = TOP_N,
        lookback_months  = LOOKBACK_MONTHS,
        skip_months      = SKIP_MONTHS,
        garp_weight      = GARP_SCORE_WEIGHT,
        mom_weight       = MOM_WEIGHT,
        max_weight       = GARP_MAX_WEIGHT,
        target_vol       = TARGET_VOL,
        max_leverage     = MAX_LEVERAGE,
        vol_lookback     = VOL_LOOKBACK,
        transaction_cost = TRANSACTION_COST,
        drawdown_stop_pct = DRAWDOWN_STOP,
    )
    garp_ret = (garp_portfolio["portfolio_value"].iloc[-1] / cap_garp) - 1
    garp_m   = compute_metrics(garp_portfolio, tbill_rate, cap_garp)
    print(f"  GARP return: {garp_ret:+.1%}  |  Sharpe: {garp_m['Sharpe Ratio']}")

    # ── Run Cross-Asset Trend ─────────────────────────────────
    print("[XAT] Running cross-asset trend (SPY · TLT · GLD) …")
    xat_portfolio = run_factor_backtest(
        xat_prices, tbill_rate, cap_xat,
        AFP_LB, 1.0,
        CORR_WINDOW, CORR_HIGH, CORR_MID,
        AFP_VOL, 0.60, AFP_LEV, AFP_VOLLB,
        AFP_TC, AFP_DD,
    )
    xat_ret = (xat_portfolio["portfolio_value"].iloc[-1] / cap_xat) - 1
    xat_m   = compute_metrics(xat_portfolio, tbill_rate, cap_xat)
    print(f"  XAT return: {xat_ret:+.1%}  |  Sharpe: {xat_m['Sharpe Ratio']}")

    # ── Run SIS ───────────────────────────────────────────────
    print("[SIS] Running intraday afternoon short …")
    bars         = fetch_intraday("SPY", START_DATE, END_DATE,
                                  timeframe="5Min", cache_dir=DATA_CACHE_DIR)
    sis_signals  = compute_daily_signals(bars, MIN_MORNING_MOVE, MIN_OVERNIGHT_GAP)
    sis_portfolio = run_intraday_backtest(
        sis_signals, tbill_rate, cap_sis, SIS_TC, SIS_STOP,
    )
    sis_ret = (sis_portfolio["portfolio_value"].iloc[-1] / cap_sis) - 1
    sis_m   = compute_metrics(sis_portfolio, tbill_rate, cap_sis)
    print(f"  SIS return: {sis_ret:+.1%}  |  Sharpe: {sis_m['Sharpe Ratio']}")

    # ── Combine ───────────────────────────────────────────────
    print("\n[portfolio] Combining …")
    date_range = (garp_portfolio.index
                  .union(xat_portfolio.index)
                  .union(sis_portfolio.index))

    garp_val = garp_portfolio["portfolio_value"].reindex(date_range).ffill().fillna(cap_garp)
    xat_val  = xat_portfolio["portfolio_value"].reindex(date_range).ffill().fillna(cap_xat)
    sis_val  = sis_portfolio["portfolio_value"].reindex(date_range).ffill().fillna(cap_sis)

    combined_val = garp_val + xat_val + sis_val
    combined     = pd.DataFrame(index=date_range)
    combined["portfolio_value"] = combined_val
    combined["daily_return"]    = combined_val.pct_change().fillna(0)
    combined["in_regime"]       = True

    # ── Metrics ───────────────────────────────────────────────
    metrics      = compute_metrics(combined, tbill_rate, INITIAL_CAPITAL)
    spy_t        = spy_cumulative.reindex(combined.index).ffill()
    spy_tot      = (spy_t.iloc[-1] / spy_t.iloc[0]) - 1
    combined_tot = (combined_val.iloc[-1] / INITIAL_CAPITAL) - 1

    print("\nInvestor Portfolio Summary")
    print("─" * 56)
    for k, v in metrics.items():
        print(f"  {k:<36} {v}")
    print(f"  {'SPY Buy-and-Hold (same window)':<36} {spy_tot:.2%}")

    print("\nComponent Breakdown")
    print("─" * 56)
    rows = [
        (f"GARP  {WEIGHT_GARP:.0%}", garp_portfolio, cap_garp),
        (f"XAT   {WEIGHT_XAT:.0%}", xat_portfolio,  cap_xat),
        (f"SIS   {WEIGHT_SIS:.0%}", sis_portfolio,   cap_sis),
    ]
    for label, pf, cap in rows:
        ret = (pf["portfolio_value"].iloc[-1] / cap) - 1
        m   = compute_metrics(pf, tbill_rate, cap)
        print(f"  {label}  return={ret:+.1%}  sharpe={m['Sharpe Ratio']}  "
              f"max_dd={m['Max Drawdown']}")

    print(f"\n  Combined total return : {combined_tot:+.1%}")
    print(f"  SPY buy-and-hold      : {spy_tot:+.1%}")
    print(f"  Excess vs SPY         : {combined_tot - spy_tot:+.1%}")

    combined.to_csv(os.path.join(OUTPUT_DIR, "investor_portfolio.csv"))
    print(f"\n[output] CSV → {OUTPUT_DIR}/investor_portfolio.csv")

    # ── Plot ──────────────────────────────────────────────────
    fig, axes = plt.subplots(3, 1, figsize=(13, 15))
    fig.suptitle(
        "Investor Portfolio  (40% GARP Momentum  ·  40% Cross-Asset Trend  ·  20% Intraday Short)\n"
        "Three uncorrelated return engines  —  individual stock alpha + bonds/gold hedge + market-neutral",
        fontsize=11, fontweight="bold",
    )

    # Panel 1: Combined vs SPY vs T-bill
    ax = axes[0]
    inv_r = combined_val / INITIAL_CAPITAL * 100
    spy_r = spy_t / INITIAL_CAPITAL * 100
    tb_r  = tbill_cumulative.reindex(combined.index).ffill() / INITIAL_CAPITAL * 100
    ax.plot(inv_r.index, inv_r, label="Investor Portfolio", color="steelblue", linewidth=2.2)
    ax.plot(spy_r.index, spy_r, label="SPY (buy & hold)",   color="darkorange",
            linestyle="--", linewidth=1.5)
    ax.plot(tb_r.index,  tb_r,  label="T-bill (BIL)",       color="seagreen",
            linestyle=":", linewidth=1.2)
    ax.axhline(100, color="black", linewidth=0.4, linestyle=":")
    ax.set_ylabel("Value (rebased to 100)")
    ax.set_title("Portfolio Value vs Benchmarks")
    ax.legend(fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Panel 2: Stacked P&L by sleeve
    ax = axes[1]
    g = garp_val - cap_garp
    x = xat_val  - cap_xat
    s = sis_val  - cap_sis
    ax.fill_between(g.index, 0,   g,         color="#2c7bb6", alpha=0.75,
                    label=f"GARP 40% (individual stocks)")
    ax.fill_between(x.index, g,   g + x,     color="#e9c46a", alpha=0.75,
                    label=f"XAT 40% (SPY · TLT · GLD)")
    ax.fill_between(s.index, g+x, g + x + s, color="seagreen", alpha=0.75,
                    label=f"SIS 20% (intraday short)")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_ylabel("Cumulative P&L ($)")
    ax.set_title("Stacked P&L — three uncorrelated return sources")
    ax.legend(fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Panel 3: Drawdown vs SPY
    ax = axes[2]
    for vals, label, color, lw, ls in [
        (combined_val, "Investor Portfolio", "steelblue",   2.2, "-"),
        (spy_t,        "SPY B&H",            "darkorange",  1.3, "--"),
    ]:
        rm = vals.cummax()
        dd = (vals - rm) / rm * 100
        ax.fill_between(dd.index, dd, 0, color=color, alpha=0.20)
        ax.plot(dd.index, dd, color=color, linewidth=lw, linestyle=ls, label=label)

    ax.axhline(-20, color="black", linewidth=0.8, linestyle=":",
               alpha=0.6, label="−20% institutional tolerance")
    ax.set_ylabel("Drawdown (%)")
    ax.set_title("Drawdown vs SPY  (dotted line = typical institutional limit)")
    ax.legend(fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    for a in axes:
        a.tick_params(axis="x", rotation=30)
        a.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "investor_portfolio.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[plot] Saved → {path}")
    print("\nDone.")


if __name__ == "__main__":
    main()
