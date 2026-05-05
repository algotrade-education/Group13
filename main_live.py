# """
# main_live.py — Group 13 Master Bot
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ĐỂ ĐỔI CHIẾN LƯỢC, chỉ cần sửa 1 dòng dưới đây:
#     ACTIVE_STRATEGY = "ema"   → Trend Following (EMA Crossover)
#     ACTIVE_STRATEGY = "orb"   → Opening Range Breakout
#     ACTIVE_STRATEGY = "mean"  → Mean Reversion (Z-Score)
# """

# # ══════════════════════════════════════════════════════
# #  👇 CHỈ SỬA DÒNG NÀY KHI MUỐN ĐỔI CHIẾN LƯỢC
# ACTIVE_STRATEGY = "ema"   # "ema" | "orb" | "mean"
# # ══════════════════════════════════════════════════════

# import time
# import logging
# import requests
# import threading
# import queue
# import re
# from datetime import datetime, timedelta

# from config.config import STRATEGY, PAPER_TRADE, TELEGRAM
# from src.data.loader import DataLoader
# from src.features.indicators import add_features
# from paperbroker.client import PaperBrokerClient

# # ── Tự động import đúng strategy ─────────────────────────────────────────────
# if ACTIVE_STRATEGY == "orb":
#     from src.strategy.orb_strategy import generate_signals
#     _STRATEGY_NAME = "ORB (Opening Range Breakout)"
#     _LOG_FILE      = "trading_orb.log"
# elif ACTIVE_STRATEGY == "mean":
#     from src.strategy.mean_reversion import generate_signals
#     _STRATEGY_NAME = "Mean Reversion (Z-Score)"
#     _LOG_FILE      = "trading_mean.log"
# else:  # mặc định "ema"
#     from src.strategy.trend_following import generate_signals
#     _STRATEGY_NAME = "Trend Following (EMA Crossover)"
#     _LOG_FILE      = "trading_ema.log"
# # ─────────────────────────────────────────────────────────────────────────────

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     handlers=[
#         logging.FileHandler(_LOG_FILE),
#         logging.StreamHandler(),
#     ],
# )


# class Group13MasterBot:
#     def __init__(self):
#         # Telegram
#         self.tg_token   = TELEGRAM["token"]
#         self.tg_chat_id = TELEGRAM["chat_id"]
#         self.tg_queue   = queue.Queue()
#         threading.Thread(target=self._tg_worker, daemon=True).start()
#         self.send_telegram(f"🚀 *Bot Group 13*: Khởi động chiến lược *{_STRATEGY_NAME}*!")

#         # State
#         self.symbol          = STRATEGY["symbol"]
#         self.target_qty_unit = STRATEGY["target_qty_unit"]
#         self.current_qty     = 0.0
#         self.avg_entry_price = 0.0
#         self.is_pending      = False
#         self.last_order_id   = None
#         self.last_order_time = 0
#         self.balance         = 0.0

#         # Broker
#         self.client = PaperBrokerClient(
#             default_sub_account=PAPER_TRADE["trader_id"],
#             username=PAPER_TRADE["username"],
#             password=PAPER_TRADE["password"],
#             rest_base_url=PAPER_TRADE["rest_base_url"],
#             socket_connect_host=PAPER_TRADE["fix_host"],
#             socket_connect_port=PAPER_TRADE["fix_port"],
#             sender_comp_id=PAPER_TRADE["sender_comp_id"],
#             target_comp_id=PAPER_TRADE["target_comp_id"],
#         )
#         self.loader = DataLoader()
#         self.setup_events()
#         self.sync_position()

#     # ── TELEGRAM ──────────────────────────────────────────────────────────────
#     def _tg_worker(self):
#         while True:
#             msg = self.tg_queue.get()
#             if msg is None:
#                 break
#             url     = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
#             payload = {"chat_id": self.tg_chat_id, "text": msg, "parse_mode": "Markdown"}
#             try:
#                 requests.post(url, json=payload, timeout=8)
#             except Exception:
#                 pass
#             self.tg_queue.task_done()

#     def send_telegram(self, message: str):
#         self.tg_queue.put(message)

#     # ── ĐỒNG BỘ VỊ THẾ ───────────────────────────────────────────────────────
#     def sync_position(self, market_price: float = None):
#         try:
#             old_qty = self.current_qty
#             old_avg = self.avg_entry_price

#             portfolio = self.client.get_portfolio_by_sub()
#             new_qty, new_avg = 0.0, 0.0

#             if portfolio and portfolio.get("success"):
#                 for item in portfolio.get("items", []):
#                     if "VN30" in (item.get("instrument") or ""):
#                         new_qty = float(item.get("quantity") or 0)
#                         new_avg = float(item.get("avgPrice") or 0)
#                         break

#             cash_info    = self.client.get_cash_balance()
#             self.balance = float(cash_info.get("remainCash") or 0)

#             # Báo cáo đóng vị thế
#             if new_qty == 0 and old_qty != 0:
#                 exit_price = market_price if market_price else old_avg
#                 pnl_pts    = (old_avg - exit_price) if old_qty < 0 else (exit_price - old_avg)
#                 pnl_vnd    = pnl_pts * abs(old_qty) * 100_000
#                 icon       = "💰" if pnl_vnd >= 0 else "💸"
#                 self.send_telegram(
#                     f"{icon} *KẾT THÚC GIAO DỊCH*\n"
#                     f"{'LÃI' if pnl_vnd >= 0 else 'LỖ'} {pnl_pts:,.1f} điểm "
#                     f"= *{pnl_vnd:,.0f} VNĐ*\n"
#                     f"Số dư: {self.balance:,.0f} VNĐ"
#                 )
#             elif new_qty != old_qty:
#                 side = "🟢 LONG" if new_qty > old_qty else "🔴 SHORT"
#                 self.send_telegram(
#                     f"🚀 *VỊ THẾ MỚI* — {_STRATEGY_NAME}\n{side}\n"
#                     f"Qty: {abs(new_qty - old_qty)} | Giá vốn: {new_avg}\n"
#                     f"Số dư: {self.balance:,.0f} VNĐ"
#                 )

#             self.current_qty     = new_qty
#             self.avg_entry_price = new_avg
#             self.is_pending      = False

#         except Exception as e:
#             logging.error(f"❌ Lỗi sync: {e}")

#     # ── SỰ KIỆN FIX ───────────────────────────────────────────────────────────
#     def setup_events(self):
#         def on_logon(session_id, **kwargs):
#             logging.info("✅ FIX Kết nối thành công!")
#             self.send_telegram(f"🔗 *SYSTEM ONLINE* — {_STRATEGY_NAME} sẵn sàng!")

#         def on_report(**kwargs):
#             status = str(kwargs.get("ord_status") or kwargs.get("ordStatus", ""))
#             qty    = kwargs.get("last_qty") or kwargs.get("qty") or 0
#             price  = kwargs.get("avg_px")  or kwargs.get("price") or 0
#             side   = "BUY" if str(kwargs.get("side")) == "1" else "SELL"

#             if float(qty) > 0 and status in ["1", "2"]:
#                 self.sync_position()
#                 self.send_telegram(
#                     f"✅ *KHỚP LỆNH*\n{side} {qty} @ {price}\n"
#                     f"Vị thế: {self.current_qty}"
#                 )
#                 if status == "2":
#                     self.is_pending = False

#         self.client.on("fix:logon", on_logon)
#         self.client.on("fix:execution_report", on_report)
#         self.client.on("fix:order:report",     on_report)

#     # ── XỬ LÝ TÍN HIỆU ───────────────────────────────────────────────────────
#     def handle_signal(self, signal: int, price: float, rsi: float):
#         if self.is_pending:
#             return

#         target_qty = signal * self.target_qty_unit
#         diff_qty   = target_qty - self.current_qty
#         if diff_qty == 0:
#             return

#         is_close = (target_qty == 0) or (abs(target_qty) < abs(self.current_qty))

#         if not is_close:
#             # Bộ lọc RSI chỉ áp dụng cho EMA (ORB/Mean tự quản lý filter trong strategy)
#             if ACTIVE_STRATEGY == "ema":
#                 if diff_qty > 0 and (rsi < 45 or rsi > 75):
#                     logging.warning(f"⚠️ Chặn Mở Long (RSI {rsi:.1f})")
#                     return
#                 if diff_qty < 0 and (rsi > 55 or rsi < 25):
#                     logging.warning(f"⚠️ Chặn Mở Short (RSI {rsi:.1f})")
#                     return

#         side        = "BUY" if diff_qty > 0 else "SELL"
#         trade_qty   = abs(int(diff_qty))
#         limit_price = price + 0.5 if side == "BUY" else price - 0.5

#         try:
#             logging.info(f"📤 {side} {trade_qty} @ {limit_price}")
#             self.client.place_order(
#                 full_symbol=self.symbol,
#                 side=side,
#                 qty=trade_qty,
#                 price=limit_price,
#                 ord_type="LIMIT",
#             )
#             self.is_pending      = True
#             self.last_order_time = time.time()
#         except Exception as e:
#             logging.error(f"❌ Lỗi đặt lệnh: {e}")

#     # ── VÒNG LẶP CHÍNH ───────────────────────────────────────────────────────
#     def run(self):
#         logging.info(f"🔥 Bot khởi động — Chiến lược: {_STRATEGY_NAME}")
#         self.client.connect()
#         time.sleep(2)

#         # Tự động parse timeframe từ config
#         tf_str = str(STRATEGY.get("timeframe", "1min")).lower()
#         match  = re.match(r"(\d+)", tf_str)
#         mult   = 60 if "h" in tf_str else 1
#         tf_minutes = int(match.group(1)) * mult if match else 1
#         logging.info(f"⏳ Timeframe: {tf_minutes} phút/nến")

#         while True:
#             try:
#                 df = self.loader.get_latest_data(self.symbol, count=250)
#                 df = add_features(df, window=STRATEGY["window"])
#                 df = generate_signals(df)

#                 if not df.empty:
#                     row       = df.iloc[-1]
#                     signal    = int(row["signal"])
#                     price     = float(row["close"])
#                     rsi       = float(row.get("rsi", 50))
#                     atr       = float(row.get("atr", 1.5))
#                     vol_ratio = row.get("volume", 0) / max(row.get("vol_ma", 1), 1)

#                     self.sync_position(price)

#                     # TP/SL dashboard
#                     tp, sl = 0.0, 0.0
#                     if self.current_qty > 0:
#                         tp = self.avg_entry_price + 2.5 * atr
#                         sl = self.avg_entry_price - 1.5 * atr
#                     elif self.current_qty < 0:
#                         tp = self.avg_entry_price - 2.5 * atr
#                         sl = self.avg_entry_price + 1.5 * atr

#                     now            = datetime.now()
#                     time_str       = now.strftime("%H:%M")
#                     is_close_time  = (
#                         "11:25" <= time_str < "11:30" or
#                         "14:40" <= time_str < "14:45"
#                     )

#                     final_signal = signal
#                     if self.current_qty != 0 and is_close_time:
#                         logging.warning(f"⏰ Giờ đóng phiên — ép thoát vị thế")
#                         final_signal = 0

#                     # Dashboard
#                     sig_txt = "🟢 LONG" if final_signal == 1 else "🔴 SHORT" if final_signal == -1 else "⚪ FLAT"
#                     print(f"\n{'═'*55}")
#                     print(f"🕒 {now.strftime('%H:%M:%S')} | {self.symbol} @ {price:,.1f}  [{_STRATEGY_NAME}]")
#                     print(f"📊 POS: {self.current_qty:+.0f} | AVG: {self.avg_entry_price:.1f}")
#                     print(f"📈 RSI: {rsi:.1f} | ATR: {atr:.2f} | Vol: {vol_ratio:.1f}×")
#                     if self.current_qty != 0:
#                         print(f"🎯 TP: {tp:.1f} | 🛡️ SL: {sl:.1f}")
#                     print(f"🚩 SIG: {sig_txt}")
#                     print(f"{'═'*55}")

#                     self.handle_signal(final_signal, price, rsi)

#                 # Ngủ đến đầu nến tiếp theo
#                 now              = datetime.now()
#                 next_mark        = ((now.minute // tf_minutes) + 1) * tf_minutes
#                 add_hrs, nxt_min = divmod(next_mark, 60)
#                 next_run         = now.replace(minute=nxt_min, second=1, microsecond=0) + timedelta(hours=add_hrs)
#                 wait             = (next_run - now).total_seconds()
#                 logging.info(f"💤 Ngủ {int(wait)}s → thức dậy lúc {next_run.strftime('%H:%M:%S')}")
#                 time.sleep(max(0, wait))

#             except Exception as e:
#                 logging.error(f"💥 Lỗi vòng lặp: {e}")
#                 time.sleep(5)


# if __name__ == "__main__":
#     Group13MasterBot().run()




"""
main_live.py — Group 13 Master Bot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ĐỂ ĐỔI CHIẾN LƯỢC, chỉ cần sửa 1 dòng dưới đây:
    ACTIVE_STRATEGY = "ema"   → Trend Following (EMA Crossover)
    ACTIVE_STRATEGY = "orb"   → Opening Range Breakout
    ACTIVE_STRATEGY = "mean"  → Mean Reversion (Z-Score)
"""

# ══════════════════════════════════════════════════════
#  👇 CHỈ SỬA DÒNG NÀY KHI MUỐN ĐỔI CHIẾN LƯỢC
ACTIVE_STRATEGY = "ema"   # "ema" | "orb" | "mean"
# ══════════════════════════════════════════════════════

import time
import logging
import requests
import threading
import queue
import re
from datetime import datetime, timedelta

from config.config import STRATEGY, PAPER_TRADE, TELEGRAM, ROLL_SCHEDULE
from src.data.loader import DataLoader
from src.features.indicators import add_features
from paperbroker.client import PaperBrokerClient

# ── Tự động import đúng strategy ─────────────────────────────────────────────
if ACTIVE_STRATEGY == "orb":
    from src.strategy.orb_strategy import generate_signals
    _STRATEGY_NAME = "ORB (Opening Range Breakout)"
    _LOG_FILE      = "trading_orb.log"
elif ACTIVE_STRATEGY == "mean":
    from src.strategy.mean_reversion import generate_signals
    _STRATEGY_NAME = "Mean Reversion (Z-Score)"
    _LOG_FILE      = "trading_mean.log"
else:
    from src.strategy.trend_following import generate_signals
    _STRATEGY_NAME = "Trend Following (EMA Crossover)"
    _LOG_FILE      = "trading_ema.log"
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(_LOG_FILE),
        logging.StreamHandler(),
    ],
)


# ── FIX 2: Tự động lấy symbol theo ngày từ ROLL_SCHEDULE ─────────────────────
def get_live_symbol() -> str:
    today = datetime.now().date()
    for roll_start, roll_end, ticker in ROLL_SCHEDULE:
        rs = datetime.strptime(roll_start, "%Y-%m-%d").date()
        re_ = datetime.strptime(roll_end, "%Y-%m-%d").date()
        if rs <= today <= re_:
            full = f"HNXDS:{ticker}" if ":" not in ticker else ticker
            logging.info(f"[Symbol] Hôm nay ({today}) dùng contract: {full}")
            return full
    fallback = STRATEGY["symbol"]
    logging.warning(f"[Symbol] Không tìm thấy contract cho {today}, fallback: {fallback}")
    return fallback
# ─────────────────────────────────────────────────────────────────────────────


class Group13MasterBot:

    PENDING_TIMEOUT = 30  # giây — tự reset nếu không nhận fill sau 30s

    def __init__(self):
        # Telegram
        self.tg_token   = TELEGRAM["token"]
        self.tg_chat_id = TELEGRAM["chat_id"]
        self.tg_queue   = queue.Queue()
        threading.Thread(target=self._tg_worker, daemon=True).start()
        self.send_telegram(f"🚀 *Bot Group 13*: Khởi động chiến lược *{_STRATEGY_NAME}*!")

        # State
        self.symbol          = get_live_symbol()   # FIX 2: tự động theo roll schedule
        self.target_qty_unit = STRATEGY["target_qty_unit"]
        self.current_qty     = 0.0
        self.avg_entry_price = 0.0
        self.is_pending      = False
        self.last_order_time = 0.0
        self.balance         = 0.0

        # Broker
        self.client = PaperBrokerClient(
            default_sub_account=PAPER_TRADE["trader_id"],
            username=PAPER_TRADE["username"],
            password=PAPER_TRADE["password"],
            rest_base_url=PAPER_TRADE["rest_base_url"],
            socket_connect_host=PAPER_TRADE["fix_host"],
            socket_connect_port=PAPER_TRADE["fix_port"],
            sender_comp_id=PAPER_TRADE["sender_comp_id"],
            target_comp_id=PAPER_TRADE["target_comp_id"],
        )
        self.loader = DataLoader()
        self.setup_events()
        self.sync_position()

    # ── TELEGRAM ──────────────────────────────────────────────────────────────
    def _tg_worker(self):
        while True:
            msg = self.tg_queue.get()
            if msg is None:
                break
            url     = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
            payload = {"chat_id": self.tg_chat_id, "text": msg, "parse_mode": "Markdown"}
            try:
                requests.post(url, json=payload, timeout=8)
            except Exception:
                pass
            self.tg_queue.task_done()

    def send_telegram(self, message: str):
        self.tg_queue.put(message)

    # ── ĐỒNG BỘ VỊ THẾ ───────────────────────────────────────────────────────
    def sync_position(self, market_price: float = None):
        # FIX 1: KHÔNG reset is_pending ở đây — chỉ execution report mới được làm điều đó
        try:
            old_qty = self.current_qty
            old_avg = self.avg_entry_price

            portfolio = self.client.get_portfolio_by_sub()
            new_qty, new_avg = 0.0, 0.0

            if portfolio and portfolio.get("success"):
                for item in portfolio.get("items", []):
                    if "VN30" in (item.get("instrument") or ""):
                        new_qty = float(item.get("quantity") or 0)
                        new_avg = float(item.get("avgPrice") or 0)
                        break

            cash_info    = self.client.get_cash_balance()
            self.balance = float(cash_info.get("remainCash") or 0)

            # Báo cáo đóng vị thế
            if new_qty == 0 and old_qty != 0:
                exit_price = market_price if market_price else old_avg
                pnl_pts    = (old_avg - exit_price) if old_qty < 0 else (exit_price - old_avg)
                pnl_vnd    = pnl_pts * abs(old_qty) * 100_000
                icon       = "💰" if pnl_vnd >= 0 else "💸"
                self.send_telegram(
                    f"{icon} *KẾT THÚC GIAO DỊCH*\n"
                    f"{'LÃI' if pnl_vnd >= 0 else 'LỖ'} {pnl_pts:,.1f} điểm "
                    f"= *{pnl_vnd:,.0f} VNĐ*\n"
                    f"Số dư: {self.balance:,.0f} VNĐ"
                )
            elif new_qty != old_qty:
                side = "🟢 LONG" if new_qty > old_qty else "🔴 SHORT"
                self.send_telegram(
                    f"🚀 *VỊ THẾ MỚI* — {_STRATEGY_NAME}\n{side}\n"
                    f"Qty: {abs(new_qty - old_qty)} | Giá vốn: {new_avg}\n"
                    f"Số dư: {self.balance:,.0f} VNĐ"
                )

            self.current_qty     = new_qty
            self.avg_entry_price = new_avg
            # ❌ self.is_pending = False  ← đã xóa (FIX 1)

        except Exception as e:
            logging.error(f"❌ Lỗi sync: {e}")

    # ── SỰ KIỆN FIX ───────────────────────────────────────────────────────────
    def setup_events(self):
        def on_logon(session_id, **kwargs):
            logging.info("✅ FIX Kết nối thành công!")
            self.send_telegram(f"🔗 *SYSTEM ONLINE* — {_STRATEGY_NAME} | `{self.symbol}`")

        def on_report(**kwargs):
            status = str(kwargs.get("ord_status") or kwargs.get("ordStatus", ""))
            qty    = kwargs.get("last_qty") or kwargs.get("qty") or 0
            price  = kwargs.get("avg_px")  or kwargs.get("price") or 0
            side   = "BUY" if str(kwargs.get("side")) == "1" else "SELL"

            if float(qty) > 0 and status in ["1", "2"]:
                # FIX 1: reset is_pending TRƯỚC khi gọi sync_position
                if status == "2":
                    self.is_pending      = False
                    self.last_order_time = 0.0
                    logging.info(f"✅ Khớp hoàn toàn: {side} {qty} @ {price}")
                else:
                    logging.info(f"🔶 Khớp một phần: {side} {qty} @ {price}")

                self.sync_position()   # sync sau — không còn reset is_pending nữa
                self.send_telegram(
                    f"✅ *KHỚP LỆNH*\n{side} {qty} @ {price}\n"
                    f"Vị thế: {self.current_qty}"
                )

        self.client.on("fix:logon", on_logon)
        self.client.on("fix:execution_report", on_report)
        self.client.on("fix:order:report",     on_report)

    # ── XỬ LÝ TÍN HIỆU ───────────────────────────────────────────────────────
    def handle_signal(self, signal: int, price: float, rsi: float):
        # FIX 3: timeout fallback — tự reset nếu lệnh bị reject và không có fill event
        if self.is_pending and self.last_order_time > 0:
            if time.time() - self.last_order_time > self.PENDING_TIMEOUT:
                logging.warning("⏳ Pending timeout 30s — reset is_pending (lệnh có thể đã bị reject)")
                self.is_pending      = False
                self.last_order_time = 0.0

        if self.is_pending:
            logging.info("⏸ Đang chờ lệnh khớp, bỏ qua tín hiệu mới.")
            return

        target_qty = signal * self.target_qty_unit
        diff_qty   = target_qty - self.current_qty
        if diff_qty == 0:
            return

        is_close = (target_qty == 0) or (abs(target_qty) < abs(self.current_qty))

        if not is_close:
            if ACTIVE_STRATEGY == "ema":
                if diff_qty > 0 and (rsi < 45 or rsi > 75):
                    logging.warning(f"⚠️ Chặn Mở Long (RSI {rsi:.1f})")
                    return
                if diff_qty < 0 and (rsi > 55 or rsi < 25):
                    logging.warning(f"⚠️ Chặn Mở Short (RSI {rsi:.1f})")
                    return

        side        = "BUY" if diff_qty > 0 else "SELL"
        trade_qty   = abs(int(diff_qty))
        limit_price = round(price + 0.5, 1) if side == "BUY" else round(price - 0.5, 1)

        try:
            logging.info(f"📤 {side} {trade_qty} @ {limit_price} | {self.symbol}")
            self.client.place_order(
                full_symbol=self.symbol,   # FIX 2: luôn dùng symbol từ roll schedule
                side=side,
                qty=trade_qty,
                price=limit_price,
                ord_type="LIMIT",
            )
            self.is_pending      = True
            self.last_order_time = time.time()
        except Exception as e:
            logging.error(f"❌ Lỗi đặt lệnh: {e}")
            self.is_pending = False  # Gửi lỗi thì không lock pending

    # ── VÒNG LẶP CHÍNH ───────────────────────────────────────────────────────
    def run(self):
        logging.info(f"🔥 Bot khởi động — {_STRATEGY_NAME} | {self.symbol}")
        self.client.connect()
        time.sleep(2)

        tf_str     = str(STRATEGY.get("timeframe", "1min")).lower()
        match      = re.match(r"(\d+)", tf_str)
        mult       = 60 if "h" in tf_str else 1
        tf_minutes = int(match.group(1)) * mult if match else 1
        logging.info(f"⏳ Timeframe: {tf_minutes} phút/nến")

        while True:
            try:
                df = self.loader.get_latest_data(self.symbol, count=250)
                df = add_features(df, window=STRATEGY["window"])
                df = generate_signals(df)

                if not df.empty:
                    row       = df.iloc[-1]
                    signal    = int(row["signal"])
                    price     = float(row["close"])
                    rsi       = float(row.get("rsi", 50))
                    atr       = float(row.get("atr", 1.5))
                    vol_ratio = row.get("volume", 0) / max(row.get("vol_ma", 1), 1)

                    self.sync_position(price)

                    tp, sl = 0.0, 0.0
                    if self.current_qty > 0:
                        tp = self.avg_entry_price + 2.5 * atr
                        sl = self.avg_entry_price - 1.5 * atr
                    elif self.current_qty < 0:
                        tp = self.avg_entry_price - 2.5 * atr
                        sl = self.avg_entry_price + 1.5 * atr

                    now           = datetime.now()
                    time_str      = now.strftime("%H:%M")
                    is_close_time = (
                        "11:25" <= time_str < "11:30" or
                        "14:40" <= time_str < "14:45"
                    )

                    final_signal = signal
                    if self.current_qty != 0 and is_close_time:
                        logging.warning("⏰ Giờ đóng phiên — ép thoát vị thế")
                        final_signal = 0

                    sig_txt  = "🟢 LONG" if final_signal == 1 else "🔴 SHORT" if final_signal == -1 else "⚪ FLAT"
                    pend_txt = " ⏸ PENDING" if self.is_pending else ""
                    print(f"\n{'═'*55}")
                    print(f"🕒 {now.strftime('%H:%M:%S')} | {self.symbol} @ {price:,.1f}  [{_STRATEGY_NAME}]{pend_txt}")
                    print(f"📊 POS: {self.current_qty:+.0f} | AVG: {self.avg_entry_price:.1f}")
                    print(f"📈 RSI: {rsi:.1f} | ATR: {atr:.2f} | Vol: {vol_ratio:.1f}×")
                    if self.current_qty != 0:
                        print(f"🎯 TP: {tp:.1f} | 🛡️ SL: {sl:.1f}")
                    print(f"🚩 SIG: {sig_txt}")
                    print(f"{'═'*55}")

                    self.handle_signal(final_signal, price, rsi)

                now              = datetime.now()
                next_mark        = ((now.minute // tf_minutes) + 1) * tf_minutes
                add_hrs, nxt_min = divmod(next_mark, 60)
                next_run         = now.replace(minute=nxt_min, second=1, microsecond=0) + timedelta(hours=add_hrs)
                wait             = (next_run - now).total_seconds()
                logging.info(f"💤 Ngủ {int(wait)}s → thức dậy lúc {next_run.strftime('%H:%M:%S')}")
                time.sleep(max(0, wait))

            except Exception as e:
                logging.error(f"💥 Lỗi vòng lặp: {e}")
                time.sleep(5)


if __name__ == "__main__":
    Group13MasterBot().run()