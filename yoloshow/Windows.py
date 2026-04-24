import sys
import os
import time
import threading
from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QTimer, Qt
import cv2
from utils import globalDict, LoggerCat

# 1. 直接在本文件里定义AlarmSystem，避免导入错误
class AlarmSystem:
    def __init__(self):
        self.logger = LoggerCat()
        self.save_dir = "alarms"
        os.makedirs(self.save_dir, exist_ok=True)

    def trigger_alarm(self, frame, detection):
        cls = detection["class"]
        conf = detection["confidence"]
        self.logger.error(f"🚨 检测到异物：{cls} ({conf})")
        name = f"alarm_{int(time.time())}.jpg"
        path = os.path.join(self.save_dir, name)
        cv2.imwrite(path, frame)
        return path

# 2. 直接在本文件里定义ImageLoader，避免导入错误
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

# 3. 直接在本文件里定义YOLOSystem，避免导入错误
class YOLOSystem:
    def __init__(self, model_path="yolov8l-best.pt"):
        self.logger = LoggerCat()
        self.model = None
        self.classes = ["stone", "plastic_bag", "branch", "metal_object"]
        self.conf_threshold = 0.5
        self.iou_threshold = 0.45
        try:
            from ultralytics import YOLO
            # 强制关闭联网更新检查
            os.environ['ULTRALYTICS_OFFLINE'] = '1'
            self.model = YOLO(model_path)
            self.logger.info(f"✅ YOLO模型加载成功：{model_path}")
        except Exception as e:
            self.logger.warning(f"⚠️ 使用模拟模式，模型加载失败：{e}")
            self.model = None

    def detect(self, frame):
        if self.model is None:
            return []
        try:
            results = self.model.predict(frame, conf=self.conf_threshold, iou=self.iou_threshold, verbose=False)
            detections = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = round(float(box.conf[0]), 2)
                    cls_id = int(box.cls[0])
                    detections.append({
                        "bbox": (x1, y1, x2, y2),
                        "confidence": conf,
                        "class": self.classes[cls_id] if cls_id < len(self.classes) else "unknown"
                    })
            globalDict.set_value("detections", detections)
            return detections
        except Exception as e:
            self.logger.error(f"推理失败：{e}")
            return []

    def draw_detections(self, frame, detections):
        img = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = f"{det['class']} {det['confidence']:.2f}"
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        return img

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