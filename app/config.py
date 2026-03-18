"""
Configuration Module - Loads settings from config.ini
"""
import os
import configparser
from pathlib import Path

# Load config.ini
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / 'config.ini'

_config = configparser.ConfigParser()
_config.read(CONFIG_PATH, encoding='utf-8')

# Helper functions
def _get(section: str, key: str, fallback: str = "") -> str:
    return _config.get(section, key, fallback=fallback)

def _getint(section: str, key: str, fallback: int = 0) -> int:
    return _config.getint(section, key, fallback=fallback)

def _getfloat(section: str, key: str, fallback: float = 0.0) -> float:
    return _config.getfloat(section, key, fallback=fallback)

def _getboolean(section: str, key: str, fallback: bool = False) -> bool:
    return _config.getboolean(section, key, fallback=fallback)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SYSTEM_VERSION = _get('system', 'version', '3.0.0')
EMBEDDING_VERSION = _get('system', 'embedding_version', 'v512')
ENVIRONMENT = _get('system', 'environment', 'production')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PATHS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VECTOR_DB_DIR = BASE_DIR / _get('paths', 'vector_db_path', 'vector_db') / EMBEDDING_VERSION
MODELS_DIR = BASE_DIR / _get('paths', 'models_dir', 'models')
DATA_DIR = BASE_DIR / _get('paths', 'data_dir', 'data')
LOGS_DIR = BASE_DIR / _get('paths', 'logs_dir', 'logs')

# Image path mapping (for database image paths)
ENABLE_PATH_MAPPING = _getboolean('paths', 'enable_path_mapping', False)
PATH_MAPPING_SOURCE = _get('paths', 'path_mapping_source', '')
PATH_MAPPING_TARGET = _get('paths', 'path_mapping_target', '')

def map_image_path(db_path: str) -> str:
    """
    Map image path from database to actual accessible path
    
    Args:
        db_path: Path from database (e.g., E:\\_TrxMedia\\2026\\02\\image.jpg)
    
    Returns:
        Mapped path (e.g., \\\\192.50.20.13\\_TrxMedia\\2026\\02\\image.jpg)
    """
    if not ENABLE_PATH_MAPPING:
        return db_path
    
    if not db_path:
        return db_path
    
    # Replace source path with target path
    if PATH_MAPPING_SOURCE in db_path:
        mapped_path = db_path.replace(PATH_MAPPING_SOURCE, PATH_MAPPING_TARGET)
        return mapped_path
    
    return db_path

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATABASE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MSSQL_SERVER = _get('database', 'server', '') or os.getenv('MSSQL_SERVER', '')
MSSQL_DATABASE = _get('database', 'database', '') or os.getenv('MSSQL_DATABASE', '')
MSSQL_USERNAME = _get('database', 'username', '') or os.getenv('MSSQL_USERNAME', '')
MSSQL_PASSWORD = os.getenv('MSSQL_PASSWORD')  # REQUIRED: Set environment variable
MSSQL_DRIVER = _get('database', 'driver', 'ODBC Driver 18 for SQL Server')
MSSQL_TRUST_CERTIFICATE = _get('database', 'trust_certificate', 'yes')
MSSQL_ENCRYPT = _get('database', 'encrypt', 'no')

MSSQL_POOL_SIZE = _getint('database', 'pool_size', 20)
MSSQL_MAX_OVERFLOW = _getint('database', 'max_overflow', 40)
MSSQL_POOL_TIMEOUT = _getint('database', 'pool_timeout', 30)
MSSQL_POOL_RECYCLE = _getint('database', 'pool_recycle', 3600)
MSSQL_QUERY_TIMEOUT = _getint('database', 'query_timeout', 30)

# Database connection aliases (for backward compatibility)
DB_DRIVER = MSSQL_DRIVER
DB_HOST = MSSQL_SERVER.split(',')[0] if ',' in MSSQL_SERVER else MSSQL_SERVER
DB_PORT = int(MSSQL_SERVER.split(',')[1]) if ',' in MSSQL_SERVER else 1433
DB_NAME = MSSQL_DATABASE
DB_USER = MSSQL_USERNAME
DB_PASSWORD = MSSQL_PASSWORD
DB_CONNECTION_TIMEOUT = MSSQL_POOL_TIMEOUT
DB_POOL_SIZE = MSSQL_POOL_SIZE

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REID MODEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REID_BACKEND = _get('reid', 'backend', 'torchreid')
REID_CHECKPOINT_PATH = BASE_DIR / _get('reid', 'checkpoint_path', 'models/reid/osnetv3.tar-50')
REID_MODEL_NAME = _get('reid', 'model_name', 'osnet_ain_x1_0')
REID_IMAGE_SIZE = _getint('reid', 'image_size', 384)
REID_MULTI_SCALE = _getboolean('reid', 'multi_scale', True)
REID_SCALES = [1.0]  # Default scale for single-scale extraction
REID_EMBEDDING_DIM = _getint('reid', 'embedding_dim', 512)
REID_OPENVINO_PATH = BASE_DIR / _get('reid', 'openvino_path', 'models/reid/openvino/osnetv3_384x384_FP16.xml')
REID_DEVICE = _get('reid', 'device', 'cuda')
USE_GPU = _getboolean('reid', 'use_gpu', True)
GPU_ID = _getint('reid', 'gpu_id', 0)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# YOLO DETECTOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOLO_BACKEND = _get('yolo', 'backend', 'openvino')
YOLO_PYTORCH_MODEL = BASE_DIR / _get('yolo', 'pytorch_model_path', 'models/detection/yolov5n_sites_v3.pt')
YOLO_OPENVINO_MODEL = BASE_DIR / _get('yolo', 'openvino_model_path', 'models/detection/yolo26n_site_v3_openvino_model/yolo26n_site_v3.xml')
YOLO_OPENVINO_DEVICE = _get('yolo', 'openvino_device', 'CPU')
YOLO_OPENVINO_PRECISION = _get('yolo', 'openvino_precision', 'FP16')
# YOLO detection thresholds
YOLO_CONFIDENCE_THRESHOLD = _getfloat('yolo', 'confidence_threshold', 0.25)
YOLO_IOU_THRESHOLD = _getfloat('yolo', 'iou_threshold', 0.45)
YOLO_IMAGE_SIZE = _getint('yolo', 'image_size', 480)
YOLO_VEHICLE_CONF_THRESHOLD = _getfloat('yolo', 'vehicle_conf_threshold', 0.15)
YOLO_VEHICLE_IOU_THRESHOLD = _getfloat('yolo', 'vehicle_iou_threshold', 0.45)
YOLO_PLATE_CONF_THRESHOLD = _getfloat('yolo', 'plate_conf_threshold', 0.30)
YOLO_PLATE_IOU_THRESHOLD = _getfloat('yolo', 'plate_iou_threshold', 0.45)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OCR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENABLE_OCR = _getboolean('ocr', 'enable', True)
OCR_BACKEND = _get('ocr', 'backend', 'paddle')

# PaddleOCR 3-model pipeline (detection, recognition, classification)
OCR_REC_MODEL_DIR = BASE_DIR / _get('ocr', 'rec_model_dir', 'models/ocr_models/PP-OCRv4_mobile_rec_infer_v16')
OCR_DET_MODEL_DIR = BASE_DIR / _get('ocr', 'det_model_dir', 'models/ocr_models/en_PP-OCRv3_det_infer')
OCR_CLS_MODEL_DIR = BASE_DIR / _get('ocr', 'cls_model_dir', 'models/ocr_models/ch_ppocr_mobile_v2.0_cls_slim_infer')
OCR_DICT_PATH = BASE_DIR / _get('ocr', 'dict_path', 'models/ocr_models/PP-OCRv4_mobile_rec_infer_v16/plate_dict.txt')

# Legacy path (for backward compatibility)
OCR_MODEL_DIR = BASE_DIR / _get('ocr', 'model_dir', 'models/ocr/PP-OCRv4_mobile_rec_infer_v16')

# PaddleOCR settings
OCR_USE_ANGLE_CLS = _getboolean('ocr', 'use_angle_cls', True)
OCR_LANG = _get('ocr', 'lang', 'en')
OCR_CONFIDENCE_THRESHOLD = _getfloat('ocr', 'confidence_threshold', 0.60)
OCR_USE_GPU = _getboolean('ocr', 'use_gpu', False)
OCR_ENABLE_MKLDNN = _getboolean('ocr', 'enable_mkldnn', True)
OCR_CPU_THREADS = _getint('ocr', 'cpu_threads', 4)
OCR_MIN_TEXT_LENGTH = _getint('ocr', 'min_text_length', 4)
OCR_MAX_TEXT_LENGTH = _getint('ocr', 'max_text_length', 10)
OCR_ALLOWED_CHARACTERS = _get('ocr', 'allowed_characters', '0123456789ABCDEFGHJKLMNOPQRSTUVWXYZ')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MATCHING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENABLE_OCR_MATCHING = _getboolean('matching', 'enable_ocr_matching', True)
OCR_EXACT_MATCH_ONLY = _getboolean('matching', 'ocr_exact_match_only', True)
OCR_MIN_CONFIDENCE = _getfloat('matching', 'ocr_min_confidence', 0.70)
OCR_BOOST_SCORE = _getfloat('matching', 'ocr_boost_score', 0.30)

EMBEDDING_WEIGHT = _getfloat('matching', 'embedding_weight', 0.40)
COLOR_WEIGHT = _getfloat('matching', 'color_weight', 0.20)
TIME_WEIGHT = _getfloat('matching', 'time_weight', 0.15)
ORB_WEIGHT = _getfloat('matching', 'orb_weight', 0.15)
SCALE_WEIGHT = _getfloat('matching', 'scale_weight', 0.10)

# Matching aliases (for backward compatibility)
MATCHING_MIN_OCR_CONFIDENCE = OCR_MIN_CONFIDENCE
MATCHING_OCR_BOOST_SCORE = OCR_BOOST_SCORE
MATCHING_WEIGHT_EMBEDDING = EMBEDDING_WEIGHT
MATCHING_WEIGHT_COLOR = COLOR_WEIGHT
MATCHING_WEIGHT_TIME = TIME_WEIGHT
MATCHING_WEIGHT_ORB = ORB_WEIGHT
MATCHING_WEIGHT_SCALE = SCALE_WEIGHT
MATCHING_ENABLE_OCR_MATCHING = ENABLE_OCR_MATCHING

# Time window settings (CRITICAL: Only search 10-hour uncombined entries)
TIME_WINDOW_HOURS = _getint('matching', 'time_window_hours', 10)
MATCHING_SEARCH_WINDOW_HOURS = TIME_WINDOW_HOURS
UNCOMBINED_SEARCH_HOURS = _getint('matching', 'uncombined_search_hours', 10)
DEFAULT_TOP_K = _getint('matching', 'default_top_k', 10)
MAX_TOP_K = _getint('matching', 'max_top_k', 50)
FAISS_K_MULTIPLIER = _getint('matching', 'faiss_k_multiplier', 4)

MIN_SIMILARITY_SCORE = _getfloat('matching', 'min_similarity_score', 0.55)
MIN_ORB_MATCHES = _getint('matching', 'min_orb_matches', 8)

SCORE_GAP_HIGH_CONFIDENCE = _getfloat('matching', 'score_gap_high', 0.15)
SCORE_GAP_MEDIUM_CONFIDENCE = _getfloat('matching', 'score_gap_medium', 0.08)

ORB_LOWE_RATIO = _getfloat('matching', 'orb_lowe_ratio', 0.75)
RANSAC_REPROJ_THRESHOLD = _getfloat('matching', 'ransac_reproj_threshold', 5.0)
MIN_RANSAC_INLIERS = _getint('matching', 'min_ransac_inliers', 8)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FAISS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FAISS_USE_IVF = _getboolean('faiss', 'use_ivf', True)
FAISS_IVF_NLIST = _getint('faiss', 'ivf_nlist', 100)
FAISS_IVF_NPROBE = _getint('faiss', 'ivf_nprobe', 12)
FAISS_LAZY_LOAD = _getboolean('faiss', 'lazy_load', True)
FAISS_PRELOAD_CURRENT = _getboolean('faiss', 'preload_current', True)
FAISS_MAX_LOADED_PARTITIONS = _getint('faiss', 'max_loaded_partitions', 3)
FAISS_PARTITION_TTL_HOURS = _getint('faiss', 'partition_ttl_hours', 20)
FAISS_AUTO_SAVE_INTERVAL = _getint('faiss', 'auto_save_interval', 20)
FAISS_SEARCH_BATCH_SIZE = _getint('faiss', 'search_batch_size', 200)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INGESTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INGESTION_BATCH_SIZE = _getint('ingestion', 'batch_size', 100)
INGESTION_WORKER_THREADS = _getint('ingestion', 'worker_threads', 6)
INGESTION_POLL_INTERVAL = _getint('ingestion', 'poll_interval', 10)
INGESTION_LOOKBACK_HOURS = _getint('ingestion', 'lookback_hours', 8)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API_HOST = _get('api', 'host', '0.0.0.0')
API_PORT = _getint('api', 'port', 8899)
API_WORKERS = _getint('api', 'workers', 1)
API_TIMEOUT = _getint('api', 'timeout', 120)
API_RELOAD = _getboolean('api', 'reload', False)
ENABLE_API_KEY_AUTH = _getboolean('api', 'enable_api_key_auth', False)
API_RATE_LIMIT = _get('api', 'rate_limit', '100/minute')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CACHE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENABLE_CACHE = _getboolean('cache', 'enable', True)
CACHE_TTL = _getint('cache', 'ttl', 600)
CACHE_MAX_SIZE = _getint('cache', 'max_size', 1000)
REDIS_HOST = _get('cache', 'redis_host', 'localhost')
REDIS_PORT = _getint('cache', 'redis_port', 6379)
REDIS_DB = _getint('cache', 'redis_db', 0)
REDIS_MAX_CONNECTIONS = _getint('cache', 'redis_max_connections', 50)
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOG_LEVEL = _get('logging', 'level', 'INFO')
LOG_FORMAT = _get('logging', 'format', '%(asctime)s | %(levelname)-8s | %(process)d:%(threadName)s | %(name)s | %(message)s')
LOG_DATE_FORMAT = _get('logging', 'date_format', '%Y-%m-%d %H:%M:%S')
LOG_MAX_SIZE_MB = _getint('logging', 'max_size_mb', 100)
LOG_BACKUP_COUNT = _getint('logging', 'backup_count', 7)

# Data subdirectories
ENTRY_TRACK_DIR = DATA_DIR / 'entry_track'
MATCH_RESULTS_DIR = DATA_DIR / 'match_results'
LAST_FETCHED_TIME_FILE = DATA_DIR / 'last_fetched_time.txt'

# Log files
LOG_API = LOGS_DIR / 'api.log'
LOG_INGESTION = LOGS_DIR / 'ingestion.log'
LOG_MATCHING = LOGS_DIR / 'matching.log'
LOG_EMBEDDING = LOGS_DIR / 'embedding.log'

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COLOR HISTOGRAM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COLOR_HIST_H_BINS = 32
COLOR_HIST_S_BINS = 8
COLOR_HIST_V_BINS = 8
COLOR_FEATURE_DIM = COLOR_HIST_H_BINS * COLOR_HIST_S_BINS * COLOR_HIST_V_BINS  # 2048

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CIRCUIT BREAKER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 60

# MODELS_DIR for model loading
MODELS_DIR = BASE_DIR / _get('paths', 'models_dir', 'models')

# Create directories if they don't exist
for directory in [DATA_DIR, LOGS_DIR, VECTOR_DB_DIR, ENTRY_TRACK_DIR, MATCH_RESULTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
