"""
Test script to verify system setup
"""
import sys
import os

def test_imports():
    """Test if all required packages are installed"""
    print("Testing imports...")
    
    packages = [
        ('torch', 'PyTorch'),
        ('torchvision', 'TorchVision'),
        ('cv2', 'OpenCV'),
        ('numpy', 'NumPy'),
        ('PIL', 'Pillow'),
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('pyodbc', 'pyODBC'),
        ('faiss', 'FAISS'),
        ('imagehash', 'ImageHash'),
        ('openvino', 'OpenVINO Runtime'),
        ('paddlepaddle', 'PaddlePaddle'),
        ('paddleocr', 'PaddleOCR'),
    ]
    
    failed = []
    for package, name in packages:
        try:
            __import__(package)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - NOT INSTALLED")
            failed.append(name)
    
    if failed:
        print(f"\n❌ Missing packages: {', '.join(failed)}")
        return False
    
    print("\n✓ All packages installed")
    return True


def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    
    try:
        from app import config
        
        print(f"✓ System Version: {config.SYSTEM_VERSION}")
        print(f"✓ Embedding Version: {config.EMBEDDING_VERSION}")
        print(f"✓ Embedding Dimension: {config.TOTAL_EMBEDDING_DIM}")
        print(f"✓ Models Directory: {config.MODELS_DIR}")
        print(f"✓ Vector DB Directory: {config.VECTOR_DB_DIR}")
        print(f"✓ YOLO Backend: {config.YOLO_BACKEND}")
        print(f"✓ OCR Enabled: {config.ENABLE_OCR}")
        print(f"✓ OCR Matching Enabled: {config.ENABLE_OCR_MATCHING}")
        
        # Check if directories exist
        dirs = [
            config.MODELS_DIR,
            config.VECTOR_DB_DIR,
            config.LOGS_DIR,
            config.DATA_DIR
        ]
        
        for d in dirs:
            if os.path.exists(d):
                print(f"✓ Directory exists: {d}")
            else:
                print(f"⚠ Directory missing: {d}")
        
        return True
    
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_models():
    """Test model weights"""
    print("\nTesting model weights...")
    
    from app import config
    
    # Check YOLO backend
    if config.YOLO_BACKEND == 'openvino':
        yolo_model = config.YOLO_OPENVINO_MODEL_PATH
        print(f"  Using OpenVINO YOLO: {yolo_model}")
    else:
        yolo_model = config.YOLO_PYTORCH_MODEL_PATH
        print(f"  Using PyTorch YOLO: {yolo_model}")
    
    models = [
        ('YOLO', yolo_model),
        ('OSNet', config.OSNET_WEIGHTS_PATH),
        ('Paddle OCR Model', config.PADDLE_MODEL_DIR + '/inference.pdmodel'),
        ('Paddle OCR Params', config.PADDLE_MODEL_DIR + '/inference.pdparams'),
    ]
    
    found = 0
    for name, path in models:
        if os.path.exists(path):
            print(f"✓ {name} weights found: {path}")
            found += 1
        else:
            print(f"✗ {name} weights missing: {path}")
    
    if found < len(models):
        print(f"\n⚠ {len(models) - found} model files missing")
        print("Please download model weights to the models/ directory")
        return False
    
    return True


def test_cuda():
    """Test CUDA availability"""
    print("\nTesting CUDA...")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            print(f"✓ CUDA available")
            print(f"✓ Device: {torch.cuda.get_device_name(0)}")
            # Safely access torch.version via getattr to avoid static analysis warnings
            version_attr = getattr(torch, 'version', None)
            cuda_version = getattr(version_attr, 'cuda', None) if version_attr else None
            print(f"✓ CUDA Version: {cuda_version if cuda_version else 'N/A'}")
        else:
            print("⚠ CUDA not available - using CPU")
        
        return True
    
    except Exception as e:
        print(f"❌ CUDA test failed: {e}")
        return False


def test_ocr():
    """Test OCR system"""
    print("\nTesting OCR system...")
    
    try:
        from app import config
        
        if not config.ENABLE_OCR:
            print("⚠ OCR disabled in config")
            return True
        
        # Check OCR models
        paddle_model = config.PADDLE_MODEL_DIR + '/inference.pdmodel'
        paddle_params = config.PADDLE_MODEL_DIR + '/inference.pdparams'
        
        if os.path.exists(paddle_model) and os.path.exists(paddle_params):
            print(f"✓ Paddle OCR models found")
            print(f"  Model: {paddle_model}")
            print(f"  Params: {paddle_params}")
        else:
            print(f"✗ Paddle OCR models missing")
            return False
        
        # Test OCR import
        from app.ocr import PaddlePlateOCR
        print("✓ OCR engine imported successfully")
        
        return True
    
    except Exception as e:
        print(f"❌ OCR test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Vehicle Forensic Matching System - Setup Test v3.0")
    print("Combined OCR + Embedding Search")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Model Weights", test_models),
        ("CUDA", test_cuda),
        ("OCR System", test_ocr)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 System ready!")
        print("\nNext steps:")
        print("1. Configure .env file with your settings")
        print("2. Start ingestion service: python -m app.ingestion")
        print("3. Start API service: python -m app.api")
    else:
        print("\n⚠ Some tests failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
