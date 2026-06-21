import numpy as np
import pandas as pd


def compute_metrics(
    portfolio: pd.DataFrame,
    tbill_daily_rate: pd.Series,
    initial_capital: float,
) -> dict:
    r = portfolio["daily_return"].dropna()

    total_return = (portfolio["portfolio_value"].iloc[-1] / initial_capital) - 1
    ann_return = (1 + total_return) ** (252 / len(r)) - 1
    ann_vol = r.std() * np.sqrt(252)

    # Sharpe uses the actual T-bill rate as the risk-free hurdle
    rf = tbill_daily_rate.reindex(r.index).ffill().dropna()
    rf_ann = (1 + rf.mean()) ** 252 - 1
    sharpe = (ann_return - rf_ann) / ann_vol if ann_vol > 0 else np.nan

    # T-bill total return over the same window
    rf_aligned = tbill_daily_rate.reindex(r.index).ffill().dropna()
    tbill_total = (1 + rf_aligned).prod() - 1
    excess_return = total_return - tbill_total

    rolling_max = portfolio["portfolio_value"].cummax()
    drawdown = (portfolio["portfolio_value"] - rolling_max) / rolling_max
    max_dd = drawdown.min()

    win_days = (r > 0).sum()
    win_rate = win_days / len(r)

    # Win rate on active (invested) days only — excludes cash days
    if "in_regime" in portfolio.columns:
        active_mask = portfolio["in_regime"].reindex(r.index).fillna(False)
        r_active    = r[active_mask]
        active_win  = (f"{(r_active > 0).sum() / len(r_active):.2%} "
                       f"({len(r_active)} active days)") if len(r_active) > 0 else "—"
    else:
        active_win = "—"

    return {
        "Total Return":              f"{total_return:.2%}",
        "T-bill Return (period)":    f"{tbill_total:.2%}",
        "Excess Return vs T-bills":  f"{excess_return:.2%}",
        "Ann. Return":               f"{ann_return:.2%}",
        "Ann. T-bill Rate (avg)":    f"{rf_ann:.2%}",
        "Ann. Volatility":           f"{ann_vol:.2%}",
        "Sharpe Ratio":              f"{sharpe:.2f}",
        "Max Drawdown":              f"{max_dd:.2%}",
        "Win Rate (all days)":       f"{win_rate:.2%}",
        "Win Rate (invested days)":  active_win,
        "Trading Days":              str(len(r)),
    }


def per_ticker_metrics(prices: pd.DataFrame, borrow_rate: float, initial_capital: float) -> pd.DataFrame:
    returns = prices.pct_change().dropna()
    n = len(prices.columns)
    alloc = initial_capital / n
    daily_borrow = borrow_rate / 252

    rows = []
    for ticker in returns.columns:
        r = returns[ticker].dropna()

        daily_pnl = r * alloc - alloc * daily_borrow   # long P&L
        cum_pnl = daily_pnl.cumsum()
        total_pnl = cum_pnl.iloc[-1]
        total_ret = total_pnl / alloc

        short_r = r   # no sign flip for long
        ann_vol = short_r.std() * np.sqrt(252)
        days = len(r)
        base = 1 + total_ret
        ann_ret = np.sign(base) * (abs(base) ** (252 / days)) - 1 if days > 0 and base != 0 else np.nan
        sharpe = ann_ret / ann_vol if ann_vol > 0 else np.nan

        rolling_max = cum_pnl.cummax()
        dd = (cum_pnl - rolling_max) / alloc
        max_dd = dd.min()

        rows.append({
            "Ticker":               ticker,
            "Alloc ($)":            f"${alloc:,.0f}",
            "Total P&L ($)":        f"${total_pnl:,.0f}",
            "Total Return (short)": f"{total_ret:.2%}",
            "Ann. Return":          f"{ann_ret:.2%}",
            "Ann. Vol":             f"{ann_vol:.2%}",
            "Sharpe":               f"{sharpe:.2f}",
            "Max Drawdown":         f"{max_dd:.2%}",
            "Days":                 days,
        })
    return pd.DataFrame(rows).set_index("Ticker")
