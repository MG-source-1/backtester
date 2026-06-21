import os
import numpy as np
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def plot_results(
    portfolio: pd.DataFrame,
    tbill_cumulative: pd.Series,
    spy_cumulative: pd.Series,
    asset_weights: pd.DataFrame,
    per_asset: pd.DataFrame,
    ticker_labels: dict,
    output_dir: str,
    initial_capital: float,
    **kwargs,
):
    os.makedirs(output_dir, exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(13, 15))
    fig.suptitle(
        "Multi-Asset Trend-Following — Risk Parity Sizing\n"
        "7 ETFs  ·  3-of-4 composite momentum  ·  Inverse-vol  ·  Vol-targeted 10% p.a.",
        fontsize=13, fontweight="bold",
    )
    colors = plt.cm.tab10.colors

    # ── 1. Portfolio vs SPY vs T-bill ────────────────────────────
    ax = axes[0]
    port_rebased  = portfolio["portfolio_value"] / initial_capital * 100
    spy_rebased   = spy_cumulative.reindex(portfolio.index).ffill() / initial_capital * 100
    tbill_rebased = tbill_cumulative.reindex(portfolio.index).ffill() / initial_capital * 100

    ax.plot(port_rebased.index, port_rebased,
            label="Risk Parity Trend", color="steelblue", linewidth=2.0)
    ax.plot(spy_rebased.index, spy_rebased,
            label="SPY (buy & hold)", color="darkorange", linestyle="--", linewidth=1.5)
    ax.plot(tbill_rebased.index, tbill_rebased,
            label="3-month T-bill", color="seagreen", linestyle=":", linewidth=1.3)
    ax.axhline(100, color="black", linewidth=0.4, linestyle=":")
    ax.set_ylabel("Value (rebased to 100)")
    ax.set_title("Portfolio Value vs Benchmarks")
    ax.legend(fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # ── 2. Dynamic allocation — stacked area ─────────────────────
    ax = axes[1]
    active_cols = [c for c in asset_weights.columns if asset_weights[c].sum() > 0]
    y_base = np.zeros(len(asset_weights))
    for i, col in enumerate(active_cols):
        vals  = asset_weights[col].clip(lower=0).values
        label = f"{col} – {ticker_labels.get(col, col).split('(')[0].strip()}"
        ax.fill_between(asset_weights.index, y_base, y_base + vals,
                        label=label, color=colors[i % len(colors)], alpha=0.80)
        y_base += vals
    ax.axhline(1.0, color="black", linewidth=0.6, linestyle=":")
    ax.set_ylabel("Portfolio Weight")
    ax.set_title("Dynamic Allocation — Risk-Parity Weights  (above 1.0 = modest leverage)")
    ax.legend(fontsize=7, ncol=4, loc="upper left")
    ax.set_ylim(0, 2.0)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # ── 3. Drawdown + stop shading ───────────────────────────────
    ax = axes[2]
    rolling_max = portfolio["portfolio_value"].cummax()
    drawdown    = (portfolio["portfolio_value"] - rolling_max) / rolling_max * 100
    ax.fill_between(drawdown.index, drawdown, 0, color="tomato", alpha=0.5)

    if "stop_active" in portfolio.columns:
        stop       = portfolio["stop_active"].astype(bool)
        stop_start = None
        for date, active in stop.items():
            if active and stop_start is None:
                stop_start = date
            elif not active and stop_start is not None:
                ax.axvspan(stop_start, date, color="gold", alpha=0.35, linewidth=0)
                stop_start = None
        if stop_start is not None:
            ax.axvspan(stop_start, portfolio.index[-1], color="gold", alpha=0.35, linewidth=0)

    dd_patch   = mpatches.Patch(color="tomato", alpha=0.6, label="Drawdown")
    stop_patch = mpatches.Patch(color="gold",   alpha=0.5, label="Stop active (21-day)")
    ax.legend(handles=[dd_patch, stop_patch], fontsize=8)
    ax.set_ylabel("Drawdown (%)")
    ax.set_title("Portfolio Drawdown  (gold = stop active)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    for a in axes:
        a.tick_params(axis="x", rotation=30)
        a.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(output_dir, "rp_trend_final.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[plot] Saved → {path}")
