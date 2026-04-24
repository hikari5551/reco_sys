from utils import globalDict

class YOLOModel:
    def __init__(self):
        self.model = None
        self.load_model()

    def load_model(self):
        name = globalDict.get_value("yoloname", "yolov8n.pt")
        print(f"[YOLO] 加载模型：{name}")
        self.model = "loaded"

    def predict(self, frame):
        return []

yolo_model = YOLOModel()