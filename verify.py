#!/usr/bin/env python3
"""
FoodSave AI — System Verification Script
Checks all components before running the full pipeline
"""

import sys
import os
from pathlib import Path
import importlib

def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} (requires 3.9+)")
        return False

def check_directories():
    """Check required directories exist"""
    print("\n📁 Checking directory structure...")
    required_dirs = [
        "ai/dataset",
        "ai/models",
        "ai/uploads",
        "ui/js"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ⚠️  {dir_path} (will be created)")
            all_exist = False
    
    # Create missing directories
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    return all_exist

def check_files():
    """Check required files exist"""
    print("\n📄 Checking required files...")
    required_files = [
        "ai/setup_dataset.py",
        "ai/train_classifier.py",
        "ai/inference_pipeline.py",
        "ai/flask_server.py",
        "ui/index.html",
        "ui/js/scene.js",
        "config.py",
        "requirements.txt",
        "README.md",
        "run.sh"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (MISSING!)")
            all_exist = False
    
    return all_exist

def check_dependencies():
    """Check Python packages"""
    print("\n📦 Checking Python dependencies...")
    required_packages = {
        'torch': 'PyTorch',
        'torchvision': 'TorchVision',
        'numpy': 'NumPy',
        'sklearn': 'scikit-learn',
        'PIL': 'Pillow',
        'flask': 'Flask',
        'matplotlib': 'Matplotlib',
        'seaborn': 'Seaborn',
        'tqdm': 'tqdm'
    }
    
    missing = []
    for package, display_name in required_packages.items():
        try:
            importlib.import_module(package)
            print(f"   ✅ {display_name}")
        except ImportError:
            print(f"   ❌ {display_name} (MISSING!)")
            missing.append(package)
    
    return len(missing) == 0, missing

def check_gpu():
    """Check GPU/MPS availability"""
    print("\n🖥️  Checking hardware acceleration...")
    try:
        import torch
        
        if torch.backends.mps.is_available():
            print(f"   ✅ MPS (Apple Silicon)")
            return "mps"
        elif torch.cuda.is_available():
            print(f"   ✅ CUDA (GPU) - {torch.cuda.get_device_name(0)}")
            print(f"      Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
            return "cuda"
        else:
            print(f"   ⚠️  No GPU/MPS available (will use CPU)")
            return "cpu"
    except Exception as e:
        print(f"   ⚠️  Could not detect GPU: {e}")
        return "cpu"

def check_config():
    """Check configuration file"""
    print("\n⚙️  Checking configuration...")
    try:
        import config
        print(f"   ✅ config.py loaded")
        print(f"      Classes: {config.CLASSES}")
        print(f"      Batch size: {config.BATCH_SIZE}")
        print(f"      Epochs: {config.EPOCHS}")
        print(f"      Destinations: {len(config.DESTINATIONS)}")
        return True
    except Exception as e:
        print(f"   ❌ Error loading config: {e}")
        return False

def check_ports():
    """Check if required ports are available"""
    print("\n🔌 Checking ports...")
    import socket
    
    ports = {5000: "API", 8000: "UI"}
    available = True
    
    for port, service in ports.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"   ⚠️  Port {port} ({service}) - Already in use")
            available = False
        else:
            print(f"   ✅ Port {port} ({service}) - Available")
    
    return available

def print_summary(results):
    """Print summary of checks"""
    print("\n" + "=" * 70)
    print("  📋 VERIFICATION SUMMARY")
    print("=" * 70)
    
    checks = [
        ("Python Version", results.get('python', False)),
        ("Directories", results.get('directories', False)),
        ("Required Files", results.get('files', False)),
        ("Dependencies", results.get('dependencies', False)),
        ("Configuration", results.get('config', False)),
        ("Ports Available", results.get('ports', False)),
    ]
    
    passed = sum(1 for _, status in checks if status)
    total = len(checks)
    
    for check_name, status in checks:
        status_text = "✅ PASS" if status else "⚠️  CHECK"
        print(f"  {status_text:12} {check_name}")
    
    print("=" * 70)
    print(f"\n  {passed}/{total} checks passed\n")
    
    return passed == total

def print_next_steps(gpu, deps_ok, missing_deps):
    """Print next steps"""
    print("🚀 NEXT STEPS:")
    print("-" * 70)
    
    if not deps_ok:
        print("\n1️⃣  Install missing dependencies:")
        print(f"   pip3 install -r requirements.txt")
        if missing_deps:
            print(f"   Missing: {', '.join(missing_deps)}")
    
    if gpu == "cpu":
        print("\n⚠️  Running on CPU (slow training)")
        print("   For faster training, install GPU support:")
        print("   - CUDA: pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
        print("   - MPS (Mac): PyTorch 1.12+ with macOS 12.3+")
    
    print("\n2️⃣  Generate dataset:")
    print("   python3 ai/setup_dataset.py")
    
    print("\n3️⃣  Train models (30-60+ minutes):")
    print("   python3 ai/train_classifier.py")
    
    print("\n4️⃣  Or run everything at once:")
    print("   chmod +x run.sh && ./run.sh")
    
    print("\n" + "=" * 70)

def main():
    """Run all checks"""
    print("\n" + "=" * 70)
    print("  🔍 FoodSave AI — System Verification")
    print("=" * 70 + "\n")
    
    results = {
        'python': check_python_version(),
        'directories': check_directories(),
        'files': check_files(),
        'config': check_config(),
        'gpu': check_gpu(),
    }
    
    deps_ok, missing = check_dependencies()
    results['dependencies'] = deps_ok
    
    results['ports'] = check_ports()
    
    # Print summary
    all_good = print_summary(results)
    
    # Print recommendations
    print_next_steps(results['gpu'], deps_ok, missing)
    
    if all_good:
        print("✅ System is ready! You can now run: ./run.sh\n")
        return 0
    else:
        if not deps_ok:
            print(f"⚠️  Missing dependencies. Run: pip3 install -r requirements.txt\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
