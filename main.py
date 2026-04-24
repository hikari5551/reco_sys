import sys
import os
import traceback
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.getcwd(), "ui"))
from PySide6.QtCore import QSharedMemory
from PySide6.QtWidgets import QApplication
from constant.GlobalConsts import GlobalConsts
from utils import LoggerCat, Cleaner, ConfigManager, globalDict


LogCat = LoggerCat()
INTEGRATION_AVAILABLE = False

try:
    from yolosam.WebSocketSys import get_yoloshow_integration
    from yolosam.Video import cleanup_video_segment_integration
    from yoloshow.Windows import YOLOSHOWWindow, YOLOSHOWVSWindow
    from yoloshow.ChangeWindow import yoloshow2vs, vs2yoloshow
    INTEGRATION_AVAILABLE = True
except Exception as e:
    LogCat.error(f"导入失败：{e}")
    raise RuntimeError("模块缺失")

_app = None
_initialized = False
_worker = None
integration = None

def get_application():
    global _app
    if _app is None:
        _app = QApplication([])
    return _app

def initialize_global_variables():
    global _initialized
    if _initialized:
        return
    yoloshow = YOLOSHOWWindow()
    yoloshowvs = YOLOSHOWVSWindow()
    globalDict.init()
    globalDict.set_value("yoloshow", yoloshow)
    globalDict.set_value("yoloshowvs", yoloshowvs)
    globalDict.set_value("yoloname", "yolov8n.pt")
    globalDict.set_value("yoloname1", "yolov8s.pt")
    globalDict.set_value("yoloname2", "yolov8m.pt")
    _initialized = True

def initialize_yoloshow_integration():
    if not INTEGRATION_AVAILABLE:
        return None
    try:
        integration = get_yoloshow_integration()
        cfg = ConfigManager.get_config(GlobalConsts.CONFIG_CAMERA_MAIN_JSON)
        if ConfigManager.get_item_bool(cfg, "websocket_config.enabled"):
            integration.start_websocket_integration()
        globalDict.set_value("yoloshow_integration", integration)
        return integration
    except Exception as e:
        LogCat.error(f"初始化失败：{e}")
        return None

def is_single_instance():
    shm = QSharedMemory("yoloshow")
    if shm.create(1):
        return True, shm
    return False, None

def start():
    global integration
    is_single, shm = is_single_instance()
    if not is_single:
        return

    app = get_application()
    initialize_global_variables()
    integration = initialize_yoloshow_integration()

    yoloshow_glo = globalDict.get_value("yoloshow")
    yoloshowvs_glo = globalDict.get_value("yoloshowvs")

    yoloshow_glo.src_vsmode.clicked.connect(yoloshow2vs)
    yoloshowvs_glo.src_singlemode.clicked.connect(vs2yoloshow)

    yoloshow_glo.show()

    def cleanup():
        try:
            if integration:
                integration.cleanup()
            ConfigManager.clear_config_cache()
            cleanup_video_segment_integration()
        except:
            pass

    app.aboutToQuit.connect(cleanup)
    app.exec()

def run_start():
    start()

if __name__ == "__main__":
    try:
        use_timer = "--timer" in sys.argv
        if use_timer:
            cfg = ConfigManager.get_config(GlobalConsts.CONFIG_GLOBAL_JSON)
            _worker = Cleaner(cfg)
            _worker.start_daily_checker()
        run_start()
    except Exception as e:
        LogCat.error(f"崩溃：{traceback.format_exc()}")