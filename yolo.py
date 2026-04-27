import cv2
import numpy as np
from utils import LoggerCat, globalDict


class YOLOSystem:
    def __init__(self, model_path="models/yolov8l-best.pt"):
        """
        机车车顶异物识别YOLO系统
        :param model_path: 训练好的YOLO模型路径
        """
        self.logger = LoggerCat()
        self.model = None
        self.classes = ["stone", "plastic_bag", "branch", "metal_object"]
        self.conf_threshold = 0.2
        self.iou_threshold = 0.45
        self._load_model(model_path)

    def _load_model(self, model_path):
        """加载YOLO模型（兼容ultralytics，无依赖时使用模拟模式）"""
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_path)
            self.logger.info(f" YOLO模型加载成功：{model_path}")
        except ImportError:
            self.logger.warning(" ultralytics未安装，使用模拟推理模式")
            self.model = None
        except Exception as e:
            self.logger.error(f"模型加载失败：{e}")
            self.model = None

    def detect(self, frame):
        """
        对输入图片进行异物检测
        :param frame: OpenCV格式的BGR图片
        :return: 检测结果列表，每个元素为字典{"bbox":(x1,y1,x2,y2), "confidence":float, "class":str}
        """
        if self.model is None:
            # 模拟推理：返回空结果，避免程序崩溃
            return []

        try:
            results = self.model.predict(
                frame,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                verbose=False
            )
            detections = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = round(float(box.conf[0]), 2)
                    cls_id = int(box.cls[0])
                    detections.append({
                        "bbox": (x1, y1, x2, y2),
                        "confidence": conf,
                        "class": self.classes[cls_id] if cls_id < len(self.classes) else "unknown"
                    })
            # 把检测结果写入全局字典，供其他模块调用
            globalDict.set_value("detections", detections)
            return detections
        except Exception as e:
            self.logger.error(f"推理失败：{e}")
            return []

    def draw_detections(self, frame, detections):
        """
        在图片上绘制检测框和标签
        :param frame: 原始图片
        :param detections: detect()返回的检测结果
        :return: 绘制好的图片
        """
        img = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            conf = det["confidence"]
            cls_name = det["class"]

            # 绘制矩形框（红色）
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)

            # 绘制标签文字
            label = f"{cls_name} {conf:.2f}"
            cv2.putText(
                img, label, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2
            )
        return img


# 全局实例（给 Window.py 调用）
yolo_system = YOLOSystem()