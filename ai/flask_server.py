#!/usr/bin/env python3
"""
FoodSave AI — Flask API Server
Production-grade REST API for food waste classification and routing
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import torch
import json
from werkzeug.utils import secure_filename
from PIL import Image
import io
import base64
import sys
sys.path.insert(0, str(Path(__file__).parent))

from inference_pipeline import FoodWasteDecisionEngine

# ━━━ FLASK CONFIG ━━━
app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'ai/uploads'
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

# Initialize engine
print("🚀 Initializing FoodSave AI Engine...")
engine = FoodWasteDecisionEngine()
print("✅ Engine ready!")

# ━━━ API ENDPOINTS ━━━

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model": "FoodSave AI",
        "version": "1.0.0"
    })

@app.route('/predict', methods=['POST'])
def predict():
    """
    Main prediction endpoint
    Accepts: image file or base64 encoded image
    Returns: freshness classification + routing decision
    """
    try:
        if 'file' not in request.files and 'image_base64' not in request.form:
            return jsonify({"error": "No image provided"}), 400
        
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            filename = secure_filename(file.filename)
            filepath = Path(app.config['UPLOAD_FOLDER']) / filename
            file.save(filepath)
            image_path = str(filepath)
        
        # Handle base64 image
        elif 'image_base64' in request.form:
            image_base64 = request.form['image_base64']
            image_data = base64.b64decode(image_base64)
            img = Image.open(io.BytesIO(image_data))
            filepath = Path(app.config['UPLOAD_FOLDER']) / 'temp_base64.jpg'
            img.save(filepath)
            image_path = str(filepath)
        
        # Run inference
        result = engine.process_food_image(image_path)
        
        return jsonify({
            "success": True,
            "data": result,
            "timestamp": str(Path(image_path).stat().st_mtime)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/batch-predict', methods=['POST'])
def batch_predict():
    """
    Batch prediction endpoint
    Accepts: multiple image files
    Returns: list of predictions
    """
    try:
        if 'files' not in request.files:
            return jsonify({"error": "No files provided"}), 400
        
        files = request.files.getlist('files')
        results = []
        
        for file in files:
            if file.filename == '':
                continue
            
            filename = secure_filename(file.filename)
            filepath = Path(app.config['UPLOAD_FOLDER']) / filename
            file.save(filepath)
            
            result = engine.process_food_image(str(filepath))
            results.append({
                "filename": filename,
                "result": result
            })
        
        return jsonify({
            "success": True,
            "count": len(results),
            "data": results
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/classes', methods=['GET'])
def get_classes():
    """Get available food classes"""
    return jsonify({
        "classes": engine.eff_model.__class__.__module__,  # Placeholder
        "destinations": list(engine.DESTINATIONS.keys())
    })

@app.route('/destinations', methods=['GET'])
def get_destinations():
    """Get all available routing destinations"""
    return jsonify({
        "destinations": engine.DESTINATIONS
    })

@app.route('/model-info', methods=['GET'])
def model_info():
    """Get model information"""
    return jsonify({
        "models": {
            "efficientnet": "✓ Loaded",
            "swin": "✓ Loaded",
            "vit": "✓ Loaded",
            "ensemble": "✓ Loaded"
        },
        "device": str(engine.eff_model.device),
        "input_size": 224
    })

# ━━━ ERROR HANDLERS ━━━
@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large (max 16MB)"}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

# ━━━ RUN SERVER ━━━
if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("  🚀 FoodSave AI — Flask API Server")
    print("=" * 70)
    print("\n📡 Server running on http://localhost:5000")
    print("\nEndpoints:")
    print("  POST /predict           → Single image prediction")
    print("  POST /batch-predict     → Multiple images")
    print("  GET  /health            → Health check")
    print("  GET  /classes           → Available classes")
    print("  GET  /destinations      → Routing destinations")
    print("  GET  /model-info        → Model details")
    print("\n" + "=" * 70 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
