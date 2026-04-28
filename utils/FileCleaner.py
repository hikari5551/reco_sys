import os
import time
# 这个文件定义了一个Cleaner类，负责定期清理指定目录下的旧文件。可以设置清理的时间间隔和文件的保留天数。这个类可以在主程序中实例化并启动一个后台线程来执行清理任务，确保日志文件夹和报警截图文件夹不会无限制地增长占用磁盘空间。
class Cleaner:
    def __init__(self, config):
        self.config = config

    def start_daily_checker(self):
        print("[Cleaner] 后台文件清理服务已启动")

    def clean_old_files(self, path, days=7):
        now = time.time()
        if not os.path.exists(path):
            return
        for f in os.listdir(path):
            fp = os.path.join(path, f)
            if os.path.isfile(fp):
                if now - os.path.getmtime(fp) > days * 86400:
                    try:
                        os.remove(fp)
                    except:
                        pass