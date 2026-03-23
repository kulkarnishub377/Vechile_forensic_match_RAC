"""
Vehicle Detector Service
YOLO-based vehicle detection with sophisticated core implementation
"""
import cv2
import numpy as np
import logging
from typing import Dict, Optional

from app.core.yolo_detector import get_vehicle_detector

logger = logging.getLogger(__name__)

class VehicleDetector:
    """Detect vehicles in images using sophisticated YOLO detector"""

    def __init__(self):
        self.detector = None
        self.ready = False

    def initialize(self):
        """Load YOLO model using sophisticated core detector"""
        try:
            logger.info("Loading YOLO detector with core implementation...")
            self.detector = get_vehicle_detector()
            self.ready = True
            logger.info("✓ YOLO detector loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO: {str(e)}")
            self.ready = False
            raise

    def detect(self, image_id: str, image_data: bytes) -> Dict:
        """
        Detect vehicles in image using sophisticated detector
        Returns dict with detection results
        """
        try:
            if not self.ready:
                return {"success": False, "error": "Model not initialized"}

            # Decode image from bytes
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                return {"success": False, "error": "Failed to decode image"}

            # Run YOLO detection using core detector
            detections = self.detector.detect(image)

            # Filter for vehicles (class 0 in custom model, or 2,5,7 in COCO)
            vehicles = [d for d in detections if d.get('class', 0) in [0, 2, 5, 7] and d.get('conf', 0) > 0.3]

            if len(vehicles) == 0:
                logger.warning(f"No vehicles detected in {image_id[:8]}...")
                return {"success": False, "error": "No vehicle detected"}

            # Use best detection
            best = max(vehicles, key=lambda x: x.get('conf', 0))
            bbox = best['bbox']
            x1, y1, x2, y2 = map(int, bbox)

            # Add padding and crop
            padding = 20
            h, w = image.shape[:2]
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(w, x2 + padding)
            y2 = min(h, y2 + padding)

            vehicle_region = image[y1:y2, x1:x2]

            logger.info(f"✓ Vehicle detected: {image_id[:8]}... (conf: {best['conf']:.2f})")

            return {
                "success": True,
                "vehicle_region": vehicle_region,
                "confidence": best['conf'],
                "bbox": [x1, y1, x2, y2],
                "original_image": image
            }

        except Exception as e:
            logger.error(f"Detection error: {str(e)}")
            return {"success": False, "error": str(e)}
