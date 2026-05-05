"""
Data Loader cho VNF301M Continuous Contract.

Flow:
    1. Dựa vào ROLL_SCHEDULE → xác định contract nào dùng trong khoảng ngày
    2. Query tick data từ quote.matched + quote.total
    3. Resample tick → OHLCV theo timeframe cấu hình
    4. Ghép (stitch) các contract lại thành continuous series
"""

import psycopg2
import pandas as pd
from config.config import DB_CONFIG, ROLL_SCHEDULE, STRATEGY
from datetime import datetime, timedelta
import re

# ── Connection ────────────────────────────────────────────────────────────────

# def get_connection():
#     """Tạo psycopg v3 connection."""
#     return psycopg.connect(
#         host=DB_CONFIG["host"],
#         port=DB_CONFIG["port"],
#         dbname=DB_CONFIG["database"],
#         user=DB_CONFIG["user"],
#         password=DB_CONFIG["password"],
#     )

def get_connection():
    """Tạo psycopg2 connection."""
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )

# ── Roll Schedule Helper ──────────────────────────────────────────────────────

def get_contracts_in_range(start_date: str, end_date: str) -> list[dict]:
    """
    Lọc ROLL_SCHEDULE để lấy danh sách contract cần query
    trong khoảng [start_date, end_date].

    Returns:
        List of {ticker, query_start, query_end}
    """
    start = pd.Timestamp(start_date)
    end   = pd.Timestamp(end_date)

    contracts = []
    for roll_start, roll_end, ticker in ROLL_SCHEDULE:
        rs = pd.Timestamp(roll_start)
        re = pd.Timestamp(roll_end)

        # Overlap check
        if rs <= end and re >= start:
            contracts.append({
                "ticker":       ticker,
                "query_start":  max(rs, start).strftime("%Y-%m-%d"),
                "query_end":    min(re, end).strftime("%Y-%m-%d 23:59:59"),
            })

    return contracts


# ── Tick Query ─────────────────────────────────────────────────────────────────

def _query_ticks(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    Query tick data từ quote.matched JOIN quote.total.

    Returns:
        DataFrame columns=[datetime, price, volume]
    """
    query = """
        SELECT
            m.datetime,
            m.price,
            COALESCE(v.quantity, 0) AS volume
        FROM "quote"."matched" m
        LEFT JOIN "quote"."total" v
            ON  m.tickersymbol = v.tickersymbol
            AND m.datetime     = v.datetime
        WHERE m.tickersymbol = %s
          AND m.datetime BETWEEN %s AND %s
        ORDER BY m.datetime ASC
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (ticker, start, end))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

    if not rows:
        print(f"  ⚠️  Không có data cho {ticker} ({start} → {end})")
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=cols)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["price"]    = df["price"].astype(float)
    df["volume"]   = df["volume"].astype(float)
    df.set_index("datetime", inplace=True)

    print(f"  📥 {ticker}: {len(df):>8,} ticks | {start[:10]} → {end[:10]}")
    return df


# ── Resample Tick → OHLCV ─────────────────────────────────────────────────────

def _resample_ohlcv(tick_df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """
    Resample tick data thành OHLCV bars.

    Args:
        tick_df:   DataFrame với index=datetime, columns=[price, volume]
        timeframe: Pandas offset string, ví dụ '1h', '15min', '1D', '5min'

    Returns:
        DataFrame columns=[open, high, low, close, volume]
    """
    # Chỉ lấy trong giờ giao dịch phái sinh: 09:00 – 14:45
    tick_df = tick_df.between_time("09:00", "14:45")

    ohlcv = pd.DataFrame()
    ohlcv["open"]   = tick_df["price"].resample(timeframe).first()
    ohlcv["high"]   = tick_df["price"].resample(timeframe).max()
    ohlcv["low"]    = tick_df["price"].resample(timeframe).min()
    ohlcv["close"]  = tick_df["price"].resample(timeframe).last()
    ohlcv["volume"] = tick_df["volume"].resample(timeframe).sum()

    # Bỏ các bar rỗng (ngoài giờ giao dịch / ngày nghỉ)
    ohlcv.dropna(subset=["open", "close"], inplace=True)

    return ohlcv


# ── Main Loader ───────────────────────────────────────────────────────────────

def load_ohlcv(
    symbol: str,
    start_date: str,
    end_date: str,
    timeframe: str = None,
) -> pd.DataFrame:
    """
    Load OHLCV continuous contract data cho VNF301M.

    Flow:
        1. Xác định các contract cần dùng từ ROLL_SCHEDULE
        2. Query tick data từng contract
        3. Resample từng contract thành OHLCV
        4. Stitch lại thành continuous series

    Args:
        symbol:     Không dùng trực tiếp, chỉ để log. Dùng ROLL_SCHEDULE.
        start_date: 'YYYY-MM-DD'
        end_date:   'YYYY-MM-DD'
        timeframe:  Pandas offset string. Mặc định lấy từ config.

    Returns:
        DataFrame với index=datetime, columns=[open, high, low, close, volume]
    """
    tf = timeframe or STRATEGY["timeframe"]

    print(f"\n[Loader] 🚀 Loading {symbol} | {start_date} → {end_date} | TF={tf}")

    contracts = get_contracts_in_range(start_date, end_date)
    if not contracts:
        raise ValueError(f"Không có contract nào trong ROLL_SCHEDULE cho {start_date} → {end_date}")

    print(f"[Loader] 📋 Sẽ query {len(contracts)} contract(s):")

    ohlcv_pieces = []

    for c in contracts:
        # 1. Query ticks
        ticks = _query_ticks(c["ticker"], c["query_start"], c["query_end"])
        if ticks.empty:
            continue

        # 2. Resample → OHLCV
        ohlcv = _resample_ohlcv(ticks, tf)
        if ohlcv.empty:
            continue

        ohlcv_pieces.append(ohlcv)

    if not ohlcv_pieces:
        raise ValueError("Không load được data. Kiểm tra lại ROLL_SCHEDULE và kết nối DB.")

    # 3. Stitch tất cả contracts lại
    df = pd.concat(ohlcv_pieces).sort_index()
    df = df[~df.index.duplicated(keep="first")]  # Bỏ duplicate index tại điểm roll

    print(f"\n[Loader] ✅ Tổng cộng {len(df):,} bars | {df.index[0]} → {df.index[-1]}")
    return df

# class DataLoader:
#     """Class này main_live.py sẽ dùng để lấy data real-time"""
#     def __init__(self):
#         pass

#     def get_latest_data(self, symbol, count=50):
#         # Lấy data 3 ngày gần nhất để đảm bảo đủ 50 nến (trừ ngày nghỉ)
#         end_dt = datetime.now()
#         start_dt = end_dt - timedelta(days=5)
        
#         # Gọi lại chính hàm load_ohlcv ở phía trên
#         df = load_ohlcv(symbol, start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d"))
#         return df.tail(count)

class DataLoader:
    """Class này main_live.py sẽ dùng để lấy data real-time một cách thông minh"""
    def __init__(self):
        pass

    def get_latest_data(self, symbol, count=250):
        # 1. Tự động đọc timeframe từ config
        tf_str = str(STRATEGY.get("timeframe", "15min")).strip().lower()
        
        # 2. Bóc tách số và đơn vị (VD: "15min" -> 15 và "min", "1h" -> 1 và "h")
        match = re.match(r"(\d+)([a-zA-Z]+)", tf_str)
        if match:
            val = int(match.group(1))
            unit = match.group(2)
            
            # Quy đổi tất cả ra phút để dễ tính toán
            if unit in ['h', 'hour', 'hr']:
                tf_minutes = val * 60
            elif unit in ['d', 'day']:
                tf_minutes = val * 270  # 1 ngày phái sinh có 270 phút
            elif unit in ['w', 'week', 'wk']:
                tf_minutes = val * 270 * 5  # 1 tuần có ~5 ngày giao dịch
            elif unit in ['mo', 'month']:
                tf_minutes = val * 270 * 22 # 1 tháng có ~22 ngày giao dịch
            else:
                tf_minutes = val # Mặc định là phút (m, min)
        else:
            tf_minutes = 15 # Fallback an toàn nếu lỡ gõ sai format

        # 3. Tính số nến trong 1 ngày giao dịch
        bars_per_day = 270 / tf_minutes
        if bars_per_day <= 0:
            bars_per_day = 1 # Tránh lỗi chia cho 0 với khung quá lớn

        # 4. Tính số ngày lịch cần lùi lại (Nhân hệ số 1.5 để trừ hao T7, CN và ngày lễ)
        days_needed = int((count / bars_per_day) * 1.5) + 1

        # 5. Xác định mốc thời gian lấy dữ liệu
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days_needed)
        
        # Gọi lại hàm load_ohlcv (đã có sẵn ở trên)
        df = load_ohlcv(
            symbol=symbol, 
            start_date=start_dt.strftime("%Y-%m-%d"), 
            end_date=end_dt.strftime("%Y-%m-%d")
        )
        
        # 6. Cắt đúng số lượng nến yêu cầu trả về cho bot
        return df.tail(count)

# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Test loader trực tiếp: python src/data/loader.py"""
    df = load_ohlcv(
        symbol     = "VNF301M",
        start_date = "2023-10-01",
        end_date   = "2025-10-31",
        timeframe  = "15min",
    )
    print("\n📊 Preview OHLCV:")
    print(df.head(10).to_string())
    print(f"\nShape: {df.shape}")
    print(f"Columns: {list(df.columns)}")





