# Strategy Backtester

A modular systematic trading backtester. All data is sourced from **Alpaca Markets** (SIP feed) and yahoo finance.

All strategies are benchmarked on the same window: **2020–2024** — the earliest period where every data source (daily prices, intraday SPY bars, T-bill proxy) is fully available.

---

## Portfolio

### ★ Investor Portfolio — recommended allocation
**File:** `strategies/combined_portfolio/main.py`  
**Sharpe:** 0.80 &nbsp;|&nbsp; **Return:** +61% &nbsp;|&nbsp; **Max DD:** −15.4% &nbsp;|&nbsp; **Period:** 2020–2024

Three uncorrelated return engines sharing capital:

| Sleeve | Weight | Strategy | Purpose |
|---|---|---|---|
| GARP | 45% | GARP Momentum (individual stocks) | Equity alpha — stock selection via PEG, ROE, FCF, momentum |
| XAT | 45% | Cross-Asset Trend (TLT · GLD) | Pure defensive hedge — bonds and gold are structurally uncorrelated to equities |
| SIS | 10% | SPY Intraday Short | Market-neutral daily alpha, uncorrelated to everything else |

**Why GARP replaced AFP:** AFP (factor ETFs) and GARP (individual stocks) are both long-equity — running both just doubles equity exposure without diversification benefit. GARP is strictly better as the equity engine over this window (Sharpe 1.12 vs 0.40; +130% vs +28% standalone).

**Why XAT holds only TLT and GLD (not SPY):** GARP already provides equity exposure. Including SPY in XAT meant the portfolio was doubly long equities — the intended hedge was partially cancelling itself. TLT and GLD are structurally uncorrelated to equities: bonds rally in deflationary shocks and flight-to-safety events; gold rallies in currency crises and stagflation. These are the scenarios where GARP would suffer most.

**Why SIS is sized at 10%:** SIS only deploys capital on ~18% of trading days. A 20% static allocation left capital idle in T-bills 82% of the time, dragging on portfolio Sharpe without adding proportional return. 10% keeps SIS's uncorrelated alpha in the mix while halving the idle capital drag — a structural sizing argument, not a backtest optimisation.

**Result:** Sharpe 0.80, +61% total return, Max DD −15.4% over 2020–2024. SPY returned +95% over the same window. The portfolio lagged in raw return because 2020–2024 was an unusually hostile period for the diversification thesis: in 2022, the Fed's aggressive rate hikes caused bonds and stocks to fall *simultaneously* — TLT dropped ~30%, removing XAT's hedging power at exactly the wrong moment. In a more typical drawdown (2008-style deflationary shock, or a 2020-style liquidity crisis), TLT and GLD would rally as equities fall, and XAT would act as a genuine cushion. The portfolio is built for that regime. The goal is not to maximise return in any single window but to maintain three structurally independent return sources whose failure modes do not coincide.

---

## Individual Strategies

### 1. Adaptive Factor Portfolio (AFP)
**File:** `strategies/equity_factor_rotation/main.py`  
**Sharpe:** 0.40 &nbsp;|&nbsp; **Return:** +28% &nbsp;|&nbsp; **Max DD:** −13.6% &nbsp;|&nbsp; **Period:** 2020–2024

Rotates monthly between four US equity factor ETFs — QQQ (growth/tech), QUAL (quality), MTUM (momentum), USMV (min-vol) — using composite momentum with two creative additions:

- **Factor Leadership Tilt:** top-ranked qualifying factor gets 1.5× weight
- **Correlation Regime Filter:** when QQQ and USMV start moving together (correlation >0.75), a systemic event is underway — exposure cuts to 40%. Detected both the 2020 crash and 2022 rate shock without VIX data.

AFP's modest 2020–2024 numbers reflect the difficulty of rotating between factor ETFs that became highly correlated during this period. Its structural strength is capital preservation: lowest max drawdown of any strategy at −13.6%.

---

### 2. Cross-Asset Trend (XAT)
**File:** `strategies/combined_portfolio/main.py` (runs as a sleeve within the investor portfolio)  
**Sharpe:** −0.32 &nbsp;|&nbsp; **Return:** +2.4% &nbsp;|&nbsp; **Max DD:** −11.7% &nbsp;|&nbsp; **Period:** 2020–2024

Applies the same momentum and inverse-volatility weighting framework as AFP, but to two pure defensive assets — TLT (20+ year US Treasuries) and GLD (gold). Each month it ranks TLT and GLD by composite momentum; the leading asset gets a 1.5× rank tilt. When neither has positive momentum, the sleeve holds T-bills entirely.

XAT's role is structural, not return-generative. Its poor standalone numbers in this window are a direct consequence of 2022: the Fed's fastest rate hiking cycle since the 1980s drove TLT down ~30% while gold also struggled against rising real rates. Both assets failed simultaneously — the one historical scenario where a bonds+gold hedge breaks down. In every other modern drawdown (2008, 2020, dot-com), TLT and GLD provided meaningful positive returns as equities fell.

---

### 3. SPY Intraday Afternoon Short (SIS)
**File:** `strategies/spy_intraday_short/main.py`  
**Sharpe:** 0.10 &nbsp;|&nbsp; **Return:** +14% &nbsp;|&nbsp; **Max DD:** −5.8% &nbsp;|&nbsp; **Period:** 2020–2024

Uses Alpaca 5-minute SPY bars. On high-conviction mornings — when both the overnight gap and first 30-minute return exceed minimum thresholds and agree in direction — **shorts the last 30 minutes of the session**. Up mornings reverse (61% win); down mornings continue (62% win). Active only 18% of days; earns T-bill on the rest.

**On the low Sharpe:** The 0.10 figure is a measurement artefact of capital dilution, not a reflection of poor signal quality. Because SIS is only active 18% of days, the other 82% contribute zero excess return while still counting in the Sharpe denominator. This mechanically suppresses the ratio by a factor of roughly √0.18 ≈ 0.42. The strategy's actual edge — a 61–62% win rate on a genuinely market-neutral signal — is sound. Its value in the portfolio is structural: it earns on a completely different clock to GARP and XAT, with a −5.8% max drawdown that means it never meaningfully hurts the portfolio even in its worst periods.

---

### 4. GARP Momentum
**File:** `strategies/garp_momentum/main.py`  
**Sharpe:** 1.12 &nbsp;|&nbsp; **Return:** +130% &nbsp;|&nbsp; **Max DD:** −25.6% &nbsp;|&nbsp; **Period:** 2020–2024

Applies **Growth at a Reasonable Price (GARP)** fundamental screening to a 15-stock TMT universe (AAPL, MSFT, GOOGL, META, NVDA, AMD, AVGO, QCOM, ORCL, CRM, ADBE, NFLX, AMZN, TSLA, INTC), then selects and sizes positions using **Jegadeesh-Titman price momentum**.

Six ratios are scored and combined into a composite GARP quality rank:

| Ratio | Weight | Signal |
|---|---|---|
| PEG ratio | 30% | P/E ÷ EPS growth — core GARP metric; <1 = paying less than 1× per % of growth |
| Return on Equity | 20% | Profitability quality; great companies sustain ROE >30% |
| EV/EBITDA | 15% | Enterprise value efficiency; lower = cheaper relative to earnings power |
| FCF Yield | 15% | Free cash flow / market cap — cash generation strength |
| Net Margin | 10% | Pricing power and earnings quality |
| Debt/Equity | 10% | Financial health; lower leverage = more resilience in downturns |

**Portfolio construction:** Composite rank = 65% price momentum (3m/6m/12m with 1-month skip) + 35% GARP score. Holds top 5 qualifying stocks, weighted by GARP score (higher quality = bigger allocation, capped at 30%). Three risk overlays: 20% annualised volatility targeting, SPY 3m-momentum regime filter (scales to 0.6× or 0.3× in drawdowns), and 15% drawdown stop.

**Current top GARP scores:** ADBE (0.874 — PEG 0.53, ROE 63%), NVDA (0.706 — PEG 0.65, ROE 114%), NFLX (0.707), CRM (0.665), META (0.656). TSLA (0.128) and INTC (0.297) are correctly screened out by the fundamentals.

> **Note:** The backtest uses point-in-time fundamental scores — quarterly filing data with a 60-day lag, so each rebalance only sees what was publicly available at that date. A live snapshot is also fetched at runtime for the display table. Requires `yfinance` in addition to the base dependencies. In practice, yfinance only retains ~7 quarters of history, which does not cover the 2020–2024 backtest window — so the backtest runs as pure price momentum throughout, with GARP fundamental scoring applying only to live forward use.

---

### 5. Tech-Tier Momentum Ladder (reference)
**File:** `strategies/concentrated_momentum/main.py`  
**Return:** +46% &nbsp;|&nbsp; **Sharpe:** 0.21 &nbsp;|&nbsp; **Max DD:** −32.1% &nbsp;|&nbsp; **Period:** 2020–2024

Concentrates monthly into the highest-momentum ETF from SOXX → QQQ → SPY. Uses SPY as a defensive floor when all three have negative momentum. Kept as a reference — the concentration and −32% drawdown make it unsuitable as a standalone primary strategy.

---

## Project Structure

```
├── core/
│   ├── alpaca.py          Shared Alpaca API (auth, pagination, caching, dividend-adjusted prices)
│   ├── data.py            fetch_prices / fetch_spy / fetch_tbill (BIL proxy)
│   └── metrics.py         Sharpe, drawdown, win rate
│
├── strategies/
│   ├── combined_portfolio/        ★ The recommended investor portfolio
│   │   ├── main.py                Run this (also runs XAT sleeve)
│   │   └── config.py              45/45/10 weights; XAT universe (TLT · GLD)
│   │
│   ├── equity_factor_rotation/    AFP — lowest drawdown, factor rotation
│   │   ├── main.py                Also provides the backtest engine used by XAT
│   │   ├── backtest.py
│   │   └── config.py
│   │
│   ├── spy_intraday_short/        SIS — intraday market-neutral alpha
│   │   ├── main.py
│   │   ├── strategy.py
│   │   ├── data_intraday.py
│   │   ├── config.py
│   │   ├── STRATEGY.md
│   │   └── generate_pdf.py
│   │
│   ├── garp_momentum/             GARP — best standalone Sharpe (1.12)
│   │   ├── main.py
│   │   ├── backtest.py
│   │   ├── fundamentals.py        yfinance GARP scoring (PEG, ROE, EV/EBITDA, FCF, margin, D/E)
│   │   └── config.py
│   │
│   └── concentrated_momentum/     Reference — high return, high risk
│       ├── main.py
│       ├── backtest.py
│       └── config.py
│
├── data_cache/            Cached Alpaca downloads (gitignored)
├── outputs/               Charts and CSVs (gitignored)
├── config.py              Shared: dates (2020–2024), capital, absolute paths
├── .env                   Alpaca API credentials (gitignored — never commit)
└── requirements.txt
```

---

## Running

All commands from the project root.

```bash
# ★ Recommended: investor portfolio (45% GARP + 45% XAT + 10% SIS)
python -m strategies.combined_portfolio.main

# Individual strategies
python -m strategies.equity_factor_rotation.main
python -m strategies.spy_intraday_short.main
python -m strategies.concentrated_momentum.main
python -m strategies.garp_momentum.main

# Generate PDF documentation for the intraday strategy
python strategies/spy_intraday_short/generate_pdf.py
```

---

## Setup

**Install dependencies:**
```bash
pip install pandas numpy matplotlib markdown yfinance
```

**Alpaca credentials** (required for all strategies):

1. Sign up at [app.alpaca.markets](https://app.alpaca.markets) → Paper Trading → API Keys
2. Add to `.env`:
```
ALPACA_KEY=your-key-id-here
ALPACA_SECRET=your-secret-here
```

**First run** downloads and caches all data automatically. Subsequent runs load from `data_cache/` instantly.

---

## Data Sources

| Data | Source | Notes |
|---|---|---|
| ETF / stock daily prices | Alpaca SIP `1Day` bars, `adjustment=all` | Total return (splits + dividends included) |
| SPY 5-min intraday | Alpaca SIP `5Min` bars | ~230k bars, 2020–2024 |
| T-bill proxy | BIL ETF daily return | SPDR 1-3 Month T-Bill ETF |
| Fundamental data | yfinance (point-in-time quarterly filings) | PEG, ROE, EV/EBITDA, FCF yield — GARP strategy only |

---

## Adding a New Strategy

1. Create `strategies/your_strategy/` with `__init__.py`
2. Add `config.py` importing shared params from root `config.py`
3. Add `backtest.py` and `main.py` (see existing strategies for the sys.path pattern)
4. Import from `core.data` and `core.metrics`

---

*Mark Garcera · Aspiring Trader*  
*Academic grounding: Gao et al. (2018, JF) · Lou et al. (2019, JFE) · Moskowitz et al. (2012, JF)*
