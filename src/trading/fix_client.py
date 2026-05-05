"""
FIX Client – Test kết nối tới Paper Trading Server.
Tương đương Example 01simplelogin.py từ tài liệu PLUTUS.

Usage:
    python src/trading/fix_client.py
"""

import time
import quickfix as fix
from Temp.config.config import PAPER_TRADE


class Application(fix.Application):

    def onCreate(self, sessionID):
        print(f"[FIX] Session created : {sessionID}")

    def onLogon(self, sessionID):
        print(f"[FIX] ✅ Logged on     : {sessionID}")

    def onLogout(self, sessionID):
        print(f"[FIX] ❌ Logged out    : {sessionID}")

    def toAdmin(self, message, sessionID):
        """Inject credentials vào Logon message."""
        msgType = fix.MsgType()
        message.getHeader().getField(msgType)

        if msgType.getValue() == fix.MsgType_Logon:
            message.setField(fix.Username(PAPER_TRADE["username"]))
            message.setField(fix.Password(PAPER_TRADE["password"]))

        print(f"[→ Server] {message}")

    def fromAdmin(self, message, sessionID):
        print(f"[← Server] {message}")

    def toApp(self, message, sessionID):
        pass

    def fromApp(self, message, sessionID):
        print(f"[← App   ] {message}")


def main():
    settings  = fix.SessionSettings("config/fix.cfg")
    app       = Application()
    store     = fix.FileStoreFactory(settings)
    log_fac   = fix.FileLogFactory(settings)
    initiator = fix.SocketInitiator(app, store, settings, log_fac)

    print("[FIX] Starting initiator...")
    initiator.start()

    try:
        time.sleep(10)   # Giữ kết nối 10 giây để test
    except KeyboardInterrupt:
        pass
    finally:
        initiator.stop()
        print("[FIX] Stopped.")


if __name__ == "__main__":
    main()
