# Strategy Backtester

A modular systematic trading backtester. Each strategy lives in its own subfolder under `strategies/` and can be run independently.

## Structure

```
├── core/                          Shared utilities
│   ├── data.py                    yfinance data fetching (prices, T-bill, SPY, VIX)
│   └── metrics.py                 Sharpe, drawdown, win rate
│
├── strategies/
│   ├── spy_intraday_short/        ★ Primary strategy (Sharpe 0.72)
│   │   ├── main.py                Run: python -m strategies.spy_intraday_short.main
│   │   ├── strategy.py            Signal logic + backtest simulation
│   │   ├── data_intraday.py       Alpaca 5-min bar fetcher
│   │   ├── config.py              Strategy parameters
│   │   ├── STRATEGY.md            Full documentation
│   │   └── generate_pdf.py        Convert docs to PDF
│   │
│   └── multi_asset_trend/         Daily trend strategy (Sharpe ~0.68)
│       ├── main.py                Run: python -m strategies.multi_asset_trend.main
│       ├── backtest.py            Risk parity trend logic
│       ├── plot.py                Charts
│       └── config.py             Strategy parameters
│
├── data_cache/                    Cached Alpaca + yfinance downloads
├── outputs/                       Charts and CSVs
├── config.py                      Shared: dates, capital, absolute paths
├── .env                           Alpaca API credentials (never commit)
├── .gitignore
└── requirements.txt
```

## Running Strategies

```bash
# From the project root:

# Intraday strategy (SPY Afternoon Short)
python -m strategies.spy_intraday_short.main

# Daily trend strategy (Multi-Asset Risk Parity)
python -m strategies.multi_asset_trend.main

# Generate strategy PDF documentation
python strategies/spy_intraday_short/generate_pdf.py
```

## Adding a New Strategy

1. Create `strategies/your_strategy_name/`
2. Add `__init__.py`, `config.py`, `strategy.py`, `main.py`
3. Import shared utilities from `core.data` and `core.metrics`
4. Add `sys.path` setup at the top of `main.py` (see existing strategies)

## Requirements

```
yfinance >= 0.2.40
pandas   >= 2.0.0
numpy    >= 1.26.0
matplotlib >= 3.8.0
```

Install: `pip install yfinance pandas numpy matplotlib`

**Alpaca credentials** required for the intraday strategy — set `ALPACA_KEY` and `ALPACA_SECRET` in `.env`.
