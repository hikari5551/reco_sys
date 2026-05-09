import os
import shutil
from tqdm import tqdm
from pycocotools.coco import COCO

# coco 标注json文件路径
anno_path = r"E:\RailFOD23_v2\coco\New_an\train_val.json"
# coco 原图文件夹
img_dir = r"E:\RailFOD23_v2\coco\Images"
# 输出 yolo 数据集保存位置
save_dir = r"../yolo_railfod"
# ==========================================================

# 建立输出文件夹
os.makedirs(os.path.join(save_dir, "images", "train"), exist_ok=True)
os.makedirs(os.path.join(save_dir, "labels", "train"), exist_ok=True)

# 加载COCO
coco = COCO(anno_path)
cat_ids = coco.getCatIds()
cats = coco.loadCats(cat_ids)

# 类别映射：coco类别id -> yolo从0开始id
cat2id = {cat["id"]: idx for idx, cat in enumerate(cats)}
print("类别对应关系：", cat2id)

img_ids = coco.getImgIds()

for img_id in tqdm(img_ids, desc="转换中"):
    img_info = coco.loadImgs(img_id)[0]
    img_name = img_info["file_name"]
    img_w = img_info["width"]
    img_h = img_info["height"]

    # 复制图片到yolo目录
    src_img = os.path.join(img_dir, img_name)
    dst_img = os.path.join(save_dir, "images", "train", img_name)
    shutil.copyfile(src_img, dst_img)

    # 获取该图所有标注
    ann_ids = coco.getAnnIds(imgIds=img_id)
    anns = coco.loadAnns(ann_ids)

    # 生成yolo txt标签
    txt_name = os.path.splitext(img_name)[0] + ".txt"
    txt_path = os.path.join(save_dir, "labels", "train", txt_name)

    with open(txt_path, "w", encoding="utf-8") as f:
        for ann in anns:
            if ann["iscrowd"] == 1:
                continue
            # coco bbox: [x, y, w, h] 左上角坐标、宽高
            x, y, w, h = ann["bbox"]
            # 转yolo归一化中心坐标 + 归一化宽高
            cx = (x + w / 2) / img_w
            cy = (y + h / 2) / img_h
            nw = w / img_w
            nh = h / img_h

            yolo_cls = cat2id[ann["category_id"]]
            f.write(f"{yolo_cls} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}\n")

print("✅ COCO 转 YOLO 完成！")
print(f"输出目录：{save_dir}")