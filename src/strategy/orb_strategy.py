"""
ORB + ATR Trailing Stop Strategy for VN30F1M  (v2)
===================================================
- Xác định High/Low của 30 phút đầu phiên (09:00-09:30) làm ORB
- Vào LONG khi phá High / SHORT khi phá Low + volume xác nhận
- ATR Stop Loss rộng (×3.5) để chịu noise nến 1min
- Trailing Stop chỉ kích hoạt sau khi lãi >= 1×ATR (không bị quét sớm)
- Tối đa 1 LONG + 1 SHORT mỗi ngày (tránh over-trade sau khi dính SL)
"""

import pandas as pd
import numpy as np


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    times   = df.index.time
    prices  = df["close"].values
    highs   = df["high"].values
    lows    = df["low"].values
    volumes = df["volume"].values
    atrs    = df["atr"].values
    vol_ma  = df["vol_ma"].values

    # ── Tham số ──────────────────────────────────────────────────────────
    atr_mult_sl    = 3.5   # SL ban đầu — đủ rộng cho noise 1min
    atr_mult_trail = 3.0   # Trailing stop khi đã có lãi
    atr_activate   = 1.0   # Trailing chỉ bật sau khi lãi >= 1×ATR
    vol_confirm    = 1.1   # Volume phải > 110% MA20

    orb_start   = pd.to_datetime("09:00").time()
    orb_end     = pd.to_datetime("09:30").time()
    trade_start = pd.to_datetime("09:30").time()
    trade_end   = pd.to_datetime("11:15").time()
    noon_start  = pd.to_datetime("11:20").time()
    noon_end    = pd.to_datetime("13:05").time()
    pm_start    = pd.to_datetime("13:05").time()
    force_exit  = pd.to_datetime("14:30").time()

    positions    = np.zeros(len(df))
    current_pos  = 0
    sl_price     = 0.0
    trail_price  = 0.0
    entry_price  = 0.0
    trail_active = False

    # ── Xây dựng ORB High/Low từng ngày ─────────────────────────────────
    dates    = df.index.date
    orb_high = {}
    orb_low  = {}
    for i, (t, d) in enumerate(zip(times, dates)):
        if orb_start <= t < orb_end:
            orb_high[d] = max(orb_high.get(d, -np.inf), highs[i])
            orb_low[d]  = min(orb_low.get(d,  np.inf), lows[i])

    # ── State Machine ─────────────────────────────────────────────────────
    prev_day       = None
    day_long_done  = False
    day_short_done = False

    for i in range(1, len(df)):
        t      = times[i]
        d      = dates[i]
        p_now  = prices[i]
        p_prev = prices[i - 1]
        atr    = max(atrs[i - 1], 0.5)
        vol_now = volumes[i]
        v_ma    = max(vol_ma[i], 1.0)

        # Reset đầu ngày mới
        if d != prev_day:
            day_long_done  = False
            day_short_done = False
            prev_day = d

        day_orb_high = orb_high.get(d)
        day_orb_low  = orb_low.get(d)
        is_vol_ok    = vol_now > (v_ma * vol_confirm)

        in_morning   = trade_start <= t <= trade_end
        in_afternoon = pm_start    <= t <  force_exit
        is_noon      = noon_start  <= t <  noon_end
        can_enter    = (in_morning or in_afternoon) and not is_noon

        # ── Quản lý lệnh đang mở ─────────────────────────────────────────
        if current_pos == 1:
            # Bật trailing sau khi lãi >= 1×ATR
            if not trail_active and p_now >= entry_price + atr_activate * atr:
                trail_active = True
                trail_price  = p_now - atr_mult_trail * atr

            if trail_active:
                trail_price = max(trail_price, p_now - atr_mult_trail * atr)

            hit_sl    = p_now <= sl_price
            hit_trail = trail_active and p_now <= trail_price
            force     = t >= force_exit or is_noon

            if hit_sl or hit_trail or force:
                current_pos = 0
                sl_price = trail_price = entry_price = 0.0
                trail_active = False

        elif current_pos == -1:
            if not trail_active and p_now <= entry_price - atr_activate * atr:
                trail_active = True
                trail_price  = p_now + atr_mult_trail * atr

            if trail_active:
                trail_price = min(trail_price, p_now + atr_mult_trail * atr)

            hit_sl    = p_now >= sl_price
            hit_trail = trail_active and p_now >= trail_price
            force     = t >= force_exit or is_noon

            if hit_sl or hit_trail or force:
                current_pos = 0
                sl_price = trail_price = entry_price = 0.0
                trail_active = False

        # ── Vào lệnh mới ─────────────────────────────────────────────────
        if current_pos == 0 and can_enter and day_orb_high and day_orb_low:
            orb_range = day_orb_high - day_orb_low
            # Bỏ qua ngày ORB quá hẹp hoặc quá rộng
            if orb_range < 0.5 or orb_range > 25:
                positions[i] = 0
                continue

            # LONG breakout
            if (not day_long_done
                    and p_prev <= day_orb_high
                    and p_now  >  day_orb_high
                    and is_vol_ok):
                current_pos  = 1
                entry_price  = p_now
                sl_price     = p_now - atr_mult_sl * atr
                trail_price  = sl_price
                trail_active = False
                day_long_done = True

            # SHORT breakout
            elif (not day_short_done
                    and p_prev >= day_orb_low
                    and p_now  <  day_orb_low
                    and is_vol_ok):
                current_pos   = -1
                entry_price   = p_now
                sl_price      = p_now + atr_mult_sl * atr
                trail_price   = sl_price
                trail_active  = False
                day_short_done = True

        positions[i] = current_pos

    df["signal"]       = positions
    df["trade_action"] = df["signal"].diff().fillna(0)
    return df