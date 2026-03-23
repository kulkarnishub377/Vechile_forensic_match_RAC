"""
Vehicle Detector Service
Simple wrapper using Ultralytics YOLO with auto-download
"""
import cv2
import numpy as np
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class VehicleDetector:
    """Simple vehicle detector using Ultralytics YOLO"""

    def __init__(self):
        self.model = None
        self.ready = False
        # Vehicle classes in COCO dataset
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck

    def initialize(self):
        """Load YOLO model with auto-download"""
        try:
            logger.info("Loading YOLO with auto-download...")

            # Import here to avoid startup delays
            from ultralytics import YOLO

            # Auto-download YOLOv8n (3MB, very fast)
            self.model = YOLO('yolov8n.pt')
            self.ready = True

            logger.info("YOLO detector ready")

        except Exception as e:
            logger.error(f"Failed to load YOLO: {str(e)}")
            self.ready = False
            raise

    def detect(self, image_id: str, image_data: bytes) -> Dict[str, Any]:
        """
        Detect vehicles in image
        Returns: {"success": bool, "vehicle_region": np.ndarray, "confidence": float}
        """
        try:
            if not self.ready:
                return {"success": False, "error": "Model not loaded"}

            # Convert bytes to image
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                return {"success": False, "error": "Invalid image"}

            # Run YOLO detection
            results = self.model(image, verbose=False)

            best_vehicle = None
            best_confidence = 0.0

            # Find best vehicle detection
            for r in results:
                boxes = r.boxes
                if boxes is not None:
                    for i in range(len(boxes)):
                        cls = int(boxes.cls[i])
                        conf = float(boxes.conf[i])

                        # Check if it's a vehicle class
                        if cls in self.vehicle_classes and conf > best_confidence:
                            x1, y1, x2, y2 = boxes.xyxy[i].cpu().numpy().astype(int)

                            # Extract vehicle region with padding
                            padding = 10
                            h, w = image.shape[:2]
                            x1 = max(0, x1 - padding)
                            y1 = max(0, y1 - padding)
                            x2 = min(w, x2 + padding)
                            y2 = min(h, y2 + padding)

                            vehicle_region = image[y1:y2, x1:x2]

                            if vehicle_region.size > 0:
                                best_vehicle = vehicle_region
                                best_confidence = conf

            if best_vehicle is not None:
                return {
                    "success": True,
                    "vehicle_region": best_vehicle,
                    "confidence": round(best_confidence, 3)
                }
            else:
                return {"success": False, "error": "No vehicle detected"}

        except Exception as e:
            logger.error(f"Detection error for {image_id}: {str(e)}")
            return {"success": False, "error": str(e)}