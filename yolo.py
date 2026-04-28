import cv2
from ultralytics import YOLO
import os
from utils import LoggerCat, globalDict  # 导入你项目里的日志和全局字典工具

# YOLO 目标检测系统类，负责模型加载、推理和结果处理
class YOLOSystem:
    """
    YOLO 目标检测系统
    功能：
    1. 纯本地加载 YOLOv8 模型，禁用所有网络请求
    2. 对输入图像进行目标检测，返回结构化结果
    3. 支持检测结果的可视化绘制
    """
    def __init__(self, model_path="models/yolov8l-best.pt"):
        """
        初始化 YOLO 系统
        :param model_path: 本地模型权重文件路径（默认：models/yolov8l-best.pt）
        """
        # 初始化日志器，用于打印运行信息和错误
        self.logger = LoggerCat()

        # 模型能识别的类别列表，和你训练模型时的类别顺序必须完全一致
        self.classes = ["stone", "plastic_bag", "branch", "metal_obj"]

        # 置信度阈值：低于此值的检测结果会被过滤掉，减少误检
        self.conf_threshold = 0.2
        # IOU阈值：非极大值抑制（NMS）时使用，过滤掉重叠过多的重复框
        self.iou_threshold = 0.45

        # 模型对象，初始为None，加载成功后才会被赋值
        self.model = None

        # 调用模型加载方法，传入模型路径
        self._load_model(model_path)

    def _load_model(self, model_path):
        """
        加载本地 YOLO 模型（私有方法，仅内部调用）
        核心特点：禁用 ultralytics 的所有网络请求，纯本地加载
        :param model_path: 本地模型权重文件路径
        """
        try:
            # 第一步：检查模型文件是否真的存在，避免路径错误
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"模型文件不存在，请检查路径：{model_path}")

            # 第二步：禁用 ultralytics 的网络请求（关键！解决 GitHub 连接报错）
            os.environ['ULTRALYTICS_HUB'] = 'False'          # 关闭模型仓库访问
            os.environ['ULTRALYTICS_CONFIG_DIR'] = os.path.abspath(".")  # 配置文件放在当前目录

            # 第三步：加载本地模型，明确指定任务类型为目标检测（detect）
            self.model = YOLO(model_path, task='detect')
            self.logger.info(f"✅ YOLO 模型加载成功，路径：{model_path}")

        except Exception as e:
            # 捕获所有加载过程中的异常，打印错误信息
            self.logger.error(f"❌ 模型加载失败，错误原因：{str(e)}")
            self.model = None  # 加载失败时，将模型设为None，后续检测会自动处理

    def detect(self, frame):
        """
        目标检测主方法，输入图像帧，返回检测结果
        :param frame: 输入图像（OpenCV 格式，BGR 通道）
        :return: 检测结果列表，每个元素包含bbox、置信度和类别名
        """
        # 先判断模型是否加载成功，避免后续调用报错
        if self.model is None:
            # 只打印一次警告，防止循环调用时刷屏
            if not hasattr(self, "_warned"):
                self.logger.warning("⚠️ 模型未加载，无法执行检测，将返回空结果")
                self._warned = True
            return []

        try:
            # 执行推理，设置参数：置信度、IOU阈值、关闭冗余日志输出
            results = self.model.predict(
                source=frame,          # 输入图像
                conf=self.conf_threshold,  # 置信度过滤
                iou=self.iou_threshold,     # 非极大值抑制
                verbose=False          # 关闭控制台冗余输出
            )

            # 解析检测结果，整理成结构化数据
            detections = []
            for result in results:
                for box in result.boxes:
                    # 提取边界框坐标（x1,y1为左上角，x2,y2为右下角）
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    # 提取置信度，保留两位小数
                    conf = round(float(box.conf[0]), 2)
                    # 提取类别ID，转换为对应的类别名称
                    cls_id = int(box.cls[0])
                    cls_name = self.classes[cls_id] if cls_id < len(self.classes) else "unknown"

                    # 将单个检测结果存入列表
                    detections.append({
                        "bbox": (x1, y1, x2, y2),
                        "confidence": conf,
                        "class": cls_name
                    })

            # 将检测结果存入全局字典，供其他模块（如WebSocket、UI界面）使用
            globalDict.set_value("detections", detections)
            return detections

        except Exception as e:
            # 捕获推理过程中的异常，打印错误信息并返回空结果
            self.logger.error(f"❌ 目标检测推理失败，错误原因：{str(e)}")
            return []

    def draw_detections(self, frame, detections):
        """
        在图像上绘制检测结果（边界框和标签）
        :param frame: 原始图像
        :param detections: detect() 方法返回的检测结果列表
        :return: 绘制了检测框的图像
        """
        # 复制一份原始图像，避免修改原图
        img = frame.copy()
        for det in detections:
            # 从检测结果中提取边界框、置信度和类别名
            x1, y1, x2, y2 = det["bbox"]
            conf = det["confidence"]
            cls_name = det["class"]

            # 绘制矩形边界框，颜色为红色，线宽2
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            # 拼接标签文本：类别名 + 置信度
            label = f"{cls_name} {conf:.2f}"
            # 在边界框上方绘制标签文本，颜色为红色，字体大小0.5
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        return img

# 实例化 YOLO 系统对象，供其他文件（如main.py）导入使用
yolo_system = YOLOSystem()
#彩蛋：如果你看到这里，说明你真的是这个项目组里面除了我以外唯一一个读完所有源码的人了，凭截图可以找我获取神必奖励
#记于2026.4.28，晚自习改了俩小时代码，最后实时监测功能也没写出来，空悲切，，，不如复习线代和大物（
#这个问题的主要报错是yolo文件很难定位到模型文件，同样的函数在main文件里可以跑但是在yolo里面跑不了，跟水土不服一样
#有个关于xcpc的打油诗挺有趣
"""惯于通宵切题时
火腿泡面榨菜丝
梦中过题常惊醒
榜单变幻大佬名
忍看排名成垫底
怒喷小人摘金银
无人陪我过春夜
次次打铁伤心神"""