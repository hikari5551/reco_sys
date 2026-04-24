import cv2
import os
import threading
import time
from utils import globalDict, LoggerCat

class ImageLoader:
    def __init__(self, image_dir="test_images", loop=True, delay=1.0):
        """
        图片读取器
        :param image_dir: 测试图片文件夹路径
        :param loop: 是否循环播放
        :param delay: 每张图片的显示间隔（秒）
        """
        self.logger = LoggerCat()
        self.image_dir = image_dir
        self.loop = loop
        self.delay = delay
        self.running = False
        self.current_frame = None
        self.lock = threading.Lock()

        # 读取文件夹里的所有图片
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
        threading.Thread(target=self._update, daemon=True).start()

    def _update(self):
        while self.running:
            if self.index >= len(self.image_paths):
                if self.loop:
                    self.index = 0
                else:
                    break

            # 读取当前图片
            path = self.image_paths[self.index]
            frame = cv2.imread(path)
            if frame is not None:
                with self.lock:
                    self.current_frame = frame
                # 写入全局字典，供YOLO模块读取
                globalDict.set_value("current_frame", frame)
                globalDict.set_value("current_image_path", path)
            else:
                self.logger.warning(f"图片读取失败: {path}")

            self.index += 1
            time.sleep(self.delay)

    def get_frame(self):
        with self.lock:
            return self.current_frame.copy() if self.current_frame is not None else None

    def stop(self):
        self.running = False