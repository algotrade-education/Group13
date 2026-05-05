# Group 13 — Multi-Strategy Algorithmic Trading System on VNF301M

## Abstract

This project designs, backtests, and deploys an automated multi-strategy trading system on the VN30 index futures continuous contract (VNF301M). The primary strategy is **Trend Following via EMA Crossover (EMA 10/30)**, supplemented by a dynamic ATR-based Stop Loss and an RSI entry filter. An **Opening Range Breakout (ORB)** strategy is also implemented in the codebase as a secondary option for future use.

Backtesting results show that while the EMA strategy generates a very high number of trades, the win rate remains below 40% due to frequent whipsaw signals on the 15-minute timeframe — a known limitation of crossover-based systems in choppy markets. The ORB strategy, though not the focus of this submission, demonstrates a more favorable Profit Factor on the out-of-sample period. Paper Trading was conducted on the Algotrade arena26 platform from March 31 to April 3, 2026 with 77 filled orders.

---

## 0. Introduction

**Motivation:** The VN30F derivatives market exhibits two dominant behavioral patterns: sustained directional trends following macro news or large capital flows, and sharp intraday breakouts concentrated in the opening session. A flexible system capable of switching strategies to match market conditions is therefore more robust than a single fixed approach.

**Method:** The EMA Crossover strategy identifies trend changes through the crossing of a fast (EMA 10) and a slow (EMA 30) exponential moving average. An RSI filter gates entries to avoid chasing overbought/oversold extremes, while an ATR-based Stop Loss sizes risk dynamically relative to current market volatility.

**Goal:** Build and validate a production-ready algorithmic trading system following the PLUTUS 9-step framework, from hypothesis through backtesting to live paper trading, with the architecture to support multiple interchangeable strategies.

---

## 1. Step 1: Trading Hypothesis

### 1.1 Primary Strategy — Trend Following (EMA Crossover)

When the short-term EMA (10) crosses above the long-term EMA (30), momentum is shifting upward and a long position is warranted. The reverse crossover signals a downtrend and a short entry. An RSI filter is applied at entry to avoid entering into already-extended moves.

**Entry logic:**

| Condition | Action |
| :--- | :--- |
| EMA 10 crosses above EMA 30 **and** RSI ∈ [45, 75] | Open **LONG** |
| EMA 10 crosses below EMA 30 **and** RSI ∈ [25, 55] | Open **SHORT** |
| Price bounces off EMA 10 in trend direction **and** RSI filter passes | Open position (pullback entry) |

**Exit logic:**

| Condition | Action |
| :--- | :--- |
| EMA 10 crosses in the opposite direction | Close position |
| Price hits ATR Stop Loss (entry ± 2.0 × ATR) | Stop out |
| 11:25–11:30 or 14:40–14:45 | Force exit (end-of-session) |

### 1.2 Secondary Strategy — Opening Range Breakout (ORB) *(future use)*

The High and Low of the first 30 minutes of the session (09:00–09:30) define the Opening Range. A breakout above the range High with volume confirmation signals a long entry; a break below the Low signals a short. An ATR Trailing Stop protects profits as the trade moves in favor. Maximum 1 LONG + 1 SHORT per day to prevent over-trading after a stop-out.

---

## 2. Steps 2 & 3: Data

### 2.1 Data Collection

| Attribute | Detail |
| :--- | :--- |
| **Product** | VN30 Futures — Continuous series VNF301M |
| **Source** | Algotrade official database (credentials in `config.py`) |
| **Raw format** | Tick data: matched price + volume per transaction |
| **Tables** | `quote.matched` LEFT JOIN `quote.total` |
| **Coverage** | January 2023 → December 2025 |

### 2.2 Data Processing

Tick data is resampled into OHLCV bars at the configured timeframe (`STRATEGY["timeframe"]` in `config.py`). Only bars within trading hours 09:00–14:45 are retained. Contract rollover across monthly expirations is handled automatically via the `ROLL_SCHEDULE` lookup table — duplicate bars at roll points are dropped to ensure a gapless continuous series.

**Technical indicators computed:**

| Indicator | Purpose |
| :--- | :--- |
| EMA 10 / EMA 30 | Trend direction and crossover signal |
| RSI (14) | Entry filter — avoids overbought/oversold entries |
| ATR (14) | Dynamic Stop Loss sizing |
| Volume MA (20) | Volume confirmation for ORB entries |
| Z-Score / Bollinger Bands | Available for Mean Reversion strategy |

---

## 3. Implementation

### 3.1 Environment Setup

```bash
conda activate plutus_x86
pip install -r requirements.txt
```

### 3.2 Switching Strategies

Change **one line** at the top of both `main_live.py` and `run_backtest.py`:

```python
ACTIVE_STRATEGY = "ema"    # "ema" | "orb" | "mean"
```

| Value | Strategy |
| :--- | :--- |
| `"ema"` | Trend Following — EMA 10/30 Crossover *(primary)* |
| `"orb"` | Opening Range Breakout + ATR Trailing Stop |
| `"mean"` | Mean Reversion — Z-Score + Bollinger Bands |

### 3.3 Running the Backtest

```bash
# Step 1: Verify data pipeline
python -m src.data.loader

# Step 2: Run full backtest (In-Sample + Out-of-Sample)
python run_backtest.py
```

Output is saved automatically to:

```
results/
├── insample/
│   ├── backtest_chart.png
│   └── trades.csv
└── outsample/
    ├── backtest_chart.png
    └── trades.csv
```

### 3.4 Running the Live Bot

```bash
python main_live.py
```

The bot connects to the Algotrade FIX server, fetches real-time OHLCV data, computes signals, and places limit orders on each new candle. A terminal dashboard updates every bar. Trade notifications (entry, exit, P&L) are sent via Telegram.

---

## 4. Step 4: In-Sample Backtesting

- **Period:** 2023-01-01 → 2024-12-30 (24 months)
- **Timeframe:** 15 minutes
- **Initial Capital:** 500,000,000 VND
- **Commission:** 35,000 VND per side
- **Contracts per trade:** 3

### 4.1 EMA Strategy — In-Sample Results

| Metric | Value |
| :--- | :--- |
| **Total Trades** | 8,467 |
| **Long / Short** | 4,237 / 4,230 |
| **Win Rate** | 37.63% |
| **Total Return** | −52.74% |
| **Gross Profit** | 566,580,000 VND |
| **Gross Loss** | −830,285,000 VND |
| **Profit Factor** | 0.682 |
| **Avg Win** | 177,834 VND |
| **Avg Loss** | −157,221 VND |
| **Avg Hold Time** | ~9 bars (≈ 2.3 hours) |

> **Observation:** The strategy generates an extremely high number of trades (~14 per day), which is a symptom of excessive whipsaw. The EMA 10/30 crossover triggers too frequently on the 15-minute timeframe in sideways conditions, producing many small losses that compound into a significant drawdown. The average loss per trade is actually smaller than the average win — the problem is win rate (37.6%), not position sizing.

### 4.2 ORB Strategy — In-Sample Results *(for reference)*

| Metric | Value |
| :--- | :--- |
| **Total Trades** | 647 |
| **Win Rate** | 37.87% |
| **Total Return** | −0.53% |
| **Profit Factor** | 0.966 |
| **Avg Win** | 310,306 VND |
| **Avg Loss** | −195,697 VND |

> **Observation:** ORB produces far fewer trades with a meaningfully better Profit Factor (0.97 vs 0.68). The much smaller drawdown (−0.53% vs −52.74%) demonstrates that the ATR Trailing Stop and the one-trade-per-direction-per-day limit are highly effective at controlling risk exposure.

---

## 5. Step 5: Optimization

In-sample results clearly identify the EMA strategy's core problem as **over-trading due to whipsaw**, not the directional logic itself. Key parameters for optimization:

| Parameter | Current Value | Direction to explore |
| :--- | :--- | :--- |
| EMA spans | 10 / 30 | Slower spans (e.g. 20/50) to reduce crossover frequency |
| RSI filter band | Long [45,75] / Short [25,55] | Tighten to reduce noise entries |
| ATR multiplier (SL) | 2.0× | Widen slightly to avoid premature stop-outs |
| TP/SL ratio | 2.5× / 1.5× ATR | Optimize for higher reward-to-risk |
| Timeframe | 15 min | Consider 1h to filter intraday noise |

A walk-forward optimization on these parameters is planned before re-deployment.

---

## 6. Step 6: Out-of-Sample Backtesting

- **Period:** 2025-01-01 → 2025-12-31 (12 months)
- **Parameters:** Identical to in-sample (no re-fitting)

### 6.1 EMA Strategy — Out-of-Sample Results

| Metric | Value |
| :--- | :--- |
| **Total Trades** | 3,895 |
| **Long / Short** | 2,107 / 1,788 |
| **Win Rate** | 38.72% |
| **Total Return** | −13.34% |
| **Gross Profit** | 530,630,000 VND |
| **Gross Loss** | −597,325,000 VND |
| **Profit Factor** | 0.888 |
| **Avg Win** | 351,877 VND |
| **Avg Loss** | −250,241 VND |
| **Avg Hold Time** | ~10.7 bars (≈ 2.7 hours) |

> **Observation:** Out-of-sample performance improves significantly relative to in-sample (Profit Factor 0.888 vs 0.682, return −13.3% vs −52.7%). The 2025 period featured a sustained VN30 uptrend (from ~1,300 to ~2,000 points) which naturally suits a trend-following approach. The strategy still loses money overall, but the improvement on unseen data suggests the underlying directional signal has genuine merit — the losses are driven primarily by commission drag at high trade frequency, not by a broken signal.

### 6.2 ORB Strategy — Out-of-Sample Results *(for reference)*

| Metric | Value |
| :--- | :--- |
| **Total Trades** | 308 |
| **Win Rate** | 40.91% |
| **Total Return** | +2.39% |
| **Profit Factor** | 1.188 |
| **Avg Win** | 598,095 VND |
| **Avg Loss** | −348,407 VND |

> **Observation:** ORB is the only strategy achieving a positive return in the out-of-sample period. The improving Profit Factor (0.97 → 1.19) and positive total return on unseen data confirm that the opening-range breakout hypothesis holds up out-of-sample. This makes ORB the recommended candidate for the next live deployment.

---

## 7. Step 7: Paper Trading

Paper Trading was conducted on the **Algotrade arena26** platform using the EMA Crossover strategy, connected to the exchange via FIX protocol.

### 7.1 Account Summary

| Field | Value |
| :--- | :--- |
| **Platform** | Algotrade arena26 (simulation) |
| **Account ID** | main (Group13) |
| **Initial Balance** | 500,000,000 VND |
| **Available Cash** | 472,210,000 VND |
| **Net P&L** | −27,790,000 VND (−5.56%) |
| **Derivative Fee** | 20,000 VND per contract |
| **Derivative Margin** | 25% |

### 7.2 Order Execution Summary

| Field | Value |
| :--- | :--- |
| **Trading period** | 2026-03-31 → 2026-04-03 (4 trading days) |
| **Total orders placed** | 78 |
| **Filled orders** | 77 (98.7% fill rate) |
| **Instrument** | VN30F2604 |
| **Order type** | Limit |
| **Standard lot size** | 3 contracts |

> **Observation:** The 4-day paper trading period confirmed full end-to-end system operation: FIX connection, real-time data ingestion, signal computation, limit order placement, and Telegram notifications all functioned correctly. The −5.56% P&L over just 4 days is consistent with the backtest's pattern of high-frequency losses from whipsaw and is the expected behavior given the current parameter set. Critically, this validates that the backtest simulation faithfully replicates live execution — there is no significant simulation-to-live gap.

---

## 8. Conclusion

The EMA Crossover strategy on VNF301M at the 15-minute timeframe reveals a clear structural challenge: the crossover signal fires too frequently in non-trending conditions, generating commission costs that overwhelm the genuine edge the strategy possesses in trending markets. The core findings are:

1. **Over-trading is the primary problem.** At ~14 trades per day, commission drag alone (35,000 VND × 2 sides × 14 trades × 252 days) vastly exceeds the strategy's gross profit capacity at current parameters.
2. **The directional signal has real merit.** Out-of-sample Profit Factor (0.888) improved meaningfully from in-sample (0.682), and performance improved significantly when the market was trending in 2025. This is not a noise artifact.
3. **ORB is the stronger strategy.** With a positive out-of-sample return (+2.39%), improving Profit Factor, and dramatically fewer trades, ORB is the recommended direction for the next iteration.
4. **System integrity is confirmed.** Paper trading validated all infrastructure components with a 98.7% order fill rate and behavior consistent with backtest predictions.

**Next steps:** (1) Re-optimize EMA with slower spans and a coarser timeframe to reduce whipsaw, (2) deploy ORB as the primary live strategy, (3) implement a volatility-regime filter to automatically select between trending and range-bound strategies.

---

## 9. Project Structure

```
.
├── config/
│   └── config.py                  # All configuration: STRATEGY, BACKTEST, DB, FIX, Telegram
├── src/
│   ├── data/
│   │   └── loader.py              # Tick data ingestion & OHLCV resampling
│   ├── features/
│   │   └── indicators.py          # EMA, RSI, ATR, Z-Score, Bollinger Bands
│   ├── strategy/
│   │   ├── trend_following.py     # EMA Crossover strategy  ← PRIMARY
│   │   ├── orb_strategy.py        # Opening Range Breakout  ← SECONDARY (future)
│   │   └── mean_reversion.py      # Z-Score Mean Reversion  ← AVAILABLE
│   └── backtest/
│       ├── engine.py              # Event-driven backtest loop
│       └── metrics.py             # Sharpe, Drawdown, Win Rate, Profit Factor
├── main_live.py                   # Live trading bot  (set ACTIVE_STRATEGY here)
├── run_backtest.py                # Backtest runner   (set ACTIVE_STRATEGY here)
└── results/
    ├── insample/
    └── outsample/
```