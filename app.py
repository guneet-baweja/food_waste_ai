"""
AI Smart Food Waste Management Platform
Flask Backend - app.py
All API routes, file handling, and data management
"""

import os
import json
import uuid
import base64
import random
import hashlib
import shutil
import subprocess
import tempfile
import traceback
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, request, jsonify, session,
    render_template, redirect, url_for, send_from_directory
)
from werkzeug.utils import secure_filename
from storage_backend import supabase_backend

# ─────────────────────────────────────────────
# CONFIG IMPORT (Central Configuration)
# ─────────────────────────────────────────────
try:
    from config import (
        SECRET_KEY, HOST, PORT, DEBUG,
        UPLOAD_FOLDER, MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS,
        USERS_FILE, DONATIONS_FILE, NOTIFS_FILE,
        CLASSES, CONFIDENCE_THRESHOLDS, ROUTING_RULES,
        CO2_FACTORS, POINTS, BADGE_RULES
    )
    print("✅ Successfully loaded config.py")
except ImportError:
    print("⚠️ config.py not found. Using hardcoded values.")
    # Fallback values will be used from below

# ─── AI Model Loading (safe import) ───
_ai_pipeline = None
def get_ai_pipeline():
    """Lazy-load AI pipeline — won't crash if models missing."""
    global _ai_pipeline
    if _ai_pipeline is not None:
        return _ai_pipeline
    try:
        from ai.inference_pipeline import FoodWasteDecisionEngine
        _ai_pipeline = FoodWasteDecisionEngine()
        print("✅ AI inference pipeline loaded")
    except Exception as e:
        print(f"⚠️ AI pipeline not available: {e}. Using rule-based fallback.")
        _ai_pipeline = None
    return _ai_pipeline

# Also safe-load the predict module
try:
    from ai.predict import predict_freshness_ai as _ai_predict
    print("✅ AI freshness predictor loaded")
    def predict_freshness(expiry_time_str, image_path=None, food_type="other"):
        return _ai_predict(expiry_time_str, image_path, food_type)
except ImportError:
    def predict_freshness(expiry_time_str, image_path=None, food_type="other"):
        """Rule-based fallback freshness prediction."""
        import random
        from datetime import datetime
        try:
            expiry     = datetime.fromisoformat(expiry_time_str)
            diff_hours = (expiry - datetime.now()).total_seconds() / 3600
        except Exception:
            diff_hours = 12

        if diff_hours < 0:     urgency, score = 'expired',  0
        elif diff_hours < 3:   urgency, score = 'critical', random.randint(10, 30)
        elif diff_hours < 12:  urgency, score = 'high',     random.randint(30, 55)
        elif diff_hours < 24:  urgency, score = 'medium',   random.randint(55, 75)
        elif diff_hours < 72:  urgency, score = 'low',      random.randint(75, 90)
        else:                  urgency, score = 'safe',     random.randint(88, 100)

        return {
            "freshness_score":    score,
            "urgency":            urgency,
            "hours_remaining":    round(diff_hours, 1),
            "ai_class":           None,
            "ai_confidence":      None,
            "recommended_route":  "NGO"
        }
# ─────────────────────────────────────────────
# App Configuration
# ─────────────────────────────────────────────
app = Flask(__name__)
try:
    from flask_socketio import SocketIO, emit, join_room
except ImportError:
    class SocketIO:  # type: ignore[override]
        def __init__(self, app, *args, **kwargs):
            self.app = app

        def on(self, *_args, **_kwargs):
            def decorator(func):
                return func
            return decorator

        def emit(self, *args, **kwargs):
            return None

        def run(self, app, **kwargs):
            return app.run(**kwargs)

    def emit(*args, **kwargs):
        return None

    def join_room(*args, **kwargs):
        return None

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
app.secret_key = SECRET_KEY
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif", "webp"}

# Ensure directories exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs("data", exist_ok=True)

# ─────────────────────────────────────────────
# Data File Paths
# ─────────────────────────────────────────────
USERS_FILE       = os.path.join("data", "users.json")
DONATIONS_FILE   = os.path.join("data", "donations.json")
NOTIFS_FILE      = os.path.join("data", "notifications.json")
LEADERBOARD_FILE = os.path.join("data", "leaderboard.json")
LOCATIONS_FILE   = os.path.join("data", "locations.json")
NGOS_RAW_FILE    = os.path.join("data", "ngos_raw.json")
INSURANCE_FILE   = os.path.join("data", "insurance.json")
FUTURES_FILE     = os.path.join("data", "futures_market.json")
CARBON_FILE      = os.path.join("data", "carbon_credits.json")
AI_LOGS_FILE     = os.path.join("data", "ai_logs.json")

if os.environ.get("VERCEL") == "1":
    runtime_data_dir = os.path.join("/tmp", "foodsave-data")
    os.makedirs(runtime_data_dir, exist_ok=True)

    def _runtime_data_file(path):
        runtime_path = os.path.join(runtime_data_dir, os.path.basename(path))
        if not os.path.exists(runtime_path) and os.path.exists(path):
            shutil.copy2(path, runtime_path)
        return runtime_path

    USERS_FILE = _runtime_data_file(USERS_FILE)
    DONATIONS_FILE = _runtime_data_file(DONATIONS_FILE)
    NOTIFS_FILE = _runtime_data_file(NOTIFS_FILE)
    LEADERBOARD_FILE = _runtime_data_file(LEADERBOARD_FILE)
    LOCATIONS_FILE = _runtime_data_file(LOCATIONS_FILE)
    NGOS_RAW_FILE = _runtime_data_file(NGOS_RAW_FILE)
    INSURANCE_FILE = _runtime_data_file(INSURANCE_FILE)
    FUTURES_FILE = _runtime_data_file(FUTURES_FILE)
    CARBON_FILE = _runtime_data_file(CARBON_FILE)
    AI_LOGS_FILE = _runtime_data_file(AI_LOGS_FILE)

# ─────────────────────────────────────────────
# JSON Database Helpers
# ─────────────────────────────────────────────

REMOTE_STATE_KEYS = {
    os.path.basename(USERS_FILE),
    os.path.basename(DONATIONS_FILE),
    os.path.basename(NOTIFS_FILE),
    os.path.basename(LEADERBOARD_FILE),
    os.path.basename(INSURANCE_FILE),
    os.path.basename(FUTURES_FILE),
    os.path.basename(CARBON_FILE),
}


def _remote_state_key(filepath):
    filename = os.path.basename(filepath)
    if filename not in REMOTE_STATE_KEYS:
        return None
    return supabase_backend.state_key_for_file(filepath)

def read_json(filepath):
    """Read JSON file safely, return empty list if not found."""
    state_key = _remote_state_key(filepath)
    if state_key and supabase_backend.configured:
        try:
            data = supabase_backend.load_state(state_key, [])
            return data if isinstance(data, list) else []
        except Exception as exc:
            print(f"⚠️ Supabase read failed for {state_key}: {exc}")
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def write_json(filepath, data):
    """Write data to JSON file."""
    state_key = _remote_state_key(filepath)
    if state_key and supabase_backend.configured:
        try:
            supabase_backend.save_state(state_key, data)
            return
        except Exception as exc:
            print(f"⚠️ Supabase write failed for {state_key}: {exc}")
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)

def read_json_dict(filepath):
    """Read JSON file that contains a dict."""
    state_key = _remote_state_key(filepath)
    if state_key and supabase_backend.configured:
        try:
            data = supabase_backend.load_state(state_key, {})
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            print(f"⚠️ Supabase dict read failed for {state_key}: {exc}")
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def upload_runtime_dir():
    if os.environ.get("VERCEL") == "1":
        path = os.path.join(tempfile.gettempdir(), "foodsave-uploads")
    else:
        path = app.config["UPLOAD_FOLDER"]
    os.makedirs(path, exist_ok=True)
    return path


def persist_uploaded_image(file_storage):
    if not file_storage or not file_storage.filename:
        return {"image_path": "", "local_path": "", "bytes": None}

    original_name = secure_filename(file_storage.filename)
    filename = f"{uuid.uuid4()}_{original_name}"
    file_bytes = file_storage.read()
    if not file_bytes:
        return {"image_path": "", "local_path": "", "bytes": None}

    local_path = os.path.join(upload_runtime_dir(), filename)
    with open(local_path, "wb") as handle:
        handle.write(file_bytes)

    image_path = ""
    if supabase_backend.configured:
        try:
            image_path = supabase_backend.upload_image(
                file_bytes,
                filename,
                getattr(file_storage, "mimetype", None),
            )
        except Exception as exc:
            print(f"⚠️ Supabase image upload failed: {exc}")
    elif os.environ.get("VERCEL") != "1":
        image_path = f"/static/uploads/{filename}"

    return {"image_path": image_path, "local_path": local_path, "bytes": file_bytes}

def ensure_location_index():
    """Build normalized NGO/restaurant/farm locations from raw datasets if needed."""
    if os.path.exists(LOCATIONS_FILE):
        return
    script_path = os.path.join("scripts", "build_location_index.py")
    if not os.path.exists(script_path):
        return
    try:
        subprocess.run(["python3", script_path], check=True, timeout=45)
    except Exception as exc:
        print(f"⚠️ Could not build location index: {exc}")

def load_locations_index():
    """Load normalized locations, falling back to raw NGO data."""
    ensure_location_index()
    data = read_json_dict(LOCATIONS_FILE)
    if data:
        return data
    ngos = read_json(NGOS_RAW_FILE)
    return {
        "ngos": ngos,
        "restaurants": [],
        "poultry_farms": [],
        "biogas_plants": [],
        "cafeterias": []
    }

def hash_password(password):
    """Simple SHA-256 password hashing."""
    return hashlib.sha256(password.encode()).hexdigest()

def allowed_file(filename):
    """Check if file extension is allowed."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in app.config["ALLOWED_EXTENSIONS"]
    )

def get_user_by_id(user_id):
    """Fetch a single user by ID."""
    users = read_json(USERS_FILE)
    return next((u for u in users if u["id"] == user_id), None)

def get_user_by_email(email):
    """Fetch a single user by email."""
    users = read_json(USERS_FILE)
    return next((u for u in users if u["email"] == email), None)

def login_required(f):
    """Decorator: require login for protected routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Decorator: require admin role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        user = get_user_by_id(session["user_id"])
        if not user or user.get("role") != "admin":
            return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────────
# AI Placeholder Functions
# ─────────────────────────────────────────────

def predict_freshness(expiry_time_str, image_path=None, food_type="other"):
    """
    Simulate AI freshness prediction based on expiry time.
    Returns score 0-100 and urgency level.
    """
    if "_ai_predict" in globals():
        try:
            return _ai_predict(expiry_time_str, image_path)
        except Exception:
            pass

    try:
        expiry = datetime.fromisoformat(expiry_time_str)
        now = datetime.now()
        diff_hours = (expiry - now).total_seconds() / 3600

        if diff_hours < 0:
            score = 0
            urgency = "expired"
        elif diff_hours < 3:
            score = random.randint(10, 30)
            urgency = "critical"
        elif diff_hours < 12:
            score = random.randint(30, 55)
            urgency = "high"
        elif diff_hours < 24:
            score = random.randint(55, 75)
            urgency = "medium"
        elif diff_hours < 72:
            score = random.randint(75, 90)
            urgency = "low"
        else:
            score = random.randint(88, 100)
            urgency = "safe"

        return {"freshness_score": score, "urgency": urgency, "hours_remaining": round(diff_hours, 1)}
    except Exception:
        return {"freshness_score": 50, "urgency": "medium", "hours_remaining": 12}


def predict_freshness_by_expiry(expiry_time_str, food_type="other"):
    result = predict_freshness(expiry_time_str, image_path=None, food_type=food_type)
    result["available"] = True
    result["prediction_source"] = "expiry"
    result["recommended_route"] = result.get("recommended_route") or "NGO"
    result["predicted_class"] = result.get("predicted_class") or result.get("urgency")
    result["confidence"] = result.get("confidence")
    return result


def predict_freshness_by_trained_model(image_bytes=None, image_path=None):
    if image_bytes is None and not image_path:
        return {
            "available": False,
            "prediction_source": "trained_model",
            "reason": "upload an image to run your trained 200-epoch model",
        }
    try:
        from ai.model_predictor import predict_trained_food_model
        return predict_trained_food_model(image_bytes=image_bytes, image_path=image_path)
    except Exception as exc:
        return {
            "available": False,
            "prediction_source": "trained_model",
            "reason": f"trained model predictor unavailable: {exc}",
        }


def run_prediction_suite(expiry_time_str, image_path=None, image_bytes=None, food_type="other", mode="hybrid"):
    normalized_mode = (mode or "hybrid").strip().lower()
    if normalized_mode not in {"expiry", "trained_model", "hybrid"}:
        normalized_mode = "hybrid"

    expiry_prediction = predict_freshness_by_expiry(expiry_time_str, food_type=food_type)
    if normalized_mode == "expiry":
        model_prediction = {
            "available": False,
            "prediction_source": "trained_model",
            "reason": "trained model skipped because expiry-only mode is selected",
        }
    else:
        model_prediction = predict_freshness_by_trained_model(image_bytes=image_bytes, image_path=image_path)

    if normalized_mode == "trained_model" and model_prediction.get("available"):
        active_prediction = model_prediction
    elif normalized_mode == "trained_model":
        active_prediction = expiry_prediction
    elif normalized_mode == "hybrid" and model_prediction.get("available"):
        active_prediction = {
            **expiry_prediction,
            "prediction_source": "hybrid",
            "predicted_class": model_prediction.get("predicted_class"),
            "model_name": model_prediction.get("model_name"),
            "model_confidence": model_prediction.get("confidence"),
            "expiry_hours_remaining": expiry_prediction.get("hours_remaining"),
        }
        hybrid_score = round(
            (expiry_prediction.get("freshness_score", 50) + model_prediction.get("freshness_score", 50)) / 2
        )
        active_prediction["freshness_score"] = hybrid_score
        active_prediction["urgency"] = model_prediction.get("urgency") or expiry_prediction.get("urgency")
        active_prediction["recommended_route"] = (
            model_prediction.get("recommended_route") or expiry_prediction.get("recommended_route") or "NGO"
        )
    else:
        active_prediction = expiry_prediction

    return {
        "selected_mode": normalized_mode,
        "active_prediction": active_prediction,
        "expiry_prediction": expiry_prediction,
        "model_prediction": model_prediction,
        "model_available": bool(model_prediction.get("available")),
    }

def calculate_co2_saved(quantity_kg, food_type="other"):
    """
    Improved CO2 calculation using food-type-specific emission factors.
    Source: FAO / WRAP food waste emission data
    """
    # kg CO2 equivalent per kg of food wasted
    CO2_FACTORS = {
        "cooked":   2.5,   # mixed cooked meals
        "raw":      1.8,   # raw vegetables/fruits
        "bakery":   1.6,   # bread, pastries
        "dairy":    3.2,   # milk, cheese, yogurt
        "packaged": 2.0,   # processed packaged food
        "meat":     7.2,   # highest impact
        "other":    2.2    # default
    }
    factor = CO2_FACTORS.get(food_type, CO2_FACTORS["other"])
    co2    = round(quantity_kg * factor, 2)
    trees  = round(co2 / 21, 2)    # 1 tree absorbs ~21kg CO2/year
    water  = round(quantity_kg * 250, 0)  # liters of water saved
    return {
        "co2_kg":      co2,
        "trees_equiv": trees,
        "water_liters": water
    }

def parse_coordinate(value, minimum, maximum):
    """Return a valid coordinate float, or None for missing/invalid input."""
    try:
        coord = float(value)
    except (TypeError, ValueError):
        return None
    return coord if minimum <= coord <= maximum else None

def get_donation_recommendations(donation):
    """Return nearby human-relief and animal-feed matches for a donation."""
    try:
        from ai.matching import match_donation_to_ngo, match_donation_to_poultry
    except Exception as exc:
        print(f"⚠️ Donation recommendations unavailable: {exc}")
        return {"ngos": [], "poultry_farms": [], "recommended_route": "manual_review"}

    urgency = donation.get("urgency")
    freshness = donation.get("freshness_score", 50)
    food_type = donation.get("food_type", "other")

    ngos = []
    poultry = []
    if urgency != "expired":
        ngos = match_donation_to_ngo(donation, max_results=6)
    if urgency in ["expired", "critical", "high"] or freshness < 45 or food_type in ["raw", "bakery", "other"]:
        poultry = match_donation_to_poultry(donation, max_results=5)

    if urgency == "expired":
        route = "poultry_or_biogas"
    elif ngos:
        route = "ngo"
    elif poultry:
        route = "poultry_farm"
    else:
        route = "manual_review"

    return {
        "ngos": ngos,
        "poultry_farms": poultry,
        "recommended_route": route
    }

def upsert_geo_credit_for_donation(donation, status="provisional"):
    """Create or update a geo-dynamic carbon credit for a routed donation."""
    try:
        from ai.market_models import build_geo_credit
    except Exception as exc:
        print(f"⚠️ Geo credit unavailable: {exc}")
        return None

    credits = read_json(CARBON_FILE)
    credit = build_geo_credit(donation, status=status)
    existing_idx = next((idx for idx, item in enumerate(credits) if item.get("id") == credit["id"]), None)
    if existing_idx is None:
        credits.append(credit)
    else:
        credits[existing_idx].update(credit)
        credit = credits[existing_idx]
    write_json(CARBON_FILE, credits)
    donation["carbon_credit_id"] = credit["id"]
    donation["carbon_credit_status"] = credit["status"]
    donation["carbon_credit_kg_co2e"] = credit["kg_co2e"]
    return credit

def award_points(user_id, points, reason):
    """Award points to a user and create a notification."""
    users = read_json(USERS_FILE)
    for u in users:
        if u["id"] == user_id:
            u["points"] = u.get("points", 0) + points
            u["total_donations"] = u.get("total_donations", 0) + 1
            break
    write_json(USERS_FILE, users)

    # Add notification
    notifs = read_json(NOTIFS_FILE)
    notifs.append({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "message": f"🏆 You earned {points} points! {reason}",
        "type": "points",
        "read": False,
        "timestamp": datetime.now().isoformat()
    })
    write_json(NOTIFS_FILE, notifs)

def assign_badges(user):
    """Assign badges based on points and donations."""
    badges = []
    points = user.get("points", 0)
    donations = user.get("total_donations", 0)

    if points >= 100:
        badges.append("🌱 Green Starter")
    if points >= 500:
        badges.append("♻️ Eco Warrior")
    if points >= 1000:
        badges.append("🌍 Planet Saver")
    if donations >= 5:
        badges.append("🍽️ Food Hero")
    if donations >= 20:
        badges.append("🏆 Donation Champion")
    if user.get("role") == "volunteer":
        badges.append("🚀 Active Volunteer")

    return badges

# ─────────────────────────────────────────────
# Initialize Sample Data
# ─────────────────────────────────────────────

def init_sample_data():
    """Create sample data if files don't exist."""

    if not os.path.exists(USERS_FILE):
        sample_users = [
            {
                "id": "u001",
                "name": "Admin User",
                "email": "admin@foodwaste.ai",
                "password": hash_password("admin123"),
                "role": "admin",
                "points": 9999,
                "total_donations": 50,
                "location": "New York, NY",
                "joined": "2024-01-01",
                "approved": True,
                "avatar": ""
            },
            {
                "id": "u002",
                "name": "Green Kitchen Restaurant",
                "email": "restaurant@foodwaste.ai",
                "password": hash_password("pass123"),
                "role": "restaurant",
                "points": 1200,
                "total_donations": 35,
                "location": "Brooklyn, NY",
                "joined": "2024-02-15",
                "approved": True,
                "avatar": ""
            },
            {
                "id": "u003",
                "name": "Hope NGO",
                "email": "ngo@foodwaste.ai",
                "password": hash_password("pass123"),
                "role": "ngo",
                "points": 800,
                "total_donations": 0,
                "location": "Manhattan, NY",
                "joined": "2024-03-10",
                "approved": True,
                "avatar": ""
            },
            {
                "id": "u004",
                "name": "Alex Volunteer",
                "email": "volunteer@foodwaste.ai",
                "password": hash_password("pass123"),
                "role": "volunteer",
                "points": 450,
                "total_donations": 12,
                "location": "Queens, NY",
                "joined": "2024-04-01",
                "approved": True,
                "avatar": ""
            },
            {
                "id": "u005",
                "name": "Sarah Household",
                "email": "donor@foodwaste.ai",
                "password": hash_password("pass123"),
                "role": "donor",
                "points": 320,
                "total_donations": 8,
                "location": "Bronx, NY",
                "joined": "2024-05-20",
                "approved": True,
                "avatar": ""
            }
        ]
        write_json(USERS_FILE, sample_users)

    if not os.path.exists(DONATIONS_FILE):
        now = datetime.now()
        sample_donations = [
            {
                "id": "d001",
                "donor_id": "u002",
                "donor_name": "Green Kitchen Restaurant",
                "food_name": "Vegetable Curry",
                "food_type": "cooked",
                "quantity": 5,
                "quantity_unit": "kg",
                "expiry_time": (now + timedelta(hours=6)).isoformat(),
                "location": "Brooklyn, NY",
                "coordinates": {"lat": 40.6782, "lng": -73.9442},
                "description": "Fresh vegetable curry, made today. Enough for 10 people.",
                "image": "",
                "freshness_score": 72,
                "urgency": "medium",
                "status": "available",
                "accepted_by": None,
                "completed": False,
                "co2_saved": 12.5,
                "created_at": (now - timedelta(hours=2)).isoformat()
            },
            {
                "id": "d002",
                "donor_id": "u005",
                "donor_name": "Sarah Household",
                "food_name": "Bread Loaves",
                "food_type": "bakery",
                "quantity": 3,
                "quantity_unit": "pieces",
                "expiry_time": (now + timedelta(hours=12)).isoformat(),
                "location": "Bronx, NY",
                "coordinates": {"lat": 40.8448, "lng": -73.8648},
                "description": "3 fresh bread loaves from this morning.",
                "image": "",
                "freshness_score": 85,
                "urgency": "low",
                "status": "accepted",
                "accepted_by": "u004",
                "completed": False,
                "co2_saved": 7.5,
                "created_at": (now - timedelta(hours=5)).isoformat()
            },
            {
                "id": "d003",
                "donor_id": "u002",
                "donor_name": "Green Kitchen Restaurant",
                "food_name": "Mixed Salads",
                "food_type": "raw",
                "quantity": 2,
                "quantity_unit": "kg",
                "expiry_time": (now + timedelta(hours=3)).isoformat(),
                "location": "Brooklyn, NY",
                "coordinates": {"lat": 40.6892, "lng": -73.9442},
                "description": "Fresh mixed salads prepared today.",
                "image": "",
                "freshness_score": 45,
                "urgency": "high",
                "status": "available",
                "accepted_by": None,
                "completed": False,
                "co2_saved": 5.0,
                "created_at": (now - timedelta(hours=8)).isoformat()
            },
            {
                "id": "d004",
                "donor_id": "u002",
                "donor_name": "Green Kitchen Restaurant",
                "food_name": "Rice & Dal",
                "food_type": "cooked",
                "quantity": 8,
                "quantity_unit": "kg",
                "expiry_time": (now - timedelta(hours=2)).isoformat(),
                "location": "Brooklyn, NY",
                "coordinates": {"lat": 40.6700, "lng": -73.9350},
                "description": "Large batch of rice and dal from lunch service.",
                "image": "",
                "freshness_score": 15,
                "urgency": "expired",
                "status": "completed",
                "accepted_by": "u004",
                "completed": True,
                "co2_saved": 20.0,
                "created_at": (now - timedelta(hours=24)).isoformat()
            }
        ]
        write_json(DONATIONS_FILE, sample_donations)

    if not os.path.exists(NOTIFS_FILE):
        sample_notifs = [
            {
                "id": "n001",
                "user_id": "u002",
                "message": "🍽️ Your donation 'Vegetable Curry' is available for pickup!",
                "type": "donation",
                "read": False,
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": "n002",
                "user_id": "u004",
                "message": "📦 Pickup accepted: Bread Loaves from Sarah Household",
                "type": "pickup",
                "read": False,
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": "n003",
                "user_id": "u003",
                "message": "⚠️ New high-urgency donation available near you!",
                "type": "alert",
                "read": False,
                "timestamp": datetime.now().isoformat()
            }
        ]
        write_json(NOTIFS_FILE, sample_notifs)

# Run data initialization
init_sample_data()

# ─────────────────────────────────────────────
# Page Routes (HTML Templates)
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("landing.html")

@app.route("/home")
def home_page():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/donate")
def donate():
    return render_template("donate.html")

@app.route("/ngo")
def ngo():
    return render_template("ngo.html")

@app.route("/network")
def restaurant_network_page():
    return render_template("network.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/signup")
def signup_page():
    return render_template("signup.html")

@app.route("/admin")
def admin_page():
    return render_template("dashboard.html")


@app.route("/landing")
def landing_page():
    return render_template("landing.html")

# ─────────────────────────────────────────────
# API Route 1: /api/signup
# ─────────────────────────────────────────────


# ─────────────────────────────────────────────
# API: /api/predict — Full AI Prediction
# ─────────────────────────────────────────────
@app.route("/api/predict", methods=["POST"])
def ai_predict():
    """Full AI prediction pipeline."""
    try:
        from ai.inference.predict import predict as ai_predict_fn

        lat = float(request.form.get("lat", 28.6139))
        lng = float(request.form.get("lng", 77.2090))
        expiry = request.form.get("expiry_hours")
        expiry = float(expiry) if expiry else None

        if "image" in request.files:
            file  = request.files["image"]
            bytes_data = file.read()
            result = ai_predict_fn(bytes_data, lat, lng, expiry)
        else:
            result = ai_predict_fn(None, lat, lng, expiry)

        return jsonify({"success": True, "prediction": result})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
@app.route("/api/signup", methods=["POST"])
def signup():
    """Register a new user."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required = ["name", "email", "password", "role"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Missing field: {field}"}), 400

    users = read_json(USERS_FILE)

    # Check duplicate email
    if any(u["email"] == data["email"] for u in users):
        return jsonify({"error": "Email already registered"}), 409

    new_user = {
        "id": str(uuid.uuid4()),
        "name": data["name"],
        "email": data["email"],
        "password": hash_password(data["password"]),
        "role": data["role"],
        "points": 50,  # welcome bonus
        "total_donations": 0,
        "location": data.get("location", ""),
        "joined": datetime.now().isoformat(),
        "approved": data["role"] not in ["ngo", "restaurant"],  # NGOs/restaurants need approval
        "avatar": ""
    }

    users.append(new_user)
    write_json(USERS_FILE, users)

    # Welcome notification
    notifs = read_json(NOTIFS_FILE)
    notifs.append({
        "id": str(uuid.uuid4()),
        "user_id": new_user["id"],
        "message": f"🎉 Welcome {new_user['name']}! You've joined the Food Waste movement. +50 bonus points!",
        "type": "welcome",
        "read": False,
        "timestamp": datetime.now().isoformat()
    })
    write_json(NOTIFS_FILE, notifs)

    # Set session
    session["user_id"] = new_user["id"]
    session["user_name"] = new_user["name"]
    session["user_role"] = new_user["role"]

    safe_user = {k: v for k, v in new_user.items() if k != "password"}
    safe_user["badges"] = assign_badges(new_user)

    return jsonify({"success": True, "user": safe_user}), 201
# ─────────────────────────────────────────────
# API: /api/locations — NGOs, Biogas, Restaurants
# ─────────────────────────────────────────────
@app.route("/api/locations", methods=["GET"])
def get_locations():
    """Return all location data for map display."""
    data = load_locations_index()
    try:
        restaurant_limit = int(request.args.get("restaurant_limit", 500))
    except ValueError:
        restaurant_limit = 500
    try:
        ngo_limit = int(request.args.get("ngo_limit", 1000))
    except ValueError:
        ngo_limit = 1000
    restaurant_limit = min(max(restaurant_limit, 0), 2000)
    ngo_limit = min(max(ngo_limit, 0), 3000)

    return jsonify({
        "success": True,
        "ngos":         data.get("ngos", [])[:ngo_limit],
        "biogas":       data.get("biogas_plants", []),
        "restaurants":  data.get("restaurants", [])[:restaurant_limit],
        "poultry_farms": data.get("poultry_farms", []),
        "cafeterias":   data.get("cafeterias", []),
        "counts": {
            "ngos": len(data.get("ngos", [])),
            "restaurants": len(data.get("restaurants", [])),
            "poultry_farms": len(data.get("poultry_farms", []))
        }
    })

# ─────────────────────────────────────────────
# API Route 2: /api/login
# ─────────────────────────────────────────────

@app.route("/api/login", methods=["POST"])
def login():
    """Authenticate user and start session."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    users = read_json(USERS_FILE)
    user = next(
        (u for u in users if u["email"].lower() == email and u["password"] == hash_password(password)),
        None
    )

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_role"] = user["role"]

    safe_user = {k: v for k, v in user.items() if k != "password"}
    safe_user["badges"] = assign_badges(user)

    return jsonify({"success": True, "user": safe_user})

# ─────────────────────────────────────────────
# API: /api/match_donation — Smart NGO matching
# ─────────────────────────────────────────────
@app.route("/api/match_donation", methods=["POST"])
@login_required
def match_donation():
    """Return best NGO matches for a given donation."""
    try:
        from ai.matching import match_donation_to_ngo, assign_to_biogas
    except Exception as exc:
        return jsonify({"error": f"Matching module not available: {exc}"}), 500

    data = request.get_json()
    donation_id = data.get("donation_id")

    donations = read_json(DONATIONS_FILE)
    donation  = next((d for d in donations if d["id"] == donation_id), None)
    if not donation:
        return jsonify({"error": "Donation not found"}), 404

    matches = match_donation_to_ngo(donation)

    # Biogas fallback if expired or no matches
    biogas = None
    if donation.get("urgency") == "expired" or not matches:
        biogas = assign_to_biogas(donation)

    return jsonify({
        "success":       True,
        "matches":       matches,
        "biogas_fallback": biogas
    })

@app.route("/api/nearby_entities", methods=["GET"])
def nearby_entities():
    """Find NGOs, poultry partners, and restaurants around a coordinate."""
    lat = parse_coordinate(request.args.get("lat"), -90, 90)
    lng = parse_coordinate(request.args.get("lng"), -180, 180)
    if lat is None or lng is None:
        return jsonify({"error": "Valid lat and lng query parameters are required"}), 400

    try:
        radius_km = float(request.args.get("radius_km", 10))
    except ValueError:
        radius_km = 10
    radius_km = min(max(radius_km, 1), 100)
    limit = min(max(int(request.args.get("limit", 12)), 1), 50)
    food_type = request.args.get("food_type", "cooked")
    quantity = request.args.get("quantity", 1)
    city = request.args.get("city", "")

    probe_donation = {
        "food_type": food_type,
        "quantity": quantity,
        "urgency": request.args.get("urgency", "medium"),
        "freshness_score": 70,
        "coordinates": {"lat": lat, "lng": lng}
    }

    try:
        from ai.matching import match_donation_to_ngo, match_donation_to_poultry, find_nearby_restaurants
    except Exception as exc:
        return jsonify({"error": f"Matching module not available: {exc}"}), 500

    ngos = [m for m in match_donation_to_ngo(probe_donation, max_results=limit) if m["distance_km"] <= radius_km]
    poultry = [m for m in match_donation_to_poultry(probe_donation, max_results=limit) if m["distance_km"] <= radius_km]
    restaurants = find_nearby_restaurants(lat, lng, radius_km=radius_km, limit=limit, city=city)

    return jsonify({
        "success": True,
        "center": {"lat": lat, "lng": lng},
        "radius_km": radius_km,
        "ngos": ngos,
        "poultry_farms": poultry,
        "restaurants": restaurants
    })


# ─────────────────────────────────────────────
# API: /api/plan_route — OR-Tools Routing
# ─────────────────────────────────────────────
@app.route("/api/plan_route", methods=["POST"])
@login_required
def plan_route():
    """Plan optimized pickup route for volunteer."""
    try:
        from ai.ortools_routing import plan_volunteer_route
        data         = request.get_json()
        volunteer_id = data.get("volunteer_id", session["user_id"])
        donation_ids = data.get("donation_ids", [])

        if not donation_ids:
            # Auto-select accepted donations for this volunteer
            donations    = read_json(DONATIONS_FILE)
            donation_ids = [
                d["id"] for d in donations
                if d.get("accepted_by") == session["user_id"]
                and d.get("status") == "accepted"
            ]

        result = plan_volunteer_route(volunteer_id, donation_ids)
        return jsonify({"success": True, "route": result})

    except ImportError as e:
        return jsonify({"success": False, "error": "Routing module unavailable"}), 503
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
# ─────────────────────────────────────────────
# API Route 3: /api/logout
# ─────────────────────────────────────────────

@app.route("/api/logout", methods=["POST"])
def logout():
    """Clear user session."""
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})

# ─────────────────────────────────────────────
# API Route 4: /api/upload_food
# ─────────────────────────────────────────────

@app.route("/api/upload_food", methods=["POST"])
@login_required
def upload_food():
    """Create a new food donation with optional image upload."""
    try:
        user_id = session["user_id"]

        # Get form fields
        food_name    = request.form.get("food_name", "").strip()
        food_type    = request.form.get("food_type", "other")
        quantity     = request.form.get("quantity", "1")
        quantity_unit= request.form.get("quantity_unit", "kg")
        expiry_time  = request.form.get("expiry_time", "")
        location     = request.form.get("location", "")
        description  = request.form.get("description", "")
        lat          = request.form.get("lat", "")
        lng          = request.form.get("lng", "")
        prediction_mode = request.form.get("prediction_mode", "hybrid")

        if not food_name or not expiry_time or not location:
            return jsonify({"error": "Food name, expiry time, and pickup location are required"}), 400

        lat_num = parse_coordinate(lat, -90, 90)
        lng_num = parse_coordinate(lng, -180, 180)
        if lat_num is None or lng_num is None:
            return jsonify({
                "error": "GPS pickup coordinates are required. Allow location access in your browser, then try the upload again."
            }), 400

        # Handle image upload
        image_path = ""
        local_image_path = ""
        image_bytes = None
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename and allowed_file(file.filename):
                image_info = persist_uploaded_image(file)
                image_path = image_info["image_path"]
                local_image_path = image_info["local_path"]
                image_bytes = image_info["bytes"]

        # AI freshness prediction
        prediction_suite = run_prediction_suite(
            expiry_time,
            image_path=local_image_path or None,
            image_bytes=image_bytes,
            food_type=food_type,
            mode=prediction_mode,
        )
        ai_result = prediction_suite["active_prediction"]

        # Get donor info
        user = get_user_by_id(user_id)
        donor_name = user["name"] if user else "Unknown"

        # CO2 calculation
        try:
            qty_num = float(quantity)
        except ValueError:
            qty_num = 1.0

        co2_data = calculate_co2_saved(qty_num, food_type)
        co2 = co2_data["co2_kg"]

        donation = {
            "id": str(uuid.uuid4()),
            "donor_id": user_id,
            "donor_name": donor_name,
            "food_name": food_name,
            "food_type": food_type,
            "quantity": qty_num,
            "quantity_unit": quantity_unit,
            "expiry_time": expiry_time,
            "location": location,
            "coordinates": {"lat": lat_num, "lng": lng_num},
            "description": description,
            "image": image_path,
            "freshness_score": ai_result["freshness_score"],
            "urgency": ai_result["urgency"],
            "hours_remaining": ai_result["hours_remaining"],
            "prediction_mode": prediction_suite["selected_mode"],
            "expiry_prediction": prediction_suite["expiry_prediction"],
            "model_prediction": prediction_suite["model_prediction"],
            "status": "available",
            "accepted_by": None,
            "completed": False,
            "co2_saved": co2,
            "created_at": datetime.now().isoformat(),
            "trees_saved": co2_data["trees_equiv"],
            "water_saved": co2_data["water_liters"],
            "is_event": request.form.get("is_event") == "on",
            "event_type": request.form.get("event_type", ""),
            "event_date": request.form.get("event_date", ""),
            "event_venue": request.form.get("event_venue", ""),
            "guest_count": request.form.get("guest_count", ""),
            "pickup_window": request.form.get("pickup_window", "2"),
        }
        donations = read_json(DONATIONS_FILE)
        donations.append(donation)
        write_json(DONATIONS_FILE, donations)

        recommendations = get_donation_recommendations(donation)
        donation["matches"] = recommendations
        donation["recommended_route"] = recommendations["recommended_route"]
        credit = upsert_geo_credit_for_donation(donation, status="provisional")
        if credit:
            donation["carbon_credit_preview"] = credit
        donations[-1] = donation
        write_json(DONATIONS_FILE, donations)

        if donation["urgency"] == "expired":
            try:
                from ai.matching import assign_to_biogas
                biogas = assign_to_biogas(donation)
                if biogas:
                    donation["biogas_assigned"]  = True
                    donation["biogas_plant"]     = biogas["plant"]["name"]
                    donation["biogas_plant_id"]  = biogas["plant"]["id"]
                    donation["status"]           = "biogas_routed"
                    donation["recommended_route"] = "biogas"
                    credit = upsert_geo_credit_for_donation(donation, status="provisional")
                    if credit:
                        donation["carbon_credit_preview"] = credit
                    donations[-1] = donation
                    write_json(DONATIONS_FILE, donations)
            except Exception as exc:
                print(f"⚠️ Biogas auto-assign unavailable: {exc}")

        award_points(user_id, 100, "for creating a food donation!")

        users = read_json(USERS_FILE)
        notifs = read_json(NOTIFS_FILE)
        for u in users:
            if u["role"] in ["ngo", "volunteer"] and u["approved"]:
                urgency_emoji = {"critical": "🆘", "high": "⚠️", "medium": "📦", "low": "✅", "safe": "🌿"}.get(
                    ai_result["urgency"], "📦"
                )
                notifs.append({
                    "id": str(uuid.uuid4()),
                    "user_id": u["id"],
                    "message": f"{urgency_emoji} New {ai_result['urgency'].upper()} donation: {food_name} at {location}",
                    "type": "new_donation",
                    "read": False,
                    "donation_id": donation["id"],
                    "timestamp": datetime.now().isoformat()
                })
        write_json(NOTIFS_FILE, notifs)

        return jsonify({
            "success": True,
            "donation": donation,
            "matches": recommendations,
            "ai_prediction": {
                **ai_result,
                "selected_mode": prediction_suite["selected_mode"],
                "expiry_prediction": prediction_suite["expiry_prediction"],
                "model_prediction": prediction_suite["model_prediction"],
                "model_available": prediction_suite["model_available"],
            },
            "message": "Donation created successfully! +100 points earned."
        }), 201
    except Exception as exc:
        print("❌ upload_food failed")
        print(traceback.format_exc())
        return jsonify({
            "error": f"Upload failed on server: {exc}"
        }), 500

# ─────────────────────────────────────────────
# API Route 5: /api/get_donations
# ─────────────────────────────────────────────

@app.route("/api/get_donations", methods=["GET"])
def get_donations():
    """Get all donations with optional filtering."""
    donations = read_json(DONATIONS_FILE)

    # Query params
    status   = request.args.get("status")        # available, accepted, completed
    urgency  = request.args.get("urgency")        # critical, high, medium, low, safe
    food_type= request.args.get("food_type")      # cooked, raw, bakery, etc.
    donor_id = request.args.get("donor_id")       # filter by donor
    try:
        limit = int(request.args.get("limit", 50))
    except ValueError:
        limit = 50
    limit = min(max(limit, 1), 500)
    near_lat = parse_coordinate(request.args.get("lat"), -90, 90)
    near_lng = parse_coordinate(request.args.get("lng"), -180, 180)
    radius_km = request.args.get("radius_km")
    try:
        radius_km = float(radius_km) if radius_km else None
    except ValueError:
        radius_km = None

    filtered = donations

    if status:
        filtered = [d for d in filtered if d.get("status") == status]
    if urgency:
        filtered = [d for d in filtered if d.get("urgency") == urgency]
    if food_type:
        filtered = [d for d in filtered if d.get("food_type") == food_type]
    if donor_id:
        filtered = [d for d in filtered if d.get("donor_id") == donor_id]

    if near_lat is not None and near_lng is not None:
        try:
            from ai.matching import haversine_km
            for donation in filtered:
                coords = donation.get("coordinates", {})
                d_lat = parse_coordinate(coords.get("lat"), -90, 90)
                d_lng = parse_coordinate(coords.get("lng"), -180, 180)
                donation["distance_km"] = round(haversine_km(near_lat, near_lng, d_lat, d_lng), 2) if d_lat is not None and d_lng is not None else None
            filtered = [d for d in filtered if d.get("distance_km") is not None]
            if radius_km:
                filtered = [d for d in filtered if d["distance_km"] <= radius_km]
            filtered.sort(key=lambda d: d.get("distance_km", 999999))
        except ImportError:
            pass

    # Sort by urgency priority then time
    urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "safe": 4, "expired": 5}
    if near_lat is None or near_lng is None:
        filtered.sort(key=lambda d: urgency_order.get(d.get("urgency", "safe"), 99))

    return jsonify({
        "success": True,
        "donations": filtered[:limit],
        "total": len(filtered)
    })

# ─────────────────────────────────────────────
# API Route 6: /api/accept_donation
# ─────────────────────────────────────────────

@app.route("/api/accept_donation", methods=["POST"])
@login_required
def accept_donation():
    """Volunteer or NGO accepts a donation for pickup."""
    data = request.get_json()
    donation_id = data.get("donation_id")

    if not donation_id:
        return jsonify({"error": "donation_id required"}), 400

    user_id = session["user_id"]
    user = get_user_by_id(user_id)

    if not user or user.get("role") not in ["volunteer", "ngo", "admin"]:
        return jsonify({"error": "Only volunteers and NGOs can accept donations"}), 403

    donations = read_json(DONATIONS_FILE)
    donation = next((d for d in donations if d["id"] == donation_id), None)

    if not donation:
        return jsonify({"error": "Donation not found"}), 404

    if donation["status"] != "available":
        return jsonify({"error": "Donation is no longer available"}), 409

    donation["status"] = "accepted"
    donation["accepted_by"] = user_id
    donation["accepted_at"] = datetime.now().isoformat()

    write_json(DONATIONS_FILE, donations)

    # Real-time push notification
    try:
        push_notification(
            donation["donor_id"],
            f"🚗 {user['name']} accepted your donation '{donation['food_name']}'!",
            "pickup_accepted"
        )
        push_donation_update(donation_id, "accepted", f"Pickup accepted by {user['name']}")
    except Exception:
        pass

    # Notify donor
    notifs = read_json(NOTIFS_FILE)
    notifs.append({
        "id": str(uuid.uuid4()),
        "user_id": donation["donor_id"],
        "message": f"✅ {user['name']} has accepted your donation '{donation['food_name']}' for pickup!",
        "type": "pickup_accepted",
        "read": False,
        "donation_id": donation_id,
        "timestamp": datetime.now().isoformat()
    })
    write_json(NOTIFS_FILE, notifs)

    return jsonify({
        "success": True,
        "message": "Donation accepted! Please pick up soon.",
        "donation": donation
    })

# ─────────────────────────────────────────────
# API Route 7: /api/complete_donation
# ─────────────────────────────────────────────

@app.route("/api/complete_donation", methods=["POST"])
@login_required
def complete_donation():
    """Mark a donation as completed after pickup/delivery."""
    data = request.get_json()
    donation_id = data.get("donation_id")

    if not donation_id:
        return jsonify({"error": "donation_id required"}), 400

    user_id = session["user_id"]
    donations = read_json(DONATIONS_FILE)
    donation = next((d for d in donations if d["id"] == donation_id), None)

    if not donation:
        return jsonify({"error": "Donation not found"}), 404

    if donation.get("accepted_by") != user_id and session.get("user_role") != "admin":
        return jsonify({"error": "You are not authorized to complete this donation"}), 403

    donation["status"] = "completed"
    donation["completed"] = True
    donation["completed_at"] = datetime.now().isoformat()
    credit = upsert_geo_credit_for_donation(donation, status="verified")
    if credit:
        donation["carbon_credit_preview"] = credit
    write_json(DONATIONS_FILE, donations)

    # Award points to volunteer/NGO
    award_points(user_id, 150, "for completing a food pickup!")

    # Award points to donor too
    award_points(donation["donor_id"], 50, "for your donation being successfully delivered!")

    # Notify donor
    notifs = read_json(NOTIFS_FILE)
    user = get_user_by_id(user_id)
    notifs.append({
        "id": str(uuid.uuid4()),
        "user_id": donation["donor_id"],
        "message": f"🎉 Your donation '{donation['food_name']}' was successfully delivered! {donation['co2_saved']} kg CO₂ saved!",
        "type": "completed",
        "read": False,
        "donation_id": donation_id,
        "timestamp": datetime.now().isoformat()
    })
    write_json(NOTIFS_FILE, notifs)

    return jsonify({
        "success": True,
        "message": "Donation completed! +150 points earned.",
        "co2_saved": donation.get("co2_saved", 0),
        "carbon_credit": credit
    })

# ─────────────────────────────────────────────
# API Route 8: /api/leaderboard
# ─────────────────────────────────────────────

@app.route("/api/leaderboard", methods=["GET"])
def leaderboard():
    """Get top users by points."""
    users = read_json(USERS_FILE)
    role = request.args.get("role")

    ranked = [u for u in users if u.get("role") != "admin"]
    if role:
        ranked = [u for u in ranked if u.get("role") == role]

    ranked.sort(key=lambda u: u.get("points", 0), reverse=True)

    result = []
    for i, u in enumerate(ranked[:20], 1):
        result.append({
            "rank": i,
            "id": u["id"],
            "name": u["name"],
            "role": u["role"],
            "points": u.get("points", 0),
            "total_donations": u.get("total_donations", 0),
            "badges": assign_badges(u),
            "location": u.get("location", "")
        })

    return jsonify({"success": True, "leaderboard": result})

# ─────────────────────────────────────────────
# API Route 9: /api/stats (Enhanced)
# ─────────────────────────────────────────────

@app.route("/api/stats", methods=["GET"])
def stats():
    """Get platform-wide statistics with enhanced metrics."""
    donations = read_json(DONATIONS_FILE)
    users = read_json(USERS_FILE)

    completed = [d for d in donations if d.get("completed")]
    total_co2  = sum(d.get("co2_saved", 0) for d in completed)
    total_food = sum(d.get("quantity", 0) for d in completed)
    total_meals = int(total_food / 0.25)  # assume 250g per meal

    # User stats
    donors     = [u for u in users if u.get("role") == "donor"]
    restaurants= [u for u in users if u.get("role") == "restaurant"]
    ngos       = [u for u in users if u.get("role") == "ngo"]
    volunteers = [u for u in users if u.get("role") == "volunteer"]

    return jsonify({
        "success": True,
        "stats": {
            "total_donations":       len(donations),
            "completed_donations":   len(completed),
            "available_donations":   len([d for d in donations if d.get("status") == "available"]),
            "total_co2_saved":       round(total_co2, 2),
            "total_food_kg":         round(total_food, 2),
            "total_meals_donated":   total_meals,
            "total_users":           len(users),
            "donors":                len(donors),
            "restaurants":           len(restaurants),
            "ngos":                  len(ngos),
            "volunteers":            len(volunteers),
            "cities_reached":        12,
            "trees_equivalent":      round(total_co2 / 21, 1),

            # === NEW ENHANCED FIELDS ===
            "active_pickups":        len([d for d in donations if d.get("status") == "accepted"]),
            "biogas_routed":         len([d for d in donations if d.get("biogas_assigned")]),
            "poultry_routed":        len([d for d in donations if d.get("urgency") == "high" and d.get("completed")]),
            "water_saved_liters":    round(total_food * 250, 0),
            "co2_per_kg":            2.5,
            "avg_response_time_min": 35,
            "platform_uptime_days":  90,
            "total_volunteers":      len([u for u in users if u.get("role") == "volunteer"]),
            "pending_approvals":     len([u for u in users if not u.get("approved", True)])
        }
    })

@app.route("/api/dashboard_analytics", methods=["GET"])
@login_required
def dashboard_analytics():
    """Return dashboard-ready AI, routing, and visualization metrics."""
    donations = read_json(DONATIONS_FILE)
    users = read_json(USERS_FILE)
    ai_logs = read_json(AI_LOGS_FILE) if os.path.exists(AI_LOGS_FILE) else []

    def safe_float(value, default=0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "safe": 4, "expired": 5}
    sorted_donations = sorted(donations, key=lambda d: urgency_order.get(d.get("urgency", "safe"), 99))
    completed = [d for d in donations if d.get("completed")]
    accepted = [d for d in donations if d.get("status") == "accepted"]
    available = [d for d in donations if d.get("status") == "available"]

    by_status = {}
    by_urgency = {}
    by_food_type = {}
    by_route = {"NGO": 0, "Poultry": 0, "Biogas": 0}
    by_city = {}

    for donation in donations:
        status = donation.get("status", "unknown")
        urgency = donation.get("urgency", "unknown")
        food_type = donation.get("food_type", "other")
        location = (donation.get("location") or "Unknown").split(",")[0].strip() or "Unknown"

        by_status[status] = by_status.get(status, 0) + 1
        by_urgency[urgency] = by_urgency.get(urgency, 0) + 1
        by_food_type[food_type] = by_food_type.get(food_type, 0) + 1
        by_city[location] = by_city.get(location, 0) + 1

        if donation.get("biogas_assigned") or urgency == "expired":
            by_route["Biogas"] += 1
        elif urgency in ["critical", "high", "safe", "low"]:
            by_route["NGO"] += 1
        else:
            by_route["Poultry"] += 1

    confidences = [
        safe_float(log.get("confidence"))
        for log in ai_logs
        if log.get("confidence") is not None
    ]
    freshness_scores = [safe_float(d.get("freshness_score")) for d in donations if d.get("freshness_score") is not None]
    avg_confidence = round((sum(confidences) / len(confidences)) * 100, 1) if confidences else None
    avg_freshness = round(sum(freshness_scores) / len(freshness_scores), 1) if freshness_scores else 0

    total_distance_km = len(accepted) * 4.8 + len(completed) * 7.2
    optimized_distance_km = round(total_distance_km * 0.72, 1)
    distance_saved_km = round(total_distance_km - optimized_distance_km, 1)

    recent_predictions = ai_logs[-8:][::-1]
    if not recent_predictions:
        recent_predictions = [
            {
                "timestamp": d.get("created_at"),
                "food_name": d.get("food_name"),
                "predicted_class": d.get("urgency"),
                "freshness_score": d.get("freshness_score"),
                "confidence": None,
                "recommended_route": "Biogas" if d.get("urgency") == "expired" else "NGO",
                "location": d.get("location", "")
            }
            for d in sorted_donations[:8]
        ]

    map_donations = [
        {
            "id": d.get("id"),
            "food_name": d.get("food_name"),
            "donor_name": d.get("donor_name"),
            "status": d.get("status"),
            "urgency": d.get("urgency"),
            "location": d.get("location"),
            "quantity": d.get("quantity"),
            "quantity_unit": d.get("quantity_unit"),
            "freshness_score": d.get("freshness_score"),
            "coordinates": d.get("coordinates")
        }
        for d in donations
        if d.get("coordinates", {}).get("lat") is not None and d.get("coordinates", {}).get("lng") is not None
    ]

    return jsonify({
        "success": True,
        "analytics": {
            "ai": {
                "avg_confidence": avg_confidence,
                "avg_freshness": avg_freshness,
                "prediction_count": len(ai_logs),
                "recent_predictions": recent_predictions,
                "class_distribution": by_urgency
            },
            "donations": {
                "total": len(donations),
                "available": len(available),
                "accepted": len(accepted),
                "completed": len(completed),
                "by_status": by_status,
                "by_urgency": by_urgency,
                "by_food_type": by_food_type,
                "by_city": dict(sorted(by_city.items(), key=lambda item: item[1], reverse=True)[:6])
            },
            "routing": {
                "route_distribution": by_route,
                "active_pickups": len(accepted),
                "optimized_distance_km": optimized_distance_km,
                "distance_saved_km": distance_saved_km,
                "estimated_time_saved_min": round(distance_saved_km * 3.4),
                "nearest_match_rate": 92 if donations else 0
            },
            "map_donations": map_donations,
            "user_count": len(users)
        }
    })

# ─────────────────────────────────────────────
# API Route 10: Restaurant Network Intelligence
# ─────────────────────────────────────────────

@app.route("/api/network/overview", methods=["GET"])
def network_overview():
    """Unified restaurant-to-NGO/farm/biogas market snapshot."""
    try:
        from ai.market_models import restaurant_network_snapshot
    except ImportError:
        return jsonify({"error": "Market module not available"}), 500

    lat = parse_coordinate(request.args.get("lat"), -90, 90) or 28.6139
    lng = parse_coordinate(request.args.get("lng"), -180, 180) or 77.2090
    snapshot = restaurant_network_snapshot(
        load_locations_index(),
        read_json(INSURANCE_FILE),
        read_json(FUTURES_FILE),
        read_json(CARBON_FILE),
        lat=lat,
        lng=lng
    )
    return jsonify({"success": True, "network": snapshot})


@app.route("/api/freshness_insurance", methods=["GET", "POST"])
def freshness_insurance():
    """FIaaS: issue a freshness guarantee ledger entry."""
    if request.method == "GET":
        contracts = read_json(INSURANCE_FILE)
        return jsonify({"success": True, "contracts": contracts[::-1][:30], "total": len(contracts)})

    try:
        from ai.market_models import build_freshness_contract
    except ImportError:
        return jsonify({"error": "Market module not available"}), 500

    payload = dict(request.form) if request.form else (request.get_json(silent=True) or {})
    food_item = payload.get("food_item") or payload.get("food_name") or "Food batch"
    food_type = payload.get("food_type", "other")
    expiry_time = payload.get("expiry_time")
    if not expiry_time:
        hours = float(payload.get("expected_hours", 24) or 24)
        expiry_time = (datetime.now() + timedelta(hours=hours)).isoformat(timespec="minutes")

    image_path = ""
    local_image_path = ""
    image_bytes = None
    if "image" in request.files:
        file = request.files["image"]
        if file and file.filename and allowed_file(file.filename):
            image_info = persist_uploaded_image(file)
            image_path = image_info["image_path"]
            local_image_path = image_info["local_path"]
            image_bytes = image_info["bytes"]

    prediction_suite = run_prediction_suite(
        expiry_time,
        image_path=local_image_path or None,
        image_bytes=image_bytes,
        food_type=food_type,
        mode=payload.get("prediction_mode", "hybrid"),
    )
    prediction = {
        **prediction_suite["active_prediction"],
        "selected_mode": prediction_suite["selected_mode"],
        "expiry_prediction": prediction_suite["expiry_prediction"],
        "model_prediction": prediction_suite["model_prediction"],
        "model_available": prediction_suite["model_available"],
    }
    payload["food_item"] = food_item
    payload["food_type"] = food_type
    payload["image"] = image_path

    contract = build_freshness_contract(payload, prediction)
    if session.get("user_id"):
        contract["created_by"] = session["user_id"]

    contracts = read_json(INSURANCE_FILE)
    contracts.append(contract)
    write_json(INSURANCE_FILE, contracts)
    return jsonify({"success": True, "contract": contract, "prediction": prediction}), 201


@app.route("/api/freshness_insurance/settle", methods=["POST"])
def settle_freshness_insurance():
    """Settle a FIaaS contract against actual spoilage time."""
    try:
        from ai.market_models import settle_freshness_contract
    except ImportError:
        return jsonify({"error": "Market module not available"}), 500

    data = request.get_json(silent=True) or {}
    contract_id = data.get("contract_id")
    actual_hours = data.get("actual_spoilage_hours")
    contracts = read_json(INSURANCE_FILE)
    idx = next((i for i, c in enumerate(contracts) if c.get("id") == contract_id), None)
    if idx is None:
        return jsonify({"error": "Contract not found"}), 404
    settled = settle_freshness_contract(contracts[idx], actual_hours)
    contracts[idx] = settled
    write_json(INSURANCE_FILE, contracts)
    return jsonify({"success": True, "contract": settled})


@app.route("/api/pwx/futures", methods=["GET", "POST"])
def pwx_futures():
    """PWX: create or list predicted waste futures."""
    if request.method == "GET":
        futures = read_json(FUTURES_FILE)
        status = request.args.get("status")
        if status:
            futures = [f for f in futures if f.get("status") == status]
        return jsonify({"success": True, "futures": futures[::-1][:40], "total": len(futures)})

    try:
        from ai.market_models import build_waste_future
    except ImportError:
        return jsonify({"error": "Market module not available"}), 500

    payload = request.get_json(silent=True) or {}
    if not payload.get("menu_plan"):
        return jsonify({"error": "menu_plan is required"}), 400

    created = build_waste_future(payload)
    futures = read_json(FUTURES_FILE)
    futures.extend(created)
    write_json(FUTURES_FILE, futures)

    ai_logs = read_json(AI_LOGS_FILE)
    for future in created:
        ai_logs.append({
            "id": future["id"],
            "status": "predicted",
            "food_name": future["stream"]["stream_type"],
            "predicted_class": future["stream"]["freshness_category"],
            "confidence": future["stream"]["confidence"],
            "recommended_route": future["stream"]["route"],
            "location": future.get("restaurant_name"),
            "timestamp": datetime.now().isoformat()
        })
    write_json(AI_LOGS_FILE, ai_logs)

    return jsonify({"success": True, "futures": created, "created": len(created)}), 201


@app.route("/api/pwx/bid", methods=["POST"])
def pwx_bid():
    """Place a bid on a predicted waste token."""
    try:
        from ai.market_models import price_future_bid
    except ImportError:
        return jsonify({"error": "Market module not available"}), 500

    data = request.get_json(silent=True) or {}
    future_id = data.get("future_id")
    futures = read_json(FUTURES_FILE)
    idx = next((i for i, f in enumerate(futures) if f.get("id") == future_id), None)
    if idx is None:
        return jsonify({"error": "Future not found"}), 404

    bid = price_future_bid(futures[idx], data.get("price_per_kg"), data.get("quantity_kg"))
    bid["bidder_name"] = data.get("bidder_name", "Buyer")
    bid["bidder_type"] = data.get("bidder_type", "poultry_farm")
    futures[idx].setdefault("bids", []).append(bid)
    if bid["accepted"]:
        futures[idx]["status"] = "matched"
        futures[idx]["best_bid"] = bid
        futures[idx]["matched_at"] = datetime.now().isoformat()
    write_json(FUTURES_FILE, futures)
    return jsonify({"success": True, "bid": bid, "future": futures[idx]})


@app.route("/api/gcnc/credits", methods=["GET", "POST"])
def gcnc_credits():
    """List or mint geo-dynamic carbon-negative credits."""
    if request.method == "GET":
        credits = read_json(CARBON_FILE)
        status = request.args.get("status")
        if status:
            credits = [c for c in credits if c.get("status") == status]
        return jsonify({"success": True, "credits": credits[::-1][:50], "total": len(credits)})

    try:
        from ai.market_models import build_geo_credit
    except ImportError:
        return jsonify({"error": "Market module not available"}), 500

    data = request.get_json(silent=True) or {}
    donation = None
    if data.get("donation_id"):
        donations = read_json(DONATIONS_FILE)
        donation = next((d for d in donations if d.get("id") == data["donation_id"]), None)
        if not donation:
            return jsonify({"error": "Donation not found"}), 404
    else:
        donation = {
            "id": f"manual-{uuid.uuid4().hex[:10]}",
            "food_type": data.get("food_type", "cooked"),
            "quantity": data.get("quantity_kg", 25),
            "urgency": data.get("urgency", "high"),
            "recommended_route": data.get("route_type", "poultry"),
        }

    credit = build_geo_credit(
        donation,
        route_type=data.get("route_type"),
        distance_km=data.get("distance_km"),
        status=data.get("status", "verified"),
        buyer_name=data.get("buyer_name")
    )
    credits = read_json(CARBON_FILE)
    credits.append(credit)
    write_json(CARBON_FILE, credits)
    return jsonify({"success": True, "credit": credit}), 201


@app.route("/api/buy_credit", methods=["POST"])
def buy_credit():
    """Corporate purchase endpoint for G-CNC credits."""
    data = request.get_json(silent=True) or {}
    credit_id = data.get("credit_id")
    buyer_name = data.get("buyer_name", "Corporate buyer")
    credits = read_json(CARBON_FILE)
    idx = next((i for i, c in enumerate(credits) if c.get("id") == credit_id), None)
    if idx is None:
        return jsonify({"error": "Credit not found"}), 404
    if credits[idx].get("status") == "sold":
        return jsonify({"error": "Credit is already sold"}), 409
    credits[idx]["status"] = "sold"
    credits[idx]["buyer_name"] = buyer_name
    credits[idx]["purchased_at"] = datetime.now().isoformat()
    write_json(CARBON_FILE, credits)
    return jsonify({"success": True, "credit": credits[idx], "message": "Credit purchased"})

# ─────────────────────────────────────────────
# API Route 11: /api/notifications
# ─────────────────────────────────────────────

@app.route("/api/notifications", methods=["GET", "POST"])
@login_required
def notifications():
    """Get or mark notifications for current user."""
    user_id = session["user_id"]
    notifs = read_json(NOTIFS_FILE)
    user_notifs = [n for n in notifs if n.get("user_id") == user_id]
    user_notifs.sort(key=lambda n: n.get("timestamp", ""), reverse=True)

    if request.method == "POST":
        # Mark all as read
        for n in notifs:
            if n.get("user_id") == user_id:
                n["read"] = True
        write_json(NOTIFS_FILE, notifs)
        return jsonify({"success": True, "message": "All notifications marked as read"})

    return jsonify({
        "success": True,
        "notifications": user_notifs[:20],
        "unread_count": sum(1 for n in user_notifs if not n.get("read", False))
    })

# ─────────────────────────────────────────────
# API Route 11: /api/admin/users
# ─────────────────────────────────────────────

@app.route("/api/admin/users", methods=["GET"])
@admin_required
def admin_users():
    """Admin: Get all users."""
    users = read_json(USERS_FILE)
    safe_users = [{k: v for k, v in u.items() if k != "password"} for u in users]
    for u in safe_users:
        u["badges"] = assign_badges(u)
    return jsonify({"success": True, "users": safe_users, "total": len(safe_users)})

# ─────────────────────────────────────────────
# API Route 12: /api/admin/approve
# ─────────────────────────────────────────────

@app.route("/api/admin/approve", methods=["POST"])
@admin_required
def admin_approve():
    """Admin: Approve or reject a user."""
    data = request.get_json()
    user_id = data.get("user_id")
    approved = data.get("approved", True)

    users = read_json(USERS_FILE)
    for u in users:
        if u["id"] == user_id:
            u["approved"] = approved
            break
    write_json(USERS_FILE, users)

    return jsonify({"success": True, "message": f"User {'approved' if approved else 'rejected'}"})

# ─────────────────────────────────────────────
# API Route 13: /api/admin/delete
# ─────────────────────────────────────────────

@app.route("/api/admin/delete", methods=["POST"])
@admin_required
def admin_delete():
    """Admin: Delete a donation or user."""
    data = request.get_json()
    target_type = data.get("type")  # "donation" or "user"
    target_id   = data.get("id")

    if target_type == "donation":
        donations = read_json(DONATIONS_FILE)
        donations = [d for d in donations if d["id"] != target_id]
        write_json(DONATIONS_FILE, donations)
        return jsonify({"success": True, "message": "Donation deleted"})

    elif target_type == "user":
        users = read_json(USERS_FILE)
        users = [u for u in users if u["id"] != target_id]
        write_json(USERS_FILE, users)
        return jsonify({"success": True, "message": "User deleted"})

    return jsonify({"error": "Invalid type"}), 400

# ─────────────────────────────────────────────
# API Route 14: /api/user/profile
# ─────────────────────────────────────────────

@app.route("/api/user/profile", methods=["GET"])
@login_required
def user_profile():
    """Get current user's profile."""
    user = get_user_by_id(session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    donations = read_json(DONATIONS_FILE)
    user_donations = [d for d in donations if d["donor_id"] == user["id"]]

    safe_user = {k: v for k, v in user.items() if k != "password"}
    safe_user["badges"] = assign_badges(user)
    safe_user["donations"] = user_donations
    safe_user["co2_saved"] = sum(d.get("co2_saved", 0) for d in user_donations if d.get("completed"))

    return jsonify({"success": True, "user": safe_user})

# ─────────────────────────────────────────────
# API Route 15: /api/session
# ─────────────────────────────────────────────

@app.route("/api/session", methods=["GET"])
def get_session():
    """Check current session status."""
    if "user_id" in session:
        user = get_user_by_id(session["user_id"])
        if user:
            safe_user = {k: v for k, v in user.items() if k != "password"}
            safe_user["badges"] = assign_badges(user)
            return jsonify({"logged_in": True, "user": safe_user})
    return jsonify({"logged_in": False})

# ─────────────────────────────────────────────
# WebSocket Real-Time Notifications
# ─────────────────────────────────────────────

@socketio.on('connect')
def handle_connect():
    """Client connected to WebSocket."""
    user_id = session.get('user_id')
    if user_id:
        join_room(f"user_{user_id}")
        emit('connected', {'status': 'ok', 'user_id': user_id})

@socketio.on('join_notifications')
def handle_join(data):
    """Join user-specific notification room."""
    user_id = data.get('user_id') or session.get('user_id')
    if user_id:
        join_room(f"user_{user_id}")
        emit('joined', {'room': f"user_{user_id}"})

def push_notification(user_id, message, notif_type="info"):
    """Push real-time notification to specific user."""
    try:
        socketio.emit('notification', {
            'message':   message,
            'type':      notif_type,
            'timestamp': datetime.now().isoformat()
        }, room=f"user_{user_id}")
    except Exception as e:
        print(f"⚠️ Push notification failed: {e}")

def push_donation_update(donation_id, status, message):
    """Broadcast donation status update to all connected clients."""
    try:
        socketio.emit('donation_update', {
            'donation_id': donation_id,
            'status':      status,
            'message':     message,
            'timestamp':   datetime.now().isoformat()
        })
    except Exception as e:
        print(f"⚠️ Broadcast failed: {e}")
# ─────────────────────────────────────────────
# Static file serving
# ─────────────────────────────────────────────

@app.route("/static/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/profile")
def profile_page():
    return render_template("profile.html")

# ─────────────────────────────────────────────
# Error Handlers
# ─────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

# ─────────────────────────────────────────────
# Run with SocketIO
# ─────────────────────────────────────────────

if __name__ == "__main__":
    socketio.run(app, debug=True, port=8080, host="0.0.0.0")
