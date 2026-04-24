import os
import time

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