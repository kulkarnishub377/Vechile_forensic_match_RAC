"""
Run ingestion service
Fetches ENTRY vehicles from database and builds FAISS index
"""
import sys
import warnings
import os
import logging as _logging
from pathlib import Path

# ============================================================================
# CRITICAL: Set MKL environment variables BEFORE any imports
# This prevents conflicts between PyTorch and PaddlePaddle
# ============================================================================
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['KMP_INIT_AT_FORK'] = 'FALSE'

# Suppress ALL warnings before any imports
warnings.filterwarnings('ignore')
os.environ['PPOCR_LOG_LEVEL'] = 'ERROR'

# Suppress ppocr and PaddleOCR loggers
_logging.getLogger('ppocr').setLevel(_logging.ERROR)
_logging.getLogger('PaddleOCR').setLevel(_logging.ERROR)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

import logging
from app.services.ingestion_service import get_ingestion_service
from app import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOGS_DIR / 'ingestion.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Run ingestion service"""
    logger.info("=" * 60)
    logger.info("[INFO] Starting Ingestion Service")
    logger.info("=" * 60)
    
    # PRE-INITIALIZE OCR BEFORE YOLO TO AVOID CONFLICTS
    logger.info("[STEP 1/3] Pre-initializing OCR engine...")
    try:
        from app.core.ocr_engine import get_ocr_engine
        ocr_engine = get_ocr_engine()
        if ocr_engine.enabled:
            logger.info("[WAIT] Triggering OCR initialization BEFORE YOLO loads...")
            # Force OCR to initialize now (before YOLO)
            import numpy as np
            dummy_img = np.zeros((50, 100, 3), dtype=np.uint8)
            ocr_engine.extract_text(dummy_img, preprocess=False)
            if ocr_engine.ocr_ready:
                logger.info("[OK] OCR initialized successfully!")
            else:
                logger.warning("[WARN] OCR initialization failed - will continue without OCR")
        else:
            logger.info("[INFO] OCR is disabled in config")
    except Exception as e:
        logger.warning(f"[WARN] OCR pre-initialization failed: {e}")
        logger.warning("[WARN] Will continue without OCR")
    
    logger.info("[STEP 2/3] Initializing ingestion service (YOLO, ReID, FAISS)...")
    
    try:
        # Get ingestion service (this loads YOLO and ReID)
        ingestion_service = get_ingestion_service()
        
        logger.info("[STEP 3/3] Starting continuous ingestion...")
        logger.info("Starting continuous ingestion...")
        logger.info("Press Ctrl+C to stop")
        
        ingestion_service.run()
    
    except KeyboardInterrupt:
        logger.info("\n[WARN] Ingestion stopped by user")
    except Exception as e:
        logger.error(f"[FAIL] Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
