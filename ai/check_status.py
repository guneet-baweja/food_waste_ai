#!/usr/bin/env python3
"""
FoodSave AI — Checkpoint Diagnostic Tool
Check status of saved model checkpoints and resume point
"""

import torch
import json
from pathlib import Path
from datetime import datetime

def check_checkpoint_status():
    """Check all model checkpoints"""
    
    model_dir = Path("ai/models")
    models = ["efficientnet", "swin", "vit", "ensemble"]
    
    print("\n" + "=" * 80)
    print("  📊 FoodSave AI — Checkpoint Status Report")
    print("=" * 80)
    
    total_checkpoints = 0
    
    for model_name in models:
        checkpoint_path = model_dir / f"{model_name}_best.pth"
        
        print(f"\n🔹 {model_name.upper()}")
        print("-" * 80)
        
        if not checkpoint_path.exists():
            print(f"  ❌ No checkpoint found")
            continue
        
        try:
            # Load checkpoint
            checkpoint = torch.load(checkpoint_path, map_location='cpu')
            
            total_checkpoints += 1
            
            # Extract info
            epoch = checkpoint.get('epoch', 'Unknown')
            val_acc = checkpoint.get('val_acc', 'Unknown')
            val_loss = checkpoint.get('val_loss', 'Unknown')
            
            # File info
            file_stat = checkpoint_path.stat()
            file_size_mb = file_stat.st_size / (1024 * 1024)
            mod_time = datetime.fromtimestamp(file_stat.st_mtime)
            
            # Model weights info
            model_state = checkpoint.get('model_state', {})
            num_params = sum(p.numel() for p in checkpoint['model_state'].values() if isinstance(p, torch.Tensor))
            
            print(f"  ✅ Checkpoint exists")
            print(f"     Epoch:          {epoch}")
            print(f"     Val Accuracy:   {val_acc:.4f}" if isinstance(val_acc, float) else f"     Val Accuracy:   {val_acc}")
            print(f"     Val Loss:       {val_loss:.4f}" if isinstance(val_loss, float) else f"     Val Loss:       {val_loss}")
            print(f"     File Size:      {file_size_mb:.1f}MB")
            print(f"     Last Modified:  {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"     Parameters:     {num_params:,}")
            print(f"     Has Optimizer:  {'✅ Yes' if 'optimizer' in checkpoint else '❌ No'}")
            print(f"     Has Scheduler:  {'✅ Yes' if 'scheduler' in checkpoint else '❌ No'}")
            
            # Calculate resume point
            next_epoch = epoch + 1 if isinstance(epoch, int) else "Unknown"
            print(f"     Resume from:    Epoch {next_epoch}")
            
        except Exception as e:
            print(f"  ⚠️  Error reading checkpoint: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("  📋 SUMMARY")
    print("=" * 80)
    print(f"  Total checkpoints: {total_checkpoints}/4")
    
    if total_checkpoints == 0:
        print("  ❌ No trained models found. Run: python3 ai/train_classifier.py")
    elif total_checkpoints < 4:
        print(f"  ⚠️  Only {total_checkpoints} models have checkpoints. Some training incomplete.")
    else:
        print("  ✅ All 4 models have checkpoints! Ready to resume training.")
    
    print("\n" + "=" * 80)
    print("  🚀 NEXT STEPS")
    print("=" * 80)
    print("  To resume training:")
    print("    python3 ai/resume_training.py")
    print("\n  To test inference with current models:")
    print("    python3 ai/inference_pipeline.py")
    print("\n" + "=" * 80 + "\n")

def check_dataset():
    """Check dataset status"""
    
    print("\n" + "=" * 80)
    print("  📁 Dataset Status")
    print("=" * 80)
    
    dataset_dir = Path("ai/dataset")
    splits = ["train", "val", "test"]
    classes = ["fresh", "semi_fresh", "rotten", "cooked", "packaged"]
    
    for split in splits:
        split_dir = dataset_dir / split
        print(f"\n{split.upper()}:")
        
        if not split_dir.exists():
            print(f"  ❌ Directory not found")
            continue
        
        total = 0
        for cls in classes:
            cls_dir = split_dir / cls
            if cls_dir.exists():
                images = list(cls_dir.glob("*.jpg")) + list(cls_dir.glob("*.png"))
                count = len(images)
                total += count
                status = "✅" if count > 0 else "❌"
                print(f"  {status} {cls:15}: {count:3d} images")
            else:
                print(f"  ❌ {cls:15}: Directory missing")
        
        print(f"  {'─' * 40}")
        print(f"  Total {split:9}: {total:3d} images")
    
    print("\n" + "=" * 80 + "\n")

def main():
    print("\n🔍 Checking FoodSave AI System Status...\n")
    
    check_dataset()
    check_checkpoint_status()

if __name__ == "__main__":
    main()
