# import pandas as pd
# import numpy as np
# from config.config import STRATEGY

# def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
#     df = df.copy()
    
#     # 1. Dùng bộ số Fibonacci nhanh hơn (8 và 21) để tăng tần suất
#     df['ema_fast'] = df['close'].ewm(span=8, adjust=False).mean()
#     df['ema_slow'] = df['close'].ewm(span=21, adjust=False).mean()
    
#     atr_mult = STRATEGY.get("atr_multiplier", 1.5) # Siết SL chặt để đánh nhiều lệnh
    
#     times = df.index.time
#     start_trade = pd.to_datetime("09:15").time() # Mở sớm hơn 5 phút
#     end_trade   = pd.to_datetime("14:20").time() # Đóng muộn hơn 5 phút
#     force_exit  = pd.to_datetime("14:40").time()

#     prices, atrs, rsi = df["close"].values, df["atr"].values, df["rsi"].values
#     ema_f, ema_s = df["ema_fast"].values, df["ema_slow"].values
    
#     positions = np.zeros(len(df))
#     current_pos, sl_price = 0, 0

#     for i in range(2, len(df)):
#         cur_time, p_now = times[i], prices[i]
        
#         if current_pos == 0:
#             if start_trade <= cur_time <= end_trade:
#                 # LONG: EMA 8 cắt lên 21 + RSI > 48 (Nới lỏng RSI một chút để lấy lệnh)
#                 if ema_f[i-1] > ema_s[i-1] and ema_f[i-2] <= ema_s[i-2] and rsi[i-1] > 48:
#                     current_pos = 1
#                     sl_price = p_now - (atr_mult * atrs[i-1])
                
#                 # SHORT: EMA 8 cắt xuống 21 + RSI < 52
#                 elif ema_f[i-1] < ema_s[i-1] and ema_f[i-2] >= ema_s[i-2] and rsi[i-1] < 52:
#                     current_pos = -1
#                     sl_price = p_now + (atr_mult * atrs[i-1])

#         elif current_pos == 1:
#             # Thoát lệnh khi trend đảo chiều hoặc dính SL
#             if ema_f[i-1] < ema_s[i-1] or p_now <= sl_price or cur_time >= force_exit:
#                 current_pos = 0
                
#         elif current_pos == -1:
#             if ema_f[i-1] > ema_s[i-1] or p_now >= sl_price or cur_time >= force_exit:
#                 current_pos = 0
        
#         positions[i] = current_pos

#     df["signal"] = positions
#     df["trade_action"] = df["signal"].diff().fillna(0)
#     return df



import pandas as pd
import numpy as np
from config.config import STRATEGY

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # 1. Khung 1m nên dùng 10 và 30 để tránh tín hiệu giả (Whipsaw)
    df['ema_fast'] = df['close'].ewm(span=10, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=30, adjust=False).mean()
    
    # ATR 2.0 để Stoploss có không gian thở trên khung 1m
    atr_mult = 2.0 
    
    times = df.index.time
    start_trade = pd.to_datetime("09:00").time() 
    end_trade   = pd.to_datetime("14:25").time() 
    force_exit  = pd.to_datetime("14:40").time()

    prices, atrs, rsi = df["close"].values, df["atr"].values, df["rsi"].values
    ema_f, ema_s = df["ema_fast"].values, df["ema_slow"].values
    
    positions = np.zeros(len(df))
    current_pos, sl_price = 0, 0

    for i in range(2, len(df)):
        cur_time, p_now = times[i], prices[i]
        
        # Khoảng cách giữa 2 EMA để đảm bảo đang có xu hướng rõ rệt
        ema_diff = abs(ema_f[i-1] - ema_s[i-1])
        
        if current_pos == 0:
            if start_trade <= cur_time <= end_trade:
                # LONG: EMA 10 > 30 VÀ (Vừa cắt LÊN HOẶC Giá chạm EMA 30 rồi rút chân)
                is_crossover_long = ema_f[i-1] > ema_s[i-1] and ema_f[i-2] <= ema_s[i-2]
                is_pullback_long = ema_f[i-1] > ema_s[i-1] and p_now <= ema_f[i-1] and ema_diff > 0.3
                
                if (is_crossover_long or is_pullback_long) and rsi[i-1] > 45:
                    current_pos = 1
                    sl_price = p_now - (atr_mult * atrs[i-1])
                
                # SHORT: EMA 10 < 30 VÀ (Vừa cắt XUỐNG HOẶC Giá hồi về EMA 30 rồi rụng)
                is_crossover_short = ema_f[i-1] < ema_s[i-1] and ema_f[i-2] >= ema_s[i-2]
                is_pullback_short = ema_f[i-1] < ema_s[i-1] and p_now >= ema_f[i-1] and ema_diff > 0.3
                
                if (is_crossover_short or is_pullback_short) and rsi[i-1] < 55:
                    current_pos = -1
                    sl_price = p_now + (atr_mult * atrs[i-1])

        elif current_pos == 1:
            # Thoát khi EMA cắt ngược hoặc dính SL hoặc hết giờ
            if ema_f[i-1] < ema_s[i-1] or p_now <= sl_price or cur_time >= force_exit:
                current_pos = 0
                
        elif current_pos == -1:
            if ema_f[i-1] > ema_s[i-1] or p_now >= sl_price or cur_time >= force_exit:
                current_pos = 0
        
        positions[i] = current_pos

    df["signal"] = positions
    df["trade_action"] = df["signal"].diff().fillna(0)
    return df


# Lời (30/10 - Không kịp thời gian)
# import pandas as pd
# import numpy as np
# from config.config import STRATEGY

# def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
#     """
#     Trend Following: EMA 10/30 Cross + RSI 50 Filter.
#     Tối ưu cho VN30F1M nến 5 phút - Tần suất cao, ăn sóng dài.
#     """
#     df = df.copy()
    
#     # 1. Tính toán EMA nhanh và chậm
#     # df['ema_fast'] = df['close'].ewm(span=10, adjust=False).mean()
#     # df['ema_slow'] = df['close'].ewm(span=30, adjust=False).mean()
#     # Sửa span để tăng tần suất vào lệnh
#     df['ema_fast'] = df['close'].ewm(span=9, adjust=False).mean()
#     df['ema_slow'] = df['close'].ewm(span=21, adjust=False).mean()
    
#     # 2. Lấy tham số
#     atr_mult = STRATEGY.get("atr_multiplier", 2.0)
    
#     times = df.index.time
#     # Khung giờ 'săn trend': 09:20 - 14:15
#     start_trade = pd.to_datetime("09:20").time()
#     end_trade   = pd.to_datetime("14:15").time()
#     force_exit  = pd.to_datetime("14:35").time()

#     prices = df["close"].values
#     atrs   = df["atr"].values
#     rsi    = df["rsi"].values
#     ema_f  = df["ema_fast"].values
#     ema_s  = df["ema_slow"].values
    
#     positions = np.zeros(len(df))
#     current_pos = 0
#     sl_price = 0

#     for i in range(2, len(df)): # Bắt đầu từ 2 để check nến i-1 và i-2
#         cur_time = times[i]
#         p_now = prices[i]
        
#         # --- LOGIC VÀO LỆNH (Giao cắt EMA) ---
#         if current_pos == 0:
#             if start_trade <= cur_time <= end_trade:
#                 # LONG: EMA10 cắt lên EMA30 và RSI trên 50 (Xác nhận trend tăng)
#                 if ema_f[i-1] > ema_s[i-1] and ema_f[i-2] <= ema_s[i-2] and rsi[i-1] > 50:
#                     current_pos = 1
#                     sl_price = p_now - (atr_mult * atrs[i-1])
                
#                 # SHORT: EMA10 cắt xuống EMA30 và RSI dưới 50 (Xác nhận trend giảm)
#                 elif ema_f[i-1] < ema_s[i-1] and ema_f[i-2] >= ema_s[i-2] and rsi[i-1] < 50:
#                     current_pos = -1
#                     sl_price = p_now + (atr_mult * atrs[i-1])

#         # --- LOGIC THOÁT LỆNH ---
#         elif current_pos == 1:
#             # Thoát khi EMA cắt ngược lại HOẶC dính SL HOẶC hết giờ
#             if ema_f[i-1] < ema_s[i-1] or p_now <= sl_price or cur_time >= force_exit:
#                 current_pos = 0
                
#         elif current_pos == -1:
#             if ema_f[i-1] > ema_s[i-1] or p_now >= sl_price or cur_time >= force_exit:
#                 current_pos = 0
        
#         positions[i] = current_pos

#     df["signal"] = positions
#     df["trade_action"] = df["signal"].diff().fillna(0)
#     return df