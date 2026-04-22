"""
FoodSave AI — YOLOv8 Food Detection
Detects food items in real-time with bounding boxes
Run: python3 ai/train_yolo.py
"""

import os
import yaml
import shutil
from pathlib import Path
from ultralytics import YOLO

MODEL_DIR  = "ai/models"
YOLO_DIR   = "ai/yolo_dataset"
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(f"{YOLO_DIR}/images/train", exist_ok=True)
os.makedirs(f"{YOLO_DIR}/images/val",   exist_ok=True)
os.makedirs(f"{YOLO_DIR}/labels/train", exist_ok=True)
os.makedirs(f"{YOLO_DIR}/labels/val",   exist_ok=True)

# ── Auto-generate YOLO labels from classifier dataset ──
def create_yolo_dataset():
    print("🔄 Creating YOLO dataset from classifier data...")
    from PIL import Image
    import random

    CLASSES = ["fresh", "semi_fresh", "rotten", "cooked", "packaged"]
    src_dir = Path("ai/dataset")

    for split in ["train", "val"]:
        src_split = src_dir / split
        if not src_split.exists():
            continue

        for cls_idx, cls_name in enumerate(CLASSES):
            cls_dir = src_split / cls_name
            if not cls_dir.exists():
                continue

            imgs = list(cls_dir.glob("*.jpg"))[:200]  # limit for speed
            for img_path in imgs:
                # Copy image
                dest_img = Path(f"{YOLO_DIR}/images/{split}/{img_path.name}")
                shutil.copy2(img_path, dest_img)

                # Create label (full image bounding box)
                label_path = Path(f"{YOLO_DIR}/labels/{split}/{img_path.stem}.txt")
                # YOLO format: class cx cy w h (normalized)
                label_path.write_text(f"{cls_idx} 0.5 0.5 0.9 0.9\n")

    print("  ✅ YOLO dataset created")

# ── Create YAML config ──
def create_yaml():
    config = {
        "path":  os.path.abspath(YOLO_DIR),
        "train": "images/train",
        "val":   "images/val",
        "nc":    5,
        "names": ["fresh", "semi_fresh", "rotten", "cooked", "packaged"]
    }
    yaml_path = f"{YOLO_DIR}/dataset.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    print(f"  ✅ YAML config → {yaml_path}")
    return yaml_path

# ── Train YOLO ──
def train_yolo(yaml_path):
    print("\n🚀 Training YOLOv8 Food Detector...")
    model = YOLO("yolov8s.pt")

    results = model.train(
        data    = yaml_path,
        epochs  = 100,
        imgsz   = 640,
        batch   = 16,
        name    = "foodsave_yolo",
        project = MODEL_DIR,
        save    = True,
        plots   = True,
        patience= 20,
        lr0     = 0.01,
        lrf     = 0.001,
        mosaic  = 1.0,
        mixup   = 0.1,
        verbose = True
    )

    # Export
    model.export(format="onnx")
    print(f"  ✅ YOLO training done!")
    print(f"  📦 Model saved in {MODEL_DIR}/foodsave_yolo/")
    return model

if __name__ == "__main__":
    print("=" * 50)
    print("  FoodSave AI — YOLOv8 Food Detector")
    print("=" * 50)
    create_yolo_dataset()
    yaml_path = create_yaml()
    train_yolo(yaml_path)
    print("\n✅ Detection model ready!")
    print("▶️  Next: python3 ai/inference/predict.py")