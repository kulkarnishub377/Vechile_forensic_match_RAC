"""
Vehicle Detector Service
YOLO-based vehicle detection
"""
import torch
import cv2
import numpy as np
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class VehicleDetector:
    """Detect vehicles in images using YOLOv5"""
    
    def __init__(self):
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.ready = False
    
    def initialize(self):
        """Load YOLO model"""
        try:
            logger.info(f"Loading YOLOv5 on device: {self.device}")
            self.model = torch.hub.load(
                'ultralytics/yolov5',
                'yolov5n',
                pretrained=True
            )
            self.model.to(self.device)
            self.model.conf = 0.5
            self.ready = True
            logger.info("✓ YOLOv5 loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO: {str(e)}")
            self.ready = False
            raise
    
    def detect(self, image_id: str, image_data: bytes) -> Dict:
        """
        Detect vehicles in image
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
            
            # Run YOLO inference
            results = self.model(image)
            
            # Extract vehicle detections (COCO: car=2, truck=7, bus=5)
            detections = []
            for *box, conf, cls in results.xyxy[0]:
                if int(cls) in [2, 5, 7]:  # vehicle classes
                    detections.append({
                        "box": [float(x) for x in box],
                        "confidence": float(conf),
                        "class": int(cls)
                    })
            
            if len(detections) == 0:
                logger.warning(f"No vehicles detected in {image_id[:8]}...")
                return {"success": False, "error": "No vehicle detected"}
            
            # Use best detection
            best = max(detections, key=lambda x: x["confidence"])
            x1, y1, x2, y2 = map(int, best["box"])
            
            # Add padding and crop
            padding = 20
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(image.shape[1], x2 + padding)
            y2 = min(image.shape[0], y2 + padding)
            
            vehicle_region = image[y1:y2, x1:x2]
            
            logger.info(f"✓ Vehicle detected: {image_id[:8]}... (conf: {best['confidence']:.2f})")
            
            return {
                "success": True,
                "vehicle_region": vehicle_region,
                "confidence": best["confidence"],
                "bbox": [x1, y1, x2, y2],
                "original_image": image
            }
        
        except Exception as e:
            logger.error(f"Detection error: {str(e)}")
            return {"success": False, "error": str(e)}
