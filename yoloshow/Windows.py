import os
import time
import threading
from types import SimpleNamespace
from pathlib import Path

import cv2
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    from utils.GlobalLog import LoggerCat
except Exception:
    try:
        from utils import LoggerCat
    except Exception:
        class LoggerCat:
            def info(self, msg): print(msg)
            def warning(self, msg): print(msg)
            def error(self, msg): print(msg)

try:
    from utils import globalDict
except Exception:
    class _GlobalDict:
        _data = {}
        def set_value(self, key, value): self._data[key] = value
        def get_value(self, key, default=None): return self._data.get(key, default)
    globalDict = _GlobalDict()

try:
    from utils.AlarmSystem import AlarmSystem
except Exception:
    class AlarmSystem:
        def trigger_alarm(self, frame, det): pass

from yolo import YOLOSystem, yolo_system


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def project_root() -> Path:
    return Path(__file__).resolve().parents[1] if len(Path(__file__).resolve().parents) > 1 else Path.cwd()


def resolve_path(path: str) -> Path:
    """Resolve a relative path from cwd, current file folder, and project root."""
    raw = Path(path)
    if raw.is_absolute():
        return raw
    candidates = [
        Path.cwd() / raw,
        Path(__file__).resolve().parent / raw,
        project_root() / raw,
    ]
    for item in candidates:
        if item.exists():
            return item
    return project_root() / raw


def frame_to_pixmap(frame, target_size):
    """Convert OpenCV BGR frame to scaled QPixmap."""
    if frame is None:
        return QPixmap()
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, c = rgb_frame.shape
    qimg = QImage(rgb_frame.data, w, h, w * c, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(qimg).scaled(
        target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )


class ImageLoader:
    """Load images from a folder to simulate a video stream."""

    def __init__(self, image_dir="test_images", loop=True, delay=1.0):
        self.logger = LoggerCat()
        self.image_dir = str(resolve_path(image_dir))
        self.loop = loop
        self.delay = delay
        self.running = False
        self.current_frame = None
        self.current_path = ""
        self.lock = threading.Lock()
        self.index = 0
        self.image_paths = self._scan_images()
        self.logger.info(f"测试图片目录：{self.image_dir}，加载 {len(self.image_paths)} 张图片")

    def _scan_images(self):
        folder = Path(self.image_dir)
        if not folder.exists():
            return []
        return sorted(
            str(p) for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        )

    def set_image_dir(self, image_dir):
        self.stop()
        self.image_dir = str(resolve_path(image_dir))
        self.index = 0
        self.image_paths = self._scan_images()
        self.current_frame = None
        self.current_path = ""
        self.logger.info(f"切换测试图片目录：{self.image_dir}，加载 {len(self.image_paths)} 张图片")

    def start(self):
        if self.running:
            return
        if not self.image_paths:
            self.logger.error(f"测试图片文件夹为空或不存在：{self.image_dir}")
            return
        self.running = True
        threading.Thread(target=self._update, daemon=True).start()

    def _update(self):
        while self.running:
            if self.index >= len(self.image_paths):
                if self.loop:
                    self.index = 0
                else:
                    self.running = False
                    break

            path = self.image_paths[self.index]
            frame = cv2.imread(path)
            if frame is not None:
                with self.lock:
                    self.current_frame = frame
                    self.current_path = path
                try:
                    globalDict.set_value("current_frame", frame)
                    globalDict.set_value("current_image_path", path)
                except Exception:
                    pass

            self.index += 1
            time.sleep(self.delay)

    def get_frame(self):
        with self.lock:
            if self.current_frame is None:
                return None, ""
            return self.current_frame.copy(), self.current_path

    def stop(self):
        self.running = False


class StatCard(QFrame):
    def __init__(self, title, value="0"):
        super().__init__()
        self.setObjectName("StatCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("StatTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("StatValue")
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(str(value))


class VideoCard(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("VideoCard")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 14, 14, 14)
        self.title = QLabel(title)
        self.title.setObjectName("PanelTitle")
        self.video_label = QLabel("等待图像输入")
        self.video_label.setObjectName("VideoLabel")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(480, 320)
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.video_label, 1)

    def set_frame(self, frame):
        pixmap = frame_to_pixmap(frame, self.video_label.size())
        self.video_label.setPixmap(pixmap)


class BaseDetectionWindow(QMainWindow):
    """Shared UI and detection logic for single mode and compare mode."""

    def __init__(self, title, image_dir="test_images"):
        super().__init__()
        self.logger = LoggerCat()
        self.setWindowTitle(title)
        self.resize(1360, 860)
        self.setMinimumSize(1180, 760)

        self.image_loader = ImageLoader(image_dir=image_dir, loop=True, delay=1.0)
        self.yolo = yolo_system if yolo_system is not None else YOLOSystem()
        self.alarm = AlarmSystem()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        self.total_frames = 0
        self.total_objects = 0
        self.last_detections = []
        self.last_path = ""

        self._apply_style()

    def _apply_style(self):
        self.setFont(QFont("Microsoft YaHei", 10))
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #0B1220;
                color: #E5EDF8;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            }
            QLabel#AppTitle {
                color: #F8FAFC;
                font-size: 26px;
                font-weight: 800;
                letter-spacing: 1px;
            }
            QLabel#SubTitle {
                color: #8EA4C8;
                font-size: 13px;
            }
            QLabel#PanelTitle {
                color: #DDE7F7;
                font-size: 16px;
                font-weight: 700;
            }
            QLabel#VideoLabel {
                background: #050A14;
                border: 1px solid #20304C;
                border-radius: 18px;
                color: #60708D;
                font-size: 16px;
            }
            QFrame#VideoCard, QFrame#StatCard, QFrame#SidePanel {
                background: #101A2E;
                border: 1px solid #213654;
                border-radius: 22px;
            }
            QLabel#StatTitle {
                color: #8EA4C8;
                font-size: 13px;
            }
            QLabel#StatValue {
                color: #38BDF8;
                font-size: 28px;
                font-weight: 800;
            }
            QPushButton {
                background: #1E3A8A;
                border: none;
                border-radius: 12px;
                color: white;
                padding: 10px 16px;
                font-weight: 700;
            }
            QPushButton:hover { background: #2563EB; }
            QPushButton:pressed { background: #1D4ED8; }
            QPushButton#GhostButton {
                background: #17233A;
                color: #BFD4F6;
                border: 1px solid #2B4369;
            }
            QPushButton#DangerButton {
                background: #991B1B;
            }
            QTableWidget {
                background: #0B1220;
                border: 1px solid #20304C;
                border-radius: 14px;
                gridline-color: #20304C;
                color: #E5EDF8;
                selection-background-color: #1D4ED8;
            }
            QHeaderView::section {
                background: #16233A;
                color: #AFC4E8;
                border: none;
                padding: 8px;
                font-weight: 700;
            }
            QSplitter::handle {
                background: #1D2B45;
                border-radius: 3px;
            }
        """)

    def start(self):
        self.image_loader.start()
        if not self.timer.isActive():
            self.timer.start(30)

    def pause_or_resume(self):
        if self.image_loader.running:
            self.image_loader.stop()
            self.pause_btn.setText("继续检测")
        else:
            self.image_loader.start()
            self.pause_btn.setText("暂停检测")

    def choose_image_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "选择测试图片文件夹", self.image_loader.image_dir)
        if not folder:
            return
        self.image_loader.set_image_dir(folder)
        if not self.image_loader.image_paths:
            QMessageBox.warning(self, "提示", "该文件夹中没有可识别的图片文件。")
            return
        self.start()
        if hasattr(self, "path_label"):
            self.path_label.setText(f"输入源：{folder}")

    def build_table(self):
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(["类别", "置信度", "左上角", "右下角", "告警"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        return table

    def refresh_table(self, detections):
        self.table.setRowCount(len(detections))
        for row, det in enumerate(detections):
            x1, y1, x2, y2 = det["bbox"]
            values = [
                det["class"],
                f'{det["confidence"]:.2f}',
                f"{x1}, {y1}",
                f"{x2}, {y2}",
                "是" if det["confidence"] >= 0.7 else "否",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

    def detect_frame(self, frame):
        detections = self.yolo.detect(frame)
        detected_frame = self.yolo.draw_detections(frame, detections)

        for det in detections:
            if det["confidence"] >= 0.7:
                try:
                    self.alarm.trigger_alarm(detected_frame, det)
                except Exception as exc:
                    self.logger.warning(f"告警触发失败：{exc}")

        return detections, detected_frame

    def update_stats(self, detections, path):
        self.total_frames += 1
        self.total_objects += len(detections)
        high_risk = sum(1 for det in detections if det["confidence"] >= 0.7)

        self.frame_card.set_value(self.total_frames)
        self.object_card.set_value(len(detections))
        self.risk_card.set_value(high_risk)

        if hasattr(self, "status_label"):
            model_path = getattr(self.yolo, "model_path", "未加载")
            image_name = Path(path).name if path else "等待输入"
            self.status_label.setText(f"当前图像：{image_name}  |  模型：{model_path}")

    def update_frame(self):
        raise NotImplementedError

    def closeEvent(self, event):
        self.timer.stop()
        self.image_loader.stop()
        event.accept()


class YOLOSHOWWindow(BaseDetectionWindow):
    """单图检测模式：展示检测结果和告警信息。"""

    def __init__(self):
        super().__init__("机车车顶异物检测系统")
        self.ui = SimpleNamespace()

        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(24, 22, 24, 24)
        main.setSpacing(16)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("机车车顶异物检测系统")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Locomotive Roof Foreign Object Detection · 单图检测模式")
        subtitle.setObjectName("SubTitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.compare_btn = QPushButton("进入对比模式")
        self.compare_btn.clicked.connect(self._open_compare_window)
        self.ui.src_vsmode = self.compare_btn

        self.choose_btn = QPushButton("选择图片目录")
        self.choose_btn.setObjectName("GhostButton")
        self.choose_btn.clicked.connect(self.choose_image_dir)

        self.pause_btn = QPushButton("暂停检测")
        self.pause_btn.setObjectName("GhostButton")
        self.pause_btn.clicked.connect(self.pause_or_resume)

        header.addLayout(title_box, 1)
        header.addWidget(self.choose_btn)
        header.addWidget(self.pause_btn)
        header.addWidget(self.compare_btn)
        main.addLayout(header)

        stats = QHBoxLayout()
        self.frame_card = StatCard("已处理帧数")
        self.object_card = StatCard("当前异物数")
        self.risk_card = StatCard("高风险告警")
        stats.addWidget(self.frame_card)
        stats.addWidget(self.object_card)
        stats.addWidget(self.risk_card)
        main.addLayout(stats)

        splitter = QSplitter(Qt.Horizontal)
        self.video_card = VideoCard("检测画面")
        splitter.addWidget(self.video_card)

        side = QFrame()
        side.setObjectName("SidePanel")
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(16, 16, 16, 16)
        side_title = QLabel("实时检测列表")
        side_title.setObjectName("PanelTitle")
        self.table = self.build_table()
        self.status_label = QLabel("系统初始化中")
        self.status_label.setObjectName("SubTitle")
        self.path_label = QLabel(f"输入源：{self.image_loader.image_dir}")
        self.path_label.setObjectName("SubTitle")

        side_layout.addWidget(side_title)
        side_layout.addWidget(self.table, 1)
        side_layout.addWidget(self.path_label)
        side_layout.addWidget(self.status_label)
        splitter.addWidget(side)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        main.addWidget(splitter, 1)

    def _open_compare_window(self):
        try:
            vs_window = globalDict.get_value("yoloshowvs")
        except Exception:
            vs_window = None
        if vs_window is None:
            vs_window = YOLOSHOWVSWindow()
        vs_window.start()
        vs_window.show()
        self.hide()

    def update_frame(self):
        frame, path = self.image_loader.get_frame()
        if frame is None:
            return

        detections, detected_frame = self.detect_frame(frame)
        self.video_card.set_frame(detected_frame)
        self.refresh_table(detections)
        self.update_stats(detections, path)

        self.last_detections = detections
        self.last_path = path


class YOLOSHOWVSWindow(BaseDetectionWindow):
    """对比模式：左侧原图，右侧检测结果。"""

    def __init__(self):
        super().__init__("对比模式 - 机车车顶异物检测系统")
        self.ui = SimpleNamespace()

        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(24, 22, 24, 24)
        main.setSpacing(16)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("对比模式")
        title.setObjectName("AppTitle")
        subtitle = QLabel("原始车顶图像与 YOLO 检测结果并排显示，便于核验漏检和误检")
        subtitle.setObjectName("SubTitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.single_btn = QPushButton("返回单图模式")
        self.single_btn.clicked.connect(self._open_single_window)
        self.ui.src_singlemode = self.single_btn

        self.choose_btn = QPushButton("选择图片目录")
        self.choose_btn.setObjectName("GhostButton")
        self.choose_btn.clicked.connect(self.choose_image_dir)

        self.pause_btn = QPushButton("暂停检测")
        self.pause_btn.setObjectName("GhostButton")
        self.pause_btn.clicked.connect(self.pause_or_resume)

        header.addLayout(title_box, 1)
        header.addWidget(self.choose_btn)
        header.addWidget(self.pause_btn)
        header.addWidget(self.single_btn)
        main.addLayout(header)

        stats = QHBoxLayout()
        self.frame_card = StatCard("已对比帧数")
        self.object_card = StatCard("当前异物数")
        self.risk_card = StatCard("高风险告警")
        stats.addWidget(self.frame_card)
        stats.addWidget(self.object_card)
        stats.addWidget(self.risk_card)
        main.addLayout(stats)

        video_grid = QGridLayout()
        self.raw_card = VideoCard("原始画面")
        self.result_card = VideoCard("检测结果")
        video_grid.addWidget(self.raw_card, 0, 0)
        video_grid.addWidget(self.result_card, 0, 1)
        main.addLayout(video_grid, 3)

        bottom = QFrame()
        bottom.setObjectName("SidePanel")
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(16, 16, 16, 16)
        bottom_title = QLabel("对比检测明细")
        bottom_title.setObjectName("PanelTitle")
        self.table = self.build_table()
        self.status_label = QLabel("系统初始化中")
        self.status_label.setObjectName("SubTitle")
        self.path_label = QLabel(f"输入源：{self.image_loader.image_dir}")
        self.path_label.setObjectName("SubTitle")

        bottom_layout.addWidget(bottom_title)
        bottom_layout.addWidget(self.table)
        bottom_layout.addWidget(self.path_label)
        bottom_layout.addWidget(self.status_label)
        main.addWidget(bottom, 2)

    def showEvent(self, event):
        super().showEvent(event)
        if not self.timer.isActive():
            self.start()

    def _open_single_window(self):
        try:
            single_window = globalDict.get_value("yoloshow")
        except Exception:
            single_window = None
        if single_window is None:
            single_window = YOLOSHOWWindow()
        single_window.start()
        single_window.show()
        self.hide()

    def update_frame(self):
        frame, path = self.image_loader.get_frame()
        if frame is None:
            return

        detections, detected_frame = self.detect_frame(frame)
        self.raw_card.set_frame(frame)
        self.result_card.set_frame(detected_frame)
        self.refresh_table(detections)
        self.update_stats(detections, path)

        self.last_detections = detections
        self.last_path = path
