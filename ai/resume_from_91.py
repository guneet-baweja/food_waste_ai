#!/usr/bin/env python3
"""
🚀 RESUME TRAINING FROM EPOCH 91 → 200
Continue training without interruption
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import json
import time
from pathlib import Path
from datetime import datetime
import sys

# ━━━ CONFIG ━━━
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
IMG_SIZE = 224
BATCH_SIZE = 32
RESUME_EPOCHS = 200  # Train to epoch 200
START_EPOCH = 91     # Resume from epoch 91
PATIENCE = 50        # Disable early stopping effectively
MODEL_DIR = Path("ai/models")
DATASET_PATH = Path("ai/dataset")

print("=" * 70)
print("  🚀 RESUME TRAINING: EPOCH 91 → 200")
print("=" * 70)
print(f"🖥️  Device: {DEVICE}")
print(f"📁 Dataset: {DATASET_PATH}")
print(f"🎯 Resume: Epoch {START_EPOCH} → {RESUME_EPOCHS}")

# ━━━ LOAD CHECKPOINT INFO ━━━
checkpoint_path = MODEL_DIR / "efficientnet_best.pth"
if not checkpoint_path.exists():
    print(f"❌ Checkpoint not found: {checkpoint_path}")
    sys.exit(1)

print(f"✅ Checkpoint found: {checkpoint_path}")
print(f"📦 Size: {checkpoint_path.stat().st_size / 1024 / 1024:.1f} MB")

# ━━━ LOAD CLASS MAP ━━━
class_map_path = MODEL_DIR / "class_map.json"
with open(class_map_path) as f:
    class_map = json.load(f)

class_names = list(class_map.keys())
num_classes = len(class_names)
print(f"🎯 Classes: {class_names}")

# ━━━ DATA LOADERS ━━━
train_transforms = transforms.Compose([
    transforms.RandomRotation(30),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.GaussianBlur(kernel_size=3),
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225])
])

val_transforms = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225])
])

train_ds = datasets.ImageFolder(str(DATASET_PATH / "train"), transform=train_transforms)
val_ds = datasets.ImageFolder(str(DATASET_PATH / "val"), transform=val_transforms)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=4, pin_memory=True)
val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=4, pin_memory=True)

print(f"\n📊 Data Loaded:")
print(f"  Train: {len(train_ds)} images")
print(f"  Val: {len(val_ds)} images")

# ━━━ LOAD MODEL ━━━
from torchvision.models import efficientnet_v2_s, EfficientNet_V2_S_Weights

model = efficientnet_v2_s(weights=EfficientNet_V2_S_Weights.DEFAULT)
model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, num_classes)
model = model.to(DEVICE)

checkpoint = torch.load(checkpoint_path, map_location=DEVICE)

# Handle different checkpoint formats
if isinstance(checkpoint, dict):
    if 'model_state_dict' in checkpoint:
        model.load_state_dict(checkpoint['model_state_dict'])
        best_acc = checkpoint.get('best_acc', 0.0)
        best_loss = checkpoint.get('best_loss', float('inf'))
    elif 'model_state' in checkpoint:
        model.load_state_dict(checkpoint['model_state'])
        best_acc = checkpoint.get('val_acc', 0.0)
        best_loss = checkpoint.get('val_loss', float('inf'))
    else:
        # Try to extract model state from checkpoint keys
        model_state = {k: v for k, v in checkpoint.items() if not k in ['epoch', 'optimizer', 'scheduler', 'class_map']}
        model.load_state_dict(model_state)
        best_acc = checkpoint.get('val_acc', 0.0)
        best_loss = checkpoint.get('val_loss', float('inf'))
else:
    # Direct state dict
    model.load_state_dict(checkpoint)
    best_acc = 0.0
    best_loss = float('inf')

print(f"\n✅ Model Loaded (EfficientNet V2-S)")
print(f"  Best Val Acc: {best_acc:.4f}")
print(f"  Best Val Loss: {best_loss:.4f}")

# ━━━ OPTIMIZER & SCHEDULER ━━━
optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
scheduler = CosineAnnealingLR(optimizer, T_max=RESUME_EPOCHS, eta_min=1e-6)

# Restore optimizer state if available
if isinstance(checkpoint, dict) and 'optimizer_state_dict' in checkpoint:
    try:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        print("✅ Optimizer state restored")
    except:
        print("⚠️  Could not restore optimizer state, starting fresh")

if isinstance(checkpoint, dict) and 'scheduler_state_dict' in checkpoint:
    try:
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        print("✅ Learning rate scheduler restored")
    except:
        print("⚠️  Could not restore scheduler state, starting fresh")

# ━━━ TRAINING LOOP ━━━
criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
patience = PATIENCE
no_improve = 0
history = {
    "train_loss": [], "train_acc": [],
    "val_loss": [], "val_acc": [], "lr": []
}

print(f"\n🚀 Starting Training: Epoch {START_EPOCH + 1} → {RESUME_EPOCHS}")
print("=" * 70)

start_time = time.time()

for epoch in range(START_EPOCH + 1, RESUME_EPOCHS + 1):
    # ━━━ TRAIN ━━━
    model.train()
    t_loss, t_correct, t_total = 0.0, 0, 0
    
    for imgs, labels in train_loader:
        imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()
        outputs = model(imgs)
        loss = criterion(outputs, labels)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        
        t_loss += loss.item() * labels.size(0)
        t_correct += (outputs.argmax(1) == labels).sum().item()
        t_total += labels.size(0)
    
    t_loss /= t_total
    t_acc = t_correct / t_total
    
    # ━━━ VALIDATE ━━━
    model.eval()
    v_loss, v_correct, v_total = 0.0, 0, 0
    
    with torch.no_grad():
        for imgs, labels in val_loader:
            imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
            outputs = model(imgs)
            loss = criterion(outputs, labels)
            
            v_loss += loss.item() * labels.size(0)
            v_correct += (outputs.argmax(1) == labels).sum().item()
            v_total += labels.size(0)
    
    v_loss /= v_total
    v_acc = v_correct / v_total
    
    scheduler.step()
    lr = scheduler.get_last_lr()[0]
    
    history["train_loss"].append(t_loss)
    history["train_acc"].append(t_acc)
    history["val_loss"].append(v_loss)
    history["val_acc"].append(v_acc)
    history["lr"].append(lr)
    
    elapsed = (time.time() - start_time) / 60
    
    if epoch % 10 == 0 or epoch == START_EPOCH + 1:
        print(f"Epoch {epoch:3d}/{RESUME_EPOCHS} | Train: {t_loss:.4f} ({t_acc:.4f}) | Val: {v_loss:.4f} ({v_acc:.4f}) | LR: {lr:.2e} | ⏱️  {elapsed:.1f}m")
    
    # ━━━ SAVE BEST ━━━
    if v_acc > best_acc or v_loss < best_loss:
        best_acc = max(best_acc, v_acc)
        best_loss = min(best_loss, v_loss)
        no_improve = 0
        
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'best_acc': best_acc,
            'best_loss': best_loss,
            'history': history
        }, checkpoint_path)
        
        if epoch % 10 == 0 or epoch == START_EPOCH + 1:
            print(f"  💾 Saved! Acc: {v_acc:.4f}, Loss: {v_loss:.4f}")
    else:
        no_improve += 1
        if no_improve >= patience:
            print(f"\n⏹️  Early stopping at epoch {epoch}")
            print(f"✅ Final Best Accuracy: {best_acc:.4f}")
            break

print("\n" + "=" * 70)
print(f"✅ Training Complete!")
print(f"📊 Best Validation Accuracy: {best_acc:.4f}")
print(f"⏱️  Total Time: {(time.time() - start_time) / 60:.1f} minutes")
print("=" * 70)

# ━━━ SAVE RESULTS ━━━
results = {
    "resume_epoch": START_EPOCH,
    "final_epoch": epoch,
    "best_accuracy": float(best_acc),
    "best_loss": float(best_loss),
    "timestamp": datetime.now().isoformat(),
    "device": str(DEVICE),
    "total_time_minutes": (time.time() - start_time) / 60
}

results_path = MODEL_DIR / "resume_results.json"
with open(results_path, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n📄 Results saved to: {results_path}")
print("\n✨ Ready for inference!")
print(f"Run: python3 ai/inference_pipeline.py")
