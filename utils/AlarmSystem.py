import os
import cv2
import time
from utils import LoggerCat, ConfigManager, globalDict

#但是这个文件好像啥用也没有，先放着吧，以后可能会用到报警系统的功能（?)
# 这个文件定义了一个AlarmSystem类，负责处理机车异物识别的报警逻辑。当检测到异物时，根据配置决定是否触发报警，保存截图，记录日志，并将报警信息写入全局字典供其他模块使用。你可以在YOLO检测到异物时调用这个AlarmSystem的trigger_alarm方法来执行报警操作。
class AlarmSystem:
    def __init__(self):
        """
        机车异物识别报警系统
        - 自动保存报警截图
        - 写入报警日志
        - 可配置报警规则
        """
        self.logger = LoggerCat()
        # 报警文件保存目录
        self.save_dir = "alarms/"
        os.makedirs(self.save_dir, exist_ok=True)
        # 加载配置（如果没有配置文件，用默认值）
        try:
            self.config = ConfigManager.get_config("config/alarm.json")
        except:
            self.config = {}
        # 报警置信度阈值
        self.conf_threshold = self.config.get("confidence_threshold", 0.7)
        # 是否保存截图
        self.save_screenshot = self.config.get("save_screenshot", True)

    def trigger_alarm(self, frame, detection):
        """
        触发报警
        :param frame: 检测到异物的原始图片
        :param detection: YOLO返回的检测结果字典
        """
        conf = detection["confidence"]
        cls_name = detection["class"]

        # 低于阈值不触发报警
        if conf < self.conf_threshold:
            return

        # 日志记录（高亮报警）
        self.logger.error(f"异物报警！类型：{cls_name}，置信度：{conf:.2f}")

        # 保存报警截图
        if self.save_screenshot:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.save_dir, f"alarm_{timestamp}_{cls_name}.jpg")
            cv2.imwrite(save_path, frame)
            self.logger.info(f"报警截图已保存：{save_path}")

        # 写入报警日志文件
        log_path = os.path.join(self.save_dir, "alarm_log.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            log_msg = f"{time.ctime()} - 类型：{cls_name} - 置信度：{conf:.2f}\n"
            f.write(log_msg)

        # 把报警信息写入全局字典，供其他模块（如WebSocket）调用
        alarm_info = {
            "timestamp": time.time(),
            "class": cls_name,
            "confidence": conf,
            "screenshot_path": save_path if self.save_screenshot else None
        }
        globalDict.set_value("latest_alarm", alarm_info)

        return alarm_info