# 测试用极简代码
from ultralytics import YOLO
import cv2
import os

model = YOLO("yolov8n.pt")


# 注意路径写法：Windows 用 r"路径" 避免转义问题
img_path = r"E:\PyCharm 2026.1\新建文件夹\test_images\2.jpg"

# 3. 先检查文件是否存在
if not os.path.exists(img_path):
        print(f"错误：图片路径不存在！{img_path}")
        exit()

    # 4. 执行推理，先不显示，只保存结果
results = model(img_path, conf=0.25)
for r in results:
    annotated_img = r.plot()
    cv2.imwrite("result.jpg", annotated_img)  # 保存到项目文件夹
    print("✅ 识别完成！请在项目文件夹中打开 result.jpg 查看结果")