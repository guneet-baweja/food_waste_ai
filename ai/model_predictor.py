import io
import json
import os
from pathlib import Path


MODEL_DIR = Path(__file__).resolve().parent / "models"
CLASS_MAP_PATH = MODEL_DIR / "class_map.json"
DEFAULT_MODEL_NAME = os.environ.get("TRAINED_MODEL_NAME", "efficientnet")
DEFAULT_CHECKPOINT_NAME = os.environ.get("TRAINED_MODEL_CHECKPOINT", "").strip()

CLASS_SCORE_MAP = {
    "fresh": 92,
    "semi_fresh": 66,
    "cooked": 72,
    "packaged": 88,
    "rotten": 18,
}

CLASS_URGENCY_MAP = {
    "fresh": "safe",
    "semi_fresh": "medium",
    "cooked": "high",
    "packaged": "low",
    "rotten": "critical",
}

CLASS_ROUTE_MAP = {
    "fresh": "NGO",
    "semi_fresh": "Poultry",
    "cooked": "NGO",
    "packaged": "NGO",
    "rotten": "Biogas",
}


class TrainedFoodModelPredictor:
    def __init__(self, model_name=DEFAULT_MODEL_NAME, checkpoint_name=DEFAULT_CHECKPOINT_NAME):
        self.model_name = model_name
        self.checkpoint_name = checkpoint_name
        self._ready = False
        self._error = None
        self._model = None
        self._classes = []
        self._device = None
        self._transforms = None
        self._Image = None
        self._torch = None
        self._checkpoint_path = None
        self._build_runtime()

    def _resolve_checkpoint_path(self):
        explicit = self.checkpoint_name.strip()
        candidates = []
        if explicit:
            candidates.append(MODEL_DIR / explicit)
        candidates.extend([
            MODEL_DIR / f"{self.model_name}_epoch_200.pth",
            MODEL_DIR / f"{self.model_name}_best.pth",
            MODEL_DIR / f"{self.model_name}_checkpoint_latest.pth",
        ])
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _build_runtime(self):
        try:
            import torch
            import torch.nn as nn
            import torchvision.transforms as transforms
            from PIL import Image
            from torchvision import models
        except Exception as exc:
            self._error = f"model runtime unavailable: {exc}"
            return

        if not CLASS_MAP_PATH.exists():
            self._error = f"class map not found at {CLASS_MAP_PATH}"
            return

        with CLASS_MAP_PATH.open("r", encoding="utf-8") as handle:
            class_map = json.load(handle)
        self._classes = class_map.get("classes", [])
        if not self._classes:
            self._error = "class map is empty"
            return

        checkpoint_path = self._resolve_checkpoint_path()
        if checkpoint_path is None:
            self._error = (
                f"checkpoint not found for {self.model_name}. "
                "Expected an explicit TRAINED_MODEL_CHECKPOINT or epoch_200/best/latest weights."
            )
            return
        self._checkpoint_path = checkpoint_path

        class EfficientNetModel(nn.Module):
            def __init__(self, num_classes):
                super().__init__()
                self.base = models.efficientnet_v2_s(weights=None)
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
                    nn.Linear(256, num_classes),
                )

            def forward(self, x):
                return self.base(x)

        class SwinModel(nn.Module):
            def __init__(self, num_classes):
                super().__init__()
                self.base = models.swin_t(weights=None)
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
                    nn.Linear(256, num_classes),
                )

            def forward(self, x):
                return self.base(x)

        class ViTModel(nn.Module):
            def __init__(self, num_classes):
                super().__init__()
                self.base = models.vit_b_16(weights=None)
                in_features = self.base.heads[0].in_features
                self.base.heads = nn.Sequential(
                    nn.Dropout(0.4),
                    nn.Linear(in_features, 512),
                    nn.ReLU(inplace=True),
                    nn.Dropout(0.3),
                    nn.Linear(512, num_classes),
                )

            def forward(self, x):
                return self.base(x)

        builders = {
            "efficientnet": EfficientNetModel,
            "swin": SwinModel,
            "vit": ViTModel,
        }
        builder = builders.get(self.model_name)
        if builder is None:
            self._error = f"unsupported trained model: {self.model_name}"
            return

        self._device = torch.device(
            "mps" if torch.backends.mps.is_available()
            else "cuda" if torch.cuda.is_available() else "cpu"
        )
        self._transforms = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        self._Image = Image
        self._torch = torch

        checkpoint = torch.load(checkpoint_path, map_location=self._device)
        state_dict = checkpoint.get("model_state_dict") or checkpoint.get("model_state") or checkpoint
        model = builder(len(self._classes))
        model.load_state_dict(state_dict)
        model = model.to(self._device).eval()

        self._model = model
        self._ready = True

    def predict(self, image_bytes=None, image_path=None):
        if not self._ready:
            return {
                "available": False,
                "prediction_source": "trained_model",
                "reason": self._error or "trained model is unavailable",
            }

        if image_bytes is None and not image_path:
            return {
                "available": False,
                "prediction_source": "trained_model",
                "reason": "image is required for trained model prediction",
            }

        try:
            if image_bytes is not None:
                image = self._Image.open(io.BytesIO(image_bytes)).convert("RGB")
            else:
                image = self._Image.open(image_path).convert("RGB")
        except Exception as exc:
            return {
                "available": False,
                "prediction_source": "trained_model",
                "reason": f"could not open image: {exc}",
            }

        tensor = self._transforms(image).unsqueeze(0).to(self._device)
        with self._torch.no_grad():
            logits = self._model(tensor)
            probs = self._torch.softmax(logits, dim=1)[0]

        pred_index = int(self._torch.argmax(probs).item())
        confidence = float(probs[pred_index].item())
        label = self._classes[pred_index]
        base_score = CLASS_SCORE_MAP.get(label, 50)
        freshness_score = max(0, min(100, int(round(base_score + (confidence - 0.5) * 20))))

        return {
            "available": True,
            "prediction_source": "trained_model",
            "model_name": self.model_name,
            "checkpoint_name": self._checkpoint_path.name if self._checkpoint_path else None,
            "predicted_class": label,
            "freshness_score": freshness_score,
            "urgency": CLASS_URGENCY_MAP.get(label, "medium"),
            "recommended_route": CLASS_ROUTE_MAP.get(label, "NGO"),
            "confidence": round(confidence * 100, 2),
            "hours_remaining": None,
            "probabilities": {
                class_name: round(float(prob.item()) * 100, 2)
                for class_name, prob in zip(self._classes, probs)
            },
        }


_predictor = None


def predict_trained_food_model(
    image_bytes=None,
    image_path=None,
    model_name=DEFAULT_MODEL_NAME,
    checkpoint_name=DEFAULT_CHECKPOINT_NAME,
):
    global _predictor
    if (
        _predictor is None
        or _predictor.model_name != model_name
        or _predictor.checkpoint_name != checkpoint_name
    ):
        _predictor = TrainedFoodModelPredictor(
            model_name=model_name,
            checkpoint_name=checkpoint_name,
        )
    return _predictor.predict(image_bytes=image_bytes, image_path=image_path)
