# 🧠 FOODSAVE AI — COMPLETE PROJECT CONTEXT DOCUMENT

> **Version**: 1.0.0  
> **Date Generated**: 2026-04-09  
> **Purpose**: Self-contained project context for ANY new AI or developer to continue this project WITHOUT prior conversation history.  
> **Project Root**: `/Users/guneetbaweja/Desktop/foodwaste-ai copy 4/`

---

## 1. 🧠 PROJECT OVERVIEW (DETAILED)

### Project Name
**FoodSave AI** — India's First AI-Powered Food Rescue Network

### Problem Statement
India wastes approximately **68 million tonnes of food annually** — enough to feed 100 million people. Most food waste ends up in landfills, producing methane (a greenhouse gas 80x worse than CO₂). Meanwhile, millions go hungry daily. There is no intelligent, automated system that can:

1. **Classify food freshness** from an image (Is it edible? Semi-fresh? Rotten?)
2. **Route food to the optimal destination** (NGO for human consumption, poultry farm for animal feed, biogas plant for energy, compost for soil)
3. **Connect donors (restaurants, households, events) to recipients (NGOs, volunteers)** in real-time with distance-optimized matching
4. **Track environmental impact** (CO₂ saved, water saved, meals donated)

### Real-World Use Case
A restaurant has 10 kg of leftover vegetable curry. They upload a photo to FoodSave AI. The system:
1. AI classifies it as "cooked, freshness score 72/100, urgency: medium"
2. Matching engine finds the nearest NGO (Hope NGO, 3.2 km away) with capacity
3. A volunteer is dispatched with optimized routing
4. Food reaches people in need within 60 minutes
5. The restaurant earns 100 points, the volunteer earns 150 points, and 12.5 kg CO₂ is saved

### Target Users
| User Type | Description | Features Available |
|-----------|-------------|-------------------|
| **Restaurants** | Commercial kitchens with surplus food | Donate food, view impact dashboard, earn badges |
| **Households** | Individuals with excess food | List food, track CO₂ savings |
| **NGOs** | Food distribution organizations | Accept donations, view available food, manage pickups |
| **Volunteers** | People willing to pick up and deliver food | Accept pickup tasks, earn points, leaderboard |
| **Poultry Farms** | Animal feed recipients | Receive semi-fresh food for animal consumption |
| **Biogas Plants** | Energy generation from organic waste | Receive expired food for energy production |
| **Admin** | Platform administrator | Approve users, manage donations, system oversight |

### End-to-End Workflow
```
USER UPLOADS FOOD IMAGE
         ↓
┌─────────────────────────────┐
│ AI CLASSIFICATION PIPELINE  │
│ (EfficientNet + Swin + ViT  │
│  + Ensemble → 4 model vote) │
│ Output: freshness class,    │
│ confidence score, urgency   │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│ DECISION ENGINE             │
│ Maps class → destination:   │
│  fresh → NGO                │
│  semi_fresh → Poultry Farm  │
│  rotten → Biogas Plant      │
│  cooked → Compost           │
│  packaged → NGO             │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│ MATCHING + ROUTING ENGINE   │
│ Haversine distance calc     │
│ NGO capacity scoring        │
│ Urgency-weighted ranking    │
│ Biogas fallback for expired │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│ NOTIFICATION + GAMIFICATION │
│ Alert NGOs/volunteers       │
│ Award points to donor       │
│ Track CO₂/water/trees saved │
│ Assign badges               │
└─────────────────────────────┘
```

---

## 2. 🏗️ FULL SYSTEM ARCHITECTURE

```
┌────────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                              │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │ Landing Page  │  │ Dashboard    │  │ Cinematic 3D UI          │ │
│  │ (landing.html)│  │ Donate Page  │  │ (Three.js + GLSL + 2D)  │ │
│  │ Three.js BG   │  │ NGO Portal   │  │ Globe + Particles +     │ │
│  │ GLSL Shaders  │  │ Profile Page │  │ AI Brain Canvas         │ │
│  │ Custom Cursor │  │ Login/Signup │  │ India Network Map        │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────────┘ │
│         └─────────────────┴──────────────────────┘                 │
│                           │ HTTP/REST                              │
└───────────────────────────┼────────────────────────────────────────┘
                            │
┌───────────────────────────┼────────────────────────────────────────┐
│                    FLASK API LAYER (app.py)                         │
│                                                                    │
│  15+ REST endpoints:                                               │
│  /api/signup, /api/login, /api/logout, /api/session                │
│  /api/upload_food, /api/get_donations, /api/accept_donation        │
│  /api/complete_donation, /api/match_donation                       │
│  /api/leaderboard, /api/stats, /api/notifications                  │
│  /api/predict, /api/locations, /api/user/profile                   │
│  /api/admin/users, /api/admin/approve, /api/admin/delete           │
│                                                                    │
│  Session management (Flask sessions + localStorage fallback)       │
│  File upload handling (16 MB limit), CORS enabled                  │
│  Role-based access (login_required, admin_required decorators)     │
└───────────────┬──────────────────────┬─────────────────────────────┘
                │                      │
┌───────────────┼──────┐  ┌────────────┼─────────────────────────────┐
│   AI/ML LAYER        │  │        DATA LAYER                        │
│                      │  │                                          │
│ Multi-Model Classif. │  │ JSON File Database                       │
│ ├── EfficientNet V2  │  │ ├── data/users.json                     │
│ ├── Swin Transformer │  │ ├── data/donations.json                 │
│ ├── ViT-B/16         │  │ ├── data/notifications.json             │
│ └── Ensemble Fusion  │  │ ├── data/locations.json                 │
│                      │  │ └── data/ngos_raw.json (600+ NGOs)      │
│ Decision Engine      │  │                                          │
│ Matching Engine      │  │ Model Checkpoints                       │
│ Routing Engine       │  │ ├── ai/models/efficientnet_best.pth     │
│ YOLO Detector (plan) │  │ ├── ai/models/efficientnet_epoch_*.pth  │
│                      │  │ └── ai/models/class_map.json            │
└──────────────────────┘  └──────────────────────────────────────────┘
```

### Why Each Component Exists

| Component | Purpose |
|-----------|---------|
| **EfficientNet V2-S** | Fast inference for edge/mobile (6.2M params) |
| **Swin Transformer** | Superior accuracy on textures (28M params) |
| **ViT-B/16** | State-of-the-art attention-based (86M params) |
| **Ensemble Fusion** | Combines all 3 via learned fusion → highest accuracy |
| **Decision Engine** | Maps freshness → routing destination |
| **Matching Engine** | Ranks NGOs by distance + capacity + urgency |
| **Routing Engine** | Finds nearest volunteer, builds route steps |
| **YOLO Detector** | Bounding-box food detection (planned) |
| **Flask API** | REST backend connecting frontend → AI → data |
| **Three.js Landing** | Cinematic 3D marketing page for engagement |
| **JSON Database** | Simple flat-file storage, no DB dependency |

---

## 3. 🤖 AI MODEL DETAILS (VERY DEEP)

### MODEL 1 — EfficientNet V2-S (Classifier)

- **Architecture**: `torchvision.models.efficientnet_v2_s` with custom classifier head
- **Parameters**: ~6.2 million
- **Custom Head**:
  ```
  Dropout(0.5) → Linear(in, 768) → BN(768) → ReLU
  → Dropout(0.4) → Linear(768, 256) → BN(256) → ReLU
  → Dropout(0.3) → Linear(256, 5)
  ```
- **Input**: 224×224 RGB, normalized `[0.485, 0.456, 0.406]` / `[0.229, 0.224, 0.225]`
- **Output**: 5-class logits → `[fresh, semi_fresh, rotten, cooked, packaged]`
- **Training**: 200 epochs, AdamW (lr=3e-4, wd=1e-4), CosineAnnealingWarmRestarts (T_0=10, T_mult=2), label_smoothing=0.15, gradient clipping=1.0
- **Augmentation**: RandomResizedCrop(scale 0.7-1.0), HFlip(0.5), VFlip(0.3), Rotation(30°), ColorJitter(0.4, 0.4, 0.4, 0.15), Grayscale(0.1), GaussianBlur(0.3), RandomAffine(0.3), RandomErasing(0.2)
- **Status**: ✅ **200 EPOCHS FULLY TRAINED** — 200 checkpoint files exist (~257 MB each)
- **Expected Accuracy**: 92-95%

### MODEL 2 — Swin Transformer (Classifier)

- **Architecture**: `torchvision.models.swin_t` (Swin-Tiny)
- **Parameters**: ~28 million
- **Custom Head**: Dropout(0.5) → Linear → BN → ReLU → Dropout(0.3) → Linear → BN → ReLU → Linear(5)
- **Same training config** as EfficientNet
- **Status**: Architecture defined, training may be incomplete (no `swin_best.pth` visible)
- **Expected Accuracy**: 94-97%

### MODEL 3 — ViT-B/16 (Classifier)

- **Architecture**: `torchvision.models.vit_b_16`
- **Parameters**: ~86 million
- **Custom Head**: Dropout(0.4) → Linear(in, 512) → ReLU → Dropout(0.3) → Linear(512, 5)
- **Expected Accuracy**: 96-98%

### MODEL 4 — Ensemble (Fusion Model)

- **Architecture**: EfficientNet + Swin + ViT → concatenate outputs → fusion MLP
- **Fusion**: Linear(15, 512) → ReLU → Dropout(0.4) → Linear(512, 256) → ReLU → Dropout(0.2) → Linear(256, 5)
- **Training**: 100 epochs (reduced since sub-models pre-trained)
- **Expected Accuracy**: 97-99% (highest)

### MODEL 5 — YOLOv8s (Object Detector)

- **Purpose**: Detect and localize food items with bounding boxes
- **Classes**: 5 — same as classifier
- **Config**: 100 epochs, imgsz=640, batch=16, patience=20
- **File**: `ai/train_yolo.py`
- **Status**: ⚠️ Script exists but **NOT YET TRAINED**

### MODEL 6 — TensorFlow Freshness (Legacy)

- **File**: `ai/predict.py` — tries to load `ai/freshness_model.h5`
- **Classes**: `['critical', 'high', 'medium', 'safe']`
- **Status**: ⚠️ Model file does NOT exist — falls back to rule-based prediction

### DECISION ENGINE — Routing Rules

| Freshness Class | Confidence Threshold | Destination | Action |
|----------------|---------------------|-------------|--------|
| `fresh` | ≥ 0.80 | NGO | ✅ DONATE for distribution |
| `semi_fresh` | ≥ 0.70 | Poultry Farm | ⚠️ Animal feed |
| `rotten` | ≥ 0.60 | Biogas Plant | ♻️ Energy generation |
| `cooked` | ≥ 0.70 | Compost | 🔄 Soil enrichment |
| `packaged` | ≥ 0.80 | NGO | ✅ Donate if unopened |
| Any (below threshold) | < threshold | Compost | Safe fallback |

### MATCHING ENGINE (`ai/matching.py`)

```
final_score = (dist_score × 0.5 + cap_score × 0.3) × (1 + urgency_mult × 0.2)

dist_score = max(0, 100 - distance_km × 2)
cap_score = min(100, (ngo_capacity / quantity) × 20)
urgency_mult = {critical:1.0, high:0.75, medium:0.5, low:0.25, safe:0.1, expired:0}
```

Biogas fallback: If expired or no NGOs match → nearest active biogas plant via Haversine.

---

## 4. 📂 COMPLETE FOLDER STRUCTURE

```
foodwaste-ai/
├── app.py                          # Main Flask backend (1149 lines, 44KB)
├── config.py                       # Configuration constants (79 lines)
├── requirements.txt                # Python dependencies (30 lines)
├── run.sh                          # Automated setup pipeline (104 lines)
├── verify.py                       # System verification (320 lines)
├── monitor_training.sh             # Training monitor script
│
├── ai/                             # 🤖 AI/ML MODULE
│   ├── setup_dataset.py            # Dataset generation + augmentation (208 lines)
│   ├── train_classifier.py         # Multi-model training engine (349 lines)
│   ├── train_yolo.py               # YOLOv8 food detector (104 lines)
│   ├── inference_pipeline.py       # Inference + decision engine (311 lines)
│   ├── predict.py                  # TF freshness predictor / fallback (89 lines)
│   ├── matching.py                 # Donation-to-NGO matching (110 lines)
│   ├── routing.py                  # Volunteer routing engine (115 lines)
│   ├── train_model.py              # Simplified training wrapper
│   ├── resume_training.py          # Resume from checkpoint
│   ├── resume_from_91.py           # Resume from epoch 91
│   ├── organize_dataset.py         # Dataset organization
│   ├── check_status.py             # Training status checker
│   ├── flask_server.py             # Standalone AI Flask API (180 lines)
│   ├── dataset/                    # Training dataset (auto-generated)
│   │   ├── train/{fresh,semi_fresh,rotten,cooked,packaged}/  # 200 imgs/class
│   │   ├── val/{...}/              # 50 imgs/class
│   │   └── test/{...}/             # 30 imgs/class
│   ├── models/                     # Trained checkpoints
│   │   ├── class_map.json          # Class ↔ index mapping
│   │   ├── efficientnet_best.pth   # Best model (~257 MB)
│   │   └── efficientnet_epoch_001.pth ... _200.pth  # All 200 epochs
│   ├── dataset_raw/                # Raw data
│   └── inference/                  # (empty)
│
├── templates/                      # Flask HTML Templates
│   ├── landing.html                # ⭐ Cinematic 3D page (901 lines, 55KB)
│   ├── index.html                  # Homepage (18KB)
│   ├── dashboard.html              # Dashboard (12KB)
│   ├── donate.html                 # Donation form (12KB)
│   ├── ngo.html                    # NGO portal (7KB)
│   ├── login.html                  # Login (4KB)
│   ├── signup.html                 # Registration (6KB)
│   └── profile.html                # User profile (23KB)
│
├── static/                         # Static Assets
│   ├── css/
│   │   ├── style.css               # Main design system (72KB)
│   │   └── landing.css             # Landing page styles (23KB)
│   ├── js/
│   │   ├── main.js                 # App logic — auth, API, pages (1630 lines, 62KB)
│   │   ├── threeScene.js           # Three.js 3D home scene (636 lines)
│   │   ├── animations.js           # UI animations module (295 lines)
│   │   ├── landing.js              # Landing page JS
│   │   └── scenes/particles.js     # Particle system (5KB)
│   ├── sections/                   # AI-generated images (6 files, ~50 MB total)
│   ├── images/
│   └── uploads/                    # User-uploaded food images
│
├── ui/                             # Standalone 3D UI (alternative)
│   ├── index.html                  # Standalone inference UI (12KB)
│   └── js/scene.js                 # 3D scene (13KB)
│
├── ai-food-waste-3d/               # Incomplete Vite+TS 3D app (can be ignored)
│   ├── package.json, vite.config.ts, tsconfig.json
│   └── src/{App.tsx, components/, scenes/, shaders/, ...}
│
├── scripts/                        # Utility scripts
│   ├── convert_dataset.py
│   └── organize_dataset.py
│
├── data/                           # Application data (JSON)
│   ├── users.json                  # User accounts (5 sample users)
│   ├── donations.json              # Food donations (4 samples)
│   ├── notifications.json          # Notifications
│   ├── ngos_raw.json               # NGO database (428KB, 600+ NGOs!)
│   └── location.json               # Map location data
│
├── models/                         # (empty — models in ai/models/)
├── src/                            # (empty)
│
├── README.md, QUICKSTART.md, SYSTEM_SUMMARY.md, INDEX.md
├── FINAL_SUMMARY.txt, RESUME_GUIDE.txt, RESUME_TRAINING.md
└── PROJECT_CONTEXT_DOCUMENT.md     # THIS FILE
```

---

## 5. 💾 IMPORTANT FILES SUMMARY

### `app.py` — Main Flask Backend (1149 lines, 44KB)
The monolithic Flask application serving as the entire backend:
- **Data layer**: JSON file read/write helpers, SHA-256 password hashing
- **Auth**: Session-based with `login_required` and `admin_required` decorators
- **Page routes** (8): `/`, `/dashboard`, `/donate`, `/ngo`, `/login`, `/signup`, `/admin`, `/landing`, `/profile`
- **API endpoints** (15+): signup, login, logout, session, upload_food, get_donations, accept_donation, complete_donation, match_donation, predict, leaderboard, stats, notifications, locations, profile, admin/users, admin/approve, admin/delete
- **Business logic**: Freshness prediction (rule-based fallback using expiry hours), CO₂ calculation (food-type-specific emission factors from FAO data), gamification (points, 6 badge types, leaderboard), notification system, biogas auto-assign for expired food
- **Runs on**: `http://0.0.0.0:8080` (debug mode)
- **Sample data**: Auto-creates 5 users and 4 donations on first run via `init_sample_data()`

### `ai/train_classifier.py` — Training Engine (349 lines)
- 4 model architectures as `nn.Module` subclasses (EfficientNet, Swin, ViT, Ensemble)
- Training loop: mixed precision (CUDA only), gradient clipping, cosine annealing warm restarts, early stopping (patience=30), label smoothing (0.15)
- **Bulletproof checkpointing**: 3 saves per epoch — latest (always overwrite), per-epoch backup, best model
- Resume from checkpoint via `--resume` CLI flag
- WeightedRandomSampler for class imbalance handling
- Device auto-detection: MPS → CUDA → CPU

### `ai/inference_pipeline.py` — Decision Engine (311 lines)
`FoodWasteDecisionEngine` class:
1. Loads all 4 trained models
2. Averages softmax outputs (ensemble voting)
3. Maps freshness → destination via confidence thresholds
4. Calculates Haversine distance to destinations
5. Generates human-readable action text
- **Known Bug**: `process_food_image()` references `thresholds` variable defined only in `decide_destination()` — will crash at runtime

### `ai/matching.py` — NGO Matching (110 lines)
- `match_donation_to_ngo()`: Composite score = distance(50%) + capacity(30%) × urgency multiplier(20%). Returns top 3 NGO matches.
- `assign_to_biogas()`: Fallback to nearest biogas plant for expired food
- Haversine formula for geographic distance

### `ai/routing.py` — Routing Engine (115 lines)
- Finds nearest active volunteer to donation
- Ranks NGOs by distance, builds route steps
- Loads NGOs from JSON or CSV files
- Returns: volunteer, pickup, NGO options, total distance, route steps

### `ai/predict.py` — Freshness Predictor (89 lines)
- Tries to load TensorFlow model `ai/freshness_model.h5` (doesn't exist)
- Falls back to rule-based: hours remaining → urgency mapping
- Designed as drop-in replacement for `predict_freshness()` in app.py
- Merges AI confidence with rule-based when AI confidence > 70%

### `templates/landing.html` — Cinematic Landing (901 lines, 55KB)
Self-contained page with ALL CSS and JS inline:
- **Three.js 3D**: Rotating globe with GLSL shaders (procedural continents, India highlight glow, fresnel rim), atmosphere, 3 orbit rings, 3200 particles, 600 nebula particles, 10 orbiting food meshes, 6 data stream bezier curves, animated grid floor
- **AI Brain Canvas (2D)**: Neural network with 22 nodes across 4 layers, animated data particles flowing through connections, output labels (Edible/NGO/Poultry/Biogas)
- **India Network Map (2D)**: 10 cities, flow particles on bezier curves, country outline
- **Custom cursor**: Dot + ring, hover state changes
- **Loading screen**: Progress bar with status messages
- **Sections**: Hero, AI Engine, How It Works (4 steps), Network, Impact (4 counters), CTA, Footer
- **Responsive**: Breakpoints at 1100px and 680px

### `static/js/main.js` — Application JavaScript (1630 lines, 62KB)
IIFE module handling all app-level functionality:
- Toast notification system, API fetch helper
- Session management (server sessions + localStorage fallback)
- Page handlers: Login, Signup, Donate (image upload, drag & drop, geolocation, AI prediction display), NGO Portal (filter, sort, accept, complete, detail modal), Dashboard, Profile
- Donation card rendering with urgency badges
- Exposed via `window.ngoApp`

### `static/js/threeScene.js` — 3D Home Scene (636 lines)
Separate Three.js scene for the homepage (NOT landing.html):
- Globe with noise-based shader, atmosphere, 2 orbit rings
- 14 food mesh items (apple, bread, carrot, pea, grain)
- 1800 particle system, 6 data stream lines
- Raycasting + mouse hover (emissive glow), click (scale pop + "+100 pts!")
- Smooth camera follow + scroll parallax

### `static/js/animations.js` — UI Animations (295 lines)
Reusable utilities: loader, theme toggle, navbar scroll effect, scroll reveal (IntersectionObserver), counter animations, testimonial carousel, map ticker, parallax hero, AI meter animations, mobile menu, button ripple effects

### `config.py` — Configuration (79 lines)
Central constants: dataset/model dirs, image size (224), batch size (32), epochs (200), LR (3e-4), 5 classes, API config, 4 routing destinations with GPS coords, confidence thresholds per class, routing rules, feature flags

---

## 6. ⚙️ TECH STACK (EXPLAINED)

### Backend
| Technology | Version | Why Used |
|-----------|---------|---------|
| **Python** | 3.9+ | Rich ML ecosystem |
| **Flask** | ≥ 2.3 | Lightweight web framework — minimal boilerplate |
| **PyTorch** | ≥ 2.0 | Dynamic graphs, Apple MPS support, better debugging than TF |
| **TorchVision** | ≥ 0.15 | Pre-trained EfficientNet/Swin/ViT and transforms |
| **scikit-learn** | ≥ 1.2 | Metrics (accuracy, confusion matrix) |
| **Pillow** | ≥ 9.4 | Image processing for dataset gen and preprocessing |
| **NumPy** | ≥ 1.23 | Numerical operations, Haversine math |
| **OR-Tools** | ≥ 9.6 (optional) | Planned for advanced vehicle routing |
| **Gunicorn** | ≥ 20.1 | Production WSGI server |

### Frontend
| Technology | Why Used |
|-----------|---------|
| **Three.js r128** | GPU-accelerated 3D rendering (globe, particles, food items). CDN loaded. |
| **Custom GLSL Shaders** | Procedural Earth, atmosphere, particles, grid, nebula. Sci-fi aesthetic. |
| **2D Canvas API** | AI brain neural network + India map visualizations (need text labels). |
| **Vanilla CSS3** | Custom design system. Glassmorphism (backdrop-filter), gradients, animations. No Tailwind/Bootstrap. |
| **Vanilla JavaScript** | All logic in plain JS IIFE modules. Zero build step, instant load. |
| **Google Fonts** | Syne (display), DM Sans (body), JetBrains Mono (metrics). |

### Data Storage
- **JSON files** in `/data/` — simple, no-dependency. Suitable for prototype. Needs PostgreSQL for production.

---

## 7. 🔄 CURRENT PROJECT STATE

### ✅ COMPLETED
1. **EfficientNet Training**: 200 epochs fully trained, all 200 checkpoint files saved (~257 MB each)
2. **Flask Backend**: All 15+ API endpoints implemented and working
3. **Cinematic Landing Page**: Complete Three.js 3D scene with GLSL shaders, AI brain canvas, India map, custom cursor, scroll animations
4. **Application UI Pages**: Homepage, dashboard, donate, NGO portal, login, signup, profile — all functional
5. **Matching Engine**: Distance + capacity + urgency scoring, biogas fallback
6. **Gamification**: Points, 6 badge types, leaderboard
7. **Documentation**: 7 documentation files

### ⚠️ PARTIALLY DONE
1. **Swin + ViT + Ensemble Training**: Architectures defined but no checkpoint files visible (only EfficientNet has them)
2. **Inference Pipeline Bug**: `process_food_image()` references undefined `thresholds` variable — crashes at runtime
3. **YOLO Detector**: Script exists but not trained
4. **TF Freshness Model**: `ai/freshness_model.h5` missing — falls back to rule-based (works fine)
5. **Vite+TS 3D App** (`ai-food-waste-3d/`): Scaffolded but not functional — abandoned approach

### ❌ PENDING
1. Real food images (currently synthetic)
2. Docker containerization (no Dockerfile)
3. Database migration (JSON → PostgreSQL)
4. WebSocket real-time updates
5. ONNX model export
6. OR-Tools vehicle routing
7. Unit tests
8. Production security (proper secrets, bcrypt, CSRF, rate limiting)

---

## 8. 🎯 NEXT STEPS (PRIORITIZED)

### Priority 1: Critical Fixes
1. **Fix `inference_pipeline.py` bug**: Move `thresholds` dict from `decide_destination()` to class attribute or pass as parameter in `process_food_image()`
2. **Train remaining models**: Run `python3 ai/train_classifier.py` for Swin, ViT, Ensemble
3. **Fix `predict.py` import conflict** in `app.py` lines 22-27 vs line 125

### Priority 2: Feature Completion
4. Train YOLO detector (`python3 ai/train_yolo.py`)
5. Integrate YOLO into inference pipeline
6. Replace synthetic images with real food photos (Food-101 dataset or custom)
7. Create `Dockerfile` and `docker-compose.yml`
8. Add WebSocket (Flask-SocketIO) for real-time notifications

### Priority 3: Production Hardening
9. Migrate JSON → PostgreSQL
10. Add API rate limiting
11. Implement HTTPS, proper secrets (`app.secret_key`), bcrypt passwords
12. Add unit tests, comprehensive logging
13. Environment variables for configuration

### Priority 4: Enhancement
14. OR-Tools routing (multi-stop VRP)
15. Progressive Web App (service worker)
16. Email notifications
17. Mobile app (React Native / Flutter)

---

## 9. ⚠️ RULES FOR FUTURE AI

1. **DO NOT rewrite from scratch.** Architecture is deliberate and modular.
2. **DO NOT change model architectures** without updating BOTH `train_classifier.py` AND `inference_pipeline.py`.
3. **DO NOT break Flask API endpoints.** Frontend depends on exact names/response formats. Add new endpoints, don't rename.
4. **DO NOT remove rule-based fallback** in freshness prediction — it's the safety net.
5. **MAINTAIN the 5 classes**: `["fresh", "semi_fresh", "rotten", "cooked", "packaged"]`. Changing requires updating 6+ files.
6. **MAINTAIN gamification** (points, badges, leaderboard) — integral to UX.
7. **MAINTAIN biogas fallback** — guarantees zero food to landfill.
8. **DO NOT delete checkpoint files** — represent weeks of GPU time.
9. **Keep templates server-rendered** (Jinja2). No SPA conversion unless asked.
10. **CSS is vanilla** — no Tailwind, no Bootstrap.
11. **JS is vanilla** — no React, no Vue, no jQuery.
12. **Landing page is self-contained** — inline CSS/JS is intentional for zero-dependency deployment.

---

## 10. 🔌 HOW TO CONTINUE

### Read These Files First (in order)
1. `config.py` — System constants
2. `app.py` — All API endpoints and data flow
3. `ai/train_classifier.py` — Model architectures
4. `ai/inference_pipeline.py` — Prediction + decision logic
5. `ai/matching.py` + `ai/routing.py` — NGO matching and routing
6. `templates/landing.html` — 3D cinematic page
7. `static/js/main.js` — Frontend application logic

### How to Run
```bash
# Install deps
pip3 install -r requirements.txt

# Generate dataset
python3 ai/setup_dataset.py

# Train models (hours, GPU recommended)
python3 ai/train_classifier.py
# Resume: python3 ai/train_classifier.py --resume ai/models/efficientnet_checkpoint_latest.pth

# Start server
python3 app.py   # → http://localhost:8080

# Demo accounts:
# admin@foodwaste.ai / admin123
# restaurant@foodwaste.ai / pass123
# ngo@foodwaste.ai / pass123
# volunteer@foodwaste.ai / pass123
# donor@foodwaste.ai / pass123

# Cinematic landing: http://localhost:8080/landing

# OR automated: chmod +x run.sh && ./run.sh
```

### Where to Make Changes
| Goal | Files |
|------|-------|
| Add food class | `config.py`, `setup_dataset.py`, `train_classifier.py`, `inference_pipeline.py`, `class_map.json` |
| Add API endpoint | `app.py` |
| Change routing | `ai/matching.py`, `ai/routing.py`, `config.py` |
| Edit landing 3D | `templates/landing.html` (JS inline at bottom) |
| Edit homepage 3D | `static/js/threeScene.js` |
| Change styling | `static/css/style.css` (app) or `landing.css` |
| Add page | Template in `templates/`, route in `app.py`, JS in `main.js` |
| Change architecture | `train_classifier.py` AND `inference_pipeline.py` (MUST match) |
| Change gamification | `app.py` → `award_points()`, `assign_badges()` |
| Change thresholds | `config.py` → `CONFIDENCE_THRESHOLDS` |

### Key Technical Notes
- **Device auto-select**: MPS (Apple Silicon) → CUDA → CPU. Force CPU in `config.py`
- **Each checkpoint is ~257 MB**. 200 epochs = ~51 GB for EfficientNet alone. Prune if needed: keep only `*_best.pth` and `*_latest.pth`
- **Dataset is synthetic**. Replace `ai/dataset/` with real images for production
- **Three.js CDN is r128** (older version). Test shader compat if updating
- **`ai-food-waste-3d/`** is abandoned — safe to ignore/delete
- **`app.secret_key`** is hardcoded — MUST change in production
- **Passwords**: SHA-256 without salt — upgrade to bcrypt for production

---

## 🔐 Security Notes for Production
- Change `app.secret_key = "food_waste_secret_key_2025"` to a random secret
- Upgrade SHA-256 passwords to bcrypt
- Add CSRF protection
- Add API rate limiting
- Add input sanitization (XSS risk in donation descriptions)
- Use HTTPS in production

---

> **This document was generated from a complete, line-by-line analysis of every file in the project. It is the ONLY reference needed for any AI or developer to understand, run, debug, and extend FoodSave AI.**
