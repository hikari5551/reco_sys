from PySide6.QtWidgets import QMainWindow, QPushButton, QWidget, QVBoxLayout

class YOLOSHOWWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLOSHOW - 单视图")
        self.setFixedSize(800, 500)
        self.ui = self

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)

        self.src_vsmode = QPushButton("切换到对比模式")
        self.layout.addWidget(self.src_vsmode)

class YOLOSHOWVSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLOSHOW VS - 对比视图")
        self.setFixedSize(1000, 500)
        self.ui = self

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)

        self.src_singlemode = QPushButton("回到单视图")
        self.layout.addWidget(self.src_singlemode)