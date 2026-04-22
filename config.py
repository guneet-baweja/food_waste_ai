"""
FoodSave AI — Central Configuration
Single source of truth for all constants
"""

import os
from datetime import timedelta

# ── Security ──
SECRET_KEY = os.environ.get("SECRET_KEY", "foodsave_ai_super_secret_key_2026_change_in_prod")
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
PERMANENT_SESSION_LIFETIME = timedelta(days=7)

# ── Server ──
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8080))
DEBUG = os.environ.get("FLASK_ENV", "development") == "development"

# ── Upload Settings ──
UPLOAD_FOLDER = os.path.join("static", "uploads")
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# ── Data Paths ──
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
DONATIONS_FILE = os.path.join(DATA_DIR, "donations.json")
NOTIFS_FILE = os.path.join(DATA_DIR, "notifications.json")
LOCATIONS_FILE = os.path.join(DATA_DIR, "locations.json")

# ── AI Configuration ──
AI_DIR = "ai"
MODEL_DIR = os.path.join(AI_DIR, "models")
DATASET_DIR = os.path.join(AI_DIR, "dataset")
IMAGE_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 200
LEARNING_RATE = 3e-4
DEVICE = "auto"

CLASSES = ["fresh", "semi_fresh", "rotten", "cooked", "packaged"]

CONFIDENCE_THRESHOLDS = {
    "fresh": 0.80,
    "semi_fresh": 0.70,
    "rotten": 0.60,
    "cooked": 0.70,
    "packaged": 0.80
}

# ── Routing Rules ──
ROUTING_RULES = {
    "fresh":      {"action": "donate_to_ngo",   "label": "Edible",      "urgency": "low"},
    "semi_fresh": {"action": "send_to_poultry", "label": "Semi-Fresh",  "urgency": "medium"},
    "rotten":     {"action": "send_to_biogas",  "label": "Biogas",      "urgency": "critical"},
    "cooked":     {"action": "donate_to_ngo",   "label": "Cooked",      "urgency": "high"},
    "packaged":   {"action": "donate_to_ngo",   "label": "Packaged",    "urgency": "low"}
}

# ── CO2 Factors ──
CO2_FACTORS = {
    "fresh":      1.8,
    "cooked":     2.5,
    "semi_fresh": 2.0,
    "rotten":     0.5,
    "packaged":   2.0,
    "default":    2.2
}

# ── Gamification ──
POINTS = {
    "signup_bonus":     50,
    "create_donation":  100,
    "accept_pickup":    75,
    "complete_pickup":  150,
    "donor_bonus":      50
}

BADGE_RULES = [
    {"name": "🌱 Green Starter",      "condition": lambda u: u.get("points", 0) >= 100},
    {"name": "♻️ Eco Warrior",        "condition": lambda u: u.get("points", 0) >= 500},
    {"name": "🌍 Planet Saver",       "condition": lambda u: u.get("points", 0) >= 1000},
    {"name": "🍽️ Food Hero",          "condition": lambda u: u.get("total_donations", 0) >= 5},
    {"name": "🏆 Donation Champion",  "condition": lambda u: u.get("total_donations", 0) >= 20},
    {"name": "🚀 Active Volunteer",   "condition": lambda u: u.get("role") == "volunteer"}
]

# ── Feature Flags ──
ENABLE_BATCH_PROCESSING = True
ENABLE_CACHING = True
ENABLE_METRICS = True