import asyncio
import json
import threading
import time

from constant.GlobalConsts import GlobalConsts
from utils.GlobalLog import LoggerCat
from utils import globalDict

log = LoggerCat()


class WebSocketIntegration:
    """向前端或调试页面推送当前检测结果。

    需要安装依赖：
        pip install websockets
    如果未安装 websockets，本模块会记录日志但不影响主程序运行。
    """

    def __init__(self):
        self.host = getattr(GlobalConsts, "WEBSOCKET_HOST", "0.0.0.0")
        self.port = getattr(GlobalConsts, "WEBSOCKET_PORT", 8765)
        self.running = False
        self.thread = None
        self.clients = set()

    def start_websocket_integration(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        log.info(f"WebSocket 服务启动：{self.host}:{self.port}")

    def _run_server(self):
        try:
            import websockets
        except Exception as e:
            log.error(f"未安装 websockets，WebSocket 服务未启动：{e}")
            self.running = False
            return

        async def handler(websocket, *args):
            self.clients.add(websocket)
            log.info("WebSocket 客户端已连接")
            try:
                await websocket.wait_closed()
            finally:
                self.clients.discard(websocket)
                log.info("WebSocket 客户端已断开")

        async def broadcast_loop():
            while self.running:
                payload = {
                    "type": "detection_update",
                    "timestamp": time.time(),
                    "detections": globalDict.get_value("detections") or [],
                    "current_image_path": globalDict.get_value("current_image_path") or "",
                }
                message = json.dumps(payload, ensure_ascii=False)
                if self.clients:
                    dead_clients = []
                    for client in list(self.clients):
                        try:
                            await client.send(message)
                        except Exception:
                            dead_clients.append(client)
                    for client in dead_clients:
                        self.clients.discard(client)
                await asyncio.sleep(0.5)

        async def server_task():
            async with websockets.serve(handler, self.host, self.port):
                await broadcast_loop()

        try:
            asyncio.run(server_task())
        except Exception as e:
            log.error(f"WebSocket 异常：{e}")
        finally:
            self.running = False

    def cleanup(self):
        self.running = False
        log.info("WebSocket 已清理")


def get_yoloshow_integration():
    return WebSocketIntegration()
