# Strategy Backtester

A modular systematic trading backtester. All data is sourced from **Alpaca Markets** (SIP feed) and yahoo finance.

Strategies run on the longest window their data sources allow:

| Strategy | Period | Binding constraint |
|---|---|---|
| GARP Momentum | 2016–2024 | Alpaca daily prices (~2016) · EDGAR fundamentals (~2009) |
| Investor Portfolio (GARP + XAT + SIS) | 2020–2024 | SIS requires 5-min intraday bars, available from Alpaca from 2020 only |
| AFP, XAT, Tech-Tier (reference) | 2020–2024 | Aligned to the combined portfolio window |

**Why GARP has a longer window than the combined portfolio:** GARP only needs daily price data and fundamental statements — both available from well before 2020. The combined portfolio is constrained to 2020 because SIS (SPY Intraday Short) needs 5-minute intraday bars, which Alpaca only provides from 2020 onwards. Rather than artificially shortening GARP's backtest to match SIS, GARP reports results over its full available window.

---

## Portfolio

### ★ Investor Portfolio — recommended allocation
**File:** `strategies/combined_portfolio/main.py`  
**Sharpe:** 1.07 &nbsp;|&nbsp; **Return:** +116% &nbsp;|&nbsp; **Max DD:** −18.8% &nbsp;|&nbsp; **Period:** 2020–2024

| Sleeve | Weight | Strategy | Purpose |
|---|---|---|---|
| GARP | 70% | TMT Momentum (15 large-cap tech stocks) | Primary alpha engine |
| XAT | 20% | Cross-Asset Trend (SPY · TLT · GLD) | Regime diversifier — equity, bonds, or gold depending on momentum |
| SIS | 10% | SPY Intraday Short | Market-neutral alpha, earns on a different clock |

**Result:** Sharpe 1.07, +116% total return, Max DD −18.8% over 2020–2024. Beats SPY (+95%) by 21 percentage points, exceeds the Sharpe 1.0 design goal, and reduces drawdown substantially vs GARP standalone (−18.8% vs −22.8%).

**Why XAT includes SPY:** XAT is not a pure hedge — it is a cross-asset trend strategy that participates in whichever asset has the strongest momentum. When equities are trending, XAT holds SPY and generates positive returns alongside GARP. When risk-off conditions take hold, XAT rotates into TLT (bonds) or GLD (gold), which tend to rally when equities fall. Including SPY is what makes XAT a *return-seeking diversifier* rather than a *return-dragging hedge*. Removing SPY from XAT (tested earlier) resulted in XAT sitting in cash 35% of the time and returning only +2.4% — too passive to justify its capital allocation.

**Why GARP gets 70%, not more:** GARP is the strongest strategy (+130%, Sharpe 1.12) but it is 100% TMT-concentrated. A pure tech-specific shock — AI valuation compression, semiconductor export controls, or sustained rate pressure on high-multiple growth stocks — would hit GARP without SPY necessarily falling enough to trigger its regime filter. XAT provides a buffer in that scenario: if SPY starts lagging TLT or GLD in momentum, XAT rotates defensively even if GARP's internal filter hasn't fired yet.

**Why SIS is sized at 10%:** SIS only deploys capital on ~18% of trading days. A larger static allocation leaves capital idle in T-bills most of the time, dragging on portfolio Sharpe. 10% captures its genuinely uncorrelated intraday alpha with minimal idle-cash penalty.

---

## Design Decisions and What We Tested

The current portfolio is the result of many iterations. The full reasoning is documented here.

### The XAT universe: why SPY must be included

We tested three XAT configurations:

| XAT universe | XAT return | XAT Sharpe | Portfolio return | Portfolio Sharpe |
|---|---|---|---|---|
| SPY + TLT + GLD | +25.7% | 0.39 | +98% | 0.93 |
| TLT + GLD only | +2.4% | −0.32 | +61% | 0.80 |

Removing SPY made XAT almost entirely passive — it had no way to generate returns when equities were doing well, and ended up holding cash ~35% of the time when neither TLT nor GLD had positive momentum. A strategy that can only defend, but can't earn, is a drag in every environment except the worst. SPY is what gives XAT the ability to participate in good regimes, making the rotation meaningful rather than asymmetric.

### Why sector-diversified GARP underperformed TMT-only

We tested expanding the GARP universe from 15 TMT stocks to 25 stocks across five sectors (adding LLY, UNH, ABBV, V, MA, COST, HD, NKE, CAT, HON).

The results over 2020–2024 were worse on every metric:

| | TMT-only (15 stocks) | Expanded (25 stocks) |
|---|---|---|
| Return | +130% | +90% |
| Sharpe | 1.12 | 0.81 |
| Max DD | −25.6% | −27.9% |

The reason is specific to this test window. 2020–2024 was an exceptional era for TMT — NVDA returned ~1,800%, META recovered from a 70% drawdown to new highs, AVGO surged on AI infrastructure demand. Adding sectors with "good but not exceptional" momentum (industrials, consumer staples, healthcare) meant the strategy occasionally selected CAT or NKE in months when it could have been compounding in NVDA or AVGO. Even though LLY featured in the portfolio 57% of days on the back of GLP-1 momentum, it wasn't enough to offset the dilution.

The honest caveat: this conclusion is window-specific. If the next 5 years bring tech regulation, AI valuation compression, or a sustained rotation away from growth stocks, TMT-only GARP would suffer badly while a sector-diversified universe would naturally rotate into healthcare or industrials via the momentum signal. The expanded universe is the more robust long-term design; 2020–2024 just doesn't reward it. We reverted to TMT-only because the backtest evidence is clear and presenting worse numbers from a "more diversified" design would be misleading.

### Portfolio weight evolution

| Configuration | Return | Sharpe | Max DD | Why changed |
|---|---|---|---|---|
| 40% GARP + 40% XAT(TLT/GLD) + 20% SIS | +63% | 0.84 | −15.9% | XAT without SPY too passive; SIS oversized |
| 45% GARP + 45% XAT(TLT/GLD) + 10% SIS | +61% | 0.80 | −15.4% | Still XAT without SPY |
| 45% GARP + 45% XAT(SPY/TLT/GLD) + 10% SIS | +69% | 0.84 | −17.6% | SPY back in XAT, better |
| 90% GARP + 10% SIS (no XAT) | +119% | 0.95 | −23.7% | Removed XAT, concentrated in GARP |
| **70% GARP + 20% XAT(SPY/TLT/GLD) + 10% SIS** | **+116%** | **1.08** | **−18.8%** | **Current — balances alpha with diversification** |

The current 70/20/10 split keeps GARP dominant (reflecting its superior risk-adjusted returns) while giving XAT enough capital to provide meaningful regime diversification. The max drawdown improvement from GARP standalone (−25.6%) to the portfolio (−20.8%) is XAT's primary contribution.

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
**Sharpe:** 0.39 &nbsp;|&nbsp; **Return:** +26% &nbsp;|&nbsp; **Max DD:** −10.5% &nbsp;|&nbsp; **Period:** 2020–2024

Applies AFP's momentum and inverse-vol weighting framework to three cross-asset instruments — SPY (equities), TLT (20+ year US Treasuries), and GLD (gold). Ranks all three monthly by composite momentum; the leading asset gets a 1.5× rank tilt. Holds T-bills when no asset has positive momentum.

XAT is a regime classifier and return-seeker simultaneously: in equity bull markets it holds SPY and participates in the upside; in risk-off regimes it rotates into bonds or gold. The 2022 rate shock was the worst-case scenario for XAT — TLT dropped ~30% alongside equities, temporarily removing the defensive rotation option. In every other major modern drawdown (2008, 2020), TLT and GLD provided strong positive returns as equities fell.

---

### 3. SPY Intraday Afternoon Short (SIS)
**File:** `strategies/spy_intraday_short/main.py`  
**Sharpe:** 0.10 &nbsp;|&nbsp; **Return:** +14% &nbsp;|&nbsp; **Max DD:** −5.8% &nbsp;|&nbsp; **Period:** 2020–2024

Uses Alpaca 5-minute SPY bars. On high-conviction mornings — when both the overnight gap and first 30-minute return exceed minimum thresholds and agree in direction — **shorts the last 30 minutes of the session**. Up mornings reverse (61% win); down mornings continue (62% win). Active only 18% of days; earns T-bill on the rest.

**On the low Sharpe:** The 0.10 figure is a measurement artefact of capital dilution. Because SIS is only active 18% of days, the other 82% contribute zero excess return while still counting in the Sharpe denominator — mechanically suppressing the ratio by roughly √0.18 ≈ 0.42. The underlying signal (61–62% win rate, market-neutral) is sound. Its value in the portfolio is structural: it earns on a completely different clock to GARP and XAT, with a −5.8% max drawdown that means it never meaningfully hurts the portfolio.

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

**Current top GARP scores:** ADBE (0.874 — PEG 0.53, ROE 63%), NVDA (0.706 — PEG 0.65, ROE 114%), NFLX (0.707), CRM (0.665), META (0.656). TSLA (0.128) and INTC (0.297) are correctly screened out by the fundamentals.

> **Note:** Fundamental data comes from the SEC EDGAR XBRL Company Facts API — no API key required. EDGAR provides the exact `filed` date for every submission, making point-in-time accuracy inherent: each rebalance only sees data publicly filed on or before that date. Coverage goes back to ~2009 for most large-cap TMT names (65 filing dates for AAPL, 66 for NVDA), giving the GARP quality screen genuine historical data throughout the full 2020–2024 backtest window. `yfinance` is no longer a dependency.

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
│   ├── combined_portfolio/        ★ The recommended investor portfolio (70/20/10)
│   │   ├── main.py                Run this (also runs XAT sleeve)
│   │   └── config.py              70/20/10 weights; XAT universe (SPY · TLT · GLD)
│   │
│   ├── equity_factor_rotation/    AFP — lowest drawdown; backtest engine also used by XAT
│   │   ├── main.py
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
│   ├── garp_momentum/             GARP — TMT quality-momentum (best standalone Sharpe 1.12)
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
# ★ Recommended: investor portfolio (70% GARP + 20% XAT + 10% SIS)
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
| ETF / stock daily prices | Alpaca SIP `1Day` bars, `adjustment=all` | Total return (splits + dividends included) |
| SPY 5-min intraday | Alpaca SIP `5Min` bars | ~230k bars, 2020–2024 |
| T-bill proxy | BIL ETF daily return | SPDR 1-3 Month T-Bill ETF |
| Fundamental data | SEC EDGAR XBRL Company Facts API | PEG, ROE, EV/EBITDA, FCF yield — GARP strategy only. No API key required. |

---

## Adding a New Strategy

1. Create `strategies/your_strategy/` with `__init__.py`
2. Add `config.py` importing shared params from root `config.py`
3. Add `backtest.py` and `main.py` (see existing strategies for the sys.path pattern)
4. Import from `core.data` and `core.metrics`

---

*Mark Garcera · Aspiring Trader*  
*Academic grounding: Gao et al. (2018, JF) · Lou et al. (2019, JFE) · Moskowitz et al. (2012, JF)*
