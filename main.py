import sys
import os
import traceback
from PySide6.QtCore import QSharedMemory
from constant.GlobalConsts import GlobalConsts
from utils.GlobalLog import LoggerCat
from utils.FileCleaner import Cleaner
from utils.ConfigManager import ConfigManager
from yolo import yolo_system
import cv2

LogCat = LoggerCat()

sys.path.append(os.path.join(os.getcwd(), "ui"))

INTEGRATION_AVAILABLE = False
try:
    from yolosam.WebSocketSys import get_yoloshow_integration
    INTEGRATION_AVAILABLE = True
except ImportError as e:
    LogCat.error(GlobalConsts.APP_NAME + f" 加载失败：{e}")

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from utils import globalDict

# ====================== 导入窗口类 ======================
from yoloshow.Windows import YOLOSHOWWindow
from yoloshow.Windows import YOLOSHOWVSWindow
from yoloshow.ChangeWindow import yoloshow2vs, vs2yoloshow

_app = None
_initialized = False
_worker = None

# ====================== YOLO图片检测函数 ======================
def run_yolo_demo():
        """子线程执行YOLO文件夹批量检测"""
        #配置文件夹路径
        test_image_dir = "test_images"  # 你的图片文件夹
        output_dir = "yolo_results"
        os.makedirs(output_dir, exist_ok=True)

        #遍历文件夹里的所有文件
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp')  # 支持的图片格式
        image_files = [f for f in os.listdir(test_image_dir)
                       if f.lower().endswith(valid_extensions)]

        if not image_files:
            LogCat.error(f"文件夹 {test_image_dir} 中没有找到图片文件")
            return

        LogCat.info(f"开始批量检测，共找到 {len(image_files)} 张图片")

        #逐个处理图片
        for filename in image_files:
            test_image_path = os.path.join(test_image_dir, filename)
            frame = cv2.imread(test_image_path)

            if frame is None:
                LogCat.error(f"无法读取图片 {test_image_path}，跳过")
                continue

            LogCat.info(f"\n处理图片：{filename}，尺寸：{frame.shape}")
            detections = yolo_system.detect(frame)
            LogCat.info(f"检测到目标数量：{len(detections)}")

            for det in detections:
                LogCat.info(f"- 类别：{det['class']}，置信度：{det['confidence']}，坐标：{det['bbox']}")

            #绘制并保存结果（文件名和原图对应）
            img_with_boxes = yolo_system.draw_detections(frame, detections)
            save_path = os.path.join(output_dir, f"result_{filename}")
            cv2.imwrite(save_path, img_with_boxes)
            LogCat.info(f"结果已保存：{os.path.abspath(save_path)}")

        LogCat.info("\n所有图片检测完成！")
def get_application():
    global _app
    if _app is None:
        _app = QApplication(sys.argv)
        _app.setWindowIcon(QIcon(GlobalConsts.ICON_PATH))
        _app.setStyleSheet("QFrame { border: none; }")
    return _app


def initialize_yoloshow_integration():
    if not INTEGRATION_AVAILABLE:
        return None
    try:
        integration = get_yoloshow_integration()
        if ConfigManager.get_item_bool(GlobalConsts.CONFIG_CAMERA_MAIN_JSON, "websocket_config.enabled"):
            integration.start_websocket_integration()
        globalDict.set_value('yoloshow_integration', integration)
        return integration
    except Exception as outer_e:
        LogCat.error(f"系统初始化失败：{outer_e}")
        return None


def initialize_global_variables():
    global _initialized
    if _initialized:
        LogCat.info("全局变量已初始化，跳过重复初始化")
        return

    # 初始化窗口类
    yoloshow = YOLOSHOWWindow()
    yoloshowvs = YOLOSHOWVSWindow()

    globalDict.init()
    globalDict.set_value('yoloshow', yoloshow)
    globalDict.set_value('yoloshowvs', yoloshowvs)
    _initialized = True


def is_single_instance():
    shared_memory_key = "yoloshow"
    shared_memory = QSharedMemory(shared_memory_key)
    if shared_memory.create(1):
        return True, shared_memory
    else:
        return False, None


def start():
    is_single, shared_memory = is_single_instance()
    if not is_single:
        return

    app = get_application()
    initialize_global_variables()
    integration = initialize_yoloshow_integration()

    if integration:
        LogCat.info(GlobalConsts.APP_NAME + " -- 初始化完成")
    else:
        LogCat.info(GlobalConsts.APP_NAME + " -- 未启用")

    yoloshow_glo = globalDict.get_value('yoloshow')
    yoloshowvs_glo = globalDict.get_value('yoloshowvs')

    # 启动图片识别窗口
    yoloshow_glo.start()
    yoloshow_glo.show()

    # 窗口切换信号
    try:
        yoloshow_glo.ui.src_vsmode.clicked.connect(yoloshow2vs)
        yoloshowvs_glo.ui.src_singlemode.clicked.connect(vs2yoloshow)
    except:
        pass

    def cleanup_on_exit():
        try:
            if integration:
                integration.cleanup()
            ConfigManager.clear_config_cache()
        except:
            pass

    app.aboutToQuit.connect(cleanup_on_exit)
    app.exec()


def handle_exception(inter_e: Exception):
    error_message = f"程序错误：{type(inter_e).__name__}：{inter_e}"
    error_trace = traceback.format_exc()
    LogCat.error(error_message)
    LogCat.error(error_trace)


def wait_for_user_input():
    LogCat.info("错误发生，程序已停止运行。请检查错误日志。")
    if sys.platform == "win32":
        os.system("pause")


def run_start():
    # 【关键】在启动Qt窗口前，先执行YOLO图片检测
    run_yolo_demo()
    # 再启动原有的Qt主程序
    start()


if __name__ == '__main__':
    use_timer_start = '--timer' in sys.argv
    try:
        if use_timer_start:
            config_kit = ConfigManager.get_config(GlobalConsts.CONFIG_GLOBAL_JSON)
            _worker = Cleaner(config_kit)
            _worker.start_daily_checker()
            run_start()
        else:
            run_start()
    except (SystemExit, KeyboardInterrupt):
        LogCat.info("\n程序被中断")
        wait_for_user_input()
    except Exception as e:
        handle_exception(e)
        wait_for_user_input()
    finally:
        LogCat.info(GlobalConsts.APP_NAME + " -- 所有服务已停止！")

