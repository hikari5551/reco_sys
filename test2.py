import cv2
import os
from yolo import yolo_system

#配置路径
test_image_path = "test_images/4.jpg"
output_dir = "yolo_results"
os.makedirs(output_dir, exist_ok=True)  # 自动创建保存文件夹

#读取图片
frame = cv2.imread(test_image_path)
if frame is None:
    print(f"错误：无法读取图片 {test_image_path}，请检查路径是否正确")
    exit()

print(f"成功读取图片，尺寸：{frame.shape}")

#执行检测
detections = yolo_system.detect(frame)
print(f" 检测到目标数量：{len(detections)}")
for det in detections:
    print(f"  - 类别：{det['class']}，置信度：{det['confidence']}，坐标：{det['bbox']}")

#绘制检测框
img_with_boxes = yolo_system.draw_detections(frame, detections)

#保存图片
save_path = os.path.join(output_dir, "result.jpg")
cv2.imwrite(save_path, img_with_boxes)
print(f" 结果已保存到：{os.path.abspath(save_path)}")

#显示图片
cv2.imshow("YOLO 检测结果", img_with_boxes)
print("\n按任意键关闭窗口...")
cv2.waitKey(0)
cv2.destroyAllWindows()