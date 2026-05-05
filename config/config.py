# import os
# from dotenv import load_dotenv

# load_dotenv()

# # ── Paper Trading ──────────────────────────────────────────────────────────────
# # PAPER_TRADE = {
# #     "username":       "Group13",
# #     "password":       os.getenv("PAPER_TRADE_PASSWORD", "yCr8g4w0tLuT"),
# #     "trader_id":      "f2c11b00bf3d41fca072225f328ce98e",
# #     "rest_base_url":  "https://papertrade.algotrade.vn/accounting",
# #     "fix_host":       "papertrade.algotrade.vn",
# #     "fix_port":       5001,
# #     "sender_comp_id": "f2c11b00bf3d41fca072225f328ce98e",
# #     "target_comp_id": "SERVER",
# # }

# PAPER_TRADE = {
#     "username":       "Group13",
#     "password":       os.getenv("PAPER_TRADE_PASSWORD", "yCr8g4w0tLuT"),
#     "trader_id":      "main",  # <--- ĐỔI TỪ MÃ DÀI THÀNH "main"
#     "rest_base_url":  "https://papertrade.algotrade.vn/accounting",
#     "fix_host":       "papertrade.algotrade.vn",
#     "fix_port":       5001,
#     "sender_comp_id": "f2c11b00bf3d41fca072225f328ce98e", # GIỮ NGUYÊN MÃ DÀI Ở ĐÂY
#     "target_comp_id": "SERVER",
# }

# # ── Database ───────────────────────────────────────────────────────────────────
# DB_CONFIG = {
#     "host":     "api.algotrade.vn",
#     "port":     5432,
#     "database": "algotradeDB",
#     "user":     "cs408_2026",
#     "password": "xaHfeq-gesfof-hance2",
# }

# # ── Continuous Contract Roll Schedule (VNF301M) ────────────────────────────────
# # Hợp đồng VN30F roll vào ngày thứ 6 sau ngày đáo hạn (thứ 5 tuần 3 mỗi tháng)
# # Key = ngày bắt đầu dùng contract đó, Value = ticker symbol
# ROLL_SCHEDULE = [
#     ("2023-01-01", "2023-01-19", "VN30F2301"),
#     ("2023-01-20", "2023-02-16", "VN30F2302"),
#     ("2023-02-17", "2023-03-16", "VN30F2303"),
#     ("2023-03-17", "2023-04-20", "VN30F2304"),
#     ("2023-04-21", "2023-05-18", "VN30F2305"),
#     ("2023-05-19", "2023-06-15", "VN30F2306"),
#     ("2023-06-16", "2023-07-20", "VN30F2307"),
#     ("2023-07-21", "2023-08-17", "VN30F2308"),
#     ("2023-08-18", "2023-09-21", "VN30F2309"),
#     ("2023-09-22", "2023-10-19", "VN30F2310"),
#     ("2023-10-20", "2023-11-16", "VN30F2311"),
#     ("2023-11-17", "2023-12-21", "VN30F2312"),
#     ("2023-12-22", "2024-01-18", "VN30F2401"),
#     ("2024-01-19", "2024-02-22", "VN30F2402"),
#     ("2024-02-23", "2024-03-21", "VN30F2403"),
#     ("2024-03-22", "2024-04-18", "VN30F2404"),
#     ("2024-04-19", "2024-05-16", "VN30F2405"),
#     ("2024-05-17", "2024-06-20", "VN30F2406"),
#     ("2024-06-21", "2024-07-18", "VN30F2407"),
#     ("2024-07-19", "2024-08-15", "VN30F2408"),
#     ("2024-08-16", "2024-09-19", "VN30F2409"),
#     ("2024-09-20", "2024-10-17", "VN30F2410"),
#     ("2024-10-18", "2024-11-21", "VN30F2411"),
#     ("2024-11-22", "2024-12-31", "VN30F2412"),
#     # Tiếp nối từ VN30F2412...
#     ("2025-01-01", "2025-01-16", "VN30F2501"),
#     ("2025-01-17", "2025-02-20", "VN30F2502"),
#     ("2025-02-21", "2025-03-20", "VN30F2503"),
#     ("2025-03-21", "2025-04-17", "VN30F2504"),
#     ("2025-04-18", "2025-05-15", "VN30F2505"),
#     ("2025-05-16", "2025-06-19", "VN30F2506"),
#     ("2025-06-20", "2025-07-17", "VN30F2507"),
#     ("2025-07-18", "2025-08-21", "VN30F2508"),
#     ("2025-08-22", "2025-09-18", "VN30F2509"),
#     ("2025-09-19", "2025-10-16", "VN30F2510"),
#     ("2025-10-17", "2025-11-20", "VN30F2511"),
#     ("2025-11-21", "2025-12-18", "VN30F2512"),
#     ("2025-12-19", "2026-01-15", "VN30F2601"),
#     ("2026-01-16", "2026-02-19", "VN30F2602"),
#     ("2026-02-20", "2026-03-19", "VN30F2603"),
#     ("2026-03-20", "2026-04-16", "VN30F2604"), # Đây là hợp đồng bạn sẽ đánh từ Thứ Hai
#     ("2026-04-17", "2026-05-21", "VN30F2605"),
# ]

# # ── Strategy MomMean 22 lệnh 6 tháng Parameters ────────────────────────────────────────────────────────
# STRATEGY = {
#     "symbol":            "VNF301M",
#     "timeframe":         "15min",     # Khung thời gian tối ưu cho MomMean
#     "window":            60,         # ~5 tiếng giao dịch, giúp EMA và Z-score ổn định
#     "entry_threshold":   1.8,        # Ngưỡng vào lệnh "Sniper" (Bắn tỉa)
#     "exit_threshold":    0.0,        # Gồng lãi sang dải BB đối diện để ăn sóng dài
#     "stop_loss":         3.5,        # Ngưỡng bảo vệ Z-score (phòng hờ cho ATR SL)
#     "contract_size":     100_000,    # VND mỗi điểm chỉ số
#     "atr_multiplier":    2.0,        # Hệ số nhân cho Stop Loss động (đã code trong strategy)
# }

# #  # ── Strategy Parameters ────────────────────────────────────────────────────────
# # STRATEGY = {
# #     "symbol":            "HNXDS:VN30F2604",
# #     "timeframe":         "1min",
# #     "window":            150,       # Thêm lại dòng này để fix lỗi KeyError
# #     "entry_threshold":   0,        # Thêm để run_backtest.py không báo lỗi khi in
# #     "exit_threshold":    0,        # Thêm để run_backtest.py không báo lỗi khi in
# #     "stop_loss":         2.0,      
# #     "atr_multiplier":    2.0,      # Hệ số cho Trend Following
# #     "contract_size":     100_000,
# #     "target_qty_unit": 3       # Số lượng hợp đồng mỗi lệnh (có thể điều chỉnh để test)
# # }

# # Đừng quên kiểm tra BACKTEST periods để xem kết quả năm 2024 có xanh không nhé

# # ── Backtest Periods ───────────────────────────────────────────────────────────
# BACKTEST = {
#     "insample_start":   "2023-01-01",
#     "insample_end":     "2024-06-30",
#     "outsample_start":  "2024-07-01",
#     "outsample_end":    "2024-12-31",
#     "initial_capital":  500_000_000,
#     "commission":       35_000,
# }



# TELEGRAM = {
#     "token": "8667107316:AAEnRi1gpMUmrW91WONTuGZNLlmm9_ZF4Hc",
#     "chat_id": "5771649786" # Ví dụ: "-100123456789"
# }






import os
from dotenv import load_dotenv

load_dotenv()

# ── Paper Trading ──────────────────────────────────────────────────────────────
PAPER_TRADE = {
    "username":       "Group13",
    "password":       os.getenv("PAPER_TRADE_PASSWORD", "yCr8g4w0tLuT"),
    "trader_id":      "main",
    "rest_base_url":  "https://papertrade.algotrade.vn/accounting",
    "fix_host":       "papertrade.algotrade.vn",
    "fix_port":       5001,
    "sender_comp_id": "f2c11b00bf3d41fca072225f328ce98e",
    "target_comp_id": "SERVER",
}

# ── Database ───────────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     "api.algotrade.vn",
    "port":     5432,
    "database": "algotradeDB",
    "user":     "cs408_2026",
    "password": "xaHfeq-gesfof-hance2",
}

# ── Roll Schedule ──────────────────────────────────────────────────────────────
ROLL_SCHEDULE = [
    ("2023-01-01", "2023-01-19", "VN30F2301"),
    ("2023-01-20", "2023-02-16", "VN30F2302"),
    ("2023-02-17", "2023-03-16", "VN30F2303"),
    ("2023-03-17", "2023-04-20", "VN30F2304"),
    ("2023-04-21", "2023-05-18", "VN30F2305"),
    ("2023-05-19", "2023-06-15", "VN30F2306"),
    ("2023-06-16", "2023-07-20", "VN30F2307"),
    ("2023-07-21", "2023-08-17", "VN30F2308"),
    ("2023-08-18", "2023-09-21", "VN30F2309"),
    ("2023-09-22", "2023-10-19", "VN30F2310"),
    ("2023-10-20", "2023-11-16", "VN30F2311"),
    ("2023-11-17", "2023-12-21", "VN30F2312"),
    ("2023-12-22", "2024-01-18", "VN30F2401"),
    ("2024-01-19", "2024-02-22", "VN30F2402"),
    ("2024-02-23", "2024-03-21", "VN30F2403"),
    ("2024-03-22", "2024-04-18", "VN30F2404"),
    ("2024-04-19", "2024-05-16", "VN30F2405"),
    ("2024-05-17", "2024-06-20", "VN30F2406"),
    ("2024-06-21", "2024-07-18", "VN30F2407"),
    ("2024-07-19", "2024-08-15", "VN30F2408"),
    ("2024-08-16", "2024-09-19", "VN30F2409"),
    ("2024-09-20", "2024-10-17", "VN30F2410"),
    ("2024-10-18", "2024-11-21", "VN30F2411"),
    ("2024-11-22", "2024-12-31", "VN30F2412"),
    ("2025-01-01", "2025-01-16", "VN30F2501"),
    ("2025-01-17", "2025-02-20", "VN30F2502"),
    ("2025-02-21", "2025-03-20", "VN30F2503"),
    ("2025-03-21", "2025-04-17", "VN30F2504"),
    ("2025-04-18", "2025-05-15", "VN30F2505"),
    ("2025-05-16", "2025-06-19", "VN30F2506"),
    ("2025-06-20", "2025-07-17", "VN30F2507"),
    ("2025-07-18", "2025-08-21", "VN30F2508"),
    ("2025-08-22", "2025-09-18", "VN30F2509"),
    ("2025-09-19", "2025-10-16", "VN30F2510"),
    ("2025-10-17", "2025-11-20", "VN30F2511"),
    ("2025-11-21", "2025-12-18", "VN30F2512"),
    ("2025-12-19", "2026-01-15", "VN30F2601"),
    ("2026-01-16", "2026-02-19", "VN30F2602"),
    ("2026-02-20", "2026-03-19", "VN30F2603"),
    ("2026-03-20", "2026-04-16", "VN30F2604"),
    ("2026-04-17", "2026-05-21", "VN30F2605"),
]

# ── ORB Strategy Parameters ────────────────────────────────────────────────────
STRATEGY = {
    "symbol":          "HNXDS:VN30F2605",       # Continuous contract (dùng cho live)
    "timeframe":       "1min",          # Khung 1 phút
    "window":          60,              # Dùng cho zscore/BB (giữ để backtest cũ chạy được)
    "atr_multiplier":  2.0,             # SL ban đầu = 2 × ATR
    "trail_multiplier":1.5,             # Trailing stop = 1.5 × ATR
    "vol_confirm":     1.1,             # Volume phải > 110% vol_ma
    "contract_size":   100_000,         # 1 điểm = 100,000 VNĐ
    "target_qty_unit": 1,               # Số hợp đồng mỗi lệnh

    # Giữ lại các key cũ để run_backtest.py không báo lỗi KeyError
    "entry_threshold": 1.8,
    "exit_threshold":  0.3,
    "stop_loss":       3.5,
}

# #  # ── Strategy Parameters ────────────────────────────────────────────────────────
# # STRATEGY = {
# #     "symbol":            "HNXDS:VN30F2604",
# #     "timeframe":         "1min",
# #     "window":            150,       # Thêm lại dòng này để fix lỗi KeyError
# #     "entry_threshold":   0,        # Thêm để run_backtest.py không báo lỗi khi in
# #     "exit_threshold":    0,        # Thêm để run_backtest.py không báo lỗi khi in
# #     "stop_loss":         2.0,      
# #     "atr_multiplier":    2.0,      # Hệ số cho Trend Following
# #     "contract_size":     100_000,
# #     "target_qty_unit": 3       # Số lượng hợp đồng mỗi lệnh (có thể điều chỉnh để test)
# # }


# ── Backtest Periods ───────────────────────────────────────────────────────────
BACKTEST = {
    "insample_start":  "2023-01-01",
    "insample_end":    "2024-12-30",
    "outsample_start": "2025-01-01",
    "outsample_end":   "2025-12-31",
    "initial_capital": 500_000_000,
    "commission":      35_000,
}

# ── Telegram ───────────────────────────────────────────────────────────────────
TELEGRAM = {
    "token":   "8667107316:AAEnRi1gpMUmrW91WONTuGZNLlmm9_ZF4Hc",
    "chat_id": "5771649786",
}