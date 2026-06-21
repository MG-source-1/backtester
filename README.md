# Strategy Backtester

A modular systematic trading backtester with two independent strategies. All data is sourced exclusively from **Alpaca Markets** (SIP feed).

---

## Strategies

### 1. Adaptive Factor Portfolio (AFP) — Primary equity strategy
**File:** `strategies/equity_factor_rotation/main.py`  
**Sharpe:** 0.97 &nbsp;|&nbsp; **Return:** +130% &nbsp;|&nbsp; **Max DD:** −13.6% &nbsp;|&nbsp; **Period:** 2016–2024

The primary growth engine. Rotates between four US equity factor ETFs — QQQ (growth/tech), QUAL (quality), MTUM (momentum), and USMV (min-vol) — using a monthly composite momentum signal with two creative additions:

- **Factor Leadership Tilt:** the top-ranked qualifying factor gets 1.5× weight vs the rest.
- **Correlation Regime Filter:** measures the 20-day rolling correlation between QQQ and USMV. When these normally-uncorrelated factors start moving together (>0.75), it signals a systemic equity event and cuts portfolio exposure to 40%. This detected the 2020 COVID crash and the 2022 rate shock without needing VIX data.

---

### 2. SPY Intraday Afternoon Short — Secondary alpha / hedging strategy
**File:** `strategies/spy_intraday_short/main.py`  
**Sharpe:** 0.72 &nbsp;|&nbsp; **Return:** +21% &nbsp;|&nbsp; **Max DD:** −4.1% &nbsp;|&nbsp; **Period:** 2020–2024

Trades only 18% of days. Uses 5-minute SPY bars (Alpaca SIP) to identify high-conviction mornings where both the overnight gap and the first 30-minute session agree strongly in direction. On those days, **shorts the last 30 minutes of the session** — up mornings tend to reverse (61% win rate), down mornings tend to continue (62% win rate). Both point the same direction: short the afternoon.

Low correlation to AFP (different timeframe, different mechanism) makes it an effective portfolio diversifier.

---

## Project Structure

```
├── core/
│   ├── alpaca.py          Shared Alpaca API utilities (auth, pagination, caching)
│   ├── data.py            Data fetching: prices, SPY benchmark, BIL T-bill proxy
│   └── metrics.py         Sharpe, drawdown, win rate — shared by all strategies
│
├── strategies/
│   ├── equity_factor_rotation/    ★ Primary strategy
│   │   ├── main.py
│   │   ├── backtest.py
│   │   └── config.py
│   │
│   └── spy_intraday_short/        ★ Secondary / hedging strategy
│       ├── main.py
│       ├── strategy.py
│       ├── data_intraday.py
│       ├── config.py
│       ├── STRATEGY.md            Full documentation
│       └── generate_pdf.py
│
├── data_cache/            Cached Alpaca downloads (gitignored)
├── outputs/               Charts and CSVs (gitignored)
├── config.py              Shared: dates, capital, absolute paths
├── .env                   Alpaca API credentials (gitignored — never commit)
└── requirements.txt
```

---

## Running Strategies

All commands run from the project root.

```bash
# Primary equity strategy
python -m strategies.equity_factor_rotation.main

# Intraday hedging strategy (requires Alpaca credentials in .env)
python -m strategies.spy_intraday_short.main

# Generate PDF documentation for the intraday strategy
python strategies/spy_intraday_short/generate_pdf.py
```

---

## Setup

**Install dependencies:**
```bash
pip install pandas numpy matplotlib markdown
```

**Alpaca credentials** (required for all strategies — data comes from Alpaca SIP):

1. Sign up at [app.alpaca.markets](https://app.alpaca.markets) → Paper Trading → API Keys
2. Add to `.env` in the project root:
```
ALPACA_KEY=your-key-id-here
ALPACA_SECRET=your-secret-here
```

**First run** downloads and caches all required bars automatically. Subsequent runs load from `data_cache/` instantly.

---

## Data Sources

| Data | Source | Notes |
|---|---|---|
| ETF daily prices | Alpaca SIP `1Day` bars | SPY, QQQ, QUAL, MTUM, USMV |
| SPY 5-min intraday | Alpaca SIP `5Min` bars | ~400k bars, 2016–2024 |
| T-bill (risk-free rate) | BIL ETF daily return | SPDR Bloomberg 1-3 Month T-Bill — proxy for ^IRX |

No external dependencies beyond standard scientific Python.

---

## Adding a New Strategy

1. Create `strategies/your_strategy_name/` with `__init__.py`
2. Add `config.py` importing shared params from root `config.py`
3. Add `backtest.py` with your signal and simulation logic
4. Add `main.py` with the sys.path setup (see existing strategies for the pattern)
5. Import from `core.data` and `core.metrics` for data and performance measurement

---

*Mark Garcera · Aspiring Trader*  
*Strategies grounded in: Gao et al. (2018, JF) · Lou et al. (2019, JFE) · Moskowitz et al. (2012, JF)*
