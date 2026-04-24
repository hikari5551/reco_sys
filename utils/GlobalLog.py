import logging
import os
from logging.handlers import RotatingFileHandler

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