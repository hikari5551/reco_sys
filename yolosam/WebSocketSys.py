import asyncio
import threading
from constant.GlobalConsts import GlobalConsts
from utils.GlobalLog import LoggerCat
log = LoggerCat()
# WebSocket集成类，提供WebSocket服务的启动和清理功能
class WebSocketIntegration:
# 初始化方法，设置WebSocket服务的主机地址、端口和运行状态
    def __init__(self):
        self.host = GlobalConsts.WEBSOCKET_HOST #默认主机地址
        self.port = GlobalConsts.WEBSOCKET_PORT #默认端口
        self.running = False #服务运行状态
        self.server = None #服务器实例

# 启动WebSocket服务，创建一个后台线程来运行服务器任务
    def start_websocket_integration(self):
        if self.running:
            return
        self.running = True
        thread = threading.Thread(target=self._run_server, daemon=True)
        thread.start()
        log.info(f"WebSocket服务启动：{self.host}:{self.port}")

# 服务器任务，持续运行直到服务停止
    def _run_server(self):
        try:
            asyncio.run(self._server_task())
        except Exception as e:
            log.error(f"WebSocket异常：{e}")

# 服务器主循环，保持服务运行
    async def _server_task(self):
        while self.running:
            await asyncio.sleep(1)
# 停止WebSocket服务，设置运行标志为False
    def cleanup(self):
        self.running = False
        log.info("WebSocket已清理")

# 获取WebSocket集成实例的函数，供外部调用
def get_yoloshow_integration():
    return WebSocketIntegration()