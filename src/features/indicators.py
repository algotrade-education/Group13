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


# def add_features(df: pd.DataFrame, window: int = 60) -> pd.DataFrame:
#     df = df.copy()

#     # Chỉ báo cốt lõi (dùng cho cả ORB và MeanRev)
#     df["rsi"]    = compute_rsi(df["close"], 14)
#     df["atr"]    = compute_atr(df, 14)
#     df["vol_ma"] = df["volume"].rolling(window=20).mean()   # ← ORB cần cái này

#     # Chỉ báo Mean Reversion (giữ lại để tương thích backtest cũ)
#     df["zscore"]   = compute_zscore(df["close"], window)
#     df["ema200"]   = df["close"].ewm(span=200, adjust=False).mean()

#     # Bollinger Bands (dùng cho chart)
#     mid = df["close"].rolling(window).mean()
#     std = df["close"].rolling(window).std()
#     df["bb_mid"]   = mid
#     df["bb_upper"] = mid + 2 * std
#     df["bb_lower"] = mid - 2 * std

#     df.dropna(inplace=True)
#     return df


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


# Code gần nhất
# import pandas as pd
# import numpy as np

# def compute_zscore(series: pd.Series, window: int) -> pd.Series:
#     mean = series.rolling(window).mean()
#     std  = series.rolling(window).std()
#     return (series - mean) / std

# def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
#     """Relative Strength Index - Xác nhận lực đảo chiều."""
#     delta = series.diff()
#     gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
#     loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
#     rs = gain / loss
#     return 100 - (100 / (1 + rs))

# def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
#     """Average True Range - Đo lường biến động để đặt Stop Loss động."""
#     high_low = df['high'] - df['low']
#     high_close = np.abs(df['high'] - df['close'].shift())
#     low_close = np.abs(df['low'] - df['close'].shift())
#     ranges = pd.concat([high_low, high_close, low_close], axis=1)
#     true_range = np.max(ranges, axis=1)
#     return true_range.rolling(window=period).mean()

# def add_features(df: pd.DataFrame, window: int = 60) -> pd.DataFrame:
#     df = df.copy()

#     # 1. Chỉ báo cốt lõi
#     df["zscore"] = compute_zscore(df["close"], window)
#     df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
#     df["rsi"] = compute_rsi(df["close"], 14)
#     df["atr"] = compute_atr(df, 14)

#     # 2. XÁC NHẬN KHỐI LƯỢNG (Bí mật của repo MomMean xịn)
#     df["vol_ma"] = df["volume"].rolling(window=20).mean()

#     # 3. Bollinger Bands (Để vẽ biểu đồ)
#     mid = df["close"].rolling(window).mean()
#     std = df["close"].rolling(window).std()
#     df["bb_mid"], df["bb_upper"], df["bb_lower"] = mid, mid + 2*std, mid - 2*std

#     df.dropna(inplace=True)
#     return df






# # Monmean

# import pandas as pd
# import numpy as np


# def compute_zscore(series: pd.Series, window: int) -> pd.Series:
#     """
#     Rolling Z-score:  z = (price - rolling_mean) / rolling_std
#     """
#     mean = series.rolling(window).mean()
#     std  = series.rolling(window).std()
#     return (series - mean) / std


# def compute_bollinger_bands(
#     series: pd.Series,
#     window: int,
#     num_std: float = 2.0,
# ) -> tuple[pd.Series, pd.Series, pd.Series]:
#     """
#     Bollinger Bands.

#     Returns:
#         (mid, upper, lower)
#     """
#     mid   = series.rolling(window).mean()
#     std   = series.rolling(window).std()
#     upper = mid + num_std * std
#     lower = mid - num_std * std
#     return mid, upper, lower


# def add_features(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
#     """
#     Thêm tất cả features vào OHLCV DataFrame.

#     Features được thêm:
#         - zscore:    Rolling Z-score của close price
#         - bb_mid:    Bollinger Band middle
#         - bb_upper:  Bollinger Band upper
#         - bb_lower:  Bollinger Band lower
#         - spread:    close - bb_mid
#         - returns:   Pct change của close
#     """
#     df = df.copy()

#     df["zscore"] = compute_zscore(df["close"], window)

#     df["bb_mid"], df["bb_upper"], df["bb_lower"] = compute_bollinger_bands(
#         df["close"], window
#     )

#     df["spread"]  = df["close"] - df["bb_mid"]
#     df["returns"] = df["close"].pct_change()

#     df.dropna(inplace=True)
#     return df
