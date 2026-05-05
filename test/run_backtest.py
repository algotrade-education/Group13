# """
# run_backtest.py — Backtest ORB Strategy
# Usage: python run_backtest.py
# """

# import os
# import pandas as pd
# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates

# from config.config import STRATEGY, BACKTEST
# from src.data.loader import load_ohlcv
# from src.features.indicators import add_features
# from src.strategy.orb_strategy import generate_signals
# from src.backtest.engine import run_backtest
# from src.backtest.metrics import compute_metrics

# os.makedirs("results/insample",  exist_ok=True)
# os.makedirs("results/outsample", exist_ok=True)


# def run_period(label: str, start: str, end: str, save_dir: str):
#     print(f"\n{'='*60}")
#     print(f"  {label}  |  {start}  →  {end}")
#     print(f"{'='*60}")

#     df = load_ohlcv(STRATEGY["symbol"], start, end)
#     df = add_features(df, window=STRATEGY["window"])
#     df = generate_signals(df)

#     # Thống kê tín hiệu để debug nhanh
#     n_long  = (df["trade_action"] >  0.5).sum()
#     n_short = (df["trade_action"] < -0.5).sum()
#     print(f"\n  📋 Tín hiệu:  LONG={n_long}  SHORT={n_short}  Tổng≈{n_long+n_short} lệnh")

#     result  = run_backtest(df)
#     # metrics = compute_metrics(
#     #     result["equity_curve"],
#     #     result["trades"],
#     #     BACKTEST["initial_capital"],
#     # )
#     metrics = compute_metrics(
#         result["equity_curve"],
#         result["trades"],
#         BACKTEST["initial_capital"],
#         timeframe_str=STRATEGY["timeframe"]  # Đưa thẳng chuỗi từ config vào đây
#     )

#     print(f"\n  📊 Performance Metrics:")
#     for k, v in metrics.items():
#         print(f"     {k:<30} {v}")

#     _save_chart(df, result, label, save_dir)

#     if not result["trades"].empty:
#         result["trades"].to_csv(f"{save_dir}/trades.csv", index=False)
#         print(f"  💾 Trades  → {save_dir}/trades.csv")

#     return result, metrics


# def _save_chart(df: pd.DataFrame, result: dict, label: str, save_dir: str):
#     fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
#     fig.suptitle(
#         f"ORB Strategy  |  {STRATEGY['symbol']}  |  {label}",
#         fontsize=14, fontweight="bold", y=0.98,
#     )

#     trades = result["trades"]

#     # ── Panel 1: Price + ORB zones + trade markers ────────────────────────
#     ax = axes[0]
#     ax.plot(df.index, df["close"], color="black", lw=0.8, label="Close", zorder=3)

#     # Tô màu vùng ORB từng ngày
#     dates = pd.to_datetime(df.index.date)
#     orb_start_t = pd.to_datetime("09:00").time()
#     orb_end_t   = pd.to_datetime("09:30").time()
#     orb_high, orb_low = {}, {}
#     for i, (t, d) in enumerate(zip(df.index.time, dates)):
#         if orb_start_t <= t < orb_end_t:
#             orb_high[d] = max(orb_high.get(d, -1e9), df["high"].iloc[i])
#             orb_low[d]  = min(orb_low.get(d,   1e9), df["low"].iloc[i])

#     prev_day = None
#     for i, (ts, d) in enumerate(zip(df.index, dates)):
#         if d != prev_day and d in orb_high:
#             ax.axhline(orb_high[d], color="tomato",   lw=0.6, ls="--", alpha=0.5)
#             ax.axhline(orb_low[d],  color="seagreen",  lw=0.6, ls="--", alpha=0.5)
#             prev_day = d

#     if not trades.empty:
#         for _, t in trades.iterrows():
#             color = "green" if t["direction"] == "LONG" else "red"
#             ax.axvline(t["entry_time"], color=color, alpha=0.25, lw=0.8)
#             ax.axvline(t["exit_time"],  color="gray", alpha=0.20, lw=0.6)

#     ax.set_ylabel("Price (VND)", fontsize=9)
#     ax.legend(fontsize=8, loc="upper left")
#     ax.grid(alpha=0.3)

#     # ── Panel 2: Volume ratio (xác nhận breakout) ─────────────────────────
#     ax = axes[1]
#     vol_ratio = df["volume"] / df["vol_ma"].replace(0, 1)
#     colors    = ["tomato" if v > 1.1 else "steelblue" for v in vol_ratio]
#     ax.bar(df.index, vol_ratio, color=colors, width=0.0005, alpha=0.7)
#     ax.axhline(1.1, color="orange", ls="--", lw=0.8, label="Ngưỡng xác nhận (1.1×)")
#     ax.axhline(1.0, color="gray",   ls=":",  lw=0.6)
#     ax.set_ylabel("Volume / MA20", fontsize=9)
#     ax.set_ylim(0, min(vol_ratio.quantile(0.99) * 1.2, 5))
#     ax.legend(fontsize=8, loc="upper left")
#     ax.grid(alpha=0.3)

#     # ── Panel 3: Equity Curve ─────────────────────────────────────────────
#     ax = axes[2]
#     equity = result["equity_curve"]
#     ax.plot(equity.index, equity.values, color="royalblue", lw=1.3, label="Portfolio")
#     ax.axhline(
#         BACKTEST["initial_capital"], color="gray", ls="--", lw=0.8,
#         label=f"Vốn ban đầu ({BACKTEST['initial_capital']:,.0f} VNĐ)",
#     )
#     ax.fill_between(
#         equity.index, equity.values, BACKTEST["initial_capital"],
#         where=(equity.values >= BACKTEST["initial_capital"]),
#         alpha=0.10, color="green",
#     )
#     ax.fill_between(
#         equity.index, equity.values, BACKTEST["initial_capital"],
#         where=(equity.values < BACKTEST["initial_capital"]),
#         alpha=0.10, color="red",
#     )
#     ax.set_ylabel("Portfolio Value (VNĐ)", fontsize=9)
#     ax.legend(fontsize=8, loc="upper left")
#     ax.grid(alpha=0.3)
#     ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
#     plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")

#     plt.tight_layout()
#     path = f"{save_dir}/backtest_chart.png"
#     plt.savefig(path, dpi=150, bbox_inches="tight")
#     plt.show()
#     print(f"  📈 Chart    → {path}")


# if __name__ == "__main__":
#     print("\n🚀 ORB Backtest — VN30F1M")
#     print(f"   ATR SL mult   : {STRATEGY['atr_multiplier']}")
#     print(f"   Trailing mult : {STRATEGY['trail_multiplier']}")
#     print(f"   Vol confirm   : {STRATEGY['vol_confirm']}×")
#     print(f"   Qty/lệnh      : {STRATEGY['target_qty_unit']} hợp đồng")

#     run_period(
#         label    = "In-Sample (2023–mid2024)",
#         start    = BACKTEST["insample_start"],
#         end      = BACKTEST["insample_end"],
#         save_dir = "results/insample",
#     )

#     run_period(
#         label    = "Out-of-Sample (H2 2024)",
#         start    = BACKTEST["outsample_start"],
#         end      = BACKTEST["outsample_end"],
#         save_dir = "results/outsample",
#     )

#     print("\n✅ Backtest xong! Kết quả ở folder results/")








# """
# Main entry point – Chạy In-Sample và Out-of-Sample Backtest.

# Usage:
#     python run_backtest.py
# """

# import os
# import pandas as pd
# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates

# from config.config import STRATEGY, BACKTEST
# from src.data.loader import load_ohlcv
# from src.features.indicators import add_features

# # from src.strategy.mean_reversion import generate_signals
# from src.strategy.trend_following import generate_signals

# from src.backtest.engine import run_backtest
# from src.backtest.metrics import compute_metrics

# os.makedirs("results/insample",  exist_ok=True)
# os.makedirs("results/outsample", exist_ok=True)


# # ── Main Runner ───────────────────────────────────────────────────────────────

# def run_period(label: str, start: str, end: str, save_dir: str):
#     print(f"\n{'='*60}")
#     print(f"  {label}  |  {start}  →  {end}")
#     print(f"{'='*60}")

#     # Pipeline
#     df = load_ohlcv(STRATEGY["symbol"], start, end)
#     df = add_features(df, window=STRATEGY["window"])
#     df = generate_signals(df)

#     result  = run_backtest(df)
#     metrics = compute_metrics(
#         result["equity_curve"],
#         result["trades"],
#         BACKTEST["initial_capital"],
#     )

#     # Print metrics
#     print(f"\n  📊 Performance Metrics:")
#     for k, v in metrics.items():
#         print(f"     {k:<28} {v}")

#     # Save outputs
#     _save_chart(df, result, label, save_dir)
#     if not result["trades"].empty:
#         result["trades"].to_csv(f"{save_dir}/trades.csv", index=False)
#         print(f"  💾 Trades saved   → {save_dir}/trades.csv")

#     return result, metrics


# # ── Charting ──────────────────────────────────────────────────────────────────

# def _save_chart(df: pd.DataFrame, result: dict, label: str, save_dir: str):
#     fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
#     fig.suptitle(
#         f"Mean Reversion  |  {STRATEGY['symbol']}  |  {label}",
#         fontsize=14,
#         fontweight="bold",
#         y=0.98,
#     )

#     trades = result["trades"]

#     # ── Panel 1: Price + Bollinger Bands + Trade Markers ─────────────────
#     ax = axes[0]
#     ax.plot(df.index, df["close"],    color="black",      lw=1.0, label="Close",    zorder=3)
#     ax.plot(df.index, df["bb_upper"], color="tomato",     lw=0.8, ls="--", label="BB Upper")
#     ax.plot(df.index, df["bb_mid"],   color="darkorange", lw=0.8, ls="-",  label="BB Mid")
#     ax.plot(df.index, df["bb_lower"], color="seagreen",   lw=0.8, ls="--", label="BB Lower")
#     ax.fill_between(df.index, df["bb_upper"], df["bb_lower"], alpha=0.05, color="blue")

#     if not trades.empty:
#         for _, t in trades.iterrows():
#             color = "green" if t["direction"] == "LONG" else "red"
#             ax.axvline(t["entry_time"], color=color, alpha=0.2, lw=0.7)
#             ax.axvline(t["exit_time"],  color="gray",  alpha=0.2, lw=0.7)

#     ax.set_ylabel("Price (VND)", fontsize=9)
#     ax.legend(fontsize=8, loc="upper left")
#     ax.grid(alpha=0.3)

#     # ── Panel 2: Z-Score ──────────────────────────────────────────────────
#     ax = axes[1]
#     ax.plot(df.index, df["zscore"], color="purple", lw=1.0, label="Z-Score")
#     ax.axhline( STRATEGY["entry_threshold"], color="red",      ls="--", lw=0.8, label=f"+{STRATEGY['entry_threshold']} Entry")
#     ax.axhline(-STRATEGY["entry_threshold"], color="green",    ls="--", lw=0.8, label=f"-{STRATEGY['entry_threshold']} Entry")
#     ax.axhline( STRATEGY["exit_threshold"],  color="orange",   ls=":",  lw=0.8, label=f"Exit zone")
#     ax.axhline(-STRATEGY["exit_threshold"],  color="orange",   ls=":",  lw=0.8)
#     ax.axhline(0, color="black", lw=0.5)
#     ax.fill_between(
#         df.index, df["zscore"], 0,
#         where=(df["zscore"] > STRATEGY["entry_threshold"]),
#         alpha=0.15, color="red",
#     )
#     ax.fill_between(
#         df.index, df["zscore"], 0,
#         where=(df["zscore"] < -STRATEGY["entry_threshold"]),
#         alpha=0.15, color="green",
#     )
#     ax.set_ylabel("Z-Score", fontsize=9)
#     ax.legend(fontsize=8, loc="upper left")
#     ax.grid(alpha=0.3)

#     # ── Panel 3: Equity Curve ─────────────────────────────────────────────
#     ax = axes[2]
#     equity = result["equity_curve"]
#     ax.plot(equity.index, equity.values, color="royalblue", lw=1.3, label="Portfolio Value")
#     ax.axhline(
#         BACKTEST["initial_capital"],
#         color="gray", ls="--", lw=0.8,
#         label=f"Initial Capital ({BACKTEST['initial_capital']:,.0f} VND)",
#     )
#     ax.fill_between(
#         equity.index,
#         equity.values,
#         BACKTEST["initial_capital"],
#         where=(equity.values >= BACKTEST["initial_capital"]),
#         alpha=0.1, color="green",
#     )
#     ax.fill_between(
#         equity.index,
#         equity.values,
#         BACKTEST["initial_capital"],
#         where=(equity.values < BACKTEST["initial_capital"]),
#         alpha=0.1, color="red",
#     )
#     ax.set_ylabel("Portfolio Value (VND)", fontsize=9)
#     ax.legend(fontsize=8, loc="upper left")
#     ax.grid(alpha=0.3)
#     ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
#     plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")

#     plt.tight_layout()
#     path = f"{save_dir}/backtest_chart.png"
#     plt.savefig(path, dpi=150, bbox_inches="tight")
#     plt.show()
#     print(f"  📈 Chart saved    → {path}")


# # ── Entry Point ───────────────────────────────────────────────────────────────

# if __name__ == "__main__":
#     print("\n🚀 Mean Reversion Backtest – VNF301M")
#     print(f"   Window          : {STRATEGY['window']}")
#     print(f"   Entry Threshold : {STRATEGY['entry_threshold']}")
#     print(f"   Exit Threshold  : {STRATEGY['exit_threshold']}")
#     print(f"   Stop Loss       : {STRATEGY['stop_loss']}")

#     run_period(
#         label    = "In-Sample",
#         start    = BACKTEST["insample_start"],
#         end      = BACKTEST["insample_end"],
#         save_dir = "results/insample",
#     )

#     run_period(
#         label    = "Out-of-Sample",
#         start    = BACKTEST["outsample_start"],
#         end      = BACKTEST["outsample_end"],
#         save_dir = "results/outsample",
#     )

#     print("\n✅ Backtest hoàn thành! Kết quả ở folder results/")



#Ema
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

from config.config import STRATEGY, BACKTEST
from src.data.loader import load_ohlcv
from src.features.indicators import add_features
from src.backtest.engine import run_backtest
from src.backtest.metrics import compute_metrics

# Tạo thư mục kết quả
os.makedirs("results/insample",  exist_ok=True)
os.makedirs("results/outsample", exist_ok=True)

def apply_group13_logic(df):
    """
    Hàm này mô phỏng chính xác logic trong handle_signal và run() của main.py
    """
    df = df.copy()
    
    # 1. Khởi tạo các cột
    df['raw_signal'] = 0  # Tín hiệu từ EMA Crossover
    df['final_signal'] = 0
    
    # Giả định EMA Fast/Slow đã có từ add_features
    # Long khi Fast > Slow, Short khi Fast < Slow
    df.loc[df['ema_fast'] > df['ema_slow'], 'raw_signal'] = 1
    df.loc[df['ema_fast'] < df['ema_slow'], 'raw_signal'] = -1

    current_pos = 0
    entry_price = 0
    signals = np.zeros(len(df))

    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # Lấy các thông số kỹ thuật
        rsi = row['rsi']
        atr = row['atr']
        price = row['close']
        time_str = df.index[i].strftime("%H:%M")
        
        # --- LOGIC THOÁT HÀNG (Ưu tiên số 1) ---
        is_closing_time = ("11:25" <= time_str < "11:30") or ("14:40" <= time_str < "14:45")
        
        # Tính TP/SL nếu đang có vị thế
        hit_tp_sl = False
        if current_pos != 0:
            if current_pos > 0: # Long
                tp = entry_price + (2.5 * atr)
                sl = entry_price - (1.5 * atr)
                if price >= tp or price <= sl: hit_tp_sl = True
            else: # Short
                tp = entry_price - (2.5 * atr)
                sl = entry_price + (1.5 * atr)
                if price <= tp or price >= sl: hit_tp_sl = True

        # Thực thi thoát lệnh
        if current_pos != 0 and (is_closing_time or hit_tp_sl):
            current_pos = 0
            signals[i] = 0
            continue

        # --- LOGIC VÀO LỆNH (Chặn bởi RSI) ---
        raw_sig = row['raw_signal']
        
        if current_pos == 0 and raw_sig != 0:
            # Kiểm tra bộ lọc RSI như trong main.py
            can_open = False
            if raw_sig == 1: # Muốn Long
                if 45 <= rsi <= 75: can_open = True
            elif raw_sig == -1: # Muốn Short
                if 25 <= rsi <= 55: can_open = True
            
            if can_open:
                current_pos = raw_sig
                entry_price = price
                signals[i] = current_pos
        else:
            # Nếu đang có vị thế mà tín hiệu raw đảo chiều, thì cũng đảo vị thế
            # (Hoặc giữ nguyên cho đến khi chạm TP/SL)
            signals[i] = current_pos

    df['signal'] = signals
    return df

def run_period(label: str, start: str, end: str, save_dir: str):
    print(f"\n{'='*60}")
    print(f"  {label}  |  {start}  →  {end}")
    print(f"{'='*60}")

    # Pipeline
    df = load_ohlcv(STRATEGY["symbol"], start, end)
    df = add_features(df, window=STRATEGY["window"])
    
    # Áp dụng logic đồng bộ với Main
    df = apply_group13_logic(df)

    result  = run_backtest(df)
    metrics = compute_metrics(
        result["equity_curve"],
        result["trades"],
        BACKTEST["initial_capital"],
    )

    print(f"\n  📊 Performance Metrics:")
    for k, v in metrics.items():
        print(f"     {k:<28} {v}")

    _save_chart_synchronized(df, result, label, save_dir)
    return result, metrics

def _save_chart_synchronized(df: pd.DataFrame, result: dict, label: str, save_dir: str):
    fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
    fig.suptitle(f"Group 13 Master Bot | {label}", fontsize=14, fontweight="bold")

    trades = result["trades"]

    # Panel 1: Price + EMAs
    ax = axes[0]
    ax.plot(df.index, df["close"], color="black", lw=1, label="Price")
    ax.plot(df.index, df["ema_fast"], color="dodgerblue", lw=0.8, label="EMA Fast (10)")
    ax.plot(df.index, df["ema_slow"], color="tomato", lw=0.8, label="EMA Slow (30)")
    
    # Đánh dấu điểm vào lệnh
    if not trades.empty:
        for _, t in trades.iterrows():
            color = "green" if t["direction"] == "LONG" else "red"
            ax.scatter(t["entry_time"], t["entry_price"], marker="^" if color=="green" else "v", color=color, s=50, zorder=5)

    ax.legend(loc="upper left")
    ax.set_ylabel("Price")
    ax.grid(alpha=0.2)

    # Panel 2: RSI Filter
    ax = axes[1]
    ax.plot(df.index, df["rsi"], color="purple", lw=1, label="RSI")
    ax.axhline(75, color="gray", ls="--", alpha=0.5)
    ax.axhline(45, color="green", ls="--", alpha=0.5, label="Long Zone (45-75)")
    ax.axhline(25, color="red", ls="--", alpha=0.5, label="Short Zone (25-55)")
    ax.axhline(55, color="gray", ls="--", alpha=0.5)
    ax.set_ylim(0, 100)
    ax.legend(loc="upper left")
    ax.set_ylabel("RSI")
    ax.grid(alpha=0.2)

    # Panel 3: Equity Curve
    ax = axes[2]
    equity = result["equity_curve"]
    ax.plot(equity.index, equity.values, color="royalblue", lw=1.5, label="Equity")
    ax.fill_between(equity.index, equity.values, BACKTEST["initial_capital"], alpha=0.1, color="blue")
    ax.set_ylabel("Portfolio Value")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.xticks(rotation=30)
    
    plt.tight_layout()
    plt.savefig(f"{save_dir}/backtest_chart_v2.png")
    plt.show()

if __name__ == "__main__":
    #run_period("In-Sample", BACKTEST["insample_start"], BACKTEST["insample_end"], "results/insample")

    # Chạy In-Sample
    run_period(
        label="In-Sample", 
        start=BACKTEST["insample_start"], 
        end=BACKTEST["insample_end"], 
        save_dir="results/insample"
    )

    # Chạy Out-Sample (THÊM DÒNG NÀY)
    run_period(
        label="Out-Sample", 
        start=BACKTEST["outsample_start"], 
        end=BACKTEST["outsample_end"], 
        save_dir="results/outsample"
    )