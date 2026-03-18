import cv2
import numpy as np
import logging
import multiprocessing
import re
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Indian state codes for validation
STATE_CODES = {
    "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD", "DL", "DN",
    "GA", "GJ", "HP", "HR", "JH", "JK", "KA", "KL", "LA", "LD",
    "MH", "ML", "MN", "MP", "MZ", "NL", "OD", "OR", "PB", "PY",
    "RJ", "SK", "TN", "TR", "TS", "TG", "UK", "UA", "UP", "WB"
}


def reprocess_ocr(ocr_text: str) -> str:
    """OCR post-processing for common Indian plate misreads"""
    try:
        if not ocr_text or len(ocr_text) < 4:
            return ocr_text
        
        ocr = ocr_text.upper().strip()
        
        # Fix: Extra character at start but valid state code at position 1-2
        if len(ocr) >= 10 and ocr[1:3] in STATE_CODES:
            ocr = ocr[1:]
        
        # Fix: Third character O/D confused with 0 in district code
        if len(ocr) >= 9 and ocr[:3].isalpha() and ocr[:2] in STATE_CODES and (ocr[2] == "O" or ocr[2] == "D"):
            ocr = ocr[:2] + "0" + ocr[3:]
        
        # Fix: Third character I/T confused with 1 in district code
        if len(ocr) >= 9 and ocr[:3].isalpha() and ocr[:2] in STATE_CODES and (ocr[2] == "I" or ocr[2] == "T"):
            ocr = ocr[:2] + "1" + ocr[3:]
        
        # Fix: Punjab plates (P8/P0/P9 → PB)
        if ocr[:2] in ["P8", "P0", "P9"]:
            ocr = "PB" + ocr[2:]
        
        # Fix: Haryana plates
        elif ocr[:3] == "HRO":
            ocr = "HR0" + ocr[3:]
        elif ocr[:4] == "HR1O":
            ocr = "HR10" + ocr[4:]
        elif ocr[:4] in ["HRSS", "HR5S", "HRS5"]:
            ocr = "HR55" + ocr[4:]
        
        # Fix: Chandigarh plates
        elif ocr[:3] == "CHO":
            ocr = "CH0" + ocr[3:]
        
        # Fix: Delhi plates (OL/0L/BL → DL)
        elif ocr[:2] in ["OL", "0L", "BL"]:
            ocr = "DL" + ocr[2:]
        elif ocr[:3] in ["DLI", "DLT"]:
            ocr = "DL1" + ocr[3:]
        
        # Fix: Nagaland plates
        elif ocr[:3] == "NLO":
            ocr = "NL0" + ocr[3:]
        
        return ocr
    except:
        return ocr_text


def is_valid_plate_format(ocr_text: str) -> bool:
    """Validate OCR text against Indian plate formats"""
    if not ocr_text or len(ocr_text) < 4:
        return False
    
    ocr_text = ocr_text.upper().strip()
    
    # Standard format: SS DD SSS NNNN
    if re.match(r'^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{1,4}$', ocr_text):
        if ocr_text[:2] in STATE_CODES:
            return True
    
    # New BH format: DDSS DDDD NNNNNNNN
    if re.match(r'^[0-9]{2}[A-Z]{2}[0-9]{4}[0-9]{4,8}$', ocr_text):
        return True
    
    return False


def enhance_plate(plate_img: np.ndarray) -> Optional[np.ndarray]:
    """Simple histogram equalization for better OCR"""
    if plate_img is None or plate_img.size == 0:
        return None
    
    # Convert to grayscale if needed
    if len(plate_img.shape) == 3:
        gray = cv2.cvtColor(plate_img, cv2.COLOR_RGB2GRAY)
    else:
        gray = plate_img
    
    return cv2.equalizeHist(gray)


class OCREngine:
    """Direct PaddleOCR implementation - 5-10x faster than subprocess"""
    
    def __init__(self):
        from app import config
        
        self.enabled = config.ENABLE_OCR
        self.ocr = None
        
        if not self.enabled:
            logger.info("[INFO] OCR is DISABLED in config")
            return
        
        try:
            from paddleocr import PaddleOCR
            
            # Dynamic CPU thread allocation (uses half of available cores)
            cpu_threads = max(1, multiprocessing.cpu_count() // 2)
            
            logger.info("Loading PaddleOCR models (direct mode - fast)...")
            
            self.ocr = PaddleOCR(
                det_model_dir=str(config.OCR_DET_MODEL_DIR),
                rec_model_dir=str(config.OCR_REC_MODEL_DIR),
                rec_char_dict_path=str(config.OCR_DICT_PATH),
                cls_model_dir=str(config.OCR_CLS_MODEL_DIR),
                use_angle_cls=True,
                lang='en',
                use_gpu=False,
                cpu_threads=cpu_threads,
                enable_mkldnn=True,
                show_log=False
            )
            
            logger.info(f"[OK] PaddleOCR loaded (cpu_threads={cpu_threads}, direct mode)")
            
        except ImportError:
            logger.error("PaddleOCR not installed. Install with: pip install paddlepaddle paddleocr")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to load PaddleOCR: {e}")
            self.enabled = False
    
    def extract_text(self, image: np.ndarray, preprocess: bool = True) -> Tuple[str, float]:
        """
        Extract text from plate image using direct PaddleOCR (FAST!)
        
        Args:
            image: Plate crop image (BGR or RGB)
            preprocess: If True, apply histogram equalization
        
        Returns:
            (text, confidence) tuple
        """
        if not self.enabled or self.ocr is None:
            return "", 0.0
        
        if image is None or image.size == 0:
            return "", 0.0
        
        try:
            # Optionally enhance plate
            if preprocess:
                enhanced = enhance_plate(image)
                if enhanced is not None and enhanced.size > 0:
                    # Convert grayscale back to RGB for PaddleOCR
                    image = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
            
            # Direct OCR call - FAST (no subprocess overhead!)
            result = self.ocr.ocr(image, cls=True)
            
            if not result or not result[0]:
                return "", 0.0
            
            # Combine all detected text parts (handles multi-line plates)
            texts = []
            confidences = []
            
            for line in result[0]:
                if line and len(line) >= 2:
                    text_data = line[1]
                    if text_data and len(text_data) >= 2:
                        text = str(text_data[0]) if text_data[0] else ""
                        conf = float(text_data[1]) if text_data[1] else 0.0
                        if text:
                            texts.append(text)
                            confidences.append(conf)
            
            if not texts:
                return "", 0.0
            
            # Join all parts and normalize
            full_text = "".join(texts).upper().replace(" ", "").replace("-", "")
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Post-process common OCR errors
            full_text = reprocess_ocr(full_text)
            
            # Validate format (but keep text even if invalid)
            is_valid = is_valid_plate_format(full_text)
            if not is_valid:
                logger.debug(f"Invalid plate format (keeping): '{full_text}'")
            
            return full_text, avg_conf
            
        except Exception as e:
            logger.warning(f"OCR error: {e}")
            return "", 0.0


# Singleton instance
_ocr_engine = None


def get_ocr_engine() -> OCREngine:
    """Get singleton OCR engine instance"""
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = OCREngine()
    return _ocr_engine
