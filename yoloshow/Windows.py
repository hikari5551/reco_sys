import os
import threading
from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QTimer, Qt
import cv2

from utils.AlarmSystem import AlarmSystem
from utils import globalDict, LoggerCat
from yolo import YOLOSystem



#直接在本文件里定义ImageLoader，避免导入错误
# 这个类负责从指定文件夹加载图片，模拟视频流输入
class ImageLoader:
    # 初始化方法，设置图片目录、循环播放和加载间隔
    def __init__(self, image_dir="test_images", loop=True, delay=1.0):
        self.logger = LoggerCat()
        self.image_dir = image_dir
        self.loop = loop
        self.delay = delay
        self.running = False
        self.current_frame = None
        self.lock = threading.Lock()
        self.image_paths = []
        if os.path.exists(image_dir):
            for f in os.listdir(image_dir):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    self.image_paths.append(os.path.join(image_dir, f))
        self.index = 0
        self.logger.info(f"加载了 {len(self.image_paths)} 张测试图片")

# 启动图片加载线程，持续更新当前帧
    def start(self):
        if not self.image_paths:
            self.logger.error("测试图片文件夹为空！")
            return
        self.running = True
        import threading
        threading.Thread(target=self._update, daemon=True).start()

# 更新当前帧的方法，循环读取图片并存储在全局字典中，供其他模块调用
    def _update(self):
        import time
        while self.running:
            if self.index >= len(self.image_paths):
                if self.loop:
                    self.index = 0
                else:
                    break
            path = self.image_paths[self.index]
            frame = cv2.imread(path)
            if frame is not None:
                with self.lock:
                    self.current_frame = frame
                globalDict.set_value("current_frame", frame)
            self.index += 1
            time.sleep(self.delay)

# 获取当前帧的方法，返回当前加载的图片
    def get_frame(self):
        with self.lock:
            return self.current_frame.copy() if self.current_frame is not None else None

# 停止图片加载线程的方法，设置运行标志为False
    def stop(self):
        self.running = False

# 主窗口类
class YOLOSHOWWindow(QMainWindow):
    # 初始化方法，设置窗口标题、大小和布局，并初始化各个模块（图片加载、YOLO检测、报警系统）
    def __init__(self):
        super().__init__()
        self.setWindowTitle("机车车顶异物识别系统")
        self.setFixedSize(1280, 800)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.video_label)
        # 初始化模块（全部在本文件内定义，无导入依赖）
        self.image_loader = ImageLoader(image_dir="test_images", loop=True, delay=1.0)
        self.yolo = YOLOSystem(model_path="yolov8l-best.pt")
        self.alarm = AlarmSystem()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

# 启动方法，启动图片加载和定时器，定时器每30ms调用一次update_frame方法更新显示
    def start(self):
        self.image_loader.start()
        self.timer.start(30)

# 更新帧的方法，获取当前帧，进行YOLO检测，绘制检测结果，并触发报警系统（如果检测到高置信度的异物），最后将处理后的帧显示在窗口中
    def update_frame(self):
        frame = self.image_loader.get_frame()
        if frame is None:
            return
        detections = self.yolo.detect(frame)
        frame = self.yolo.draw_detections(frame, detections)
        for det in detections:
            if det["confidence"] > 0.7:
                self.alarm.trigger_alarm(frame, det)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, c = rgb_frame.shape
        qimg = QImage(rgb_frame.data, w, h, w * c, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qimg).scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

# 关闭事件处理方法，停止定时器和图片加载线程，确保资源清理干净
    def closeEvent(self, event):
        self.timer.stop()
        self.image_loader.stop()
        event.accept()

# 对比模式窗口类，结构与主窗口类似，但可以在这里添加对比显示的功能（如原图和检测结果并排显示）
class YOLOSHOWVSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("对比模式 - 机车车顶异物识别系统")
        self.setFixedSize(1280, 800)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)