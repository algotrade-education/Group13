

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




# import pandas as pd
# import numpy as np
# from config.config import STRATEGY

# def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
#     # Tham số tối ưu cho chiến dịch 30 lệnh
#     entry_z    = 1.3  # Hạ xuống 1.3 để tăng tần suất (đạt KPI 30 lệnh dễ hơn)
#     exit_z     = 0.2  # Chốt lời nhanh hơn để giữ lợi nhuận
#     atr_mult   = 1.5  # Siết SL chặt hơn để bảo vệ vốn

#     df = df.copy()
#     times = df.index.time
    
#     start_trade = pd.to_datetime("09:15").time()
#     end_trade   = pd.to_datetime("14:20").time()
#     force_exit  = pd.to_datetime("14:35").time()

#     zscores, prices, atrs = df["zscore"].values, df["close"].values, df["atr"].values
#     ema200, rsis = df["ema200"].values, df["rsi"].values
#     volumes, vol_ma = df["volume"].values, df["vol_ma"].values
    
#     positions = np.zeros(len(df))
#     current_pos, entry_price, sl_price = 0, 0, 0

#     for i in range(1, len(df)):
#         z_prev, p_now, trend_prev, rsi_prev = zscores[i-1], prices[i], ema200[i-1], rsis[i-1]
#         atr_prev, cur_time, vol_now, v_ma_now = atrs[i-1], times[i], volumes[i], vol_ma[i]

#         # BÙA CHÚ 1: Né giờ nghỉ trưa (11:15 - 13:00) - Nơi các lệnh thua thường xuất hiện
#         is_lunch = pd.to_datetime("11:15").time() <= cur_time <= pd.to_datetime("13:00").time()
        
#         # BÙA CHÚ 2: Xác nhận Volume - Chỉ đánh khi Von cao hơn 1.2 lần trung bình
#         # Điều này giúp loại bỏ các cú đảo chiều "giả"
#         is_vol_confirmed = vol_now > (v_ma_now * 1.2)

#         if current_pos == 0:
#             if start_trade <= cur_time <= end_trade and not is_lunch:
#                 # LONG: Rẻ + Von nổ + RSI thoát đáy
#                 if z_prev < -entry_z and rsi_prev > 25 and is_vol_confirmed:
#                     current_pos, entry_price = 1, p_now
#                     sl_price = entry_price - (atr_mult * atr_prev)
#                 # SHORT: Đắt + Von nổ + RSI thoát đỉnh
#                 elif z_prev > entry_z and rsi_prev < 75 and is_vol_confirmed:
#                     current_pos, entry_price = -1, p_now
#                     sl_price = entry_price + (atr_mult * atr_prev)

#         elif current_pos == 1:
#             if z_prev >= exit_z or p_now <= sl_price or cur_time >= force_exit:
#                 current_pos = 0 
                
#         elif current_pos == -1:
#             if z_prev <= -exit_z or p_now >= sl_price or cur_time >= force_exit:
#                 current_pos = 0
        
#         positions[i] = current_pos

#     df["signal"] = positions
#     df["trade_action"] = df["signal"].diff().fillna(0)
#     return df






# Mom Mean Lời
# import pandas as pd
# import numpy as np
# from config.config import STRATEGY

# def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
#     # 1. Tham số chiến thuật
#     entry_z    = STRATEGY["entry_threshold"]
#     exit_z     = STRATEGY["exit_threshold"]
#     atr_mult   = 2.0  # Hệ số nhân ATR cho Stop Loss (Thử mức 1.5 - 2.5)

#     df = df.copy()
#     times = df.index.time
    
#     # Khung giờ giao dịch
#     start_trade = pd.to_datetime("09:15").time() # Mở rộng khung giờ một chút
#     end_trade   = pd.to_datetime("14:15").time()
#     force_exit  = pd.to_datetime("14:30").time()

#     # Chuyển data sang numpy để MacBook chạy nhanh hơn
#     zscores = df["zscore"].values
#     prices  = df["close"].values
#     atrs    = df["atr"].values
#     ema200  = df["ema200"].values
#     rsis    = df["rsi"].values
    
#     positions   = np.zeros(len(df))
#     current_pos = 0
#     entry_price = 0
#     sl_price    = 0

#     # 2. Vòng lặp State Machine
#     for i in range(1, len(df)):
#         z_prev     = zscores[i-1]
#         p_now      = prices[i]    # Giá hiện tại để check SL/TP
#         p_prev     = prices[i-1]
#         trend_prev = ema200[i-1]
#         rsi_prev   = rsis[i-1]
#         atr_prev   = atrs[i-1]
#         cur_time   = times[i]

#         # --- LOGIC VÀO LỆNH (ENTRY) ---
#         if current_pos == 0:
#             if start_trade <= cur_time <= end_trade:
#                 # LONG: Xu hướng tăng + Giá rẻ + RSI bắt đầu hồi
#                 if p_prev > trend_prev and z_prev < -entry_z and rsi_prev > 25:
#                     current_pos = 1
#                     entry_price = p_now
#                     sl_price    = entry_price - (atr_mult * atr_prev)
                
#                 # SHORT: Xu hướng giảm + Giá đắt + RSI bắt đầu quay đầu
#                 elif p_prev < trend_prev and z_prev > entry_z and rsi_prev < 75:
#                     current_pos = -1
#                     entry_price = p_now
#                     sl_price    = entry_price + (atr_mult * atr_prev)

#         # --- LOGIC THOÁT LỆNH (EXIT & DYNAMIC SL) ---
#         elif current_pos == 1: # Đang Long
#             # Thoát khi: Z hồi về mục tiêu OR Dính ATR Stop Loss OR Hết giờ
#             if z_prev >= exit_z or p_now <= sl_price or cur_time >= force_exit:
#                 current_pos = 0 
                
#         elif current_pos == -1: # Đang Short
#             if z_prev <= -exit_z or p_now >= sl_price or cur_time >= force_exit:
#                 current_pos = 0
        
#         positions[i] = current_pos

#     df["signal"] = positions
#     df["trade_action"] = df["signal"].diff().fillna(0)
    
#     return df



# #Mommean lỗ
# import pandas as pd
# import numpy as np
# from config.config import STRATEGY

# def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
#     entry = STRATEGY["entry_threshold"]
#     exit_ = STRATEGY["exit_threshold"]
#     stop  = STRATEGY["stop_loss"]

#     df = df.copy()
#     times = df.index.time
#     start_trade = pd.to_datetime("09:30").time()
#     end_trade   = pd.to_datetime("14:15").time()
#     force_exit  = pd.to_datetime("14:30").time()

#     zscores = df["zscore"].values
#     prices  = df["close"].values
#     ema200  = df["ema200"].values # Xu hướng dài hạn
#     positions = np.zeros(len(df))
#     current_pos = 0

#     for i in range(1, len(df)):
#         z_prev = zscores[i-1]
#         p_prev = prices[i-1]
#         trend_prev = ema200[i-1]
#         current_time = times[i]

#         # --- LOGIC VÀO LỆNH (MOMMEAN - HYBRID) ---
#         if current_pos == 0:
#             if start_trade <= current_time <= end_trade:
#                 # Chỉ LONG khi giá đang trên xu hướng tăng (Price > EMA200)
#                 if z_prev < -entry and p_prev > trend_prev:
#                     current_pos = 1
#                 # Chỉ SHORT khi giá đang trên xu hướng giảm (Price < EMA200)
#                 elif z_prev > entry and p_prev < trend_prev:
#                     current_pos = -1

#         # --- LOGIC THOÁT LỆNH (Giữ nguyên) ---
#         elif current_pos == 1:
#             if z_prev >= exit_ or z_prev < -stop or current_time >= force_exit:
#                 current_pos = 0 
                
#         elif current_pos == -1:
#             if z_prev <= -exit_ or z_prev > stop or current_time >= force_exit:
#                 current_pos = 0
        
#         positions[i] = current_pos

#     df["signal"] = positions
#     df["trade_action"] = df["signal"].diff().fillna(0)
#     return df



