

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
