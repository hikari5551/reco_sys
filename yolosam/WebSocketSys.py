import asyncio
import threading
from constant.GlobalConsts import GlobalConsts
from utils.GlobalLog import LoggerCat

log = LoggerCat()

class WebSocketIntegration:
    def __init__(self):
        self.host = GlobalConsts.WEBSOCKET_HOST
        self.port = GlobalConsts.WEBSOCKET_PORT
        self.running = False
        self.server = None

    def start_websocket_integration(self):
        if self.running:
            return
        self.running = True
        thread = threading.Thread(target=self._run_server, daemon=True)
        thread.start()
        log.info(f"WebSocket服务启动：{self.host}:{self.port}")

    def _run_server(self):
        try:
            asyncio.run(self._server_task())
        except Exception as e:
            log.error(f"WebSocket异常：{e}")

    async def _server_task(self):
        while self.running:
            await asyncio.sleep(1)

    def cleanup(self):
        self.running = False
        log.info("WebSocket已清理")

def get_yoloshow_integration():
    return WebSocketIntegration()