from ultralytics import YOLO
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2

# ===================== 你只需要改这里 =====================
IMG_PATH = "runs/04-perception/dectect/test.png"
SAVE_DIR = "runs/04-perception/dectect"
FONT_SIZE = 40  # 字体大小
# ========================================================

# 加载模型
model = YOLO("yolov8l-seg.pt")
results = model(IMG_PATH)
res = results[0]

# 读取原图
img = np.array(Image.open(IMG_PATH))
h, w = img.shape[:2]

# -------------------- 1. 目标检测图 --------------------
detect_img = res.plot(boxes=True, masks=False, conf=True, labels=True)
Image.fromarray(detect_img[:, :, ::-1]).save(f"{SAVE_DIR}detection.jpg")

# -------------------- 2. 语义分割（黑底 + 同类同色）【正确版】 --------------------
semantic_mask = np.zeros((h, w, 3), dtype=np.uint8)

if res.masks is not None:
    masks = res.masks.data.cpu().numpy()  # 所有实例mask
    classes = res.boxes.cls.cpu().numpy().astype(int)  # 每个实例的类别

    # 给每个类别分配固定颜色
    unique_classes = np.unique(classes)
    color_map = {cls: np.random.randint(0, 255, 3, dtype=np.uint8) for cls in unique_classes}

    # 按类别合并mask（关键！！！）
    cls_mask_dict = {cls: np.zeros((h, w), dtype=bool) for cls in unique_classes}

    for mask, cls in zip(masks, classes):
        mask_resized = cv2.resize(mask, (w, h)) > 0.5
        cls_mask_dict[cls] = np.logical_or(cls_mask_dict[cls], mask_resized)

    # 给每个类别统一上色
    for cls, cls_mask in cls_mask_dict.items():
        semantic_mask[cls_mask] = color_map[cls]

Image.fromarray(semantic_mask).save(f"{SAVE_DIR}semantic_mask.jpg")

# -------------------- 3. 实例分割（黑底 + 每个物体不同色） --------------------
instance_mask = np.zeros((h, w, 3), dtype=np.uint8)

if res.masks is not None:
    masks = res.masks.data.cpu().numpy()
    for mask in masks:
        mask = cv2.resize(mask, (w, h))
        color = np.random.randint(0, 255, 3, dtype=np.uint8)
        instance_mask[mask > 0.5] = color

Image.fromarray(instance_mask).save(f"{SAVE_DIR}instance_mask.jpg")

# -------------------- 读取四张图 --------------------
original = Image.open(IMG_PATH)
detect = Image.open(f"{SAVE_DIR}detection.jpg")
semantic = Image.open(f"{SAVE_DIR}semantic_mask.jpg")
instance = Image.open(f"{SAVE_DIR}instance_mask.jpg")

# -------------------- 给每张图标注文字（可改大小） --------------------
def add_label(img_pil, text):
    draw = ImageDraw.Draw(img_pil)
    # 加载支持大小变化的字体
    font = ImageFont.truetype("arial.ttf", FONT_SIZE)
    draw.text((15, 10), text, fill=(255, 255, 255), font=font)

add_label(original, "Original")
add_label(detect, "Detection")
add_label(semantic, "Semantic Segmentation")
add_label(instance, "Instance Segmentation")

# -------------------- 拼接四宫格 --------------------
original = np.array(original)
detect = np.array(detect)
semantic = np.array(semantic)
instance = np.array(instance)

top_row = np.hstack((original, detect))
bottom_row = np.hstack((semantic, instance))
four_grid = np.vstack((top_row, bottom_row))

Image.fromarray(four_grid).save(f"{SAVE_DIR}four_grid.jpg")
