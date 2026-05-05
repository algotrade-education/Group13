"""
run_backtest.py — Group 13 Backtest Runner
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ĐỂ ĐỔI CHIẾN LƯỢC, chỉ cần sửa 1 dòng dưới đây:
    ACTIVE_STRATEGY = "ema"   → Trend Following (EMA Crossover)
    ACTIVE_STRATEGY = "orb"   → Opening Range Breakout
    ACTIVE_STRATEGY = "mean"  → Mean Reversion (Z-Score)
"""

# ══════════════════════════════════════════════════════
#  👇 CHỈ SỬA DÒNG NÀY KHI MUỐN ĐỔI CHIẾN LƯỢC
ACTIVE_STRATEGY = "ema"   # "ema" | "orb" | "mean"
# ══════════════════════════════════════════════════════

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from config.config import STRATEGY, BACKTEST
from src.data.loader import load_ohlcv
from src.features.indicators import add_features
from src.backtest.engine import run_backtest
from src.backtest.metrics import compute_metrics

# ── Tự động import đúng strategy ─────────────────────────────────────────────
if ACTIVE_STRATEGY == "orb":
    from src.strategy.orb_strategy import generate_signals
    _STRATEGY_NAME = "ORB (Opening Range Breakout)"
elif ACTIVE_STRATEGY == "mean":
    from src.strategy.mean_reversion import generate_signals
    _STRATEGY_NAME = "Mean Reversion (Z-Score)"
else:  # mặc định "ema"
    from src.strategy.trend_following import generate_signals as _ema_signals
    _STRATEGY_NAME = "Trend Following (EMA Crossover)"
# ─────────────────────────────────────────────────────────────────────────────

os.makedirs("results/insample",  exist_ok=True)
os.makedirs("results/outsample", exist_ok=True)


# ── EMA: bọc thêm lớp logic RSI + TP/SL giống main_live ─────────────────────
def _apply_ema_with_live_logic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mô phỏng chính xác handle_signal() của main_live khi dùng EMA:
    RSI filter khi mở lệnh + ATR-based TP/SL + force-exit giờ nghỉ.
    """
    df      = _ema_signals(df)          # Tính raw signal từ EMA crossover
    prices  = df["close"].values
    rsis    = df["rsi"].values
    atrs    = df["atr"].values
    raw_sig = df["signal"].values
    times   = df.index.time

    signals      = np.zeros(len(df))
    current_pos  = 0
    entry_price  = 0.0

    for i in range(1, len(df)):
        time_str     = df.index[i].strftime("%H:%M")
        price        = prices[i]
        rsi          = rsis[i]
        atr          = atrs[i]
        is_close_time = (
            "11:25" <= time_str < "11:30" or
            "14:40" <= time_str < "14:45"
        )

        # TP/SL check
        hit_tp_sl = False
        if current_pos != 0:
            if current_pos > 0:
                hit_tp_sl = price >= entry_price + 2.5 * atr or price <= entry_price - 1.5 * atr
            else:
                hit_tp_sl = price <= entry_price - 2.5 * atr or price >= entry_price + 1.5 * atr

        # Thoát lệnh
        if current_pos != 0 and (is_close_time or hit_tp_sl):
            current_pos = 0
            signals[i]  = 0
            continue

        # Mở lệnh mới — áp RSI filter như main_live
        sig = int(raw_sig[i])
        if current_pos == 0 and sig != 0:
            can_open = (
                (sig ==  1 and 45 <= rsi <= 75) or
                (sig == -1 and 25 <= rsi <= 55)
            )
            if can_open:
                current_pos = sig
                entry_price = price
        elif current_pos != 0 and sig != current_pos and sig != 0:
            # EMA đảo chiều → đóng vị thế cũ (không mở ngược ngay)
            current_pos = 0

        signals[i] = current_pos

    df["signal"] = signals
    return df


# ── Pipeline chính ────────────────────────────────────────────────────────────
def _build_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Gọi đúng generate_signals theo ACTIVE_STRATEGY."""
    if ACTIVE_STRATEGY == "ema":
        return _apply_ema_with_live_logic(df)
    else:
        return generate_signals(df)         # orb / mean tự quản lý logic


def run_period(label: str, start: str, end: str, save_dir: str):
    print(f"\n{'='*60}")
    print(f"  [{_STRATEGY_NAME}]  {label}  |  {start} → {end}")
    print(f"{'='*60}")

    df = load_ohlcv(STRATEGY["symbol"], start, end)
    df = add_features(df, window=STRATEGY["window"])
    df = _build_signals(df)

    # Debug: số lệnh phát hiện
    n_long  = (df["signal"].diff() > 0.5).sum()
    n_short = (df["signal"].diff() < -0.5).sum()
    print(f"\n  📋 Tín hiệu:  LONG={n_long}  SHORT={n_short}  Tổng≈{n_long + n_short} lệnh")

    result  = run_backtest(df)
    metrics = compute_metrics(
        result["equity_curve"],
        result["trades"],
        BACKTEST["initial_capital"],
        timeframe_str=STRATEGY["timeframe"],
    )

    print(f"\n  📊 Performance Metrics:")
    for k, v in metrics.items():
        print(f"     {k:<35} {v}")

    _save_chart(df, result, label, save_dir)

    if not result["trades"].empty:
        result["trades"].to_csv(f"{save_dir}/trades.csv", index=False)
        print(f"  💾 Trades → {save_dir}/trades.csv")

    return result, metrics


# ── Chart (tự động chọn panel phù hợp theo strategy) ────────────────────────
def _save_chart(df: pd.DataFrame, result: dict, label: str, save_dir: str):
    fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
    fig.suptitle(
        f"{_STRATEGY_NAME}  |  {STRATEGY['symbol']}  |  {label}",
        fontsize=14, fontweight="bold", y=0.98,
    )

    trades = result["trades"]

    # ── Panel 1: Price ────────────────────────────────────────────────────
    ax = axes[0]
    ax.plot(df.index, df["close"], color="black", lw=0.8, label="Close", zorder=3)

    if ACTIVE_STRATEGY == "ema":
        ax.plot(df.index, df["ema_fast"], color="dodgerblue", lw=0.8, label="EMA Fast (10)")
        ax.plot(df.index, df["ema_slow"], color="tomato",     lw=0.8, label="EMA Slow (30)")

    elif ACTIVE_STRATEGY == "mean":
        ax.plot(df.index, df["bb_upper"], color="tomato",     lw=0.8, ls="--", label="BB Upper")
        ax.plot(df.index, df["bb_mid"],   color="darkorange", lw=0.8, ls="-",  label="BB Mid")
        ax.plot(df.index, df["bb_lower"], color="seagreen",   lw=0.8, ls="--", label="BB Lower")
        ax.fill_between(df.index, df["bb_upper"], df["bb_lower"], alpha=0.05, color="blue")

    elif ACTIVE_STRATEGY == "orb":
        # Vẽ đường ORB High/Low từng ngày
        orb_start_t = pd.to_datetime("09:00").time()
        orb_end_t   = pd.to_datetime("09:30").time()
        orb_high, orb_low = {}, {}
        for i, (t, d) in enumerate(zip(df.index.time, df.index.date)):
            if orb_start_t <= t < orb_end_t:
                orb_high[d] = max(orb_high.get(d, -1e9), df["high"].iloc[i])
                orb_low[d]  = min(orb_low.get(d,   1e9), df["low"].iloc[i])
        prev_day = None
        for ts in df.index:
            d = ts.date()
            if d != prev_day and d in orb_high:
                ax.axhline(orb_high[d], color="tomato",  lw=0.6, ls="--", alpha=0.4)
                ax.axhline(orb_low[d],  color="seagreen",lw=0.6, ls="--", alpha=0.4)
                prev_day = d

    # Trade markers
    if not trades.empty:
        for _, t in trades.iterrows():
            color = "green" if t["direction"] == "LONG" else "red"
            ax.axvline(t["entry_time"], color=color, alpha=0.2, lw=0.8)
            ax.axvline(t["exit_time"],  color="gray", alpha=0.15, lw=0.6)

    ax.set_ylabel("Price (VND)", fontsize=9)
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)

    # ── Panel 2: Indicator phụ ────────────────────────────────────────────
    ax = axes[1]
    if ACTIVE_STRATEGY == "mean":
        ax.plot(df.index, df["zscore"], color="purple", lw=1.0, label="Z-Score")
        ax.axhline( STRATEGY["entry_threshold"], color="red",   ls="--", lw=0.8)
        ax.axhline(-STRATEGY["entry_threshold"], color="green", ls="--", lw=0.8)
        ax.axhline(0, color="black", lw=0.5)
        ax.set_ylabel("Z-Score", fontsize=9)
    else:
        # RSI cho cả EMA và ORB
        ax.plot(df.index, df["rsi"], color="purple", lw=1.0, label="RSI")
        ax.axhline(70, color="red",   ls="--", lw=0.8, alpha=0.6)
        ax.axhline(30, color="green", ls="--", lw=0.8, alpha=0.6)
        ax.axhline(50, color="gray",  ls=":",  lw=0.6)
        ax.set_ylim(0, 100)
        ax.set_ylabel("RSI", fontsize=9)

    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)

    # ── Panel 3: Equity Curve ──────────────────────────────────────────────
    ax     = axes[2]
    equity = result["equity_curve"]
    init   = BACKTEST["initial_capital"]
    ax.plot(equity.index, equity.values, color="royalblue", lw=1.3, label="Portfolio")
    ax.axhline(init, color="gray", ls="--", lw=0.8, label=f"Money ({init:,.0f} VNĐ)")
    ax.fill_between(equity.index, equity.values, init,
                    where=(equity.values >= init), alpha=0.10, color="green")
    ax.fill_between(equity.index, equity.values, init,
                    where=(equity.values  < init), alpha=0.10, color="red")
    ax.set_ylabel("Portfolio Value (VNĐ)", fontsize=9)
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")

    plt.tight_layout()
    path = f"{save_dir}/backtest_chart.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"  📈 Chart → {path}")


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n🚀 Backtest — {_STRATEGY_NAME}  |  {STRATEGY['symbol']}")
    print(f"   Timeframe : {STRATEGY['timeframe']}")
    print(f"   Capital   : {BACKTEST['initial_capital']:,.0f} VNĐ")
    print(f"   Commission: {BACKTEST['commission']:,.0f} VNĐ/lệnh")

    run_period(
        label    = "In-Sample",
        start    = BACKTEST["insample_start"],
        end      = BACKTEST["insample_end"],
        save_dir = "results/insample",
    )

    run_period(
        label    = "Out-of-Sample",
        start    = BACKTEST["outsample_start"],
        end      = BACKTEST["outsample_end"],
        save_dir = "results/outsample",
    )

    print("\n✅ Backtest hoàn thành! Kết quả ở folder results/")