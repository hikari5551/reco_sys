import os
import threading
from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QTimer, Qt
import cv2

from AlarmSystem import AlarmSystem
from utils import globalDict, LoggerCat
from yolo import YOLOSystem



#直接在本文件里定义ImageLoader，避免导入错误
class ImageLoader:
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

    def start(self):
        if not self.image_paths:
            self.logger.error("测试图片文件夹为空！")
            return
        self.running = True
        import threading
        threading.Thread(target=self._update, daemon=True).start()

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

    def get_frame(self):
        with self.lock:
            return self.current_frame.copy() if self.current_frame is not None else None

    def stop(self):
        self.running = False

# 主窗口类
class YOLOSHOWWindow(QMainWindow):
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

    def start(self):
        self.image_loader.start()
        self.timer.start(30)

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

    def closeEvent(self, event):
        self.timer.stop()
        self.image_loader.stop()
        event.accept()


class YOLOSHOWVSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("对比模式 - 机车车顶异物识别系统")
        self.setFixedSize(1280, 800)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)