#!/usr/bin/env python3
"""
FoodSave AI — Intelligent Inference Pipeline + Decision Engine
Combines multiple models to make smart food waste management decisions
"""

import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision import models
from pathlib import Path
import json
import numpy as np
from PIL import Image
import warnings

warnings.filterwarnings('ignore')

# ━━━ CONFIG ━━━
DEVICE = torch.device("mps" if torch.backends.mps.is_available()
          else "cuda" if torch.cuda.is_available() else "cpu")
MODEL_DIR = Path("ai/models")
IMG_SIZE = 224

# Load class map
with open(MODEL_DIR / "class_map.json") as f:
    CLASS_MAP = json.load(f)
    CLASSES = CLASS_MAP["classes"]
    CLASS_TO_IDX = CLASS_MAP["class_to_idx"]
    IDX_TO_CLASS = {v: k for k, v in CLASS_TO_IDX.items()}

# ━━━ IMAGE PREPROCESSING ━━━
val_transforms = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

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

class EnsembleModel(nn.Module):
    def __init__(self, model1, model2, model3, num_classes):
        super().__init__()
        self.m1 = model1
        self.m2 = model2
        self.m3 = model3
        self.fusion = nn.Sequential(
            nn.Linear(num_classes * 3, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.4),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        o1 = self.m1(x)
        o2 = self.m2(x)
        o3 = self.m3(x)
        combined = torch.cat([o1, o2, o3], dim=1)
        return self.fusion(combined)

# ━━━ MODEL LOADER ━━━
def load_model(model_name):
    """Load a trained model from checkpoint"""
    model_path = MODEL_DIR / f"{model_name}_best.pth"
    
    if model_name == "efficientnet":
        model = EfficientNetModel(len(CLASSES))
    elif model_name == "swin":
        model = SwinModel(len(CLASSES))
    elif model_name == "vit":
        model = ViTModel(len(CLASSES))
    elif model_name == "ensemble":
        # Need to load individual models first
        eff = EfficientNetModel(len(CLASSES))
        swin = SwinModel(len(CLASSES))
        vit = ViTModel(len(CLASSES))
        model = EnsembleModel(eff, swin, vit, len(CLASSES))
    
    if model_path.exists():
        checkpoint = torch.load(model_path, map_location=DEVICE)
        model.load_state_dict(checkpoint['model_state'])
        print(f"✓ Loaded {model_name} from {model_path}")
    else:
        print(f"⚠️  Model not found: {model_path}")
    
    return model.to(DEVICE).eval()

# ━━━ INFERENCE ENGINE ━━━
class FoodWasteDecisionEngine:
    """Intelligent decision engine for food waste management"""
    
    # Routing destinations with coordinates (lat, lon)
    DESTINATIONS = {
        "ngo": {"name": "Local NGO", "lat": 28.6139, "lon": 77.2090},
        "poultry_farm": {"name": "Poultry Farm", "lat": 28.6200, "lon": 77.2200},
        "biogas_plant": {"name": "Biogas Plant", "lat": 28.6050, "lon": 77.2000},
        "compost": {"name": "Composting Unit", "lat": 28.5900, "lon": 77.1950},
    }
    
    def __init__(self):
        """Initialize with all 4 models"""
        print("\n📦 Loading trained models...")
        self.eff_model = load_model("efficientnet")
        self.swin_model = load_model("swin")
        self.vit_model = load_model("vit")
        self.ensemble_model = load_model("ensemble")
        
    def predict(self, image_path):
        """Make prediction on an image"""
        img = Image.open(image_path).convert('RGB')
        img_tensor = val_transforms(img).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            # Get predictions from all models
            eff_out = torch.softmax(self.eff_model(img_tensor), dim=1)
            swin_out = torch.softmax(self.swin_model(img_tensor), dim=1)
            vit_out = torch.softmax(self.vit_model(img_tensor), dim=1)
            ensemble_out = torch.softmax(self.ensemble_model(img_tensor), dim=1)
        
        # Average predictions
        avg_probs = (eff_out + swin_out + vit_out + ensemble_out) / 4.0
        confidence, pred_idx = avg_probs.max(1)
        
        freshness = CLASSES[pred_idx.item()]
        confidence = confidence.item()
        
        return {
            "freshness": freshness,
            "confidence": confidence,
            "probabilities": {c: float(avg_probs[0, i].item()) for i, c in enumerate(CLASSES)}
        }
    
    def decide_destination(self, freshness, confidence):
        """Decide where to send the food based on freshness"""
        thresholds = {
            "fresh": (0.8, "ngo"),  # High confidence fresh → NGO
            "semi_fresh": (0.7, "poultry_farm"),  # Semi-fresh → Poultry
            "rotten": (0.6, "biogas_plant"),  # Rotten → Biogas
            "cooked": (0.7, "compost"),  # Cooked → Compost
            "packaged": (0.8, "ngo"),  # Packaged → NGO
        }
        
        conf_thresh, default_dest = thresholds.get(freshness, (0.7, "compost"))
        
        # If confidence below threshold, send to safest option
        if confidence < conf_thresh:
            destination = "compost"
        else:
            destination = default_dest
        
        return destination
    
    def calculate_distance(self, dest_key, user_lat=28.6139, user_lon=77.2090):
        """Calculate Haversine distance to destination"""
        dest = self.DESTINATIONS[dest_key]
        
        # Haversine formula
        lat1, lon1 = np.radians(user_lat), np.radians(user_lon)
        lat2, lon2 = np.radians(dest["lat"]), np.radians(dest["lon"])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        r = 6371  # Earth radius in km
        
        return r * c
    
# FIND THIS (broken):
def process_food_image(self, image_input, donor_lat=28.6139, donor_lng=77.2090):
    ...
    destination = self.decide_destination(freshness_class, confidence)
    # BUG: thresholds not defined here
    if confidence < thresholds.get(freshness_class, 0.6):

# REPLACE WITH THIS (fixed):
def process_food_image(self, image_input, donor_lat=28.6139, donor_lng=77.2090):
    """
    Full pipeline: image → classify → decide → route
    """
    # Confidence thresholds per class (moved here from decide_destination)
    thresholds = {
        "fresh":      0.80,
        "semi_fresh": 0.70,
        "rotten":     0.60,
        "cooked":     0.70,
        "packaged":   0.80
    }

    result = {
        "food_class":    "unknown",
        "freshness":     "unknown",
        "confidence":    0.0,
        "action":        "send_to_biogas",
        "label":         "Unknown",
        "urgency":       "medium",
        "route":         "Biogas Plant",
        "nearest":       None,
        "model_used":    "rule_based",
        "ai_scores":     {},
        "co2_saved":     0.0,
        "water_saved":   0
    }

    # Load image
    try:
        if isinstance(image_input, str):
            img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, bytes):
            import io
            img = Image.open(io.BytesIO(image_input)).convert("RGB")
        elif isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")
        else:
            result["error"] = "Invalid image input"
            return result
    except Exception as e:
        result["error"] = str(e)
        return result

    # Run classification
    try:
        cls_result = self.classify_image(img)
        freshness_class = cls_result.get("class", "rotten")
        confidence      = cls_result.get("confidence", 0.0)
        result["food_class"]  = freshness_class
        result["freshness"]   = freshness_class
        result["confidence"]  = round(confidence * 100, 2)
        result["ai_scores"]   = cls_result.get("all_scores", {})
        result["model_used"]  = "ensemble"
    except Exception as e:
        print(f"⚠️ Classification error: {e}")
        freshness_class = "rotten"
        confidence      = 0.5

    # Low confidence → safe fallback
    if confidence < thresholds.get(freshness_class, 0.6):
        freshness_class = "rotten"
        result["freshness"] = freshness_class

    # Get destination
    destination_info = self.decide_destination(freshness_class, confidence)
    result.update(destination_info)

    # Find nearest facility
    try:
        nearest = self.find_nearest_facility(
            destination_info["action"], donor_lat, donor_lng
        )
        result["nearest"] = nearest
    except Exception as e:
        print(f"⚠️ Routing error: {e}")

    # CO2 calculation
    result["co2_saved"]   = round(confidence * 2.5, 2)
    result["water_saved"] = int(confidence * 250)

    return result
    
    def _get_action_text(self, freshness, destination):
        """Generate human-readable action text"""
        actions = {
            ("fresh", "ngo"): "✅ DONATE to NGO for food distribution",
            ("fresh", "compost"): "✅ SAFE to consume",
            ("semi_fresh", "poultry_farm"): "⚠️  SEND to poultry farm for animal feed",
            ("semi_fresh", "compost"): "🔄 COMPOST for soil enrichment",
            ("rotten", "biogas_plant"): "♻️  SEND to biogas plant for energy",
            ("rotten", "compost"): "🔄 COMPOST for soil enrichment",
            ("cooked", "compost"): "🔄 COMPOST for soil enrichment",
            ("packaged", "ngo"): "✅ DONATE to NGO if unopened",
        }
        
        return actions.get((freshness, destination), "🔄 PROCESS appropriately")
    
    @staticmethod
    def batch_process(image_folder):
        """Process multiple images from a folder"""
        engine = FoodWasteDecisionEngine()
        results = []
        
        image_folder = Path(image_folder)
        for img_path in image_folder.glob("*.jpg") + image_folder.glob("*.png"):
            result = engine.process_food_image(str(img_path))
            results.append(result)
            print(f"  → {result['action']}")
        
        return results

# ━━━ DEMO ━━━
if __name__ == "__main__":
    print("=" * 70)
    print("  🍔 FoodSave AI — Intelligent Food Waste Decision Engine")
    print("=" * 70)
    
    engine = FoodWasteDecisionEngine()
    
    # Test with sample images from validation set
    test_images = list(Path("ai/dataset/val").rglob("*.jpg"))[:3]
    
    if test_images:
        print("\n📸 Testing on sample images...")
        for img_path in test_images:
            result = engine.process_food_image(str(img_path))
            print(f"\n{json.dumps(result, indent=2)}\n")
    else:
        print("⚠️  No test images found. Run setup_dataset.py first.")
