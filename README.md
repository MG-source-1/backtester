# Strategy Backtester

A modular systematic trading backtester. All data is sourced from **Alpaca Markets** (SIP feed) and **SEC EDGAR** (XBRL Company Facts API).

Strategies run on the longest window their data sources allow:

| Strategy | Period | Binding constraint |
|---|---|---|
| Investor Portfolio (GARP + XAT) | 2016–2024 | Alpaca daily prices (~2016) |
| GARP Momentum | 2016–2024 | Alpaca daily prices (~2016) · EDGAR fundamentals (~2009) |
| AFP, XAT, Tech-Tier (reference) | 2016–2024 | Alpaca daily prices (~2016) |
| SIS (reference) | 2020–2024 | Alpaca 5-min intraday bars (available from 2020 only) |

**Why SIS has a shorter window:** SIS (SPY Intraday Afternoon Short) needs 5-minute intraday bars, which Alpaca only provides from 2020 onwards. Rather than constraining the entire portfolio to 2020 to accommodate SIS, it is kept as a reference strategy only. The investor portfolio runs on the full 2016–2024 window.

---

## Portfolio

### ★ Investor Portfolio — recommended allocation
**File:** `strategies/combined_portfolio/main.py`  
**Sharpe:** 1.03 &nbsp;|&nbsp; **Return:** +364% &nbsp;|&nbsp; **Max DD:** −21.3% &nbsp;|&nbsp; **Period:** 2016–2024

| Sleeve | Weight | Strategy | Purpose |
|---|---|---|---|
| GARP | 80% | TMT Momentum (15 large-cap tech stocks) | Primary alpha engine |
| XAT | 20% | Cross-Asset Trend (SPY · TLT · GLD) | Regime diversifier |

**Result:** Sharpe 1.03, +364% total return, Max DD −21.3% over 2016–2024. Beats SPY (+237%) by 127 percentage points with Sharpe above 1.0.

**Why XAT includes SPY:** XAT is a cross-asset trend strategy, not a pure hedge. Including SPY lets XAT participate in equity upside when equities are trending, while rotating into TLT (bonds) or GLD (gold) in risk-off regimes. Removing SPY makes XAT entirely passive — it holds cash 35%+ of the time and generates negligible return.

**Honest caveat on XAT:** XAT returned −1.7% over the full 2016–2024 window (Sharpe −0.60), making it a mild drag on the portfolio. It did reduce max drawdown from GARP standalone's −22.8% to the portfolio's −21.3%, but only marginally. The 2016–2024 window includes two unusually bad environments for cross-asset trend — the 2022 rate shock (bonds and equities fell simultaneously) and a long equity bull run where SPY dominated. In a 2008-style deflationary crash, XAT would be expected to earn meaningfully as TLT rallies. Whether to keep XAT in the portfolio is a forward-looking judgment call about which regime comes next.

---

## Design Decisions and What We Tested

### Why SIS was removed from the investor portfolio

SIS (SPY Intraday Short) was originally included at 10–20% of the portfolio. Removing it was motivated purely by data availability: SIS requires 5-minute intraday bars, which Alpaca only provides from 2020 onwards. Keeping SIS in the portfolio would have forced the entire backtest to start in 2020 — losing 4 years of the EDGAR-powered GARP backtest. Since the goal is a long-term performance picture, SIS was moved to reference status.

SIS's standalone edge is genuine — a 61–62% win rate on a market-neutral signal with −5.8% max drawdown — but its low reported Sharpe (0.10) is a measurement artefact: it only deploys ~18% of days, and the idle 82% suppresses the Sharpe ratio by √0.18 ≈ 0.42 mechanically.

### Why XAT includes SPY (not just TLT + GLD)

We tested XAT with TLT + GLD only (no SPY). Results over 2020–2024:

| XAT universe | XAT return | Portfolio Sharpe |
|---|---|---|
| SPY + TLT + GLD | +26% | 1.08 |
| TLT + GLD only | +2% | 0.80 |

Removing SPY made XAT almost entirely passive — it sat in cash 35% of the time and generated almost no return in normal environments. A strategy that can only defend in bad regimes but can't earn in good ones is a drag in every environment except the worst. SPY is what allows XAT to rotate meaningfully rather than defensively.

### Why sector-diversified GARP underperformed TMT-only

We tested expanding the GARP universe from 15 TMT stocks to 25 stocks across five sectors (adding LLY, UNH, ABBV, V, MA, COST, HD, NKE, CAT, HON).

| | TMT-only (15 stocks) | Expanded (25 stocks) |
|---|---|---|
| Return | +130% | +90% |
| Sharpe | 1.12 | 0.81 |
| Max DD | −25.6% | −27.9% |

*(Over 2020–2024 for comparability)*

Adding sectors with "good but not exceptional" momentum diluted exposure to the core TMT compounders (NVDA, META, AVGO) during a window where tech dominated everything. The honest caveat: if the next 5 years bring tech regulation or sustained rotation away from growth stocks, the expanded universe would likely outperform. We reverted to TMT-only because the backtest evidence is clear and the data window doesn't reward diversification.

### Portfolio weight evolution

| Configuration | Return | Sharpe | Max DD | Period | Notes |
|---|---|---|---|---|---|
| 40/40/20 GARP/XAT(TLT+GLD)/SIS | +63% | 0.84 | −15.9% | 2020–2024 | XAT without SPY too passive |
| 45/45/10 GARP/XAT(SPY+TLT+GLD)/SIS | +69% | 0.84 | −17.6% | 2020–2024 | SPY back in XAT |
| 70/20/10 GARP/XAT/SIS | +116% | 1.08 | −18.8% | 2020–2024 | With EDGAR fundamentals |
| **80/20 GARP/XAT (no SIS)** | **+364%** | **1.03** | **−21.3%** | **2016–2024** | **Current — full window, no intraday constraint** |

---

## Individual Strategies

### 1. Adaptive Factor Portfolio (AFP)
**File:** `strategies/equity_factor_rotation/main.py`  
**Sharpe:** 0.97 &nbsp;|&nbsp; **Return:** +130% &nbsp;|&nbsp; **Max DD:** −13.6% &nbsp;|&nbsp; **Period:** 2016–2024

Rotates monthly between four US equity factor ETFs — QQQ (growth/tech), QUAL (quality), MTUM (momentum), USMV (min-vol) — using composite momentum with two creative additions:

- **Factor Leadership Tilt:** top-ranked qualifying factor gets 1.5× weight
- **Correlation Regime Filter:** when QQQ and USMV start moving together (correlation >0.75), a systemic event is underway — exposure cuts to 40%. Detected both the 2020 crash and 2022 rate shock without VIX data.

AFP's Sharpe of 0.97 reflects a regime where factor rotation added genuine value — the 2016–2019 bull market rewarded systematic tilt between growth (QQQ), quality (QUAL), momentum (MTUM), and defensive (USMV). Its defining structural strength remains capital preservation: lowest max drawdown of any strategy at −13.6%, achieved through the correlation regime filter that cut exposure in both the 2020 crash and the 2022 rate shock.

---

### 2. Cross-Asset Trend (XAT) — reference
**File:** runs as a sleeve within `strategies/combined_portfolio/main.py`  
**Sharpe:** −0.60 &nbsp;|&nbsp; **Return:** −1.7% &nbsp;|&nbsp; **Max DD:** −20.3% &nbsp;|&nbsp; **Period:** 2016–2024

Applies AFP's momentum and inverse-vol weighting to three cross-asset instruments — SPY, TLT (20+ year US Treasuries), and GLD (gold). Ranks all three monthly; the leading asset gets a 1.5× rank tilt. Holds T-bills when no asset has positive momentum.

XAT's poor 2016–2024 standalone numbers reflect two back-to-back hostile environments: a long equity bull run (2016–2021) where the trend signal was slow to rotate, followed by the 2022 rate shock where TLT and SPY fell simultaneously. In a 2008-style deflationary crash, TLT rallies strongly while equities fall — the regime XAT is built for. Retained in the portfolio at 20% for its regime-classification role despite the drag in this window.

---

### 3. SPY Intraday Afternoon Short (SIS) — reference
**File:** `strategies/spy_intraday_short/main.py`  
**Sharpe:** 0.10 &nbsp;|&nbsp; **Return:** +14% &nbsp;|&nbsp; **Max DD:** −5.8% &nbsp;|&nbsp; **Period:** 2020–2024

Uses Alpaca 5-minute SPY bars. On high-conviction mornings — when both the overnight gap and first 30-minute return exceed minimum thresholds and agree in direction — **shorts the last 30 minutes of the session**. Up mornings reverse (61% win); down mornings continue (62% win). Active only 18% of days; earns T-bill on the rest.

**On the low Sharpe:** The 0.10 figure is a measurement artefact of capital dilution. Because SIS is only active 18% of days, the other 82% contribute zero excess return while still counting in the Sharpe denominator — mechanically suppressing the ratio by roughly √0.18 ≈ 0.42. The underlying signal is sound. Excluded from the investor portfolio because its 2020 data start would shorten the backtest by 4 years.

---

### 4. GARP Momentum
**File:** `strategies/garp_momentum/main.py`  
**Sharpe:** 1.06 &nbsp;|&nbsp; **Return:** +455% &nbsp;|&nbsp; **Max DD:** −22.8% &nbsp;|&nbsp; **Period:** 2016–2024

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

**Portfolio construction:** Composite rank = 65% price momentum (3m/6m/12m with 1-month skip) + 35% GARP score. Holds top 5 qualifying stocks, weighted by GARP score (higher quality = bigger allocation, capped at 30%). Three risk overlays: 20% annualised vol targeting, SPY 3m-momentum regime filter (scales to 0.6× or 0.3× in drawdowns), and 15% drawdown stop.

**Current top GARP scores:** NVDA (0.793 — PEG 0.30, ROE 75%), MSFT (0.746), QCOM (0.736), GOOGL (0.721), AAPL (0.721). TSLA (0.203) and INTC (0.265) are correctly screened out by the fundamentals.

> **Data source:** Fundamental data comes from the SEC EDGAR XBRL Company Facts API — no API key required. EDGAR provides the exact `filed` date for every submission, making point-in-time accuracy inherent: each rebalance only sees data publicly filed on or before that date. Coverage goes back to ~2009 for most large-cap TMT names, giving the GARP quality screen genuine historical data throughout the full 2016–2024 backtest window. `yfinance` is not used.

---

### 5. Tech-Tier Momentum Ladder (reference)
**File:** `strategies/concentrated_momentum/main.py`  
**Return:** +305% &nbsp;|&nbsp; **Sharpe:** 0.54 &nbsp;|&nbsp; **Max DD:** −34.3% &nbsp;|&nbsp; **Period:** 2016–2024

Concentrates monthly into the highest-momentum ETF from SOXX → QQQ → SPY. Uses SPY as a defensive floor when all three have negative momentum. Kept as a reference — the concentration and −34% drawdown make it unsuitable as a standalone primary strategy.

---

## Project Structure

```
├── core/
│   ├── alpaca.py          Shared Alpaca API (auth, pagination, caching, dividend-adjusted prices)
│   ├── data.py            fetch_prices / fetch_spy / fetch_tbill (BIL proxy)
│   └── metrics.py         Sharpe, drawdown, win rate
│
├── strategies/
│   ├── combined_portfolio/        ★ The recommended investor portfolio (80% GARP + 20% XAT)
│   │   ├── main.py                Run this
│   │   └── config.py              80/20 weights; 2016–2024
│   │
│   ├── equity_factor_rotation/    AFP — lowest drawdown; backtest engine also used by XAT
│   │   ├── main.py
│   │   ├── backtest.py
│   │   └── config.py
│   │
│   ├── spy_intraday_short/        SIS — reference only (2020–2024, intraday data constraint)
│   │   ├── main.py
│   │   ├── strategy.py
│   │   ├── data_intraday.py
│   │   ├── config.py
│   │   ├── STRATEGY.md
│   │   └── generate_pdf.py
│   │
│   ├── garp_momentum/             GARP — TMT quality-momentum (Sharpe 1.06 over 2016–2024)
│   │   ├── main.py
│   │   ├── backtest.py
│   │   ├── fundamentals.py        SEC EDGAR GARP scoring (PEG, ROE, EV/EBITDA, FCF, margin, D/E)
│   │   └── config.py
│   │
│   └── concentrated_momentum/     Reference — high return, high risk
│       ├── main.py
│       ├── backtest.py
│       └── config.py
│
├── data_cache/            Cached downloads (gitignored)
│                          Includes Alpaca price CSVs and EDGAR JSON facts files
├── outputs/               Charts and CSVs (gitignored)
├── config.py              Shared: START_DATE=2016, capital, absolute paths
├── .env                   Alpaca API credentials (gitignored — never commit)
└── requirements.txt
```

---

## Running

All commands from the project root.

```bash
# ★ Recommended: investor portfolio (80% GARP + 20% XAT), 2016–2024
python -m strategies.combined_portfolio.main

# Individual strategies
python -m strategies.equity_factor_rotation.main
python -m strategies.spy_intraday_short.main      # reference only, 2020–2024
python -m strategies.concentrated_momentum.main
python -m strategies.garp_momentum.main

# Generate PDF documentation for the intraday strategy
python strategies/spy_intraday_short/generate_pdf.py
```

---

## Setup

**Install dependencies:**
```bash
pip install pandas numpy matplotlib markdown
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
| ETF / stock daily prices | Alpaca SIP `1Day` bars, `adjustment=all` | Total return (splits + dividends included) · ~2016 onwards |
| SPY 5-min intraday | Alpaca SIP `5Min` bars | ~230k bars · 2020–2024 · SIS only |
| T-bill proxy | BIL ETF daily return | SPDR 1-3 Month T-Bill ETF |
| Fundamental data | SEC EDGAR XBRL Company Facts API | No API key required · exact filing dates · ~2009 onwards |

---

## Adding a New Strategy

1. Create `strategies/your_strategy/` with `__init__.py`
2. Add `config.py` importing shared params from root `config.py`
3. Add `backtest.py` and `main.py` (see existing strategies for the sys.path pattern)
4. Import from `core.data` and `core.metrics`

---

*Mark Garcera · Aspiring Trader*  
*Academic grounding: Gao et al. (2018, JF) · Lou et al. (2019, JFE) · Moskowitz et al. (2012, JF)*
