from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from client.api_client import ApiError, LocoRoofApiClient
from client.config import API_KEY, SERVER_URL

# =========================================================
# 客户端主窗口
# =========================================================
# 客户端只负责：
# 1. 上传图片；
# 2. 上传模型；
# 3. 请求服务器检测；
# 4. 显示服务器返回的原图和检测结果图。
# =========================================================

STYLE = """
QMainWindow { background: #07111f; }
QWidget { color: #eaf4ff; font-family: "Microsoft YaHei"; font-size: 14px; }
QFrame#Card { background: #10223d; border: 1px solid rgba(0, 194, 255, 0.22); border-radius: 14px; }
QLabel#Title { color: #ffffff; font-size: 24px; font-weight: bold; }
QLabel#SubTitle { color: #9fb6d8; font-size: 12px; }
QLabel#ImageView { background: #020817; border: 1px solid rgba(0, 194, 255, 0.28); border-radius: 12px; color: #6d83a7; }
QLineEdit, QComboBox, QTextEdit, QListWidget { background: #07182f; border: 1px solid rgba(135, 180, 255, 0.28); border-radius: 8px; padding: 6px; color: #eaf4ff; }
QPushButton { background: #16345c; border: 1px solid rgba(118, 178, 255, 0.32); border-radius: 10px; padding: 8px 12px; color: #eaf4ff; font-weight: bold; }
QPushButton:hover { background: #1d477b; }
QPushButton#PrimaryButton { background: #0ea5e9; border: none; }
"""


class MainWindow(QMainWindow):
    # 前后端交互客户端主窗口。

    def __init__(self):
        super().__init__()
        self.setWindowTitle("机车车顶异物识别系统 - 客户端")
        self.resize(1350, 820)
        self.setStyleSheet(STYLE)

        self.api = LocoRoofApiClient(SERVER_URL, API_KEY)

        self.current_dataset_id = None
        self.current_image_id = None
        self.current_image_url = None
        self.current_result_url = None

        self._build_ui()

    def _build_ui(self):
        # 创建界面布局。
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(12)

        header = QFrame()
        header.setObjectName("Card")
        header_layout = QHBoxLayout(header)

        title_box = QVBoxLayout()
        title = QLabel("机车车顶异物识别系统")
        title.setObjectName("Title")
        subtitle = QLabel("客户端只负责接口调用；数据集、测试集、模型和 YOLO 推理均在云服务器端完成")
        subtitle.setObjectName("SubTitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box, 1)

        self.server_input = QLineEdit(SERVER_URL)
        self.key_input = QLineEdit(API_KEY)
        self.key_input.setEchoMode(QLineEdit.Password)

        btn_connect = QPushButton("测试连接")
        btn_connect.setObjectName("PrimaryButton")
        btn_connect.clicked.connect(self.test_connection)

        header_layout.addWidget(QLabel("服务器："))
        header_layout.addWidget(self.server_input, 2)
        header_layout.addWidget(QLabel("密钥："))
        header_layout.addWidget(self.key_input, 1)
        header_layout.addWidget(btn_connect)

        root_layout.addWidget(header)

        splitter = QSplitter(Qt.Horizontal)
        root_layout.addWidget(splitter, 1)

        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.log_box = QTextEdit()
        self.log_box.setFixedHeight(135)
        self.log_box.setReadOnly(True)
        root_layout.addWidget(self.log_box)

    def _build_left_panel(self):
        # 左侧控制区。
        panel = QFrame()
        panel.setObjectName("Card")
        panel.setMinimumWidth(390)
        panel.setMaximumWidth(440)
        layout = QVBoxLayout(panel)

        layout.addWidget(QLabel("数据集管理"))
        ds_row = QHBoxLayout()
        self.dataset_name_input = QLineEdit("locomotive_roof_v1")
        btn_create_ds = QPushButton("创建")
        btn_create_ds.clicked.connect(self.create_dataset)
        ds_row.addWidget(self.dataset_name_input, 1)
        ds_row.addWidget(btn_create_ds)
        layout.addLayout(ds_row)

        self.dataset_combo = QComboBox()
        self.dataset_combo.currentIndexChanged.connect(self.on_dataset_changed)
        layout.addWidget(self.dataset_combo)

        btn_refresh_ds = QPushButton("刷新数据集")
        btn_refresh_ds.clicked.connect(self.refresh_datasets)
        layout.addWidget(btn_refresh_ds)

        layout.addWidget(QLabel("图片 / 测试集"))
        self.split_combo = QComboBox()
        self.split_combo.addItems(["test", "train", "val", "unassigned"])
        layout.addWidget(self.split_combo)

        btn_upload_img = QPushButton("上传图片到服务器")
        btn_upload_img.setObjectName("PrimaryButton")
        btn_upload_img.clicked.connect(self.upload_image)
        layout.addWidget(btn_upload_img)

        btn_refresh_img = QPushButton("刷新图片列表")
        btn_refresh_img.clicked.connect(self.refresh_images)
        layout.addWidget(btn_refresh_img)

        self.image_list = QListWidget()
        self.image_list.itemClicked.connect(self.on_image_clicked)
        layout.addWidget(self.image_list, 1)

        layout.addWidget(QLabel("模型管理"))
        btn_upload_model = QPushButton("上传 .pt 模型到服务器")
        btn_upload_model.clicked.connect(self.upload_model)
        layout.addWidget(btn_upload_model)

        btn_refresh_model = QPushButton("刷新模型列表")
        btn_refresh_model.clicked.connect(self.refresh_models)
        layout.addWidget(btn_refresh_model)

        self.model_combo = QComboBox()
        layout.addWidget(self.model_combo)

        btn_activate_model = QPushButton("激活选中模型")
        btn_activate_model.clicked.connect(self.activate_model)
        layout.addWidget(btn_activate_model)

        layout.addWidget(QLabel("检测操作"))
        self.conf_input = QLineEdit("0.25")
        layout.addWidget(self.conf_input)

        btn_detect = QPushButton("检测当前图片")
        btn_detect.setObjectName("PrimaryButton")
        btn_detect.clicked.connect(self.detect_current_image)
        layout.addWidget(btn_detect)

        btn_stats = QPushButton("查看服务器统计")
        btn_stats.clicked.connect(self.show_stats)
        layout.addWidget(btn_stats)

        return panel

    def _build_right_panel(self):
        # 右侧图片对比区。
        panel = QWidget()
        layout = QVBoxLayout(panel)

        grid = QGridLayout()
        self.raw_label = QLabel("原始图片")
        self.raw_label.setObjectName("ImageView")
        self.raw_label.setAlignment(Qt.AlignCenter)
        self.raw_label.setMinimumSize(430, 520)

        self.result_label = QLabel("检测结果")
        self.result_label.setObjectName("ImageView")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setMinimumSize(430, 520)

        grid.addWidget(QLabel("原图（服务器文件）"), 0, 0)
        grid.addWidget(QLabel("检测结果（服务器 YOLO 输出）"), 0, 1)
        grid.addWidget(self.raw_label, 1, 0)
        grid.addWidget(self.result_label, 1, 1)
        layout.addLayout(grid, 1)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFixedHeight(145)
        layout.addWidget(self.result_text)

        return panel

    def reset_api(self):
        # 根据界面输入重建 API 客户端。
        self.api = LocoRoofApiClient(self.server_input.text().strip(), self.key_input.text().strip())

    def log(self, message):
        self.log_box.append(message)

    def show_error(self, message):
        QMessageBox.critical(self, "错误", message)
        self.log(f"[错误] {message}")

    def test_connection(self):
        self.reset_api()
        try:
            data = self.api.health()
            self.log(f"服务器连接成功：{data}")
            self.refresh_datasets()
            self.refresh_models()
        except ApiError as exc:
            self.show_error(str(exc))

    def create_dataset(self):
        self.reset_api()
        name = self.dataset_name_input.text().strip()
        if not name:
            self.show_error("请输入数据集名称")
            return
        try:
            item = self.api.create_dataset(name, "机车车顶异物识别数据集")
            self.log(f"数据集创建成功：{item}")
            self.refresh_datasets()
        except ApiError as exc:
            self.show_error(str(exc))

    def refresh_datasets(self):
        self.reset_api()
        try:
            datasets = self.api.list_datasets()
            self.dataset_combo.clear()
            for ds in datasets:
                self.dataset_combo.addItem(f"{ds['id']} - {ds['name']}", ds["id"])
            self.log(f"已刷新数据集，共 {len(datasets)} 个")
        except ApiError as exc:
            self.show_error(str(exc))

    def on_dataset_changed(self):
        self.current_dataset_id = self.dataset_combo.currentData()
        if self.current_dataset_id:
            self.refresh_images()

    def upload_image(self):
        self.reset_api()
        if not self.current_dataset_id:
            self.show_error("请先选择或创建数据集")
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.jpg *.jpeg *.png *.bmp *.webp)")
        if not file_path:
            return

        try:
            item = self.api.upload_image(self.current_dataset_id, file_path, self.split_combo.currentText())
            self.log(f"图片上传成功：image_id={item['id']}，url={item['url']}")
            self.refresh_images()
        except ApiError as exc:
            self.show_error(str(exc))

    def refresh_images(self):
        self.reset_api()
        if not self.current_dataset_id:
            return
        try:
            images = self.api.list_images(self.current_dataset_id, self.split_combo.currentText())
            self.image_list.clear()
            for img in images:
                text = f"{img['id']} | {img['original_name']} | {img['width']}x{img['height']}"
                item = QListWidgetItem(text)
                item.setData(Qt.UserRole, img)
                self.image_list.addItem(item)
            self.log(f"已刷新图片列表，共 {len(images)} 张")
        except ApiError as exc:
            self.show_error(str(exc))

    def on_image_clicked(self, item):
        img = item.data(Qt.UserRole)
        self.current_image_id = img["id"]
        self.current_image_url = img["url"]
        self.current_result_url = None
        self.result_label.setText("等待检测结果")
        self.result_text.clear()
        self.show_image_from_url(self.raw_label, self.current_image_url)
        self.log(f"当前选择图片：image_id={self.current_image_id}")

    def upload_model(self):
        self.reset_api()
        file_path, _ = QFileDialog.getOpenFileName(self, "选择 YOLO .pt 模型", "", "PyTorch Model (*.pt)")
        if not file_path:
            return
        model_name = Path(file_path).stem
        try:
            item = self.api.upload_model(model_name, file_path, active=True)
            self.log(f"模型上传成功：model_id={item['id']}，active={item['active']}")
            self.refresh_models()
        except ApiError as exc:
            self.show_error(str(exc))

    def refresh_models(self):
        self.reset_api()
        try:
            models = self.api.list_models()
            self.model_combo.clear()
            for m in models:
                tag = "当前" if m["active"] else "未激活"
                self.model_combo.addItem(f"{m['id']} - {m['name']} - {tag}", m["id"])
            self.log(f"已刷新模型列表，共 {len(models)} 个")
        except ApiError as exc:
            self.show_error(str(exc))

    def activate_model(self):
        self.reset_api()
        model_id = self.model_combo.currentData()
        if not model_id:
            self.show_error("请先选择模型")
            return
        try:
            item = self.api.activate_model(model_id)
            self.log(f"模型已激活：{item}")
            self.refresh_models()
        except ApiError as exc:
            self.show_error(str(exc))

    def detect_current_image(self):
        self.reset_api()
        if not self.current_image_id:
            self.show_error("请先选择一张图片")
            return
        try:
            conf = float(self.conf_input.text().strip())
        except ValueError:
            self.show_error("置信度阈值必须是数字，例如 0.25")
            return
        try:
            data = self.api.detect_image(self.current_image_id, conf=conf)
            self.current_result_url = data.get("result_image_url")
            if self.current_result_url:
                self.show_image_from_url(self.result_label, self.current_result_url)

            detections = data.get("detections", [])
            if not detections:
                self.result_text.setPlainText("未检测到异物。")
            else:
                lines = []
                for i, det in enumerate(detections, 1):
                    lines.append(
                        f"#{i} 类别：{det['class_name']}  "
                        f"置信度：{det['confidence']:.3f}  "
                        f"坐标：({det['x1']:.1f}, {det['y1']:.1f}, {det['x2']:.1f}, {det['y2']:.1f})"
                    )
                self.result_text.setPlainText("\n".join(lines))

            self.log(f"检测完成：image_id={self.current_image_id}，目标数={len(detections)}")
        except ApiError as exc:
            self.show_error(str(exc))

    def show_stats(self):
        self.reset_api()
        try:
            stats = self.api.get_stats()
            text = (
                f"数据集数量：{stats['datasets']}\n"
                f"图片数量：{stats['images']}\n"
                f"人工标注数量：{stats['annotations']}\n"
                f"模型数量：{stats['models']}\n"
                f"检测结果数量：{stats['detections']}"
            )
            QMessageBox.information(self, "服务器统计", text)
            self.log(f"服务器统计：{stats}")
        except ApiError as exc:
            self.show_error(str(exc))

    def show_image_from_url(self, label, url):
        # 从服务器下载图片字节，并显示到 QLabel。
        try:
            data = self.api.download_bytes(url)
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if pixmap.isNull():
                label.setText("图片加载失败")
                return
            label.setPixmap(pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except ApiError as exc:
            self.show_error(str(exc))
