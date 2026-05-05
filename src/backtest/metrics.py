# import pandas as pd
# import numpy as np


# def compute_metrics(
#     equity_curve: pd.Series,
#     trades: pd.DataFrame,
#     initial_capital: float,
# ) -> dict:
#     """
#     Tính các chỉ số hiệu năng chuẩn.

#     Returns dict gồm:
#         Total Trades, Win Rate, Total Return,
#         Sharpe Ratio, Max Drawdown, Profit Factor,
#         Avg Win, Avg Loss, Gross Profit, Gross Loss, Final Capital
#     """
#     if trades.empty:
#         return {"error": "No trades executed – hãy giảm entry_threshold"}

#     n_trades = len(trades)

#     # ── Returns ──────────────────────────────────────────────────────────────
#     total_return = (equity_curve.iloc[-1] - initial_capital) / initial_capital
#     daily_ret    = equity_curve.pct_change().dropna()

#     # ── Sharpe Ratio (annualized, 252 trading days) ───────────────────────
#     sharpe = (
#         daily_ret.mean() / daily_ret.std() * np.sqrt(252)
#         if daily_ret.std() != 0 else 0.0
#     )

#     # ── Max Drawdown ─────────────────────────────────────────────────────────
#     rolling_max  = equity_curve.cummax()
#     drawdown     = (equity_curve - rolling_max) / rolling_max
#     max_drawdown = drawdown.min()

#     # ── Win / Loss Stats ──────────────────────────────────────────────────────
#     wins   = trades[trades["pnl"] > 0]
#     losses = trades[trades["pnl"] < 0]

#     win_rate      = len(wins) / n_trades
#     gross_profit  = wins["pnl"].sum()   if not wins.empty   else 0.0
#     gross_loss    = abs(losses["pnl"].sum()) if not losses.empty else 0.0
#     profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

#     avg_win  = wins["pnl"].mean()   if not wins.empty   else 0.0
#     avg_loss = losses["pnl"].mean() if not losses.empty else 0.0

#     return {
#         "Total Trades":        n_trades,
#         "Win Rate":            f"{win_rate:.2%}",
#         "Total Return":        f"{total_return:.2%}",
#         "Sharpe Ratio":        round(sharpe, 3),
#         "Max Drawdown":        f"{max_drawdown:.2%}",
#         "Profit Factor":       round(profit_factor, 3),
#         "Avg Win (VND)":       f"{avg_win:,.0f}",
#         "Avg Loss (VND)":      f"{avg_loss:,.0f}",
#         "Gross Profit (VND)":  f"{gross_profit:,.0f}",
#         "Gross Loss (VND)":    f"{gross_loss:,.0f}",
#         "Final Capital (VND)": f"{equity_curve.iloc[-1]:,.0f}",
#     }




import pandas as pd
import numpy as np
import re

def _parse_annual_bars(tf_str: str) -> tuple[float, str]:
    """
    Dịch chuỗi timeframe thành số nến trong 1 năm và tên nhãn hiển thị.
    Hỗ trợ: min/m (phút), h (giờ), d (ngày), w (tuần), mo/month (tháng).
    """
    tf_clean = str(tf_str).strip().lower()
    
    # Tách phần số và phần chữ (VD: "15min" -> val=15, unit="min")
    match = re.match(r"(\d+)([a-zA-Z]+)", tf_clean)
    if not match:
        return 27720, tf_clean # Mặc định rơi về 1min nếu viết sai format

    val = int(match.group(1))
    unit = match.group(2)

    # Phái sinh VN có 270 phút giao dịch/ngày
    if unit in ['m', 'min']:
        bars_per_year = (270 / val) * 252
        label = f"{val}min"
    elif unit in ['h', 'hour', 'hr']:
        bars_per_year = (270 / (val * 60)) * 252
        label = f"{val}h"
    elif unit in ['d', 'day']:
        bars_per_year = 252 / val
        label = f"{val}D"
    elif unit in ['w', 'week', 'wk']:
        bars_per_year = 52 / val
        label = f"{val}W"
    elif unit in ['mo', 'month']:
        bars_per_year = 12 / val
        label = f"{val}M"
    else:
        bars_per_year = 252  # Fallback mặc định
        label = tf_str

    return bars_per_year, label


def compute_metrics(
    equity_curve: pd.Series,
    trades: pd.DataFrame,
    initial_capital: float,
    timeframe_str: str = "15min",   # NHẬN TRỰC TIẾP CHUỖI TỪ CONFIG
) -> dict:
    
    if trades.empty:
        return {"error": "No trades — kiểm tra lại logic entry hoặc filter"}

    n_trades = len(trades)

    # ── Tự động parse timeframe ───────────────────────────────────────────
    bars_per_year, tf_label = _parse_annual_bars(timeframe_str)
    # ──────────────────────────────────────────────────────────────────────

    # ── Return ────────────────────────────────────────────────────────────
    final_eq     = equity_curve.iloc[-1]
    total_return = (final_eq - initial_capital) / initial_capital

    # ── Sharpe (annualized chuẩn xác cho mọi khung) ───────────────────────
    bar_ret = equity_curve.pct_change().dropna()
    sharpe  = (
        bar_ret.mean() / bar_ret.std() * np.sqrt(bars_per_year)
        if bar_ret.std() > 0 else 0.0
    )

    # ── Max Drawdown ──────────────────────────────────────────────────────
    roll_max     = equity_curve.cummax()
    drawdown     = (equity_curve - roll_max) / roll_max
    max_drawdown = drawdown.min()

    # ── Win/Loss ──────────────────────────────────────────────────────────
    wins   = trades[trades["pnl"] > 0]
    losses = trades[trades["pnl"] <= 0]

    win_rate      = len(wins) / n_trades
    gross_profit  = wins["pnl"].sum()        if not wins.empty   else 0.0
    gross_loss    = abs(losses["pnl"].sum()) if not losses.empty else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    avg_win       = wins["pnl"].mean()        if not wins.empty   else 0.0
    avg_loss      = losses["pnl"].mean()      if not losses.empty else 0.0

    # ── Thống kê thêm ─────────────────────────────────────────────────────
    expectancy = trades["pnl"].mean()

    if "entry_time" in trades.columns and "exit_time" in trades.columns:
        hold_mins = (
            pd.to_datetime(trades["exit_time"]) - pd.to_datetime(trades["entry_time"])
        ).dt.total_seconds().mean() / 60
        
        # Nếu hold quá lâu, tự động đổi hiển thị sang Giờ hoặc Ngày cho dễ đọc
        if hold_mins < 60:
            hold_str = f"{hold_mins:.0f} phút"
        elif hold_mins < 1440:
            hold_str = f"{hold_mins/60:.1f} giờ"
        else:
            hold_str = f"{hold_mins/1440:.1f} ngày"
    else:
        hold_str = "N/A"

    return {
        "Total Trades":           n_trades,
        "Win Rate":               f"{win_rate:.2%}",
        "Total Return":           f"{total_return:.2%}",
        f"Sharpe Ratio ({tf_label})": round(sharpe, 3), # Nhãn hiển thị siêu chuẩn
        "Max Drawdown":           f"{max_drawdown:.2%}",
        "Profit Factor":          round(profit_factor, 3),
        "Expectancy / lệnh":      f"{expectancy:,.0f} VND",
        "Avg Hold Time":          hold_str,
        "Avg Win (VND)":          f"{avg_win:,.0f}",
        "Avg Loss (VND)":         f"{avg_loss:,.0f}",
        "Gross Profit (VND)":     f"{gross_profit:,.0f}",
        "Gross Loss (VND)":       f"{gross_loss:,.0f}",
        "Final Capital (VND)":    f"{final_eq:,.0f}",
    }








# """
# metrics.py — Tính hiệu năng chiến lược
# Sửa lỗi Sharpe: annualize theo số bars/năm thực tế (1min = ~27,720 bars/năm)
# thay vì nhân sqrt(252) sai với dữ liệu intraday.
# """
# import pandas as pd
# import numpy as np


# def compute_metrics(
#     equity_curve: pd.Series,
#     trades: pd.DataFrame,
#     initial_capital: float,
#     bars_per_year: int = 27_720,   # 1min: ~252 ngày × ~110 bar/ngày
# ) -> dict:
#     """
#     bars_per_year:
#         1min  → 27_720  (252 × 110)
#         5min  → 5_544   (252 × 22)
#         15min → 1_848   (252 × ~7.3)
#         1day  → 252
#     """
#     if trades.empty:
#         return {"error": "No trades — giảm entry threshold hoặc vol_confirm"}

#     n_trades = len(trades)

#     # ── Return ────────────────────────────────────────────────────────────
#     final_eq     = equity_curve.iloc[-1]
#     total_return = (final_eq - initial_capital) / initial_capital

#     # ── Sharpe (annualized đúng cho intraday) ─────────────────────────────
#     bar_ret = equity_curve.pct_change().dropna()
#     sharpe  = (
#         bar_ret.mean() / bar_ret.std() * np.sqrt(bars_per_year)
#         if bar_ret.std() > 0 else 0.0
#     )

#     # ── Max Drawdown ──────────────────────────────────────────────────────
#     roll_max     = equity_curve.cummax()
#     drawdown     = (equity_curve - roll_max) / roll_max
#     max_drawdown = drawdown.min()

#     # ── Win/Loss ──────────────────────────────────────────────────────────
#     wins   = trades[trades["pnl"] > 0]
#     losses = trades[trades["pnl"] <= 0]

#     win_rate      = len(wins) / n_trades
#     gross_profit  = wins["pnl"].sum()        if not wins.empty   else 0.0
#     gross_loss    = abs(losses["pnl"].sum()) if not losses.empty else 0.0
#     profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
#     avg_win       = wins["pnl"].mean()        if not wins.empty   else 0.0
#     avg_loss      = losses["pnl"].mean()      if not losses.empty else 0.0

#     # ── Thống kê thêm ─────────────────────────────────────────────────────
#     # Expectancy: kỳ vọng lợi nhuận mỗi lệnh
#     expectancy = trades["pnl"].mean()

#     # Avg hold time
#     if "entry_time" in trades.columns and "exit_time" in trades.columns:
#         hold_mins = (
#             pd.to_datetime(trades["exit_time"]) - pd.to_datetime(trades["entry_time"])
#         ).dt.total_seconds().mean() / 60
#         hold_str = f"{hold_mins:.0f} phút"
#     else:
#         hold_str = "N/A"

#     return {
#         "Total Trades":           n_trades,
#         "Win Rate":               f"{win_rate:.2%}",
#         "Total Return":           f"{total_return:.2%}",
#         "Sharpe Ratio (1min)":    round(sharpe, 3),
#         "Max Drawdown":           f"{max_drawdown:.2%}",
#         "Profit Factor":          round(profit_factor, 3),
#         "Expectancy / lệnh":      f"{expectancy:,.0f} VND",
#         "Avg Hold Time":          hold_str,
#         "Avg Win (VND)":          f"{avg_win:,.0f}",
#         "Avg Loss (VND)":         f"{avg_loss:,.0f}",
#         "Gross Profit (VND)":     f"{gross_profit:,.0f}",
#         "Gross Loss (VND)":       f"{gross_loss:,.0f}",
#         "Final Capital (VND)":    f"{final_eq:,.0f}",
#     }