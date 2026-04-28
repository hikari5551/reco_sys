import logging
import os
from logging.handlers import RotatingFileHandler
# 这个文件定义了一个LoggerCat类，封装了Python的logging模块，提供了一个简单的接口来记录日志。日志会同时输出到控制台和文件中，文件会自动轮转以防止过大。你可以在项目的其他模块中导入并使用这个LoggerCat类来记录信息、错误、警告等日志。
class LoggerCat:
    def __init__(self, log_path="logs/app.log", max_bytes=10*1024*1024, backup_count=5):
        self.logger = logging.getLogger("LoggerCat")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if self.logger.handlers:
            return

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path, encoding="utf-8", maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg):
        self.logger.error(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def debug(self, msg):
        self.logger.debug(msg)