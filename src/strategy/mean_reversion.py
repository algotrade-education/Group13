

#Tích hợp ATR Stop Loss vào chiến thuật Mean Reversion 
# -> Lời nhưng không kịp 30 trade 
import pandas as pd
import numpy as np
from Temp.config.config import STRATEGY

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    MomMean Strategy: Mean Reversion + Trend Filter (EMA200) + Momentum (RSI)
    tích hợp ATR Dynamic Stop Loss.
    """
    # 1. Lấy tham số từ config
    entry_z    = STRATEGY["entry_threshold"]
    exit_z     = STRATEGY["exit_threshold"]
    # Hệ số nhân ATR (Thường dùng 2.0 cho VN30F1M nến 5 phút)
    atr_multiplier = 2.0 

    df = df.copy()
    times = df.index.time
    
    # Khung giờ giao dịch chuẩn
    start_trade = pd.to_datetime("09:30").time()
    end_trade   = pd.to_datetime("14:15").time()
    force_exit  = pd.to_datetime("14:30").time()

    # Chuyển đổi dữ liệu sang mảng Numpy để tối ưu tốc độ
    zscores    = df["zscore"].values
    prices     = df["close"].values
    atrs       = df["atr"].values
    ema200     = df["ema200"].values
    rsis       = df["rsi"].values
    
    positions   = np.zeros(len(df))
    current_pos = 0
    entry_price = 0
    sl_price    = 0

    # 2. Vòng lặp State Machine duyệt qua từng nến
    for i in range(1, len(df)):
        z_prev     = zscores[i-1]
        p_now      = prices[i]      # Giá hiện tại để kiểm tra SL
        p_prev     = prices[i-1]
        trend_prev = ema200[i-1]
        rsi_prev   = rsis[i-1]
        atr_prev   = atrs[i-1]
        cur_time   = times[i]

        # --- LOGIC VÀO LỆNH (ENTRY) ---
        if current_pos == 0:
            if start_trade <= cur_time <= end_trade:
                # Điều kiện LONG: Xu hướng tăng + Giá rẻ + RSI hồi phục
                if p_prev > trend_prev and z_prev < -entry_z and rsi_prev > 25:
                    current_pos = 1
                    entry_price = p_now
                    # Cắt lỗ dưới giá vào lệnh một khoảng bằng 2 lần độ biến động (ATR)
                    sl_price    = entry_price - (atr_multiplier * atr_prev)
                
                # Điều kiện SHORT: Xu hướng giảm + Giá đắt + RSI quay đầu
                elif p_prev < trend_prev and z_prev > entry_z and rsi_prev < 75:
                    current_pos = -1
                    entry_price = p_now
                    # Cắt lỗ trên giá vào lệnh một khoảng bằng 2 lần độ biến động (ATR)
                    sl_price    = entry_price + (atr_multiplier * atr_prev)

        # --- LOGIC THOÁT LỆNH (EXIT & DYNAMIC SL) ---
        elif current_pos == 1: # Đang giữ vị thế Long
            # Thoát khi: Z-score hồi về mục tiêu HOẶC Giá chạm Stop Loss HOẶC Hết phiên
            if z_prev >= exit_z or p_now <= sl_price or cur_time >= force_exit:
                current_pos = 0 
                
        elif current_pos == -1: # Đang giữ vị thế Short
            if z_prev <= -exit_z or p_now >= sl_price or cur_time >= force_exit:
                current_pos = 0
        
        positions[i] = current_pos

    # 3. Ghi kết quả vào DataFrame
    df["signal"] = positions
    df["trade_action"] = df["signal"].diff().fillna(0)
    
    return df



