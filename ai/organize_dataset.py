"""
FoodSave AI — Dataset Organizer
Extracts all ZIPs, merges, cleans, augments
Run: python3 ai/organize_dataset.py
"""

import os
import shutil
import zipfile
import random
import hashlib
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np

# ── Config ──
RAW_DIR    = "ai/dataset_raw"
OUT_DIR    = "ai/dataset"
IMG_SIZE   = (224, 224)
VAL_SPLIT  = 0.15
TEST_SPLIT = 0.05

CLASSES = ["fresh", "semi_fresh", "rotten", "cooked", "packaged"]

# Create output dirs
for split in ["train", "val", "test"]:
    for cls in CLASSES:
        os.makedirs(f"{OUT_DIR}/{split}/{cls}", exist_ok=True)

# ── STEP 1: Extract all ZIPs ──
def extract_all_zips():
    raw = Path(RAW_DIR)
    if not raw.exists():
        print("⚠️  No dataset_raw folder found")
        return

    for zf in raw.glob("**/*.zip"):
        dest = raw / zf.stem
        if not dest.exists():
            print(f"📦 Extracting {zf.name}...")
            try:
                with zipfile.ZipFile(zf, 'r') as z:
                    z.extractall(dest)
                print(f"  ✅ Done → {dest}")
            except Exception as e:
                print(f"  ❌ Failed: {e}")

# ── STEP 2: Map folders to classes ──
FOLDER_MAP = {
    # fresh → edible
    "fresh":           "fresh",
    "freshapple":      "fresh",
    "freshbanana":     "fresh",
    "freshorange":     "fresh",
    "freshcarrot":     "fresh",
    "fresh_fruit":     "fresh",
    "fresh_veg":       "fresh",
    "healthy":         "fresh",
    "good":            "fresh",
    "unripe":          "fresh",
    "ripe":            "fresh",

    # semi_fresh → slightly old
    "stale":           "semi_fresh",
    "semifresh":       "semi_fresh",
    "semi_fresh":      "semi_fresh",
    "medium":          "semi_fresh",
    "used":            "semi_fresh",

    # rotten → biogas
    "rotten":          "rotten",
    "rottenapple":     "rotten",
    "rottenbanana":    "rotten",
    "rottenorange":    "rotten",
    "spoiled":         "rotten",
    "bad":             "rotten",
    "waste":           "rotten",
    "expired":         "rotten",
    "moldy":           "rotten",

    # cooked food
    "cooked":          "cooked",
    "indian":          "cooked",
    "food":            "cooked",
    "meal":            "cooked",
    "curry":           "cooked",

    # packaged
    "packaged":        "packaged",
    "processed":       "packaged",
    "canned":          "packaged",
}

def get_class_for_folder(folder_name):
    name = folder_name.lower().replace(" ", "").replace("_", "")
    for key, cls in FOLDER_MAP.items():
        if key.replace("_", "") in name:
            return cls
    return None

def get_image_hash(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

# ── STEP 3: Collect and copy images ──
def collect_images():
    raw  = Path(RAW_DIR)
    seen = set()
    counts = {cls: 0 for cls in CLASSES}

    all_images = []

    for img_path in raw.glob("**/*"):
        if img_path.suffix.lower() not in ['.jpg','.jpeg','.png','.webp']:
            continue

        folder = img_path.parent.name
        cls    = get_class_for_folder(folder)
        if not cls:
            # Try parent's parent
            cls = get_class_for_folder(img_path.parent.parent.name)
        if not cls:
            continue

        # Check duplicate
        try:
            h = get_image_hash(img_path)
            if h in seen:
                continue
            seen.add(h)
        except:
            continue

        all_images.append((img_path, cls))

    print(f"\n📊 Found {len(all_images)} unique images")

    # Shuffle and split
    random.shuffle(all_images)

    for cls in CLASSES:
        cls_imgs = [(p,c) for p,c in all_images if c==cls]
        n        = len(cls_imgs)
        if n == 0:
            print(f"  ⚠️  No images for class: {cls}")
            continue

        n_val  = max(1, int(n * VAL_SPLIT))
        n_test = max(1, int(n * TEST_SPLIT))
        n_train = n - n_val - n_test

        splits = [
            ("train", cls_imgs[:n_train]),
            ("val",   cls_imgs[n_train:n_train+n_val]),
            ("test",  cls_imgs[n_train+n_val:])
        ]

        for split_name, split_imgs in splits:
            for i, (src, c) in enumerate(split_imgs):
                dest_dir  = Path(f"{OUT_DIR}/{split_name}/{c}")
                dest_path = dest_dir / f"{c}_{split_name}_{i:05d}.jpg"
                try:
                    img = Image.open(src).convert("RGB").resize(IMG_SIZE)
                    img.save(dest_path, "JPEG", quality=92)
                    counts[c] += 1
                except Exception as e:
                    pass

        print(f"  ✅ {cls}: {n} images → train/val/test split")

    return counts

# ── STEP 4: Augment training data ──
def augment_dataset():
    print("\n🔄 Augmenting training data...")
    train_dir = Path(f"{OUT_DIR}/train")

    for cls_dir in train_dir.iterdir():
        if not cls_dir.is_dir():
            continue

        images  = list(cls_dir.glob("*.jpg"))
        n       = len(images)
        target  = max(1500, n)
        needed  = target - n

        print(f"  {cls_dir.name}: {n} → {target} images (+{needed} augmented)")

        aug_count = 0
        while aug_count < needed:
            src = random.choice(images)
            try:
                img = Image.open(src).convert("RGB")

                # Random augmentations
                ops = random.sample([
                    lambda i: i.rotate(random.randint(-30,30)),
                    lambda i: i.transpose(Image.FLIP_LEFT_RIGHT),
                    lambda i: ImageEnhance.Brightness(i).enhance(random.uniform(0.6,1.4)),
                    lambda i: ImageEnhance.Contrast(i).enhance(random.uniform(0.7,1.3)),
                    lambda i: i.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5,2))),
                    lambda i: ImageEnhance.Saturation(i).enhance(random.uniform(0.5,1.5)),
                    lambda i: ImageEnhance.Sharpness(i).enhance(random.uniform(0,2)),
                ], k=random.randint(2,4))

                for op in ops:
                    img = op(img)

                # Crop simulation
                if random.random() > 0.5:
                    w, h = img.size
                    margin = int(min(w,h)*0.1)
                    left   = random.randint(0, margin)
                    top    = random.randint(0, margin)
                    right  = w - random.randint(0, margin)
                    bottom = h - random.randint(0, margin)
                    img    = img.crop((left, top, right, bottom))

                img = img.resize(IMG_SIZE)
                dest = cls_dir / f"aug_{cls_dir.name}_{aug_count:05d}.jpg"
                img.save(dest, "JPEG", quality=88)
                aug_count += 1

            except Exception:
                pass

    print("  ✅ Augmentation complete")

# ── MAIN ──
if __name__ == "__main__":
    print("🚀 FoodSave AI — Dataset Organizer")
    print("=" * 45)

    print("\n📦 Step 1: Extracting ZIPs...")
    extract_all_zips()

    print("\n🗂️  Step 2: Collecting & cleaning images...")
    counts = collect_images()

    print("\n📊 Dataset Summary:")
    for cls, n in counts.items():
        print(f"  {cls}: {n} images")

    print("\n🔄 Step 3: Augmenting...")
    augment_dataset()

    # Final count
    print("\n✅ Final Dataset:")
    for split in ["train","val","test"]:
        for cls in CLASSES:
            p = Path(f"{OUT_DIR}/{split}/{cls}")
            n = len(list(p.glob("*.jpg"))) if p.exists() else 0
            if n > 0:
                print(f"  {split}/{cls}: {n}")

    print("\n🎉 Dataset ready for training!")