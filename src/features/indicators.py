"""
indicators.py — Tính toán tất cả chỉ báo kỹ thuật
Hỗ trợ cả Mean Reversion và ORB strategy
"""
import pandas as pd
import numpy as np


def compute_zscore(series: pd.Series, window: int) -> pd.Series:
    mean = series.rolling(window).mean()
    std  = series.rolling(window).std()
    return (series - mean) / std


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs    = gain / loss
    return 100 - (100 / (1 + rs))


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low   = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift())
    low_close  = np.abs(df["low"]  - df["close"].shift())
    tr         = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()




def add_features(df: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    df = df.copy()

    # 1. Các chỉ báo cốt lõi
    df["rsi"]    = compute_rsi(df["close"], 14)
    df["atr"]    = compute_atr(df, 14)
    df["vol_ma"] = df["volume"].rolling(window=20).mean()

    # 2. THÊM VÀO ĐÂY: Tính EMA Fast (10) và EMA Slow (30) để sửa lỗi KeyError
    df["ema_fast"] = df["close"].ewm(span=10, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=30, adjust=False).mean()

    # 3. Các chỉ báo Mean Reversion (Giữ nguyên theo code của bạn)
    df["zscore"]   = compute_zscore(df["close"], window)
    df["ema200"]   = df["close"].ewm(span=200, adjust=False).mean()

    # 4. Bollinger Bands (dùng cho chart)
    mid = df["close"].rolling(window).mean()
    std = df["close"].rolling(window).std()
    df["bb_mid"]   = mid
    df["bb_upper"] = mid + 2 * std
    df["bb_lower"] = mid - 2 * std

    df.dropna(inplace=True)
    return df
