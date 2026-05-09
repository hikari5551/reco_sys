import sys
from PySide6.QtWidgets import QApplication
from client.main_window import MainWindow

# =========================================================
# 客户端启动入口
# =========================================================
# 注意：客户端不再运行 yolo.py，不再保存 .pt 模型。
# =========================================================


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
