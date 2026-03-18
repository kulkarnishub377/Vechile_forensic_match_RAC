"""
=============================================================================
VEHICLE ReID DATASET - 4 WORKERS + THREAD LOCK + PROGRESS BAR
=============================================================================
"""

import os
import cv2
import gc
import time
import numpy as np
import logging
from pathlib import Path
from tqdm import tqdm
import random
import pyodbc
from concurrent.futures import ThreadPoolExecutor
import threading

# ==========================================
# CONFIGURATION
# ==========================================

VEHICLE_CLASSES = {
    "CAR":   [4],
    "LCV":   [5, 20],
    "TRUCK": [10, 11, 12, 13, 14, 15],
    "BUS":   [7, 8, 9],
}

TIME_PERIODS = {
    "EARLY_MORNING": ("05:00:00", "07:00:00"),
    "MORNING":       ("07:00:00", "10:00:00"),
    "AFTERNOON":     ("12:00:00", "16:00:00"),
    "EVENING":       ("16:00:00", "19:00:00"),
    "NIGHT":         ("19:00:00", "22:00:00"),
    "LATE_NIGHT":    ("22:00:00", "05:00:00"),
}

# 4 classes × 6 times × 208 = ~5000 vehicles = ~10000 images
SAMPLES_PER_CLASS_PER_TIME = 208

START_DATE = "2025-11-18"
END_DATE = "2026-02-05"
TRAIN_RATIO = 0.90
OUTPUT_DIR = "vehicle_reid_by_class"

# ==========================================
# PERFORMANCE SETTINGS
# ==========================================
MAX_WORKERS = 4
BATCH_SIZE = 52

# DATBASE
DB_SERVER = '192.50.20.15'
DB_PORT = '1433'
DB_NAME = 'HTMS_EPE'
DB_USER = 'admin'
DB_PASS = 'WHOAMI@4PLACE'
DB_DRIVER = 'ODBC Driver 18 for SQL Server'

# PATH MAPPING
ENABLE_PATH_MAPPING = True
PATH_MAPPING_SOURCE = 'E:\\_TrxMedia'
PATH_MAPPING_TARGET = '\\\\192.50.20.13\\_TrxMedia'

# YOLO
YOLO_MODEL_PATH = "models/detection/yolov5n_sites_v3.pt"
MIN_VEHICLE_WIDTH = 50
MIN_VEHICLE_HEIGHT = 50

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger()
os.environ['YOLO_VERBOSE'] = 'False'

# ==========================================
# UTILITIES
# ==========================================

def get_memory_mb():
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    except:
        return 0

def get_db_connection():
    conn_str = (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER},{DB_PORT};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASS};"
        f"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

def fetch_segment(cch_classes, time_period, start_time, end_time, limit):
    cch_list = ','.join(str(c) for c in cch_classes)
    
    if time_period == "LATE_NIGHT":
        query = f"""
        SELECT TOP {limit} EN_ANPR_IMAGE_PATH, EX_ANPR_IMAGE_PATH
        FROM [HTMS_EPE].[dbo].[TBL_COMBINED_TRANSACTION]
        WHERE TXN_COMBINE_TIME >= '{START_DATE}' AND TXN_COMBINE_TIME <= '{END_DATE} 23:59:59'
        AND LEN(EN_ANPR_IMAGE_PATH) > 5 AND LEN(EX_ANPR_IMAGE_PATH) > 5
        AND EN_TAG_CCH_CLASS IN ({cch_list})
        AND (CAST(TXN_COMBINE_TIME AS TIME) >= '22:00:00' OR CAST(TXN_COMBINE_TIME AS TIME) < '05:00:00')
        ORDER BY NEWID()
        """
    else:
        query = f"""
        SELECT TOP {limit} EN_ANPR_IMAGE_PATH, EX_ANPR_IMAGE_PATH
        FROM [HTMS_EPE].[dbo].[TBL_COMBINED_TRANSACTION]
        WHERE TXN_COMBINE_TIME >= '{START_DATE}' AND TXN_COMBINE_TIME <= '{END_DATE} 23:59:59'
        AND LEN(EN_ANPR_IMAGE_PATH) > 5 AND LEN(EX_ANPR_IMAGE_PATH) > 5
        AND EN_TAG_CCH_CLASS IN ({cch_list})
        AND CAST(TXN_COMBINE_TIME AS TIME) >= '{start_time}' AND CAST(TXN_COMBINE_TIME AS TIME) < '{end_time}'
        ORDER BY NEWID()
        """
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    data = [(str(row[0]), str(row[1])) for row in rows]
    cursor.close()
    conn.close()
    return data

def map_path(db_path):
    if ENABLE_PATH_MAPPING and PATH_MAPPING_SOURCE in str(db_path):
        return str(db_path).replace(PATH_MAPPING_SOURCE, PATH_MAPPING_TARGET)
    return db_path

# ==========================================
# YOLO DETECTOR WITH THREAD LOCK
# ==========================================

class Detector:
    def __init__(self, model_path):
        self.model = None
        self.lock = threading.Lock()  # THREAD LOCK
        
        if model_path and os.path.exists(model_path):
            from ultralytics import YOLO
            self.model = YOLO(model_path)
            # Warmup
            dummy = np.zeros((480, 640, 3), dtype=np.uint8)
            self.model(dummy, verbose=False)
            logger.info("YOLO ready (with thread lock)")
    
    def crop(self, img):
        if self.model is None:
            return img
        try:
            # THREAD-SAFE INFERENCE
            with self.lock:
                results = self.model(img, verbose=False)
            
            boxes = []
            for r in results:
                for box in r.boxes:
                    if int(box.cls[0]) == 0 and float(box.conf[0]) > 0.3:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        boxes.append([int(x1), int(y1), int(x2), int(y2)])
            del results
            
            if not boxes:
                return img
            
            x1, y1, x2, y2 = max(boxes, key=lambda b: (b[2]-b[0]) * (b[3]-b[1]))
            if (x2-x1) < MIN_VEHICLE_WIDTH or (y2-y1) < MIN_VEHICLE_HEIGHT:
                return img
            
            h, w = img.shape[:2]
            return img[max(0,y1):min(h,y2), max(0,x1):min(w,x2)].copy()
        except:
            return img

# Global detector
detector = None

# ==========================================
# PROCESS ONE VEHICLE
# ==========================================

def process_one(args):
    vid, en_path, ex_path, class_name, output_dir = args
    global detector
    
    try:
        # Load entry
        entry_path = map_path(en_path)
        if not os.path.exists(entry_path):
            return None
        entry_img = cv2.imread(entry_path)
        if entry_img is None:
            return None
        entry_crop = detector.crop(entry_img)
        del entry_img
        
        # Load exit
        exit_path = map_path(ex_path)
        if not os.path.exists(exit_path):
            del entry_crop
            return None
        exit_img = cv2.imread(exit_path)
        if exit_img is None:
            del entry_crop
            return None
        exit_crop = detector.crop(exit_img)
        del exit_img
        
        # Save
        vid_str = f"{vid:06d}"
        cv2.imwrite(str(output_dir / f"{vid_str}_{class_name}_c1_s1.jpg"), entry_crop)
        cv2.imwrite(str(output_dir / f"{vid_str}_{class_name}_c2_s1.jpg"), exit_crop)
        
        del entry_crop, exit_crop
        return vid
    except:
        return None

# ==========================================
# MAIN
# ==========================================

def main():
    global detector
    
    print("=" * 70)
    print("VEHICLE ReID DATASET - 4 WORKERS + THREAD LOCK")
    print("=" * 70)
    
    total = len(VEHICLE_CLASSES) * len(TIME_PERIODS) * SAMPLES_PER_CLASS_PER_TIME
    print(f"Target: ~{total} vehicles = ~{total*2} images")
    print(f"Workers: {MAX_WORKERS}, Batch: {BATCH_SIZE}")
    print()
    
    # Directories
    dirs = {
        'train': Path(OUTPUT_DIR) / 'bounding_box_train',
        'gallery': Path(OUTPUT_DIR) / 'bounding_box_test'
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    
    # Load YOLO
    print("Loading YOLO...")
    detector = Detector(YOLO_MODEL_PATH)
    print(f"Memory: {get_memory_mb():.0f} MB")
    print()
    
    vehicle_id = 1
    stats = {}
    start_time = time.time()
    
    for class_idx, (class_name, cch_classes) in enumerate(VEHICLE_CLASSES.items(), 1):
        print(f"\n[{class_idx}/4] {class_name}")
        print("-" * 40)
        class_count = 0
        
        for time_name, (t_start, t_end) in TIME_PERIODS.items():
            # Fetch
            data = fetch_segment(cch_classes, time_name, t_start, t_end, SAMPLES_PER_CLASS_PER_TIME)
            if not data:
                print(f"  {time_name}: no data")
                continue
            
            random.shuffle(data)
            split = int(len(data) * TRAIN_RATIO)
            train_data = data[:split]
            test_data = data[split:]
            
            success = 0
            
            # Process TRAIN in batches with 4 workers
            for batch_start in range(0, len(train_data), BATCH_SIZE):
                batch = train_data[batch_start:batch_start + BATCH_SIZE]
                tasks = [(vehicle_id + i, en, ex, class_name, dirs['train']) 
                         for i, (en, ex) in enumerate(batch)]
                
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    results = list(tqdm(
                        executor.map(process_one, tasks),
                        total=len(tasks),
                        desc=f"  {time_name} train",
                        leave=False,
                        ncols=70
                    ))
                    success += sum(1 for r in results if r is not None)
                
                vehicle_id += len(batch)
            
            # Process TEST in batches with 4 workers
            for batch_start in range(0, len(test_data), BATCH_SIZE):
                batch = test_data[batch_start:batch_start + BATCH_SIZE]
                tasks = [(vehicle_id + i, en, ex, class_name, dirs['gallery']) 
                         for i, (en, ex) in enumerate(batch)]
                
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    results = list(tqdm(
                        executor.map(process_one, tasks),
                        total=len(tasks),
                        desc=f"  {time_name} test",
                        leave=False,
                        ncols=70
                    ))
                    success += sum(1 for r in results if r is not None)
                
                vehicle_id += len(batch)
            
            class_count += success
            print(f"  {time_name}: {success}/{len(data)} saved")
            gc.collect()
        
        stats[class_name] = class_count
        print(f"  {class_name} total: {class_count}")
    
    elapsed = time.time() - start_time
    
    # Summary
    print()
    print("=" * 70)
    print("COMPLETE!")
    print("=" * 70)
    
    train_count = len(list(dirs['train'].glob('*.jpg')))
    gallery_count = len(list(dirs['gallery'].glob('*.jpg')))
    
    print(f"\nOutput: {OUTPUT_DIR}/")
    print(f"  train:   {train_count} images")
    print(f"  gallery: {gallery_count} images")
    print(f"  TOTAL:   {train_count + gallery_count} images")
    print()
    
    for cls, cnt in stats.items():
        print(f"  {cls}: {cnt} vehicles")
    
    print(f"\nTime: {elapsed/60:.1f} minutes")
    print(f"Memory: {get_memory_mb():.0f} MB")
    print("\nNEXT: Zip folder and upload to Google Drive!")

if __name__ == "__main__":
    main()
