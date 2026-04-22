#!/usr/bin/env python3
"""
FoodSave AI — Resume Training Script
Continues training from saved checkpoint (handles early stopping)
Run this to continue training from epoch 9/91 onwards
"""

import os
import json
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, transforms, models
from torch.cuda.amp import GradScaler, autocast
import numpy as np
from pathlib import Path
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys
from tqdm import tqdm
import warnings

warnings.filterwarnings('ignore')

# ━━━ CONFIG ━━━
DATASET_DIR = "ai/dataset"
MODEL_DIR = "ai/models"
os.makedirs(MODEL_DIR, exist_ok=True)

CLASSES = ["fresh", "semi_fresh", "rotten", "cooked", "packaged"]
NUM_CLS = len(CLASSES)
IMG_SIZE = 224
BATCH_SIZE = 32
RESUME_EPOCHS = 200  # Total epochs to train (will continue from checkpoint)
LR = 3e-4
DEVICE = torch.device("mps" if torch.backends.mps.is_available()
          else "cuda" if torch.cuda.is_available() else "cpu")

print(f"\n🖥️  Device: {DEVICE} | Batch: {BATCH_SIZE} | Resume Training")
print(f"📁 Dataset: {DATASET_DIR}")
print(f"🎯 Classes: {CLASSES}\n")

# ━━━ ADVANCED AUGMENTATION ━━━
train_transforms = transforms.Compose([
    transforms.RandomResizedCrop(IMG_SIZE, scale=(0.7, 1.0)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.3),
    transforms.RandomRotation(30),
    transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.4, hue=0.15),
    transforms.RandomGrayscale(p=0.1),
    transforms.RandomApply([transforms.GaussianBlur(kernel_size=5)], p=0.3),
    transforms.RandomApply([transforms.RandomAffine(degrees=0, translate=(0.1, 0.1))], p=0.3),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    transforms.RandomErasing(p=0.2, scale=(0.02, 0.3))
])

val_transforms = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# ━━━ DATASET LOADERS ━━━
def get_loaders():
    train_path = Path(f"{DATASET_DIR}/train")
    val_path = Path(f"{DATASET_DIR}/val")

    if not train_path.exists():
        raise FileNotFoundError(f"Training data not found at {train_path}")

    train_ds = datasets.ImageFolder(str(train_path), transform=train_transforms)
    val_ds = datasets.ImageFolder(str(val_path), transform=val_transforms)

    targets = train_ds.targets
    counts = np.bincount(targets)
    weights = 1.0 / counts
    samples_w = torch.DoubleTensor([weights[t] for t in targets])
    sampler = WeightedRandomSampler(samples_w, len(samples_w))

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE,
                              sampler=sampler, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE,
                            shuffle=False, num_workers=0, pin_memory=True)

    print(f"  Train: {len(train_ds)} | Val: {len(val_ds)}")
    print(f"  Class map: {train_ds.class_to_idx}\n")
    return train_loader, val_loader, train_ds.class_to_idx

# ━━━ MODEL ARCHITECTURES ━━━
class EfficientNetModel(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.base = models.efficientnet_v2_s(weights=models.EfficientNet_V2_S_Weights.DEFAULT)
        in_features = self.base.classifier[1].in_features
        self.base.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(in_features, 768),
            nn.BatchNorm1d(768),
            nn.ReLU(inplace=True),
            nn.Dropout(0.4),
            nn.Linear(768, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        return self.base(x)

class SwinModel(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.base = models.swin_t(weights=models.Swin_T_Weights.DEFAULT)
        in_features = self.base.head.in_features
        self.base.head = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(in_features, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        return self.base(x)

class ViTModel(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.base = models.vit_b_16(weights=models.ViT_B_16_Weights.DEFAULT)
        in_features = self.base.heads[0].in_features
        self.base.heads = nn.Sequential(
            nn.Dropout(0.4),
            nn.Linear(in_features, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )

    def forward(self, x):
        return self.base(x)

# ━━━ RESUME TRAINING ━━━
def resume_training(model, train_loader, val_loader, model_name, total_epochs=RESUME_EPOCHS):
    model = model.to(DEVICE)
    
    criterion = nn.CrossEntropyLoss(label_smoothing=0.15, reduction='mean')
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4, betas=(0.9, 0.999))
    scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(
        optimizer, T_0=10, T_mult=2, eta_min=LR/100
    )

    scaler = GradScaler() if DEVICE.type == 'cuda' else None
    use_amp = DEVICE.type == 'cuda'

    # Load checkpoint
    best_path = f"{MODEL_DIR}/{model_name}_best.pth"
    start_epoch = 1
    best_acc = 0.0
    best_loss = float('inf')
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": [], "lr": []}
    no_improve = 0
    
    if Path(best_path).exists():
        print(f"  📂 Loading checkpoint from {best_path}...")
        checkpoint = torch.load(best_path, map_location=DEVICE)
        model.load_state_dict(checkpoint['model_state'])
        optimizer.load_state_dict(checkpoint['optimizer'])
        scheduler.load_state_dict(checkpoint['scheduler'])
        start_epoch = checkpoint.get('epoch', 1) + 1
        best_acc = checkpoint.get('val_acc', 0.0)
        best_loss = checkpoint.get('val_loss', float('inf'))
        print(f"  ✅ Resuming from epoch {start_epoch} (best_acc: {best_acc:.4f})")
    else:
        print(f"  ⚠️  No checkpoint found. Starting fresh training.")

    patience = 30

    print(f"\n🚀 Resuming {model_name} from epoch {start_epoch} to {total_epochs}...")
    start_time = time.time()

    for epoch in range(start_epoch, total_epochs + 1):
        # ━━━ TRAIN ━━━
        model.train()
        t_loss, t_correct, t_total = 0, 0, 0
        train_bar = tqdm(train_loader, desc=f"Epoch {epoch}/{total_epochs} [TRAIN]", leave=False)

        for imgs, labels in train_bar:
            imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()

            if use_amp and scaler:
                with autocast():
                    outputs = model(imgs)
                    loss = criterion(outputs, labels)
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
            else:
                outputs = model(imgs)
                loss = criterion(outputs, labels)
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()

            scheduler.step(epoch + (train_loader.__len__() - len(train_bar)) / train_loader.__len__())
            t_loss += loss.item() * imgs.size(0)
            preds = outputs.argmax(1)
            t_correct += (preds == labels).sum().item()
            t_total += imgs.size(0)
            train_bar.set_postfix({'loss': f'{loss.item():.4f}'})

        t_loss /= t_total
        t_acc = t_correct / t_total

        # ━━━ VALIDATE ━━━
        model.eval()
        v_loss, v_correct, v_total = 0, 0, 0
        val_bar = tqdm(val_loader, desc=f"Epoch {epoch}/{total_epochs} [VAL]", leave=False)

        with torch.no_grad():
            for imgs, labels in val_bar:
                imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
                outputs = model(imgs)
                loss = criterion(outputs, labels)
                v_loss += loss.item() * imgs.size(0)
                preds = outputs.argmax(1)
                v_correct += (preds == labels).sum().item()
                v_total += imgs.size(0)
                val_bar.set_postfix({'loss': f'{loss.item():.4f}'})

        v_loss /= v_total
        v_acc = v_correct / v_total
        lr = scheduler.get_last_lr()[0]

        history["train_loss"].append(t_loss)
        history["train_acc"].append(t_acc)
        history["val_loss"].append(v_loss)
        history["val_acc"].append(v_acc)
        history["lr"].append(lr)

        elapsed = (time.time() - start_time) / 60

        if epoch % 10 == 0 or epoch == start_epoch:
            print(f"  Epoch {epoch:3d}/{total_epochs} | "
                  f"Train: {t_acc:.4f} ({t_loss:.4f}) | "
                  f"Val: {v_acc:.4f} ({v_loss:.4f}) | "
                  f"LR: {lr:.6f} | "
                  f"Time: {elapsed:.1f}m")

        if v_acc > best_acc or v_loss < best_loss:
            best_acc = max(best_acc, v_acc)
            best_loss = min(best_loss, v_loss)
            torch.save({
                'epoch': epoch,
                'model_state': model.state_dict(),
                'optimizer': optimizer.state_dict(),
                'scheduler': scheduler.state_dict(),
                'val_acc': v_acc,
                'val_loss': v_loss,
                'class_map': CLASSES
            }, best_path)
            no_improve = 0
            print(f"  💾 Saved! Acc: {v_acc:.4f}, Loss: {v_loss:.4f}")
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"  ⏹️  Early stopping at epoch {epoch}")
                break

    print(f"\n✅ {model_name} training complete! Best Val Acc: {best_acc:.4f}")
    return model, history, best_acc

# ━━━ MAIN ━━━
if __name__ == "__main__":
    print("=" * 70)
    print("  🚀 FoodSave AI — Resume Training (Early Stopping Recovery)")
    print("=" * 70)

    train_loader, val_loader, class_map = get_loaders()

    results = {}

    # ━━━ RESUME EFFICIENTNET ━━━
    print("\n🔹 RESUMING: EfficientNet V2-S")
    print("=" * 70)
    eff_model = EfficientNetModel(NUM_CLS)
    eff_model, eff_hist, eff_acc = resume_training(
        eff_model, train_loader, val_loader, "efficientnet", total_epochs=RESUME_EPOCHS
    )
    results["efficientnet"] = float(eff_acc)

    # ━━━ RESUME SWIN ━━━
    print("\n🔹 RESUMING: Swin Transformer")
    print("=" * 70)
    swin_model = SwinModel(NUM_CLS)
    swin_model, swin_hist, swin_acc = resume_training(
        swin_model, train_loader, val_loader, "swin", total_epochs=RESUME_EPOCHS
    )
    results["swin"] = float(swin_acc)

    # ━━━ RESUME VIT ━━━
    print("\n🔹 RESUMING: Vision Transformer")
    print("=" * 70)
    vit_model = ViTModel(NUM_CLS)
    vit_model, vit_hist, vit_acc = resume_training(
        vit_model, train_loader, val_loader, "vit", total_epochs=RESUME_EPOCHS
    )
    results["vit"] = float(vit_acc)

    # ━━━ FINAL REPORT ━━━
    print("\n" + "=" * 70)
    print("  🏆 RESUME TRAINING COMPLETE — RESULTS")
    print("=" * 70)
    for name, acc in sorted(results.items(), key=lambda x: x[1], reverse=True):
        print(f"  {name:15} → {acc:.4f} ({acc*100:.2f}%)")

    with open(f"{MODEL_DIR}/resume_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ All models resumed and trained!")
    print(f"📊 Results saved to {MODEL_DIR}/resume_results.json\n")
