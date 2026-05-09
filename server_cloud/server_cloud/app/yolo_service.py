from pathlib import Path
from typing import Any
import uuid

import cv2

from app.config import PUBLIC_BASE_URL, RESULT_DIR

# =========================================================
# YOLO 推理服务
# =========================================================
# 该文件只在服务器端使用。
# 客户端不需要安装 ultralytics，也不需要保存 .pt。
# =========================================================


class YOLOService:
    # YOLO 模型加载与推理封装。

    def __init__(self):
        self._model = None
        self._model_path = None

    def load(self, model_path: str):
        # 加载模型。为了节省时间，已经加载过的模型会被缓存。
        try:
            from ultralytics import YOLO
        except Exception as exc:
            raise RuntimeError("服务器未安装 ultralytics，请安装 requirements.txt") from exc

        path = Path(model_path)
        if not path.exists() or path.suffix.lower() != ".pt":
            raise FileNotFoundError(f"模型文件不存在：{model_path}")

        if self._model is None or str(path) != self._model_path:
            self._model = YOLO(str(path), task="detect")
            self._model_path = str(path)

        return self._model

    def predict(self, image_path: str, model_path: str, conf: float = 0.25) -> list[dict[str, Any]]:
        # 对单张图片执行 YOLO 检测，返回类别、置信度和坐标。
        model = self.load(model_path)
        results = model.predict(source=image_path, conf=conf, verbose=False)

        names = getattr(model, "names", {})
        detections = []

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(float, box.xyxy[0])
                cls_id = int(box.cls[0])
                class_name = names.get(cls_id, f"class_{cls_id}") if isinstance(names, dict) else f"class_{cls_id}"

                detections.append({
                    "class_name": str(class_name),
                    "confidence": float(box.conf[0]),
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                })

        return detections

    def draw_result_image(self, image_path: str, detections: list[dict[str, Any]]) -> tuple[str | None, str | None]:
        # 将检测框绘制到图片上，并保存成结果图。
        image = cv2.imread(str(image_path))
        if image is None:
            return None, None

        for det in detections:
            x1, y1, x2, y2 = map(int, [det["x1"], det["y1"], det["x2"], det["y2"]])
            conf = float(det["confidence"])
            class_name = str(det["class_name"])

            # 高置信度用红色，低置信度用橙色。
            color = (0, 0, 255) if conf >= 0.7 else (0, 165, 255)

            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            label = f"{class_name} {conf:.2f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
            y0 = max(0, y1 - th - 8)
            cv2.rectangle(image, (x1, y0), (x1 + tw + 8, y1), color, -1)
            cv2.putText(image, label, (x1 + 4, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        RESULT_DIR.mkdir(parents=True, exist_ok=True)
        result_name = f"result_{uuid.uuid4().hex}.jpg"
        result_path = RESULT_DIR / result_name
        cv2.imwrite(str(result_path), image)

        result_url = f"{PUBLIC_BASE_URL}/results/{result_name}"
        return str(result_path), result_url


# 全局单例，整个后端进程共用一个模型服务对象。
yolo_service = YOLOService()
