import torch
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import logging
import threading

from .. import config

logger = logging.getLogger(__name__)


class VehicleDetector:
    """YOLO vehicle detector with dual backend support and Intelligent Fallback"""
    
    # Class-level lock for thread-safe model loading and inference
    _model_lock = threading.Lock()
    
    def __init__(self, backend: str = 'pytorch'):
        self.backend = backend
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.img_size = 480  # Match reference code (faster than 640)
        # Use config value (0.15 set in config.ini)
        self.conf_threshold = config.YOLO_VEHICLE_CONF_THRESHOLD
        self.iou_threshold = config.YOLO_VEHICLE_IOU_THRESHOLD
        
        with self._model_lock:
            self._load_model()
        logger.info(f"[OK] Vehicle detector initialized ({backend}) | Conf: {self.conf_threshold}")
    
    def _load_model(self):
        """Load YOLO model based on backend"""
        try:
            if self.backend == 'pytorch':
                self._load_pytorch_model()
            elif self.backend == 'openvino':
                self._load_openvino_model()
            else:
                raise ValueError(f"Unsupported backend: {self.backend}")
        except Exception as e:
            logger.error(f"Failed to load vehicle detector: {e}")
            raise
    
    def _load_pytorch_model(self):
        """Load PyTorch YOLO model directly from local file"""
        model_path = config.YOLO_PYTORCH_MODEL
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        try:
            # Load model directly without torch.hub (no internet needed)
            from ultralytics import YOLO
            self.model = YOLO(str(model_path))
            logger.info(f"[OK] Loaded PyTorch YOLOv5 model from {model_path}")
        except ImportError:
            # Fallback to torch.hub if ultralytics not available
            logger.warning("Ultralytics not found, using torch.hub (requires internet)")
            self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(model_path))
            self.model.to(self.device)
            self.model.conf = self.conf_threshold
            self.model.iou = self.iou_threshold
            logger.info(f"[OK] Loaded PyTorch model from {model_path}")
    
    def _load_openvino_model(self):
        """Load OpenVINO model using Ultralytics (same as reference implementation)"""
        try:
            from ultralytics import YOLO
            
            # Reference uses the FOLDER path, not the .xml file
            # Ultralytics auto-detects OpenVINO format and uses optimized inference
            model_path = config.YOLO_OPENVINO_MODEL.parent  # Get folder, not .xml
            
            if not model_path.exists():
                logger.warning(f"OpenVINO model folder not found: {model_path}, falling back to PyTorch")
                self.backend = 'pytorch'
                self._load_pytorch_model()
                return
            
            # Load with Ultralytics - it automatically uses OpenVINO backend!
            # This is the same approach as the reference preprocessor.py
            self.model = YOLO(str(model_path))
            self.img_size = 480  # Match reference
            
            logger.info(f"[OK] Loaded OpenVINO YOLO from {model_path}")
            logger.info(f"  Using Ultralytics OpenVINO backend (fast CPU inference)")
        
        except ImportError:
            logger.warning("Ultralytics not available, falling back to PyTorch")
            self.backend = 'pytorch'
            self._load_pytorch_model()
    
    def detect(self, image: np.ndarray) -> List[Dict]:
        """Detect vehicles in image (thread-safe)"""
        with self._model_lock:
            # Both PyTorch and OpenVINO now use Ultralytics, so same detection code
            return self._detect_ultralytics(image)
    
    def _detect_ultralytics(self, image: np.ndarray) -> List[Dict]:
        """Ultralytics YOLO inference (works with both PyTorch and OpenVINO backends)"""
        try:
            # Try ultralytics YOLO format first with PERFORMANCE OPTIMIZATIONS from reference
            # CRITICAL: Use LOW confidence (0.10) to detect plates (small objects)
            # We filter vehicles with higher threshold later, but plates need low conf
            results = self.model(
                image, 
                conf=0.10,           # LOW conf to detect plates! (filter vehicles later)
                iou=0.4,             # Tighter NMS (matches reference)
                imgsz=self.img_size,
                half=True,           # FP16 precision - 2x speed boost!
                max_det=30,          # Limit detections for speed
                agnostic_nms=True,   # Class-agnostic NMS - faster
                verbose=False
            )
            detections = []
            
            # Extract detections from ultralytics format
            for result in results:
                boxes = result.boxes
                for i in range(len(boxes)):
                    box = boxes.xyxy[i].cpu().numpy()
                    conf = float(boxes.conf[i])
                    cls = int(boxes.cls[i])
                    
                    detections.append({
                        'bbox': box.tolist(),
                        'conf': conf,  # Use 'conf' key for consistency
                        'class': cls
                    })
            
            return detections
            
        except AttributeError:
            # Fallback to torch.hub format
            results = self.model(image)
            detections = []
            
            for *box, conf, cls in results.xyxy[0].cpu().numpy():
                detections.append({
                    'bbox': box,
                    'conf': float(conf),  # Use 'conf' key for consistency
                    'class': int(cls)
                })
            
            return detections
    
    def _detect_openvino(self, image: np.ndarray) -> List[Dict]:
        """OpenVINO inference with Direct Resize (No Letterbox)"""
        # Preprocess
        img_resized = cv2.resize(image, (self.img_size, self.img_size))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_norm = img_rgb.astype(np.float32) / 255.0
        img_input = np.transpose(img_norm, (2, 0, 1))[np.newaxis, ...]
        
        # Inference
        output = self.model([img_input])[self.output_layer]
        
        # Post-process
        return self._postprocess_openvino(output, image.shape[:2])
    
    def _postprocess_openvino(self, output, original_shape) -> List[Dict]:
        """Post-process OpenVINO output with Intelligent Fallback"""
        detections = []
        plates = []
        h_orig, w_orig = original_shape
        
        for det in output[0]:
            if len(det) >= 6:
                x1, y1, x2, y2, conf, cls = det[:6]
                cls = int(cls)
                
                # Scale to original image
                x1 = int(x1 * w_orig / self.img_size)
                y1 = int(y1 * h_orig / self.img_size)
                x2 = int(x2 * w_orig / self.img_size)
                y2 = int(y2 * h_orig / self.img_size)
                
                # Clip to image bounds
                x1 = max(0, min(x1, w_orig))
                y1 = max(0, min(y1, h_orig))
                x2 = max(0, min(x2, w_orig))
                y2 = max(0, min(y2, h_orig))
                
                if x2 <= x1 or y2 <= y1:
                    continue

                if cls == 0 and conf > self.conf_threshold:
                    detections.append({
                        'bbox': [x1, y1, x2, y2],
                        'conf': float(conf),
                        'class': 0
                    })
                elif cls == 1 and conf > 0.2:  # Keep plate detections (threshold 0.2)
                    plates.append({
                        'bbox': [x1, y1, x2, y2],
                        'conf': float(conf)
                    })
        
        # Fallback: using plate to infer vehicle if no vehicle found
        if not detections and plates:
            return self._apply_fallback(plates, original_shape)
            
        return detections

    def _apply_fallback(self, plates: List[Dict], shape: Tuple[int, int]) -> List[Dict]:
        """Infer vehicle bounding box from plate"""
        h_orig, w_orig = shape
        best_plate = max(plates, key=lambda x: x['conf'])
        px1, py1, px2, py2 = best_plate['bbox']
        
        # Heuristic: Vehicle is roughly 4x plate width, 6x plate height
        w_plate = px2 - px1
        h_plate = py2 - py1
        
        w_vehicle = w_plate * 4
        h_vehicle = h_plate * 6
        
        # Center of plate
        cx = (px1 + px2) / 2
        
        # Estimate vehicle box
        vx1 = int(cx - w_vehicle / 2)
        vx2 = int(cx + w_vehicle / 2)
        vy2 = int(py2 + h_plate * 1.5) # Bottom slightly below plate
        vy1 = int(vy2 - h_vehicle)
        
        # Clip
        vx1 = max(0, min(vx1, w_orig))
        vx2 = max(0, min(vx2, w_orig))
        vy1 = max(0, min(vy1, h_orig))
        vy2 = max(0, min(vy2, h_orig))
        
        # Only log if confident logic works
        # logger.warning(f"Fallback: Inferred vehicle detection from plate (conf={best_plate['conf']:.2f})")
        
        return [{
            'bbox': [vx1, vy1, vx2, vy2],
            'conf': float(best_plate['conf']),
            'class': 0  # Treat as vehicle
        }]


class PlateDetector:
    """Dedicated Plate Detector (Class 1)"""
    
    def __init__(self, backend: str = 'openvino'):
        self.backend = backend
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.img_size = 480
        self.conf_threshold = config.YOLO_PLATE_CONF_THRESHOLD
        self.plate_class_id = 1
        
        self._load_model()
        logger.info(f"[OK] Plate detector initialized ({backend})")
    
    def _load_model(self):
        """Use same loading logic as VehicleDetector"""
        try:
            if self.backend == 'pytorch':
                self._load_pytorch_model()
            elif self.backend == 'openvino':
                self._load_openvino_model()
            else:
                raise ValueError(f"Unsupported backend: {self.backend}")
        except Exception as e:
            logger.error(f"Failed to load plate detector: {e}")
            raise

    def _load_pytorch_model(self):
        model_path = config.YOLO_PYTORCH_MODEL
        if not model_path.exists(): return
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(model_path))
        self.model.to(self.device)
        self.model.conf = self.conf_threshold
        
    def _load_openvino_model(self):
        try:
            from openvino.runtime import Core
            model_xml = config.YOLO_OPENVINO_MODEL
            if not model_xml.exists():
                self.backend = 'pytorch'
                self._load_pytorch_model()
                return
            
            ie = Core()
            self.model = ie.compile_model(model=str(model_xml), device_name='CPU')
            self.input_layer = self.model.input(0)
            self.output_layer = self.model.output(0)
            
            input_shape = self.input_layer.partial_shape
            if len(input_shape) >= 4:
                height_dim = input_shape[2]
                self.img_size = height_dim.get_length() if hasattr(height_dim, 'get_length') else int(str(height_dim))
        except ImportError:
            self.backend = 'pytorch'
            self._load_pytorch_model()

    def detect(self, image: np.ndarray) -> List[Dict]:
        if self.base_model_detect(image):
             return self.base_model_detect(image)
        return []

    # Simplified reuse to avoid code duplication - but explicit here for clarity
    def detect(self, image: np.ndarray) -> List[Dict]:
        if self.model is None: return []
        
        if self.backend == 'pytorch':
            results = self.model(image)
            detections = []
            for *box, conf, cls in results.xyxy[0].cpu().numpy():
                if int(cls) == self.plate_class_id:
                    detections.append({'bbox': [int(x) for x in box], 'conf': float(conf)})
            return detections
        else:
            # OpenVINO
            img_resized = cv2.resize(image, (self.img_size, self.img_size))
            img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
            img_norm = img_rgb.astype(np.float32) / 255.0
            img_input = np.transpose(img_norm, (2, 0, 1))[np.newaxis, ...]
            
            output = self.model([img_input])[self.output_layer]
            
            detections = []
            h_orig, w_orig = image.shape[:2]
            for det in output[0]:
                if len(det) >= 6:
                    x1, y1, x2, y2, conf, cls = det[:6]
                    if int(cls) == self.plate_class_id and conf > self.conf_threshold:
                         detections.append({
                            'bbox': [
                                int(max(0, x1 * w_orig / self.img_size)),
                                int(max(0, y1 * h_orig / self.img_size)),
                                int(min(w_orig, x2 * w_orig / self.img_size)),
                                int(min(h_orig, y2 * h_orig / self.img_size))
                            ],
                            'conf': float(conf)
                        })
            return detections


# Global instances
_vehicle_detector = None
_plate_detector = None

def get_vehicle_detector() -> VehicleDetector:
    global _vehicle_detector
    if _vehicle_detector is None:
        _vehicle_detector = VehicleDetector(backend=config.YOLO_BACKEND)
    return _vehicle_detector

def get_plate_detector() -> PlateDetector:
    global _plate_detector
    if _plate_detector is None:
        _plate_detector = PlateDetector(backend=config.YOLO_BACKEND)
    return _plate_detector
