import os
import sys
import time
import logging
from threading import Event as ThreadEvent
from paperbroker.client import PaperBrokerClient
from src.data.loader import DataLoader # Đảm bảo loader hoạt động

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    # --- THÔNG TIN GIẢI CỨU ---
    SYMBOL = "HNXDS:VN30F2604" 
    ACCOUNT = "main"
    USERNAME = "Group13"
    PASSWORD = "yCr8g4w0tLuT"
    SENDER_ID = "f2c11b00bf3d41fca072225f328ce98e"
    RESCUE_QTY = 3 # Số lượng cần mua lại để về 0

    order_filled = ThreadEvent()

    def on_filled(**kwargs):
        qty = kwargs.get('qty') or kwargs.get('last_qty') or kwargs.get('cum_qty', 7)
        logger.info(f"✅ KHỚP LỆNH GIẢI CỨU! Đã mua lại: {qty} hợp đồng.")
        order_filled.set()

    client = PaperBrokerClient(
        default_sub_account=ACCOUNT,
        username=USERNAME,
        password=PASSWORD,
        rest_base_url="https://papertrade.algotrade.vn/accounting",
        socket_connect_host="papertrade.algotrade.vn",
        socket_connect_port=5001,
        sender_comp_id=SENDER_ID,
        target_comp_id="SERVER"
    )

    client.on("fix:order:filled", on_filled)

    logger.info("🔌 Đang kết nối sàn để giải cứu vị thế...")
    client.connect()

    try:
        if not client.wait_until_logged_on(timeout=10):
            logger.error("❌ Logon thất bại!")
            return

        # 1. Lấy giá mới nhất để đảm bảo khớp ngay
        loader = DataLoader()
        df = loader.get_latest_data("VNF301M", count=1)
        curr_price = float(df['close'].iloc[-1])
        
        # Đặt giá cao hơn 1.0 điểm (Slippage) để "quét" hết lệnh bán đang treo
        buy_price = curr_price + 1.0 
        
        logger.info(f"📊 Giá hiện tại: {curr_price} -> Đặt lệnh BUY {RESCUE_QTY} @ {buy_price}")

        # 2. Thực hiện mua lại 7 cái
        order_filled.clear()
        client.place_order(
            full_symbol=SYMBOL, 
            side="BUY", 
            qty=RESCUE_QTY,
            price=buy_price, 
            ord_type="LIMIT"
        )
        
        if order_filled.wait(timeout=30):
            logger.info("🎊 CHÚC MỪNG! Vị thế đã được đưa về 0 thành công.")
        else:
            logger.warning("⏳ Lệnh giải cứu chưa khớp. Khang hãy kiểm tra lại trên Web sàn.")

    except Exception as e:
        logger.error(f"💥 Lỗi: {e}")
    finally:
        logger.info("🏁 Kết thúc phiên giải cứu.")
        os._exit(0)

if __name__ == "__main__":
    main()










# import os
# import sys
# import time
# import logging
# from threading import Event as ThreadEvent
# from paperbroker.client import PaperBrokerClient

# logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
# logger = logging.getLogger(__name__)

# def main():
#     # --- CẤU HÌNH THÔNG TIN ---
#     SYMBOL = "HNXDS:VN30F2604" 
#     ACCOUNT = "main"
#     USERNAME = "Group13"
#     PASSWORD = "yCr8g4w0tLuT"
#     SENDER_ID = "f2c11b00bf3d41fca072225f328ce98e"

#     order_filled = ThreadEvent()

#     # def on_filled(cl_ord_id, status, qty, **kwargs):
#     #     logger.info(f"✅ KHỚP LỆNH! ID: {cl_ord_id[:8]}... | Khối lượng: {qty}")
#     #     order_filled.set()
#     def on_filled(**kwargs):
#         # Lấy các thông tin từ kwargs, dùng .get để không bao giờ bị lỗi thiếu argument
#         cl_ord_id = kwargs.get('cl_ord_id', 'Unknown')
#         # Thư viện có thể dùng 'qty', 'last_qty' hoặc 'cum_qty'
#         qty = kwargs.get('qty') or kwargs.get('last_qty') or kwargs.get('cum_qty', 1)
        
#         logger.info(f"✅ KHỚP LỆNH THÀNH CÔNG! ID: {str(cl_ord_id)[:8]}... | Khối lượng: {qty}")
#         order_filled.set()

#     def on_rejected(cl_ord_id, reason, **kwargs):
#         logger.error(f"❌ LỆNH BỊ TỪ CHỐI: {reason}")

#     client = PaperBrokerClient(
#         default_sub_account=ACCOUNT,
#         username=USERNAME,
#         password=PASSWORD,
#         rest_base_url="https://papertrade.algotrade.vn/accounting",
#         socket_connect_host="papertrade.algotrade.vn",
#         socket_connect_port=5001,
#         sender_comp_id=SENDER_ID,
#         target_comp_id="SERVER"
#     )

#     client.on("fix:order:filled", on_filled)
#     client.on("fix:order:rejected", on_rejected)

#     logger.info("🔌 Đang kết nối sàn...")
#     client.connect()

#     try:
#         if not client.wait_until_logged_on(timeout=10):
#             logger.error("❌ Logon thất bại!")
#             return

#         # --- LẤY GIÁ HIỆN TẠI ĐỂ ĐẶT LỆNH LIMIT ---
#         # (Giả sử Khang đang xem Terminal thấy giá khoảng 18xx.x)
#         # Cách tốt nhất là lấy giá từ nến gần nhất:
#         from src.data.loader import DataLoader
#         loader = DataLoader()
#         df = loader.get_latest_data("VNF301M", count=1)
#         curr_price = float(df['close'].iloc[-1])
        
#         logger.info(f"📊 Giá thị trường hiện tại: {curr_price}")

#         # --- BƯỚC 1: MỞ LONG (Dùng giá cao hơn 0.5 điểm để khớp ngay) ---
#         buy_price = curr_price + 0.5 
#         logger.info(f"\n🚀 BƯỚC 1: ĐẶT LỆNH LIMIT BUY @ {buy_price}...")
        
#         order_filled.clear()
#         client.place_order(
#             full_symbol=SYMBOL, side="BUY", qty=1,
#             price=buy_price, ord_type="LIMIT" # <--- SỬA THÀNH LIMIT
#         )
        
#         if order_filled.wait(timeout=20):
#             logger.info("🔥 Đã khớp Long. Nghỉ 3 giây...")
#             time.sleep(3)
#         else:
#             logger.warning("⏳ Lệnh Buy chưa khớp. Có thể giá đã nhảy quá nhanh.")
#             return

#         # --- BƯỚC 2: ĐÓNG VỊ THẾ (Dùng giá thấp hơn 0.5 điểm để khớp ngay) ---
#         sell_price = curr_price - 0.5
#         logger.info(f"\n📉 BƯỚC 2: ĐẶT LỆNH LIMIT SELL @ {sell_price}...")
        
#         order_filled.clear()
#         client.place_order(
#             full_symbol=SYMBOL, side="SELL", qty=1,
#             price=sell_price, ord_type="LIMIT" # <--- SỬA THÀNH LIMIT
#         )

#         if order_filled.wait(timeout=20):
#             logger.info("🎊 CHÚC MỪNG! Round-trip LIMIT hoàn tất.")
#         else:
#             logger.warning("⏳ Lệnh Sell chưa khớp.")

#     except Exception as e:
#         logger.error(f"💥 Lỗi hệ thống: {e}")
#     finally:
#         logger.info("\n🏁 Kết thúc phiên Test.")
#         os._exit(0)

# if __name__ == "__main__":
#     main()