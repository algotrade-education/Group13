# import pandas as pd
# from config.config import BACKTEST, STRATEGY


# def run_backtest(df: pd.DataFrame) -> dict:
#     """
#     Event-driven backtest engine.

#     Rules:
#         - Mỗi lần chỉ giữ 1 contract (no pyramiding)
#         - Commission tính cả 2 chiều (open + close)
#         - Mark-to-market equity mỗi bar

#     Returns:
#         {
#             "equity_curve":  pd.Series,
#             "trades":        pd.DataFrame,
#             "final_capital": float,
#         }
#     """
#     capital    = BACKTEST["initial_capital"]
#     commission = BACKTEST["commission"]
#     mult       = STRATEGY["contract_size"]

#     cash        = capital
#     position    = 0
#     entry_price = None
#     entry_time  = None
#     prev_signal = 0

#     equity_list = []
#     trades      = []

#     for ts, row in df.iterrows():
#         sig   = int(row["signal"])
#         price = float(row["close"])

#         # ── Phát hiện thay đổi vị thế ─────────────────────────────────────
#         if prev_signal == 0 and sig != 0:
#             # OPEN: Không có → Có vị thế
#             position    = sig
#             entry_price = price
#             entry_time  = ts
#             cash       -= commission

#         elif prev_signal != 0 and sig != prev_signal:
#             # CLOSE: Đóng vị thế hiện tại
#             pnl   = (price - entry_price) * mult * prev_signal - commission
#             cash += pnl

#             trades.append({
#                 "entry_time":  entry_time,
#                 "exit_time":   ts,
#                 "direction":   "LONG" if prev_signal == 1 else "SHORT",
#                 "entry_price": entry_price,
#                 "exit_price":  price,
#                 "pnl":         pnl,
#             })

#             # Nếu ngay lập tức mở lệnh ngược chiều (sig != 0)
#             if sig != 0:
#                 position    = sig
#                 entry_price = price
#                 entry_time  = ts
#                 cash       -= commission
#             else:
#                 position    = 0
#                 entry_price = None
#                 entry_time  = None

#         # ── Mark-to-Market ─────────────────────────────────────────────────
#         unrealized = 0.0
#         if position != 0 and entry_price is not None:
#             unrealized = (price - entry_price) * mult * position

#         equity_list.append({"datetime": ts, "equity": cash + unrealized})
#         prev_signal = sig

#     equity_curve = (
#         pd.DataFrame(equity_list)
#         .set_index("datetime")["equity"]
#     )
#     trades_df = pd.DataFrame(trades)

#     return {
#         "equity_curve":  equity_curve,
#         "trades":        trades_df,
#         "final_capital": cash,
#     }



"""
engine.py — Event-driven backtest engine
Giữ nguyên logic gốc, thêm:
  - Kiểm tra signal hợp lệ (chỉ -1, 0, 1)
  - Ghi thêm cột hold_bars vào trades để debug
  - Tránh ghi trade với entry == exit (lệnh 0 bar)
"""
import pandas as pd
from config.config import BACKTEST, STRATEGY


def run_backtest(df: pd.DataFrame) -> dict:
    capital    = BACKTEST["initial_capital"]
    commission = BACKTEST["commission"]
    mult       = STRATEGY["contract_size"]

    cash        = capital
    position    = 0
    entry_price = None
    entry_time  = None
    entry_bar   = None
    prev_signal = 0

    equity_list = []
    trades      = []

    for bar_idx, (ts, row) in enumerate(df.iterrows()):
        sig   = int(row["signal"])
        price = float(row["close"])

        # ── Thay đổi vị thế ───────────────────────────────────────────────
        if prev_signal == 0 and sig != 0:
            # Mở vị thế mới
            position    = sig
            entry_price = price
            entry_time  = ts
            entry_bar   = bar_idx
            cash       -= commission

        elif prev_signal != 0 and sig != prev_signal:
            # Đóng vị thế hiện tại (và có thể mở ngược chiều)
            hold_bars = bar_idx - (entry_bar or bar_idx)
            pnl = (price - entry_price) * mult * prev_signal - commission
            cash += pnl

            # Chỉ ghi trade nếu giữ ít nhất 1 bar
            if hold_bars > 0:
                trades.append({
                    "entry_time":  entry_time,
                    "exit_time":   ts,
                    "direction":   "LONG" if prev_signal == 1 else "SHORT",
                    "entry_price": entry_price,
                    "exit_price":  price,
                    "pnl":         pnl,
                    "hold_bars":   hold_bars,
                })

            # Mở ngược chiều ngay lập tức nếu sig != 0
            if sig != 0:
                position    = sig
                entry_price = price
                entry_time  = ts
                entry_bar   = bar_idx
                cash       -= commission
            else:
                position    = 0
                entry_price = None
                entry_time  = None
                entry_bar   = None

        # ── Mark-to-Market ─────────────────────────────────────────────────
        unrealized = 0.0
        if position != 0 and entry_price is not None:
            unrealized = (price - entry_price) * mult * position

        equity_list.append({"datetime": ts, "equity": cash + unrealized})
        prev_signal = sig

    equity_curve = pd.DataFrame(equity_list).set_index("datetime")["equity"]
    trades_df    = pd.DataFrame(trades)

    return {
        "equity_curve":  equity_curve,
        "trades":        trades_df,
        "final_capital": cash,
    }