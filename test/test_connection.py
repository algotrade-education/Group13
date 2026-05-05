

import time
import requests # Đảm bảo đã 'pip install requests'
from config.config import PAPER_TRADE, TELEGRAM
from paperbroker.client import PaperBrokerClient

def test_telegram():
    print("📡 Đang thử 'hú' qua Telegram...")
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM['token']}/sendMessage"
        payload = {
            "chat_id": TELEGRAM['chat_id'], 
            "text": "🔔 *THÔNG BÁO TEST*\nBot Group 13 đã kết nối Telegram thành công! 🚀",
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            print("✅ Telegram: Đã gửi tin nhắn thành công! Check điện thoại ngay Khang ơi.")
        else:
            print(f"❌ Telegram: Lỗi rồi! (Mã lỗi: {response.status_code})")
            print(f"Chi tiết: {response.text}")
    except Exception as e:
        print(f"❌ Telegram: Không thể gửi yêu cầu. Lỗi: {e}")

def test_fix():
    print("🔍 Khởi tạo Client FIX...")
    client = PaperBrokerClient(
        default_sub_account=PAPER_TRADE['trader_id'],
        username=PAPER_TRADE['username'],
        password=PAPER_TRADE['password'],
        rest_base_url=PAPER_TRADE['rest_base_url'],
        socket_connect_host=PAPER_TRADE['fix_host'],
        socket_connect_port=PAPER_TRADE['fix_port'],
        sender_comp_id=PAPER_TRADE['sender_comp_id'],
        target_comp_id=PAPER_TRADE['target_comp_id']
    )

    client.on("fix:logon", lambda session_id, **kw: print(f"✅ FIX: Logon thành công!"))
    client.connect()

    if client.wait_until_logged_on(timeout=10):
        print("✅ FIX: Sẵn sàng đặt lệnh.")
        time.sleep(1)
        client.disconnect()
    else:
        print("❌ FIX: Logon thất bại.")

if __name__ == "__main__":
    # Test cả 2 cho chắc cú
    test_fix()
    print("-" * 30)
    test_telegram()




