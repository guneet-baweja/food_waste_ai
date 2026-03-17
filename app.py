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
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, request, jsonify, session,
    render_template, redirect, url_for, send_from_directory
)
from werkzeug.utils import secure_filename

# ─────────────────────────────────────────────
# App Configuration
# ─────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "food_waste_secret_key_2025"
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

# ─────────────────────────────────────────────
# JSON Database Helpers
# ─────────────────────────────────────────────

def read_json(filepath):
    """Read JSON file safely, return empty list if not found."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def write_json(filepath, data):
    """Write data to JSON file."""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)

def read_json_dict(filepath):
    """Read JSON file that contains a dict."""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

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

def predict_freshness(expiry_time_str):
    """
    Simulate AI freshness prediction based on expiry time.
    Returns score 0-100 and urgency level.
    """
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

def calculate_co2_saved(quantity_kg):
    """Calculate approximate CO₂ saved by donating food (kg CO₂ per kg food)."""
    co2_per_kg = 2.5  # average kg CO₂ per kg food waste
    return round(quantity_kg * co2_per_kg, 2)

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

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/signup")
def signup_page():
    return render_template("signup.html")

@app.route("/admin")
def admin_page():
    return render_template("dashboard.html")

# ─────────────────────────────────────────────
# API Route 1: /api/signup
# ─────────────────────────────────────────────

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
    user_id = session["user_id"]

    # Get form fields
    food_name    = request.form.get("food_name", "").strip()
    food_type    = request.form.get("food_type", "other")
    quantity     = request.form.get("quantity", "1")
    quantity_unit= request.form.get("quantity_unit", "kg")
    expiry_time  = request.form.get("expiry_time", "")
    location     = request.form.get("location", "")
    description  = request.form.get("description", "")
    lat          = request.form.get("lat", "40.7128")
    lng          = request.form.get("lng", "-74.0060")

    if not food_name or not expiry_time:
        return jsonify({"error": "Food name and expiry time are required"}), 400

    # Handle image upload
    image_path = ""
    if "image" in request.files:
        file = request.files["image"]
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)
            image_path = f"/static/uploads/{filename}"

    # AI freshness prediction
    ai_result = predict_freshness(expiry_time)

    # Get donor info
    user = get_user_by_id(user_id)
    donor_name = user["name"] if user else "Unknown"

    # CO2 calculation
    try:
        qty_num = float(quantity)
    except ValueError:
        qty_num = 1.0

    co2 = calculate_co2_saved(qty_num)

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
        "coordinates": {"lat": float(lat), "lng": float(lng)},
        "description": description,
        "image": image_path,
        "freshness_score": ai_result["freshness_score"],
        "urgency": ai_result["urgency"],
        "hours_remaining": ai_result["hours_remaining"],
        "status": "available",
        "accepted_by": None,
        "completed": False,
        "co2_saved": co2,
        "created_at": datetime.now().isoformat()
    }

    donations = read_json(DONATIONS_FILE)
    donations.append(donation)
    write_json(DONATIONS_FILE, donations)

    # Award points to donor
    award_points(user_id, 100, "for creating a food donation!")

    # Notify NGOs
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
        "ai_prediction": ai_result,
        "message": "Donation created successfully! +100 points earned."
    }), 201

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
    limit    = int(request.args.get("limit", 50))

    filtered = donations

    if status:
        filtered = [d for d in filtered if d.get("status") == status]
    if urgency:
        filtered = [d for d in filtered if d.get("urgency") == urgency]
    if food_type:
        filtered = [d for d in filtered if d.get("food_type") == food_type]
    if donor_id:
        filtered = [d for d in filtered if d.get("donor_id") == donor_id]

    # Sort by urgency priority then time
    urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "safe": 4, "expired": 5}
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
        "co2_saved": donation.get("co2_saved", 0)
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
# API Route 9: /api/stats
# ─────────────────────────────────────────────

@app.route("/api/stats", methods=["GET"])
def stats():
    """Get platform-wide statistics."""
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
            "total_donations": len(donations),
            "completed_donations": len(completed),
            "available_donations": len([d for d in donations if d.get("status") == "available"]),
            "total_co2_saved": round(total_co2, 2),
            "total_food_kg": round(total_food, 2),
            "total_meals_donated": total_meals,
            "total_users": len(users),
            "donors": len(donors),
            "restaurants": len(restaurants),
            "ngos": len(ngos),
            "volunteers": len(volunteers),
            "cities_reached": 12,
            "trees_equivalent": round(total_co2 / 21, 1)
        }
    })

# ─────────────────────────────────────────────
# API Route 10: /api/notifications
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
# Run
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=8080, host="0.0.0.0")