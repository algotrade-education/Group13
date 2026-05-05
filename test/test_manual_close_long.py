import os
import sys
import time
import logging
from threading import Event as ThreadEvent
from paperbroker.client import PaperBrokerClient
from src.data.loader import DataLoader 

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    # --- THÔNG TIN MỞ VỊ THẾ SHORT ---
    SYMBOL = "HNXDS:VN30F2604" 
    ACCOUNT = "main"
    USERNAME = "Group13"
    PASSWORD = "yCr8g4w0tLuT"
    SENDER_ID = "f2c11b00bf3d41fca072225f328ce98e"
    SHORT_QTY = 3 # Khang muốn Short 3 hợp đồng

    order_filled = ThreadEvent()

    def on_filled(**kwargs):
        qty = kwargs.get('qty') or kwargs.get('last_qty') or kwargs.get('cum_qty', 0)
        logger.info(f"✅ KHỚP LỆNH THÀNH CÔNG! Đã BÁN (Short): {qty} hợp đồng.")
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

    # Lắng nghe sự kiện khớp lệnh
    client.on("fix:order:filled", on_filled)
    client.on("fix:execution_report", on_filled) # Bọc lót thêm cổng này

    logger.info("🔌 Đang kết nối sàn để mở vị thế SHORT...")
    client.connect()

    try:
        if not client.wait_until_logged_on(timeout=10):
            logger.error("❌ Logon thất bại!")
            return

        # 1. Lấy giá mới nhất
        loader = DataLoader()
        df = loader.get_latest_data("VNF301M", count=1)
        curr_price = float(df['close'].iloc[-1])
        
        # Để khớp ngay lập tức khi SHORT, ta đặt giá THẤP hơn giá hiện tại 1.0 điểm
        # Sàn sẽ ưu tiên khớp cho Khang ở giá cao nhất hiện có (Giá tốt cho bạn)
        sell_price = curr_price - 1.0 
        
        logger.info(f"📊 Giá hiện tại: {curr_price} -> Đặt lệnh SELL {SHORT_QTY} @ {sell_price}")

        # 2. Thực hiện lệnh SELL
        order_filled.clear()
        client.place_order(
            full_symbol=SYMBOL, 
            side="SELL",  # <--- Đổi thành SELL để Short
            qty=SHORT_QTY,
            price=sell_price, 
            ord_type="LIMIT"
        )
        
        if order_filled.wait(timeout=30):
            logger.info(f"🎊 XONG! Group 13 đã giữ vị thế SHORT {SHORT_QTY} thành công.")
        else:
            logger.warning("⏳ Lệnh chưa khớp ngay. Khang check bảng điện xem có ai đang ép giá không nhé.")

    except Exception as e:
        logger.error(f"💥 Lỗi: {e}")
    finally:
        logger.info("🏁 Kết thúc phiên đặt lệnh.")
        time.sleep(2) # Đợi xíu để log kịp in ra
        os._exit(0)

if __name__ == "__main__":
    main()