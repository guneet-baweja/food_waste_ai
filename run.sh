#!/bin/bash

# FoodSave AI — Complete Automated Setup & Training
# Runs all steps: Dataset → Training → API → UI

set -e

echo "════════════════════════════════════════════════════════════════════"
echo "  🚀 FoodSave AI — Automated Setup & Training Pipeline"
echo "════════════════════════════════════════════════════════════════════"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# STEP 1: Setup Dataset
echo -e "\n${BLUE}━━━ STEP 1: DATASET PREPARATION ━━━${NC}"
echo "📁 Setting up dataset structure and generating images..."
python3 ai/setup_dataset.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dataset ready!${NC}"
else
    echo -e "${YELLOW}⚠️  Dataset setup had issues, but continuing...${NC}"
fi

# STEP 2: Train Models
echo -e "\n${BLUE}━━━ STEP 2: MULTI-MODEL TRAINING ━━━${NC}"
echo "🧠 Training 4 advanced models (EfficientNet, Swin, ViT, Ensemble)..."
echo "⏱️  This may take 30-60+ minutes depending on your hardware..."
python3 ai/train_classifier.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Training complete!${NC}"
else
    echo -e "${YELLOW}⚠️  Training completed with warnings${NC}"
fi

# STEP 3: Test Inference
echo -e "\n${BLUE}━━━ STEP 3: INFERENCE PIPELINE ━━━${NC}"
echo "🔍 Testing inference on sample images..."
python3 ai/inference_pipeline.py

echo -e "\n${GREEN}✅ Inference pipeline tested!${NC}"

# STEP 4: Start Flask Server
echo -e "\n${BLUE}━━━ STEP 4: STARTING API SERVER ━━━${NC}"
echo "🌐 Launching Flask API on http://localhost:5000"
echo "⚠️  Keep this running! Open a new terminal to access UI."

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask and dependencies..."
    pip3 install flask flask-cors pillow
fi

python3 ai/flask_server.py &
FLASK_PID=$!

# Wait for server to start
sleep 3

# STEP 5: Open UI
echo -e "\n${BLUE}━━━ STEP 5: CINEMATIC UI ━━━${NC}"
echo "🎬 Opening cinematic 3D interface..."
echo "📍 Open your browser to: file://$(pwd)/ui/index.html"
echo "   OR host it with: python3 -m http.server 8000"

# Try to open in browser
if command -v open &> /dev/null; then
    open "file://$(pwd)/ui/index.html"
elif command -v xdg-open &> /dev/null; then
    xdg-open "file://$(pwd)/ui/index.html"
fi

echo -e "\n${GREEN}════════════════════════════════════════════════════════════════════${NC}"
echo "  ✅ FoodSave AI SETUP COMPLETE!"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "🎯 NEXT STEPS:"
echo "  1. Keep Flask server running (PID: $FLASK_PID)"
echo "  2. Open a new terminal to host the UI:"
echo "     cd $(pwd)"
echo "     python3 -m http.server 8000"
echo "  3. Visit: http://localhost:8000/ui"
echo ""
echo "📡 API Endpoints:"
echo "  POST /predict           → Single image prediction"
echo "  POST /batch-predict     → Multiple images"
echo "  GET  /health            → Health check"
echo "  GET  /destinations      → Routing destinations"
echo ""
echo "📊 Check results in:"
echo "  ai/models/              → Trained models"
echo "  ai/models/results.json  → Training results"
echo "  ai/models/*.png         → Training plots & confusion matrices"
echo ""
echo "════════════════════════════════════════════════════════════════════"

# Keep the script running to keep Flask alive
wait $FLASK_PID
