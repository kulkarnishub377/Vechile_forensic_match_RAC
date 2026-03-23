"""
Configuration Module - Vehicle Re-ID System (No Database)
Clean, environment-based configuration for all services
"""

import os
import logging
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════
# BASE PATHS
# ═══════════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
MODELS_DIR = BASE_DIR / "models"
TEMP_DIR = BASE_DIR / "temp"

# Create directories
TEMP_DIR.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════
# SYSTEM & LOGGING
# ═══════════════════════════════════════════════════════════════════════

SYSTEM_NAME = "Vehicle Re-Identification System"
SYSTEM_VERSION = "2.0.0"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ═══════════════════════════════════════════════════════════════════════
# API SERVER
# ═══════════════════════════════════════════════════════════════════════

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
API_WORKERS = int(os.getenv("API_WORKERS", 4))

# ═══════════════════════════════════════════════════════════════════════
# SESSION CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

MAX_SESSIONS = 100
MAX_IMAGES_PER_SESSION = 100
MAX_SESSION_DURATION_HOURS = 24
SESSION_CLEANUP_INTERVAL_MINUTES = 60

# ═══════════════════════════════════════════════════════════════════════
# FILE UPLOAD
# ═══════════════════════════════════════════════════════════════════════

MAX_FILE_SIZE_MB = 50
SUPPORTED_FORMATS = ["jpg", "jpeg", "png", "bmp", "webp"]
SUPPORTED_FORMATS_MIME = [
    "image/jpeg",
    "image/png",
    "image/bmp",
    "image/webp"
]

# ═══════════════════════════════════════════════════════════════════════
# ML MODELS
# ═══════════════════════════════════════════════════════════════════════

# YOLO Detection - Core Module Configuration
YOLO_BACKEND = os.getenv("YOLO_BACKEND", "pytorch")  # pytorch or openvino
YOLO_MODEL = os.getenv("YOLO_MODEL", "yolov5n")
YOLO_CONF_THRESHOLD = float(os.getenv("YOLO_CONF_THRESHOLD", 0.5))
YOLO_IOU_THRESHOLD = float(os.getenv("YOLO_IOU_THRESHOLD", 0.4))
YOLO_MAX_DET = int(os.getenv("YOLO_MAX_DET", 10))

# Vehicle-specific YOLO thresholds (for core module compatibility)
YOLO_VEHICLE_CONF_THRESHOLD = float(os.getenv("YOLO_VEHICLE_CONF_THRESHOLD", 0.3))
YOLO_VEHICLE_IOU_THRESHOLD = float(os.getenv("YOLO_VEHICLE_IOU_THRESHOLD", 0.4))

# Model paths (for core module compatibility)
YOLO_PYTORCH_MODEL = MODELS_DIR / "yolov5n.pt"
YOLO_OPENVINO_MODEL_XML = MODELS_DIR / "yolov5n.xml"
YOLO_OPENVINO_MODEL_BIN = MODELS_DIR / "yolov5n.bin"

# OSNet ReID - Core Module Configuration
OSNET_MODEL = os.getenv("OSNET_MODEL", "osnet_ain_x1_0")
OSNET_BACKEND = os.getenv("OSNET_BACKEND", "pytorch")  # pytorch or openvino
OSNET_EMBEDDING_DIM = int(os.getenv("OSNET_EMBEDDING_DIM", 512))
OSNET_IMG_SIZE = (256, 128)

# ReID model paths (for core module compatibility)
REID_PYTORCH_MODEL = MODELS_DIR / "osnet_ain_x1_0.pth"
REID_OPENVINO_MODEL_XML = MODELS_DIR / "osnet_ain_x1_0.xml"
REID_OPENVINO_MODEL_BIN = MODELS_DIR / "osnet_ain_x1_0.bin"

# FAISS Search
FAISS_USE_GPU = os.getenv("FAISS_USE_GPU", "false").lower() == "true"
FAISS_DISTANCE_METRIC = os.getenv("FAISS_DISTANCE_METRIC", "l2")  # l2 or cosine
FAISS_TOP_K = int(os.getenv("FAISS_TOP_K", 50))

# ═══════════════════════════════════════════════════════════════════════
# MATCHING ALGORITHM
# ═══════════════════════════════════════════════════════════════════════

MATCH_CONFIDENCE_THRESHOLD = float(os.getenv("MATCH_CONFIDENCE_THRESHOLD", 0.85))
MATCH_CONFIDENT_LEVEL = float(os.getenv("MATCH_CONFIDENT_LEVEL", 0.92))
MATCH_PROBABLE_LEVEL = float(os.getenv("MATCH_PROBABLE_LEVEL", 0.85))

# ═══════════════════════════════════════════════════════════════════════
# PROCESSING TIMEOUTS
# ═══════════════════════════════════════════════════════════════════════

DETECTION_TIMEOUT_SECONDS = int(os.getenv("DETECTION_TIMEOUT_SECONDS", 30))
EMBEDDING_TIMEOUT_SECONDS = int(os.getenv("EMBEDDING_TIMEOUT_SECONDS", 30))
SEARCH_TIMEOUT_SECONDS = int(os.getenv("SEARCH_TIMEOUT_SECONDS", 10))

# ═══════════════════════════════════════════════════════════════════════
# PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════

ENABLE_GPU = os.getenv("ENABLE_GPU", "false").lower() == "true"
NUM_WORKERS = int(os.getenv("NUM_WORKERS", 4))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 1))

# ═══════════════════════════════════════════════════════════════════════
# NOTE: NO DATABASE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════
# This is a stateless, in-memory system
# - Images stored in RAM (session-based)
# - Embeddings in FAISS in-memory index
# - No persistent database required
# - Results temporary per session
# - Perfect for testing and real-time matching

print(f"✓ Configuration loaded: {SYSTEM_NAME} v{SYSTEM_VERSION}")
