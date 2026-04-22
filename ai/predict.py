"""
FoodSave AI — Freshness Predictor
Load this into Flask to replace the placeholder predict_freshness()
"""

import numpy as np
from PIL import Image
import io

# Lazy-load model (only once)
_model = None
_class_names = ['critical', 'high', 'medium', 'safe']

def load_model():
    global _model
    if _model is None:
        try:
            import tensorflow as tf
            _model = tf.keras.models.load_model('ai/freshness_model.h5')
            print("✅ AI freshness model loaded")
        except Exception as e:
            print(f"⚠️ Could not load AI model: {e}. Using rule-based fallback.")
    return _model

def predict_from_image(image_bytes):
    """
    Predict food freshness from image bytes.
    Returns: { label, confidence, urgency }
    """
    model = load_model()
    if model is None:
        return {"label": "unknown", "confidence": 0, "urgency": "medium"}

    img = Image.open(io.BytesIO(image_bytes)).resize((224, 224)).convert('RGB')
    arr = np.array(img) / 255.0
    arr = np.expand_dims(arr, axis=0)

    preds = model.predict(arr, verbose=0)[0]
    idx   = int(np.argmax(preds))
    label = _class_names[idx]
    conf  = float(preds[idx])

    return {
        "label":      label,
        "confidence": round(conf * 100, 1),
        "urgency":    label
    }

def predict_freshness_ai(expiry_time_str, image_path=None):
    """
    Drop-in replacement for existing predict_freshness() in app.py
    Uses AI if image available, else falls back to rule-based.
    """
    from datetime import datetime
    import random

    # AI prediction if image available
    ai_result = None
    if image_path:
        try:
            with open(image_path, 'rb') as f:
                ai_result = predict_from_image(f.read())
        except Exception:
            pass

    # Rule-based fallback
    try:
        expiry = datetime.fromisoformat(expiry_time_str)
        diff_hours = (expiry - datetime.now()).total_seconds() / 3600
        if diff_hours < 0:      urgency, score = 'expired',  0
        elif diff_hours < 3:    urgency, score = 'critical', random.randint(10, 30)
        elif diff_hours < 12:   urgency, score = 'high',     random.randint(30, 55)
        elif diff_hours < 24:   urgency, score = 'medium',   random.randint(55, 75)
        elif diff_hours < 72:   urgency, score = 'low',      random.randint(75, 90)
        else:                   urgency, score = 'safe',     random.randint(88, 100)
    except Exception:
        urgency, score, diff_hours = 'medium', 50, 12

    # Merge AI + rule-based
    if ai_result and ai_result['confidence'] > 70:
        urgency = ai_result['urgency']
        score   = int(ai_result['confidence'])

    return {
        "freshness_score": score,
        "urgency":         urgency,
        "hours_remaining": round(diff_hours, 1),
        "ai_confidence":   ai_result['confidence'] if ai_result else None
    }