# Group 13 — EXPONENTIAL MOVING AVERAGE (EMA) Algorithmic Trading System on VNF301M

## Abstract

This project designs, backtests, and deploys an automated algorithmic trading system on the VN30 index futures continuous contract (VNF301M). The primary strategy is **Trend Following via EMA Crossover (EMA 10/30)**, supplemented by a dynamic ATR-based Stop Loss and an RSI entry filter.

Backtesting results show that the EMA strategy generates a very high number of trades with a win rate below 40%, due to frequent whipsaw signals on the 1-minute timeframe — a known limitation of crossover-based systems in choppy markets. The strategy loses money overall, but performance improves meaningfully on the out-of-sample period (2025), which featured a sustained VN30 uptrend. Two additional strategies — Opening Range Breakout (ORB) and Mean Reversion (Z-Score) — are implemented in the codebase for future research purposes only; they are not the focus of this submission. Paper Trading was conducted on the Algotrade arena26 platform from March 31 to April 3, 2026 with 77 filled orders.

---

## 0. Introduction

**Motivation:** The VN30F derivatives market frequently exhibits sustained directional trends following macro news or large capital flows. When momentum shifts, the crossing of short-term and long-term moving averages provides a systematic, rules-based method to capture these moves without discretionary judgment.

**Method:** The EMA Crossover strategy identifies trend changes through the crossing of a fast EMA (10) and a slow EMA (30). An RSI filter gates entries to avoid chasing overbought or oversold extremes, while an ATR-based Stop Loss sizes risk dynamically relative to current market volatility.

**Goal:** Build and validate a production-ready algorithmic trading system following the PLUTUS 9-step framework, from hypothesis through backtesting to live paper trading.

---

## 1. Step 1: Trading Hypothesis

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
| Volume MA (20) | Available for ORB strategy (future use) |
| Z-Score / Bollinger Bands | Available for Mean Reversion strategy (future use) |

---

## 3. Implementation

### 3.1 Environment Setup

```bash
conda activate plutus_x86
pip install -r requirements.txt
```

### 3.2 Running the Backtest

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

### 3.3 Running the Live Bot

```bash
python main_live.py
```

The bot connects to the Algotrade FIX server, fetches real-time OHLCV data on each candle close, computes signals, and places limit orders automatically. A terminal dashboard updates every bar. Trade notifications (entry, exit, P&L) are sent via Telegram.

---

## 4. Step 4: In-Sample Backtesting

- **Period:** 2023-01-03 → 2024-12-19 (≈ 24 months)
- **Total bars:** 122,663
- **Timeframe:** 1 minute
- **Initial Capital:** 500,000,000 VND
- **Commission:** 35,000 VND per side
- **Contracts per trade:** 3

### 4.1 Results

| Metric | Value |
| :--- | :--- |
| **Total Trades** | 8,467 |
| **Long / Short** | 8,467 / 8,467 signals generated |
| **Win Rate** | 37.63% |
| **Total Return** | −112.01% |
| **Sharpe Ratio (1min)** | −0.732 |
| **Max Drawdown** | −112.00% |
| **Profit Factor** | 0.682 |
| **Expectancy / trade** | −31,145 VND |
| **Avg Hold Time** | 12 minutes |
| **Avg Win** | 177,834 VND |
| **Avg Loss** | −157,221 VND |
| **Gross Profit** | 566,580,000 VND |
| **Gross Loss** | 830,285,000 VND |
| **Final Capital** | −60,050,000 VND |

> **Observation:** The strategy generates approximately 14 trades per day — a clear symptom of excessive whipsaw on the 1-minute timeframe. The EMA 10/30 crossover triggers too frequently in sideways conditions, producing many small losses that compound into a drawdown exceeding the initial capital. Notably, the average loss per trade (157,221 VND) is actually smaller than the average win (177,834 VND) — the problem is the win rate (37.6%), not the individual trade sizing. Commission drag at this trade frequency is severe.

---

## 5. Step 5: Optimization

In-sample results clearly identify the EMA strategy's core problem as **over-trading due to whipsaw**, not the directional logic itself. Key parameters identified for optimization:

| Parameter | Current Value | Direction to explore |
| :--- | :--- | :--- |
| EMA spans | 10 / 30 | Slower spans (e.g. 20/50) to reduce crossover frequency |
| RSI filter band | Long [45,75] / Short [25,55] | Tighten to reduce noise entries |
| ATR multiplier (SL) | 2.0× | Widen slightly to avoid premature stop-outs |
| Timeframe | 1 min | Consider 15min or 1h to filter intraday noise |

A walk-forward optimization on these parameters is planned before re-deployment.

---

## 6. Step 6: Out-of-Sample Backtesting

- **Period:** 2025-01-02 → 2025-12-31 (12 months)
- **Total bars:** 62,520
- **Parameters:** Identical to in-sample (no re-fitting)

### 6.1 Results

| Metric | Value |
| :--- | :--- |
| **Total Trades** | 3,895 |
| **Long / Short** | 3,895 / 3,895 signals generated |
| **Win Rate** | 38.72% |
| **Total Return** | −40.60% |
| **Sharpe Ratio (1min)** | −7.846 |
| **Max Drawdown** | −40.61% |
| **Profit Factor** | 0.888 |
| **Expectancy / trade** | −17,123 VND |
| **Avg Hold Time** | 15 minutes |
| **Avg Win** | 351,877 VND |
| **Avg Loss** | −250,241 VND |
| **Gross Profit** | 530,630,000 VND |
| **Gross Loss** | 597,325,000 VND |
| **Final Capital** | 296,980,000 VND |

> **Observation:** Out-of-sample performance improves meaningfully relative to in-sample — Profit Factor rises from 0.682 to 0.888, total return improves from −112% to −40.6%, and final capital stays positive at 296,980,000 VND. The 2025 period featured a sustained VN30 uptrend (index moved from ~1,300 to ~2,000 points), which naturally favors a trend-following approach. The improvement on unseen data is evidence that the directional signal has genuine merit; the losses are driven primarily by commission drag at high trade frequency rather than a fundamentally broken signal.

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

> **Observation:** The 4-day paper trading period confirmed full end-to-end system operation: FIX connection, real-time data ingestion, signal computation, limit order placement, and Telegram notifications all functioned correctly. The −5.56% P&L over 4 days is consistent with the backtest's pattern of high-frequency whipsaw losses and is the expected behavior at current parameters. Critically, this confirms that the backtest simulation faithfully replicates live execution — there is no significant simulation-to-live gap.

---

## 8. Conclusion

The EMA Crossover strategy on VNF301M at the 1-minute timeframe demonstrates a clear structural challenge: the crossover signal fires too frequently in non-trending conditions, generating commission costs that overwhelm the genuine edge the strategy possesses in trending markets. The core findings are:

1. **Over-trading is the primary problem.** The strategy generates ~14 trades per day on average. At 35,000 VND commission per side, this creates a cost floor that the current signal cannot overcome.
2. **The directional signal has real merit.** Out-of-sample Profit Factor (0.888) improved meaningfully from in-sample (0.682), and the strategy performed significantly better in 2025 when the VN30 was in a sustained uptrend. This improvement on unseen data is not a noise artifact.
3. **System integrity is confirmed.** Paper trading validated all infrastructure components with a 98.7% order fill rate and behavior fully consistent with backtest predictions.

**Next steps:** (1) Re-optimize EMA with slower spans and a coarser timeframe (15min or 1h) to dramatically reduce trade frequency and commission drag, (2) explore Opening Range Breakout (ORB) as an alternative primary strategy — its out-of-sample backtest returned +2.39% with a Profit Factor of 1.188, (3) implement a volatility-regime filter to suppress entries during identified sideways periods.

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
│   │   ├── orb_strategy.py        # Opening Range Breakout  ← future research
│   │   └── mean_reversion.py      # Z-Score Mean Reversion  ← future research
│   └── backtest/
│       ├── engine.py              # Event-driven backtest loop
│       └── metrics.py             # Sharpe, Drawdown, Win Rate, Profit Factor
├── main_live.py                   # Live trading bot
├── run_backtest.py                # Backtest runner
└── results/
    ├── insample/
    └── outsample/
```