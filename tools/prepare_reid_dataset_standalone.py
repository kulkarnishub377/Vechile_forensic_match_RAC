import os
import cv2
import numpy as np
import logging
from pathlib import Path
from tqdm import tqdm
import random
import pyodbc 
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# 1. PARAMETERS
# ==========================================
TARGET_DATE = "2026-02-04" 
SAMPLES_PER_HOUR = 100
MAX_WORKERS = 4
TRAIN_RATIO = 0.90
OUTPUT_DIR = "custom_vehicle_reid_dataset"

# DATABASE CONFIG (Load from environment variables)
DB_SERVER = os.getenv('MSSQL_SERVER')
DB_NAME = os.getenv('MSSQL_DATABASE')
DB_USER = os.getenv('MSSQL_USERNAME')
DB_PASS = os.getenv('MSSQL_PASSWORD')
DB_DRIVER = os.getenv('MSSQL_DRIVER', 'ODBC Driver 18 for SQL Server')

# Validate required environment variables
if not all([DB_SERVER, DB_NAME, DB_USER, DB_PASS]):
    raise ValueError("Missing required database credentials. Set: MSSQL_SERVER, MSSQL_DATABASE, MSSQL_USERNAME, MSSQL_PASSWORD")

# PATH MAPPING CONFIG
ENABLE_PATH_MAPPING = os.getenv('ENABLE_PATH_MAPPING', 'false').lower() == 'true'
PATH_MAPPING_SOURCE = os.getenv('PATH_MAPPING_SOURCE', '')
PATH_MAPPING_TARGET = os.getenv('PATH_MAPPING_TARGET', '')

# YOLO MODEL PATH (Adjust based on your file structure)
# Assuming models are relative to this script
YOLO_MODEL_PATH = "models/yolov5n_sites_v3.pt" 

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("DatasetPrep")

# ==========================================
# 2. STANDALONE DATABASE HELPER
# ==========================================
def get_db_connection():
    """Create independent DB connection"""
    conn_str = (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER},1433;"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASS};"
        f"TrustServerCertificate=yes;"
        f"Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)

def execute_query_standalone(query, params=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"SQL Error: {e}")
        return []

# ==========================================
# 3. STANDALONE IMAGE HELPER
# ==========================================
def map_image_path(db_path):
    if not ENABLE_PATH_MAPPING or not db_path:
        return db_path
    if PATH_MAPPING_SOURCE in db_path:
        return db_path.replace(PATH_MAPPING_SOURCE, PATH_MAPPING_TARGET)
    return db_path

# ==========================================
# 4. STANDALONE YOLO DETECTOR
# ==========================================
class StandaloneDetector:
    def __init__(self, model_path):
        self.model = None
        self.load_model(model_path)
        
    def load_model(self, path):
        import torch
        logger.info(f"Loading YOLO from: {path}")
        try:
             # Try Ultralytics first
            from ultralytics import YOLO
            self.model = YOLO(path)
            self.mode = 'ultralytics'
        except ImportError:
            # Fallback to torch.hub
            self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=path)
            self.mode = 'hub'
        logger.info("YOLO Model Loaded.")

    def detect(self, img):
        if self.model is None: return []
        
        detections = []
        if self.mode == 'ultralytics':
            results = self.model(img, verbose=False)
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    cls = int(box.cls[0])
                    if cls == 0: # Vehicle
                        detections.append([int(x1), int(y1), int(x2), int(y2)])
        else:
            # Hub mode
            results = self.model(img)
            for *box, conf, cls in results.xyxy[0].cpu().numpy():
                if int(cls) == 0:
                    detections.append([int(b) for b in box])
        return detections

# ==========================================
# 5. CORE LOGIC
# ==========================================
def process_pair(row, pid_str, dirs, detector):
    try:
        entry_path_db = row[0]
        exit_path_db = row[1]
        
        entry_path = map_image_path(entry_path_db)
        exit_path = map_image_path(exit_path_db)

        # Helper to crop
        def process_image(path):
            if not os.path.exists(path): return None
            img = cv2.imread(path)
            if img is None: return None
            
            # Detect
            boxes = detector.detect(img)
            if not boxes: return None
            
            # Largest Vehicle
            best_box = max(boxes, key=lambda b: (b[2]-b[0])*(b[3]-b[1]))
            x1, y1, x2, y2 = best_box
            
            # Crop
            h, w = img.shape[:2]
            x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
            return img[y1:y2, x1:x2]

        crop1 = process_image(entry_path)
        if crop1 is None: return False
        
        crop2 = process_image(exit_path)
        if crop2 is None: return False
        
        # Save
        if random.random() < TRAIN_RATIO:
             cv2.imwrite(str(dirs['train'] / f"{pid_str}_c1_01.jpg"), crop1)
             cv2.imwrite(str(dirs['train'] / f"{pid_str}_c2_01.jpg"), crop2)
        else:
             cv2.imwrite(str(dirs['query'] / f"{pid_str}_c2_01.jpg"), crop2)
             cv2.imwrite(str(dirs['gallery'] / f"{pid_str}_c1_01.jpg"), crop1)
             
        return True
    except Exception:
        return False

def main():
    dirs = {
        'train': Path(OUTPUT_DIR) / 'bounding_box_train',
        'query': Path(OUTPUT_DIR) / 'query',
        'gallery': Path(OUTPUT_DIR) / 'bounding_box_test'
    }
    for d in dirs.values(): d.mkdir(parents=True, exist_ok=True)

    logger.info("Initializing Standalone Detector...")
    detector = StandaloneDetector(YOLO_MODEL_PATH)
    
    current_pid = 0
    total_saved = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for hour in range(24):
            start = f"{TARGET_DATE} {hour:02d}:00:00"
            end = f"{TARGET_DATE} {hour:02d}:59:59"
            
            query = f"""
            SELECT TOP {SAMPLES_PER_HOUR} EN_ANPR_IMAGE_PATH, EX_ANPR_IMAGE_PATH 
            FROM [HTMS_EPE].[dbo].[TBL_COMBINED_TRANSACTION]
            WHERE TXN_COMBINE_TIME >= ? AND TXN_COMBINE_TIME <= ?
            AND LEN(EN_ANPR_IMAGE_PATH) > 5 AND LEN(EX_ANPR_IMAGE_PATH) > 5
            ORDER BY NEWID()
            """
            
            rows = execute_query_standalone(query, (start, end))
            if not rows: continue
            
            logger.info(f"Hour {hour:02d}: Processing {len(rows)} records...")
            
            futures = []
            for row in rows:
                pid_str = f"{current_pid:06d}"
                futures.append(executor.submit(process_pair, row, pid_str, dirs, detector))
                current_pid += 1
                
            for f in tqdm(as_completed(futures), total=len(futures)):
                if f.result(): total_saved += 1
                
    logger.info(f"Done! Saved {total_saved} pairs to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
