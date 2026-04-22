"""
FoodSave AI — Advanced Multi-Model Training System
🚀 Elite Production-Grade AI with Bulletproof Checkpointing
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
from tqdm import tqdm
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import warnings
import warnings
import argparse
from tqdm import tqdm   # ✅ ADD THIS LINE

warnings.filterwarnings('ignore')

# ━━━ CONFIG ━━━
DATASET_DIR = "ai/dataset"
MODEL_DIR = Path("ai/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

CLASSES = ["fresh", "semi_fresh", "rotten", "cooked", "packaged"]
NUM_CLS = len(CLASSES)
IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 200
LR = 3e-4
DEVICE = torch.device("mps" if torch.backends.mps.is_available()
                      else "cuda" if torch.cuda.is_available() else "cpu")

print(f"\n🖥️  Device: {DEVICE} | Batch: {BATCH_SIZE} | Epochs: {EPOCHS}")
print(f"📁 Dataset: {DATASET_DIR}\n")

# ━━━ ARGUMENT PARSER ━━━
parser = argparse.ArgumentParser()
parser.add_argument('--resume', type=str, default=None, 
                    help='Path to checkpoint to resume training from')
args = parser.parse_args()

# ━━━ TRANSFORMS & DATA LOADERS (unchanged) ━━━
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

def get_loaders():
    train_path = Path(f"{DATASET_DIR}/train")
    val_path = Path(f"{DATASET_DIR}/val")
    test_path = Path(f"{DATASET_DIR}/test")

    if not train_path.exists():
        raise FileNotFoundError(f"Training data not found at {train_path}")

    train_ds = datasets.ImageFolder(str(train_path), transform=train_transforms)
    val_ds = datasets.ImageFolder(str(val_path), transform=val_transforms)
    test_ds = datasets.ImageFolder(str(test_path), transform=val_transforms) if test_path.exists() else None

    targets = train_ds.targets
    counts = np.bincount(targets)
    weights = 1.0 / counts
    samples_w = torch.DoubleTensor([weights[t] for t in targets])
    sampler = WeightedRandomSampler(samples_w, len(samples_w))

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, sampler=sampler, 
                              num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, 
                            num_workers=0, pin_memory=True)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False, 
                             num_workers=0) if test_ds else None

    print(f"  Train: {len(train_ds)} | Val: {len(val_ds)} | Test: {len(test_ds) if test_ds else 'N/A'}")
    return train_loader, val_loader, test_loader, train_ds.class_to_idx


# Models (same as before)
class EfficientNetModel(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.base = models.efficientnet_v2_s(weights=models.EfficientNet_V2_S_Weights.DEFAULT)
        in_features = self.base.classifier[1].in_features
        self.base.classifier = nn.Sequential(
            nn.Dropout(0.5), nn.Linear(in_features, 768), nn.BatchNorm1d(768),
            nn.ReLU(inplace=True), nn.Dropout(0.4), nn.Linear(768, 256),
            nn.BatchNorm1d(256), nn.ReLU(inplace=True), nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )
    def forward(self, x): return self.base(x)

class SwinModel(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.base = models.swin_t(weights=models.Swin_T_Weights.DEFAULT)
        in_features = self.base.head.in_features
        self.base.head = nn.Sequential(
            nn.Dropout(0.5), nn.Linear(in_features, 512), nn.BatchNorm1d(512),
            nn.ReLU(inplace=True), nn.Dropout(0.3), nn.Linear(512, 256),
            nn.BatchNorm1d(256), nn.ReLU(inplace=True), nn.Linear(256, num_classes)
        )
    def forward(self, x): return self.base(x)

class ViTModel(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.base = models.vit_b_16(weights=models.ViT_B_16_Weights.DEFAULT)
        in_features = self.base.heads[0].in_features
        self.base.heads = nn.Sequential(
            nn.Dropout(0.4), nn.Linear(in_features, 512),
            nn.ReLU(inplace=True), nn.Dropout(0.3), nn.Linear(512, num_classes)
        )
    def forward(self, x): return self.base(x)

class EnsembleModel(nn.Module):
    def __init__(self, model1, model2, model3, num_classes):
        super().__init__()
        self.m1, self.m2, self.m3 = model1, model2, model3
        self.fusion = nn.Sequential(
            nn.Linear(num_classes * 3, 512), nn.ReLU(inplace=True), nn.Dropout(0.4),
            nn.Linear(512, 256), nn.ReLU(inplace=True), nn.Dropout(0.2),
            nn.Linear(256, num_classes)
        )
    def forward(self, x):
        o1 = self.m1(x)
        o2 = self.m2(x)
        o3 = self.m3(x)
        return self.fusion(torch.cat([o1, o2, o3], dim=1))


# ━━━ TRAINING ENGINE - BULLETPROOF CHECKPOINTING ━━━
def train_model(model, train_loader, val_loader, model_name, epochs=EPOCHS, resume_path=None):
    model = model.to(DEVICE)
    
    total_params = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Parameters: {total_params:,} (Trainable: {trainable:,})")

    criterion = nn.CrossEntropyLoss(label_smoothing=0.15)
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4, betas=(0.9, 0.999))
    scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(
        optimizer, T_0=10, T_mult=2, eta_min=LR/100
    )

    scaler = GradScaler() if DEVICE.type == 'cuda' else None
    use_amp = DEVICE.type == 'cuda'

    best_acc = 0.0
    best_loss = float('inf')
    best_path = MODEL_DIR / f"{model_name}_best.pth"

    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": [], "lr": []}
    patience = 30
    no_improve = 0

    # ==================== RESUME LOGIC ====================
    start_epoch = 1
    if resume_path and os.path.exists(resume_path):
        print(f"🔁 Resuming from {resume_path}")
        checkpoint = torch.load(resume_path, map_location=DEVICE)
        
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        
        start_epoch = checkpoint.get('epoch', 0) + 1
        best_acc = checkpoint.get('best_acc', 0.0)
        best_loss = checkpoint.get('best_loss', float('inf'))
        # history can be partially restored if needed, but we start fresh for simplicity
        
        print(f"✅ Resumed training from epoch {start_epoch}")

    print(f"\n🚀 Starting {model_name} training from epoch {start_epoch}...")

    start_time = time.time()

    for epoch in range(start_epoch, epochs + 1):
        # === TRAIN ===
        model.train()
        t_loss, t_correct, t_total = 0, 0, 0
        train_bar = tqdm(train_loader, desc=f"Epoch {epoch}/{epochs} [TRAIN]", leave=False)

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

            scheduler.step(epoch + (len(train_loader) - len(train_bar)) / len(train_loader))
            t_loss += loss.item() * imgs.size(0)
            t_correct += (outputs.argmax(1) == labels).sum().item()
            t_total += imgs.size(0)

        t_loss /= t_total
        t_acc = t_correct / t_total

        # === VALIDATE ===
        model.eval()
        v_loss, v_correct, v_total = 0, 0, 0
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
                outputs = model(imgs)
                loss = criterion(outputs, labels)
                v_loss += loss.item() * imgs.size(0)
                v_correct += (outputs.argmax(1) == labels).sum().item()
                v_total += imgs.size(0)

        v_loss /= v_total
        v_acc = v_correct / v_total
        lr = scheduler.get_last_lr()[0]

        history["train_loss"].append(t_loss)
        history["train_acc"].append(t_acc)
        history["val_loss"].append(v_loss)
        history["val_acc"].append(v_acc)
        history["lr"].append(lr)

        # ==================== CHECKPOINT SAVING (PRO LEVEL) ====================
        checkpoint_dict = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'best_acc': best_acc,
            'best_loss': best_loss,
            'history': history
        }

        # 1. Latest Checkpoint (always overwrite - safest for resume after crash)
        latest_path = MODEL_DIR / f"{model_name}_checkpoint_latest.pth"
        torch.save(checkpoint_dict, latest_path)

        # 2. Per-Epoch Backup (permanent history)
        epoch_path = MODEL_DIR / f"{model_name}_epoch_{epoch:03d}.pth"
        torch.save(checkpoint_dict, epoch_path)

        print(f"  💾 Checkpoint saved → {model_name}_checkpoint_latest.pth | epoch_{epoch:03d}.pth")

        # 3. Best Model
        if v_acc > best_acc or v_loss < best_loss:
            best_acc = max(best_acc, v_acc)
            best_loss = min(best_loss, v_loss)
            torch.save({
                **checkpoint_dict,
                'class_map': CLASSES
            }, best_path)
            print(f"  🏆 New Best! Val Acc: {v_acc:.4f} | Loss: {v_loss:.4f}")

        # Early Stopping
        if v_acc >= best_acc - 0.001:
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"  ⏹️ Early stopping triggered at epoch {epoch}")
                break

    print(f"\n✅ {model_name} training finished! Best Val Acc: {best_acc:.4f}")
    return model, history, best_acc


# evaluate, export_onnx, save_plots functions remain the same as previous version
# (Copy them from the last code I gave you - they are already good)

# ━━━ MAIN ━━━ (simplified a bit)
if __name__ == "__main__":
    print("=" * 80)
    print("  🚀 FoodSave AI — Advanced Multi-Model Training System")
    print("=" * 80)

    train_loader, val_loader, test_loader, class_map = get_loaders()

    with open(MODEL_DIR / "class_map.json", "w") as f:
        json.dump({"classes": CLASSES, "class_to_idx": class_map}, f, indent=2)

    results = {}
    models_dict = {}

    # Train individual models
    for name, ModelClass, ep in [
        ("efficientnet", EfficientNetModel, EPOCHS),
        ("swin", SwinModel, EPOCHS),
        ("vit", ViTModel, EPOCHS),
    ]:
        print(f"\n🔹 Training {name.upper()}...")
        model = ModelClass(NUM_CLS)
        trained, hist, acc = train_model(model, train_loader, val_loader, name, epochs=ep, resume_path=args.resume)
        save_plots(hist, name)
        results[name] = float(acc)
        models_dict[name] = trained

    # Ensemble
    print("\n🔹 Training ENSEMBLE...")
    ensemble = EnsembleModel(models_dict["efficientnet"], models_dict["swin"], models_dict["vit"], NUM_CLS)
    ens_model, ens_hist, ens_acc = train_model(ensemble, train_loader, val_loader, "ensemble", epochs=100, resume_path=args.resume)
    save_plots(ens_hist, "ensemble")
    results["ensemble"] = float(ens_acc)

    # Final Evaluation & Export (keep as before)

    print("\n" + "="*80)
    print("  🏆 TRAINING COMPLETE")
    for name, acc in sorted(results.items(), key=lambda x: x[1], reverse=True):
        print(f"  {name:15} → {acc:.4f} ({acc*100:.2f}%)")

    print(f"\n✅ All checkpoints saved in {MODEL_DIR}/")
    print("   → Use --resume with *_checkpoint_latest.pth for safest recovery")