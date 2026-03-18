"""
Complete System Verification Script
Checks all components before starting services
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import os
from datetime import datetime
from app import config


def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def check_icon(passed):
    return "[PASS]" if passed else "[FAIL]"


def test_python_packages():
    """Test Python package imports"""
    print_header("PYTHON PACKAGES")
    
    packages = [
        ('torch', 'PyTorch'),
        ('torchvision', 'TorchVision'),
        ('torchreid', 'TorchReID'),
        ('cv2', 'OpenCV'),
        ('numpy', 'NumPy'),
        ('faiss', 'FAISS'),
        ('paddleocr', 'PaddleOCR'),
        ('pyodbc', 'PyODBC'),
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
    ]
    
    all_pass = True
    for module, name in packages:
        try:
            __import__(module)
            print(f"  {check_icon(True)} {name:<20}")
        except ImportError as e:
            print(f"  {check_icon(False)} {name:<20} - MISSING: {e}")
            all_pass = False
    
    return all_pass


def test_openvino():
    """Test OpenVINO availability"""
    print_header("OPENVINO")
    
    try:
        from openvino.runtime import Core
        ie = Core()
        devices = ie.available_devices
        print(f"  {check_icon(True)} OpenVINO available")
        print(f"      Devices: {', '.join(devices)}")
        return True
    except Exception as e:
        print(f"  {check_icon(False)} OpenVINO not available: {e}")
        return False


def test_models():
    """Test model file existence"""
    print_header("MODEL FILES")
    
    models = [
        (config.YOLO_OPENVINO_MODEL, 'YOLO OpenVINO Model'),
        (config.REID_CHECKPOINT_PATH, 'ReID TorchReID Model'),
        (config.OCR_REC_MODEL_DIR, 'OCR Recognition Model'),
        (config.OCR_DICT_PATH, 'OCR Dictionary'),
    ]
    
    all_pass = True
    for model_path, name in models:
        exists = model_path.exists()
        print(f"  {check_icon(exists)} {name}")
        if exists:
            print(f"      Path: {model_path}")
        else:
            print(f"      MISSING: {model_path}")
            all_pass = False
    
    return all_pass


def test_directories():
    """Test directory structure"""
    print_header("DIRECTORIES")
    
    dirs = [
        (config.VECTOR_DB_DIR, 'Vector DB'),
        (config.LOGS_DIR, 'Logs'),
        (config.DATA_DIR, 'Data'),
        (config.ENTRY_TRACK_DIR, 'Entry Tracking'),
        (config.MODELS_DIR, 'Models'),
    ]
    
    all_pass = True
    for dir_path, name in dirs:
        exists = dir_path.exists()
        print(f"  {check_icon(exists)} {name:<20} - {dir_path}")
        if not exists:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"      Created directory")
            except Exception as e:
                print(f"      Failed to create: {e}")
                all_pass = False
    
    return all_pass


def test_database():
    """Test database connection"""
    print_header("DATABASE CONNECTION")
    
    try:
        from app.database.db_connection import get_db_connection
        db = get_db_connection()
        
        # Test query
        result = db.execute_query("SELECT 1 AS test")
        
        if result:
            print(f"  {check_icon(True)} Database connection OK")
            print(f"      Server: {config.MSSQL_SERVER}")
            print(f"      Database: {config.MSSQL_DATABASE}")
            print(f"      User: {config.MSSQL_USERNAME}")
            return True
        else:
            print(f"  {check_icon(False)} Query returned no results")
            return False
    
    except Exception as e:
        print(f"  {check_icon(False)} Database connection FAILED")
        print(f"      Error: {e}")
        return False


def test_image_path():
    """Test image path accessibility"""
    print_header("IMAGE PATH ACCESS")
    
    test_path = Path(config.PATH_MAPPING_TARGET)
    
    print(f"  Path Mapping: {'ENABLED' if config.ENABLE_PATH_MAPPING else 'DISABLED'}")
    print(f"  Source: {config.PATH_MAPPING_SOURCE}")
    print(f"  Target: {config.PATH_MAPPING_TARGET}")
    
    try:
        if test_path.exists():
            print(f"  {check_icon(True)} Network path accessible")
            
            # Try to list files
            files = list(test_path.rglob('*.jpg'))[:5]
            if files:
                print(f"      Found {len(files)} sample images")
            return True
        else:
            print(f"  {check_icon(False)} Network path NOT accessible")
            print(f"      Path: {test_path}")
            print(f"      Try: net use Z: {config.PATH_MAPPING_TARGET}")
            return False
    
    except Exception as e:
        print(f"  {check_icon(False)} Error accessing path: {e}")
        return False


def test_configuration():
    """Test configuration values"""
    print_header("CONFIGURATION")
    
    print(f"  System Version:      {config.SYSTEM_VERSION}")
    print(f"  Embedding Version:   {config.EMBEDDING_VERSION}")
    print(f"  Environment:         {config.ENVIRONMENT}")
    print(f"  YOLO Backend:        {config.YOLO_BACKEND}")
    print(f"  ReID Backend:        {config.REID_BACKEND}")
    print(f"  OCR Backend:         {config.OCR_BACKEND}")
    print(f"  Use GPU:             {config.USE_GPU}")
    print()
    print(f"  Ingestion:")
    print(f"    Batch Size:        {config.INGESTION_BATCH_SIZE}")
    print(f"    Poll Interval:     {config.INGESTION_POLL_INTERVAL}s")
    print(f"    Lookback Hours:    {config.INGESTION_LOOKBACK_HOURS}")
    print()
    print(f"  API:")
    print(f"    Host:              {config.API_HOST}")
    print(f"    Port:              {config.API_PORT}")
    print(f"    Workers:           {config.API_WORKERS}")
    
    return True


def test_faiss_database():
    """Test FAISS database"""
    print_header("FAISS DATABASE")
    
    if not config.VECTOR_DB_DIR.exists():
        print(f"  {check_icon(False)} Vector DB directory not found")
        return False
    
    partitions = [d for d in config.VECTOR_DB_DIR.iterdir() if d.is_dir()]
    
    if not partitions:
        print(f"  [WARN] No FAISS partitions found (will be created on first ingestion)")
        return True
    
    print(f"  {check_icon(True)} Found {len(partitions)} partition(s)")
    
    total_vectors = 0
    for partition in partitions:
        index_file = partition / 'index.faiss'
        ids_file = partition / 'ids.pkl'
        
        if index_file.exists() and ids_file.exists():
            print(f"      [OK] {partition.name}")
            try:
                import pickle
                with open(ids_file, 'rb') as f:
                    ids = pickle.load(f)
                    total_vectors += len(ids)
            except:
                pass
        else:
            print(f"      [WARN] {partition.name} - incomplete")
    
    if total_vectors > 0:
        print(f"  Total vectors: ~{total_vectors:,}")
    
    return True


def test_last_checkpoint():
    """Test last checkpoint file"""
    print_header("INGESTION CHECKPOINT")
    
    if config.LAST_FETCHED_TIME_FILE.exists():
        try:
            with open(config.LAST_FETCHED_TIME_FILE, 'r') as f:
                timestamp_str = f.read().strip()
                dt = datetime.fromisoformat(timestamp_str)
                
            print(f"  {check_icon(True)} Checkpoint found")
            print(f"      Last fetched: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"      Will resume from this time")
            return True
        except Exception as e:
            print(f"  [WARN] Checkpoint file corrupted: {e}")
            return True  # Not critical
    else:
        print(f"  [WARN] No checkpoint (first run)")
        print(f"      Will fetch last {config.INGESTION_LOOKBACK_HOURS} hours on startup")
        return True


def main():
    """Run all tests"""
    print("=" * 80)
    print(" " * 20 + "CAR MATCH SERVICE - SYSTEM VERIFICATION")
    print("=" * 80)
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Python: {sys.version}")
    
    results = {
        'Python Packages': test_python_packages(),
        'OpenVINO': test_openvino(),
        'Model Files': test_models(),
        'Directories': test_directories(),
        'Database': test_database(),
        'Image Path': test_image_path(),
        'FAISS Database': test_faiss_database(),
        'Checkpoint': test_last_checkpoint(),
        'Configuration': test_configuration(),
    }
    
    # Summary
    print_header("SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        print(f"  {check_icon(result)} {name}")
    
    print()
    print(f"  Passed: {passed}/{total}")
    
    if passed == total:
        print()
        print("  " + "*" * 40)
        print("  " * 10 + "ALL TESTS PASSED!")
        print("  " + "*" * 40)
        print()
        print("  [PASS] System is ready to run!")
        print()
        print("  Next steps:")
        print("    1. Run: start_services.bat")
        print("    2. Or manually: python run_ingestion.py")
        print("                    python run_api.py")
        print("    3. Monitor: python monitor_ingestion.py")
    else:
        print()
        print("  [WARN] Some tests failed. Please fix the issues above.")
        print()
        failed = [name for name, result in results.items() if not result]
        print("  Failed tests:")
        for name in failed:
            print(f"    - {name}")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
