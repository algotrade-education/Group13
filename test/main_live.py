
# #ORB
# """
# main_live.py — Group 13 Master Bot
# Chiến lược: Opening Range Breakout + ATR Trailing Stop
# Khung thời gian: Động (Lấy tự động từ config.STRATEGY)
# """
# import time
# import logging
# import requests
# import threading
# import queue
# import re
# from datetime import datetime, timedelta

# from config.config import STRATEGY, PAPER_TRADE, TELEGRAM
# from src.data.loader import DataLoader

# # ── ĐỔI IMPORT SANG ORB ───────────────────────────────────────────────────────
# from src.strategy.orb_strategy import generate_signals   

# from paperbroker.client import PaperBrokerClient
# from src.features.indicators import add_features

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     handlers=[
#         logging.FileHandler("trading_orb.log"),
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
#         self.send_telegram("🚀 *Bot ORB*: Khởi động chiến lược Opening Range Breakout!")

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

#     # ── TELEGRAM ─────────────────────────────────────────────────────────────
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
#             portfolio = self.client.get_portfolio_by_sub()
#             new_qty, new_avg = 0.0, 0.0

#             if portfolio and portfolio.get("success"):
#                 for item in portfolio.get("items", []):
#                     if "VN30" in (item.get("instrument") or ""):
#                         new_qty = float(item.get("quantity") or 0)
#                         new_avg = float(item.get("avgPrice") or 0)
#                         break

#             # Lấy số dư
#             cash = self.client.get_cash_balance()
#             self.balance = float(cash.get("remainCash") or 0)

#             # Báo cáo khi đóng vị thế
#             if new_qty == 0 and old_qty != 0:
#                 exit_price = market_price if market_price else old_avg
#                 pnl_pts    = (old_avg - exit_price) if old_qty < 0 else (exit_price - old_avg)
#                 pnl_vnd    = pnl_pts * abs(old_qty) * 100_000
#                 icon       = "💰" if pnl_vnd >= 0 else "💸"
#                 self.send_telegram(
#                     f"{icon} *KẾT THÚC LỆNH ORB*\n"
#                     f"{'LÃI' if pnl_vnd >= 0 else 'LỖ'} {pnl_pts:,.1f} điểm "
#                     f"= *{pnl_vnd:,.0f} VNĐ*\n"
#                     f"Số dư: {self.balance:,.0f} VNĐ"
#                 )
#             elif new_qty != old_qty:
#                 side = "🟢 LONG" if new_qty > old_qty else "🔴 SHORT"
#                 self.send_telegram(
#                     f"🚀 *VỊ THẾ MỚI*\n{side}\n"
#                     f"Qty: {abs(new_qty - old_qty)} | Giá vốn: {new_avg}\n"
#                     f"Số dư: {self.balance:,.0f} VNĐ"
#                 )

#             self.current_qty     = new_qty
#             self.avg_entry_price = new_avg
#             self.is_pending      = False

#         except Exception as e:
#             logging.error(f"❌ Lỗi sync: {e}")

#     # ── SỰ KIỆN FIX ──────────────────────────────────────────────────────────
#     def setup_events(self):
#         def on_logon(session_id, **kwargs):
#             logging.info("✅ FIX Kết nối thành công!")
#             self.send_telegram("🔗 *SYSTEM ONLINE* — ORB Bot sẵn sàng!")

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
#             # Lọc RSI nhẹ cho lệnh mở mới
#             if diff_qty > 0 and rsi > 80:
#                 logging.warning(f"⚠️ RSI {rsi:.1f} quá cao — bỏ qua LONG")
#                 return
#             if diff_qty < 0 and rsi < 20:
#                 logging.warning(f"⚠️ RSI {rsi:.1f} quá thấp — bỏ qua SHORT")
#                 return

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
#         logging.info("🔥 ORB Bot — Bắt đầu!")
#         self.client.connect()
#         time.sleep(2)

#         # ── TỰ ĐỘNG PARSE TIMEFRAME TỪ CONFIG ──
#         tf_str = str(STRATEGY.get("timeframe", "1min")).lower()
#         match = re.match(r"(\d+)", tf_str)
#         # Nếu dùng h/hour thì nhân 60, ngược lại coi là phút
#         multiplier = 60 if 'h' in tf_str else 1
#         tf_minutes = int(match.group(1)) * multiplier if match else 1
        
#         logging.info(f"⏳ Cấu hình đồng hồ chạy chuẩn theo nến: {tf_minutes} phút/lần.")

#         while True:
#             try:
#                 # Lấy đủ 250 nến của khung hiện tại
#                 df = self.loader.get_latest_data(self.symbol, count=250)
#                 df = add_features(df, window=STRATEGY["window"])
#                 df = generate_signals(df)

#                 if not df.empty:
#                     row        = df.iloc[-1]
#                     signal     = int(row["signal"])
#                     price      = float(row["close"])
#                     rsi        = float(row.get("rsi", 50))
#                     atr        = float(row.get("atr", 1.5))
#                     vol_ratio  = row.get("volume", 0) / max(row.get("vol_ma", 1), 1)

#                     self.sync_position(price)

#                     # TP/SL dashboard
#                     tp, sl = 0.0, 0.0
#                     if self.current_qty > 0:
#                         tp = self.avg_entry_price + 2.5 * atr
#                         sl = self.avg_entry_price - 2.0 * atr
#                     elif self.current_qty < 0:
#                         tp = self.avg_entry_price - 2.5 * atr
#                         sl = self.avg_entry_price + 2.0 * atr

#                     now = datetime.now()
#                     is_close_time = (
#                         "11:20" <= now.strftime("%H:%M") < "11:30" or
#                         "14:30" <= now.strftime("%H:%M") < "14:45"
#                     )

#                     final_signal = signal
#                     if self.current_qty != 0 and is_close_time:
#                         logging.warning(f"⏰ Giờ đóng phiên — ép thoát vị thế")
#                         final_signal = 0

#                     # Dashboard
#                     print(f"\n{'═'*55}")
#                     print(f"🕒 {now.strftime('%H:%M:%S')} | {self.symbol} @ {price:,.1f}")
#                     print(f"📊 POS: {self.current_qty:+.0f} | AVG: {self.avg_entry_price:.1f}")
#                     print(f"📈 RSI: {rsi:.1f} | ATR: {atr:.2f} | Vol: {vol_ratio:.1f}×")
#                     if self.current_qty != 0:
#                         print(f"🎯 TP: {tp:.1f} | 🛡️ SL: {sl:.1f}")
#                     sig_txt = "🟢 LONG" if final_signal == 1 else "🔴 SHORT" if final_signal == -1 else "⚪ FLAT"
#                     print(f"🚩 SIG: {sig_txt}")
#                     print(f"{'═'*55}")

#                     self.handle_signal(final_signal, price, rsi)

#                 # ── NGỦ ĐÔNG THÔNG MINH THEO TIMEFRAME ──
#                 now = datetime.now()
                
#                 # Tính số phút để tròn nến tiếp theo (VD: TF=15 -> 0, 15, 30, 45)
#                 next_minute_mark = ((now.minute // tf_minutes) + 1) * tf_minutes
                
#                 # Xử lý khi số phút cộng dồn vượt qua 60 (chuyển sang giờ tiếp theo)
#                 add_hours, next_minute = divmod(next_minute_mark, 60)
                
#                 # Setup thời điểm thức dậy: nhảy đến phút tiếp theo và luôn cộng thêm 1 giây (second=1)
#                 next_run = now.replace(minute=next_minute, second=1, microsecond=0) + timedelta(hours=add_hours)
                
#                 wait_seconds = (next_run - now).total_seconds()
                
#                 logging.info(f"💤 Hệ thống ngủ đông. Đợi {int(wait_seconds)}s để đóng nến, thức dậy lúc {next_run.strftime('%H:%M:%S')}")
#                 time.sleep(max(0, wait_seconds))

#             except Exception as e:
#                 logging.error(f"💥 Lỗi vòng lặp: {e}")
#                 time.sleep(5)


# if __name__ == "__main__":
#     Group13MasterBot().run()

#Ema
import time
import logging
import requests
import threading
import queue
import os
from datetime import datetime, timedelta

from config.config import STRATEGY, PAPER_TRADE, TELEGRAM
from src.data.loader import DataLoader
from src.strategy.trend_following import generate_signals
from paperbroker.client import PaperBrokerClient
from src.features.indicators import add_features

# 1. Logging chuyên nghiệp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler("trading_pro.log"), logging.StreamHandler()]
)

class Group13MasterBot:
    def __init__(self):
        # Telegram Setup
        self.tg_token = TELEGRAM['token']
        self.tg_chat_id = TELEGRAM['chat_id']
        self.tg_queue = queue.Queue()
        threading.Thread(target=self._tg_worker, daemon=True).start()
        self.send_telegram("🧪 *Bot Group 13 Master*: Đã cập nhật Logic thoát hiểm & Dashboard!")

        self.symbol = STRATEGY["symbol"]
        self.target_qty_unit = STRATEGY["target_qty_unit"] 
        self.current_qty = 0.0
        self.avg_entry_price = 0.0 # Lưu giá vốn để hiện Terminal
        self.is_pending = False
        self.last_order_id = None
        self.last_order_time = 0

        self.client = PaperBrokerClient(
            default_sub_account=PAPER_TRADE['trader_id'],
            username=PAPER_TRADE['username'],
            password=PAPER_TRADE['password'],
            rest_base_url=PAPER_TRADE['rest_base_url'],
            socket_connect_host=PAPER_TRADE['fix_host'],
            socket_connect_port=PAPER_TRADE['fix_port'],
            sender_comp_id=PAPER_TRADE['sender_comp_id'],
            target_comp_id=PAPER_TRADE['target_comp_id']
        )
        self.loader = DataLoader()
        self.setup_events()
        
        self.sync_initial_position()

    def _tg_worker(self):
        while True:
            msg = self.tg_queue.get()
            if msg is None: break
            url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
            payload = {"chat_id": self.tg_chat_id, "text": msg, "parse_mode": "Markdown"}
            try: requests.post(url, json=payload, timeout=8)
            except: pass
            self.tg_queue.task_done()

    def send_telegram(self, message):
        self.tg_queue.put(message)


    def sync_initial_position(self, current_market_price=None):
        """TRẠM KIỂM SOÁT: Check Vị thế, Giá vốn, Tiền mặt và Lời/Lỗ thực tế"""
        try:
            old_qty = self.current_qty
            old_avg = self.avg_entry_price

            # 1. Lấy vị thế từ Portfolio
            portfolio = self.client.get_portfolio_by_sub()
            new_qty, new_avg = 0.0, 0.0
            
            if portfolio and portfolio.get("success"):
                for item in portfolio.get("items", []):
                    if "VN30" in (item.get("instrument") or ""):
                        new_qty = float(item.get("quantity") or 0)
                        new_avg = float(item.get("avgPrice") or 0)
                        break

            # 2. Lấy số dư tiền mặt (Dùng hàm Khang vừa tìm được)
            cash_info = self.client.get_cash_balance()
            # 'remainCash' là tiền thực tế Khang đang có để giao dịch
            self.balance = float(cash_info.get('remainCash') or 0)

            # 3. LOGIC BÁO CÁO KHI ĐÓNG VỊ THẾ (VỀ 0)
            if new_qty == 0 and old_qty != 0:
                # Tính số điểm ăn được (PnL Points)
                # Nếu cũ là Short (âm), PnL = Entry - Exit. Nếu cũ là Long (dương), PnL = Exit - Entry.
                exit_price = current_market_price if current_market_price else old_avg
                pnl_points = (old_avg - exit_price) if old_qty < 0 else (exit_price - old_avg)
                
                # Quy ra tiền mặt (1 điểm = 100,000 VNĐ)
                pnl_money = pnl_points * abs(old_qty) * 100000
                
                status_icon = "💰" if pnl_money >= 0 else "💸"
                pnl_text = "LÃI" if pnl_money >= 0 else "LỖ"

                msg = (f"{status_icon} *KẾT THÚC GIAO DỊCH*\n"
                       f"━━━━━━━━━━━━━━━\n"
                       f"📈 Kết quả: *{pnl_text} {pnl_points:,.1f} điểm*\n"
                       f"💵 Tiền về/mất: *{pnl_money:,.0f} VNĐ*\n"
                       f"🏦 Số dư khả dụng: *{self.balance:,.0f} VNĐ*\n"
                       f"🏁 Vị thế: Đã sạch hàng (0.0)")
                self.send_telegram(msg)

            # 4. BÁO CÁO KHI MỞ VỊ THẾ MỚI
            elif new_qty != old_qty:
                side_txt = "🟢 MUA (Long)" if new_qty > old_qty else "🔴 BÁN (Short)"
                msg = (f"🚀 *GIAO DỊCH MỚI*\n"
                       f"━━━━━━━━━━━━━━━\n"
                       f"➡️ Loại: {side_txt}\n"
                       f"📦 Số lượng: {abs(new_qty - old_qty)}\n"
                       f"💰 Giá vốn: *{new_avg}*\n"
                       f"🏦 Số dư khả dụng: *{self.balance:,.0f} VNĐ*")
                self.send_telegram(msg)

            # Cập nhật biến nội bộ
            self.current_qty = new_qty
            self.avg_entry_price = new_avg
            self.is_pending = False

        except Exception as e:
            logging.error(f"❌ Lỗi báo cáo: {e}")

    def setup_events(self):
        def on_logon(session_id, **kwargs):
            logging.info(f"✅ [FIX] Kết nối sàn thành công!")
            self.send_telegram("🚀 *SYSTEM ONLINE*")

        def on_report(**kwargs):
            # LẤY THÔNG TIN TỪ EXECUTION REPORT ĐỂ BÁO TELEGRAM
            status = str(kwargs.get('ord_status') or kwargs.get('ordStatus', ''))
            side = "BUY" if str(kwargs.get('side')) == '1' else "SELL"
            price = kwargs.get('avg_px') or kwargs.get('price') or 0
            qty = kwargs.get('last_qty') or kwargs.get('qty') or 0

            # Nếu có khối lượng khớp (Status 1: Khớp một phần, 2: Khớp hết)
            if float(qty) > 0 and status in ['1', '2']:
                self.sync_initial_position()
                msg = (f"✅ *KHỚP LỆNH*\n"
                       f"➡️ Loại: {side}\n"
                       f"💰 Giá khớp: *{price}*\n"
                       f"📦 Qty: {qty}\n"
                       f"🚩 Vị thế hiện tại: {self.current_qty}")
                self.send_telegram(msg)
                if status == '2': self.is_pending = False

        self.client.on("fix:logon", on_logon)
        self.client.on("fix:execution_report", on_report)
        self.client.on("fix:order:report", on_report)

    def handle_signal(self, signal, current_price, rsi_now):
        if self.is_pending: return

        target_qty = signal * self.target_qty_unit
        diff_qty = target_qty - self.current_qty
        if diff_qty == 0: return

        # --- YÊU CẦU 1: LOGIC ĐÓNG MỞ VỊ THẾ (NO RSI EXIT) ---
        is_closing_order = (target_qty == 0) or (abs(target_qty) < abs(self.current_qty))

        if is_closing_order:
            logging.info(f"🚨 LỆNH THOÁT VỊ THỀ: {self.current_qty} -> {target_qty}. BỎ QUA RSI.")
        else:
            # Chỉ lọc RSI khi mở mới
            if diff_qty > 0 and (rsi_now < 45 or rsi_now > 75):
                logging.warning(f"⚠️ Chặn Mở Long (RSI {rsi_now:.1f})")
                return
            if diff_qty < 0 and (rsi_now > 55 or rsi_now < 25):
                logging.warning(f"⚠️ Chặn Mở Short (RSI {rsi_now:.1f})")
                return

        side = "BUY" if diff_qty > 0 else "SELL"
        trade_qty = abs(int(diff_qty))
        limit_price = current_price + 0.5 if side == "BUY" else current_price - 0.5

        try:
            logging.info(f"📤 Gửi lệnh {side} {trade_qty} @ {limit_price}")
            self.client.place_order(full_symbol=self.symbol, side=side, qty=trade_qty, price=limit_price, ord_type="LIMIT")
            self.is_pending = True
            self.last_order_time = time.time()
        except Exception as e:
            logging.error(f"❌ Lỗi đặt lệnh: {e}")


    def run(self):
        logging.info("🔥 Bot Group 13 Master: KÍCH HOẠT CHẾ ĐỘ QUẢN TRỊ THỜI GIAN")
        self.client.connect()
        time.sleep(2) 

        while True:
            try:
                # 1. Lấy dữ liệu và đồng bộ
                df = self.loader.get_latest_data(self.symbol, count=200)
                df = add_features(df, window=STRATEGY["window"])
                df_with_signals = generate_signals(df)
                
                if not df_with_signals.empty:
                    last_row = df_with_signals.iloc[-1]
                    signal = int(last_row['signal'])
                    curr_price = float(last_row['close'])
                    rsi_val = last_row.get('rsi', 50)
                    atr_val = last_row.get('atr', 1.5)

                    self.sync_initial_position(curr_price)

                    # --- TÍNH TOÁN NGƯỠNG TP/SL ---
                    tp_price, sl_price = 0.0, 0.0
                    if self.current_qty > 0:
                        tp_price = self.avg_entry_price + (2.5 * atr_val)
                        sl_price = self.avg_entry_price - (1.5 * atr_val)
                    elif self.current_qty < 0:
                        tp_price = self.avg_entry_price - (2.5 * atr_val)
                        sl_price = self.avg_entry_price + (1.5 * atr_val)

                    # --- LOGIC KIỂM TRA THỜI GIAN ĐÓNG CỬA ---
                    now = datetime.now()
                    current_time = now.strftime("%H:%M")
                    
                    # Quy định giờ thoát hàng (5 phút cuối mỗi phiên)
                    is_closing_time = ("11:25" <= current_time < "11:30") or \
                                      ("14:40" <= current_time < "14:45")

                    # --- GHI ĐÈ TÍN HIỆU (FINAL SIGNAL) ---
                    final_signal = signal
                    
                    if self.current_qty != 0:
                        # ƯU TIÊN 1: Nếu đến giờ nghỉ -> Thoát bằng mọi giá
                        if is_closing_time:
                            logging.warning(f"⏰ GIỜ NGHỈ PHIÊN ({current_time}): Đang ép đóng vị thế để an toàn!")
                            final_signal = 0
                        
                        # ƯU TIÊN 2: Nếu chạm TP/SL
                        elif (self.current_qty < 0 and (curr_price <= tp_price or curr_price >= sl_price)) or \
                             (self.current_qty > 0 and (curr_price >= tp_price or curr_price <= sl_price)):
                            logging.info(f"🎯 CHẠM NGƯỠNG TP/SL. Thực thi lệnh thoát.")
                            final_signal = 0

                    # DASHBOARD
                    # print(f"\n" + "═"*55)
                    # print(f"🕒 {current_time}:{now.strftime('%S')} | {self.symbol} @ {curr_price:,.1f}")
                    if is_closing_time: print("⚠️ TRẠNG THÁI: ĐANG TRONG GIỜ THOÁT LỆNH AN TOÀN")
                    # print(f"📊 POS: {self.current_qty} | AVG: {self.avg_entry_price:.1f}")
                    # print("═"*55)
                    # print(f"\n" + "═"*55)

                    print(f"🕒 {datetime.now().strftime('%H:%M:%S')} | {self.symbol} @ {curr_price:,.1f}")
                    print(f"📊 POS: {self.current_qty} | AVG: {self.avg_entry_price:.1f} | ATR: {atr_val:.2f}")
                    if self.current_qty != 0:
                        print(f"🎯 TP (ATR): {tp_price:.1f} | 🛡️ SL (ATR): {sl_price:.1f}")
                    print(f"📈 EMA10/30: {last_row.get('ema_fast',0):.1f}/{last_row.get('ema_slow',0):.1f} | RSI: {rsi_val:.1f}")
                    print("═"*55)

                    self.handle_signal(final_signal, curr_price, rsi_val)

                # Đợi nến
                now = datetime.now()
                next_run = (now + timedelta(minutes=1)).replace(second=1, microsecond=0)
                wait_seconds = (next_run - now).total_seconds()
                time.sleep(max(0, wait_seconds))

            except Exception as e:
                logging.error(f"💥 Lỗi: {e}")
                time.sleep(5)


if __name__ == "__main__":
    Group13MasterBot().run()







# Mean reversion 
# import time
# from config.config import STRATEGY, PAPER_TRADE
# from src.data.loader import DataLoader
# from src.strategy.trend_following import generate_signals
# from paperbroker.client import PaperBrokerClient

# def run_live():
#     print("🚀 [Group 13] Khởi động hệ thống giao dịch tự động...")
    
#     client = PaperBrokerClient(
#         default_sub_account=PAPER_TRADE['trader_id'],
#         username=PAPER_TRADE['username'],
#         password=PAPER_TRADE['password'],
#         rest_base_url=PAPER_TRADE['rest_base_url'],
#         socket_connect_host=PAPER_TRADE['fix_host'],
#         socket_connect_port=PAPER_TRADE['fix_port'],
#         sender_comp_id=PAPER_TRADE['sender_comp_id'],
#         target_comp_id=PAPER_TRADE['target_comp_id']
#     )

#     client.connect()
#     if not client.wait_until_logged_on(timeout=15):
#         print("❌ Lỗi kết nối FIX. Vui lòng kiểm tra config!")
#         return

#     loader = DataLoader()
#     symbol = STRATEGY["symbol"]
#     current_pos = 0 # Khởi tạo vị thế ban đầu

#     while True:
#         try:
#             # Lấy data và tính tín hiệu
#             df = loader.get_latest_data(symbol, count=50)
#             df_with_signals = generate_signals(df)
#             last_signal = int(df_with_signals['signal'].iloc[-1])

#             # Nếu tín hiệu thay đổi so với vị thế hiện tại
#             if last_signal != current_pos:
#                 print(f"🔔 Tín hiệu mới: {last_signal} (Hiện tại: {current_pos})")
                
#                 # Logic đặt lệnh chuẩn FIX
#                 if last_signal == 1:
#                     side = "BUY"
#                 elif last_signal == -1:
#                     side = "SELL"
#                 else: # last_signal == 0 (Đóng vị thế)
#                     side = "SELL" if current_pos == 1 else "BUY"

#                 # Đặt lệnh qua cổng FIX (Cực nhanh)
#                 client.place_order(
#                     symbol=symbol,
#                     side=side,
#                     quantity=5, # 5 hợp đồng ~ 500,000 VND/điểm
#                     order_type="MTL"
#                 )
                
#                 print(f"✅ Đã gửi lệnh {side} 5 hợp đồng VN30F2604")
#                 current_pos = last_signal # Cập nhật vị thế nội bộ

#             print(f"⌛ [{time.strftime('%H:%M:%S')}] Đang quét trend... Vị thế: {current_pos}")
#             time.sleep(60) # Quét mỗi phút
            
#         except Exception as e:
#             print(f"❌ Lỗi: {e}")
#             time.sleep(10)

# if __name__ == "__main__":
#     run_live()






