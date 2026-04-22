"""
Organize raw downloaded images into 4 FoodSave AI classes.
Run AFTER downloading datasets from Kaggle.
"""

import os
import shutil
import random
from pathlib import Path

RAW_DIR  = "ai/dataset_raw"
OUT_DIR  = "ai/dataset"
CLASSES  = ["edible", "ngo_grade", "poultry_grade", "biogas"]

# Create output folders
for cls in CLASSES:
    os.makedirs(f"{OUT_DIR}/{cls}", exist_ok=True)

def move_images(src_folder, dest_class, limit=None):
    """Move images from source folder to a class folder."""
    src  = Path(src_folder)
    dest = Path(f"{OUT_DIR}/{dest_class}")
    if not src.exists():
        print(f"⚠️ Folder not found: {src_folder}")
        return 0

    images = list(src.glob("*.jpg")) + list(src.glob("*.png")) + list(src.glob("*.jpeg"))
    if limit:
        images = images[:limit]

    for img in images:
        shutil.copy2(img, dest / img.name)

    print(f"✅ Moved {len(images)} images → {dest_class}")
    return len(images)

# ── MAP YOUR DOWNLOADED FOLDERS TO CLASSES ──
# Adjust paths based on what Kaggle gave you

# Fresh fruits/vegetables → edible
move_images("ai/dataset_raw/fruits/train/freshapples",    "edible",        800)
move_images("ai/dataset_raw/fruits/train/freshbanana",    "edible",        800)
move_images("ai/dataset_raw/fruits/train/freshoranges",   "edible",        800)

# Slightly old → ngo_grade (use "stale" or "used" images)
move_images("ai/dataset_raw/fruits/train/rottenapples",   "ngo_grade",     400)
move_images("ai/dataset_raw/fruits/train/rottenbanana",   "ngo_grade",     400)

# More rotten → poultry grade
move_images("ai/dataset_raw/food/stale",                  "poultry_grade", 500)

# Fully rotten → biogas
move_images("ai/dataset_raw/fruits/train/rottenoranges",  "biogas",        400)

# Count final dataset
print("\n📊 Final Dataset:")
for cls in CLASSES:
    count = len(list(Path(f"{OUT_DIR}/{cls}").glob("*")))
    print(f"  {cls}: {count} images")