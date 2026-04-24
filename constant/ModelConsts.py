class ModelConsts:
   __slots__ = ()  # 禁止动态添加属性


   # 模型名称映射规则 yoloclass
   MODEL_MAPPING = {
       'yolov8n-class-best': 'yoloclass',
       'yolov8n-best-lt': 'yolov8',
       'yolov8l': 'yolov8',
       'yolov8n': 'yolov8',
       'yolov5n': 'yolov5',
       'yolov5s': 'yolov5',
       'yolov5m': 'yolov5',
       'yolov5l': 'yolov5',
       'yolov5x': 'yolov5',
       'yolov7': 'yolov7',
       'yolov9': 'yolov9',
       'yolov10': 'yolov10',
       'yolov11': 'yolov11',
       'rtdetr': 'rtdetr',
       'fastsam': 'fastsam',
       'sam': 'sam'
   }

   DEFAULT_MODELS = ["yolov8n", "yolov8s", "yolov8m", "yolov8l"]

   ALL_MODEL_NAMES = ["yolov5", "yolov7", "yolov8", "yolov9", "yolov10",
                       "yolov11", "yolov5-seg", "yolov8-seg", "rtdetr",
                       "yolov8-pose", "yolov8-obb", "fastsam", "sam", "samv2"]

    # GlobalConsts.MODEL_NAMES_STR
   MODEL_NAMES_STR = "yolov5 yolov7 yolov8 yolov9 yolov10 yolov5-seg yolov8-seg rtdetr yolov8-pose yolov8-obb"

