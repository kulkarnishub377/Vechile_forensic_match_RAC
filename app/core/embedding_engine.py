import cv2
import numpy as np
import time
import os
import gc
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from .. import config
from .yolo_detector import get_vehicle_detector, get_plate_detector
from .reid_models import get_reid_model
from .ocr_engine import get_ocr_engine

logger = logging.getLogger(__name__)


@dataclass
class VehicleEmbedding:
    """Standardized vehicle data structure"""
    reid_embedding: np.ndarray
    ocr_text: str
    ocr_conf: float
    color_hist: np.ndarray
    dominant_color: str
    bbox: List[int]
    vehicle_conf: float
    aspect_ratio: float
    is_grayscale: bool  # NEW: Night/BW camera detection
    gray_confidence: float  # NEW: Grayscale detection confidence


class EmbeddingEngine:
    """Core engine for extracting vehicle features"""
    
    def __init__(self):
        self.vehicle_detector = get_vehicle_detector()
        self.reid_model = get_reid_model()
        self.ocr_engine = get_ocr_engine()
        self.color_names = ['black', 'white', 'silver', 'gray', 'red', 'blue', 'yellow', 'green']
        logger.info("[OK] Embedding Engine initialized")

    def process_image(self, image_path: str) -> Optional[VehicleEmbedding]:
        """Process single image"""
        results = self.process_batch([image_path])
        if results and results[0]:
            return results[0]
        return None

    def process_batch(self, image_paths: List[str]) -> List[Optional[VehicleEmbedding]]:
        """Process batch of images"""
        if not image_paths:
            return []
        
        images = []
        valid_indices = []
        results = [None] * len(image_paths)
        
        for i, path in enumerate(image_paths):
            try:
                if not Path(path).exists():
                    logger.warning(f"Image not found: {path}")
                    continue
                    
                img = cv2.imread(str(path))
                if img is None:
                    logger.warning(f"Failed to load image: {path}")
                    continue
                
                images.append(img)
                valid_indices.append(i)
            except Exception as e:
                logger.error(f"Error loading {path}: {e}")
        
        if not images:
            return results

        all_vehicle_crops = []
        all_metadata = []
        det_count = 0
        
        for i, img in enumerate(images):
            # Detect ALL classes (vehicles AND plates) - YOLO uses low conf for plates
            all_dets = self.vehicle_detector.detect(img)
            # Filter vehicles by higher threshold (plates already detected with low conf)
            vehicle_dets = [d for d in all_dets if d.get('class') == 0 and d.get('conf', 0) >= config.YOLO_VEHICLE_CONF_THRESHOLD]
            
            # Select best detection
            if vehicle_dets:
                vehicle_det = max(vehicle_dets, key=lambda x: x['conf'])
                bbox = vehicle_det['bbox']
                
                # Convert to integers (bbox might be list of floats or numpy array)
                if isinstance(bbox, (list, tuple)):
                    x1, y1, x2, y2 = [int(c) for c in bbox]
                else:
                    x1, y1, x2, y2 = [int(c) for c in bbox.tolist()]
                
                # Clip
                h, w = img.shape[:2]
                x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
                
                if x2 > x1 and y2 > y1:
                    crop = img[y1:y2, x1:x2]
                    if crop.size > 0:
                        all_vehicle_crops.append(crop)
                        all_metadata.append({
                            'bbox': bbox,
                            'conf': vehicle_det['conf'],
                            'original_image': img,  # Full image for plate cropping
                            'all_detections': all_dets  # All detections including plates
                        })
                        det_count += 1
                        continue
            
            # Failure handling
            all_vehicle_crops.append(None)
            all_metadata.append(None)
            
            # DEBUG: Save failed images for review (Limited to last 20)
            self._save_debug_image(img, valid_indices[i])

        logger.info(f"Batch Detection: {det_count}/{len(images)} vehicles found")

        # 3. Batch ReID Feature Extraction
        # Filter None crops for batch processing to save compute
        valid_crops_for_reid = [c for c in all_vehicle_crops if c is not None]
        
        batch_embeddings = []
        if valid_crops_for_reid:
            try:
                # Extract 512-D vectors
                batch_embeddings = self.reid_model.extract_batch_features(valid_crops_for_reid)
            except Exception as e:
                logger.error(f"ReID Batch Extraction Failed: {e}")
                # Fallback to empty list will cause downstream failure gracefully
        
        # 4. Process Individual Results (Combine Embedding + OCR)
        embedding_idx = 0
        
        for i, original_idx in enumerate(valid_indices):
            metadata = all_metadata[i]
            
            if metadata is None:
                # Detection failed
                results[original_idx] = None
                continue
            
            # Get ReID result
            reid_vec = None
            if embedding_idx < len(batch_embeddings):
                reid_vec = batch_embeddings[embedding_idx]
                embedding_idx += 1
            
            if reid_vec is None:
                results[original_idx] = None
                continue
            
            # 5. Perform OCR on PLATE crop (not vehicle crop!)
            vehicle_crop = all_vehicle_crops[i]
            full_image = metadata['original_image']
            vehicle_bbox = metadata['bbox']
            all_detections = metadata['all_detections']
            
            ocr_text, ocr_conf = self._perform_ocr(vehicle_crop, full_image, vehicle_bbox, all_detections)
            
            # 6. Extract Color + Grayscale Detection
            hist, dom_color, is_gray, gray_conf = self._extract_color_and_grayscale(vehicle_crop)
            
            # 7. Aspect Ratio
            h, w = vehicle_crop.shape[:2]
            aspect_ratio = w / h if h > 0 else 0
            
            # Create Result Object
            results[original_idx] = VehicleEmbedding(
                reid_embedding=reid_vec,
                ocr_text=ocr_text,
                ocr_conf=ocr_conf,
                color_hist=hist,
                dominant_color=dom_color,
                bbox=metadata['bbox'],
                vehicle_conf=metadata['conf'],
                aspect_ratio=aspect_ratio,
                is_grayscale=is_gray,
                gray_confidence=gray_conf
            )
        
        # CRITICAL: Force memory cleanup after batch processing
        # This prevents memory fragmentation from accumulating tensor allocations
        del images, all_vehicle_crops, all_metadata, batch_embeddings
        gc.collect()
        
        return results

    def _perform_ocr(self, vehicle_crop: np.ndarray, full_image: np.ndarray, vehicle_bbox: list, all_detections: list) -> Tuple[str, float]:
        """
        Run OCR on license plate crop (NOT vehicle crop)
        
        Args:
            vehicle_crop: Vehicle crop (for fallback if no plate detected)
            full_image: Full original image
            vehicle_bbox: Vehicle bounding box [x1, y1, x2, y2]
            all_detections: All YOLO detections including plates (class 1)
        
        Returns:
            Tuple of (text, confidence)
        """
        if not config.ENABLE_OCR:
            return "", 0.0
            
        try:
            # Find plate detections (class 1) inside this vehicle bbox
            vx1, vy1, vx2, vy2 = [int(c) for c in vehicle_bbox]
            plates_in_vehicle = []
            
            for det in all_detections:
                if det.get('class') == 1:  # Plate class
                    # Check if plate is inside vehicle bbox
                    plate_bbox = det['bbox']
                    px1, py1, px2, py2 = [int(c) for c in plate_bbox]
                    plate_center_x = (px1 + px2) / 2
                    plate_center_y = (py1 + py2) / 2
                    
                    if vx1 <= plate_center_x <= vx2 and vy1 <= plate_center_y <= vy2:
                        plates_in_vehicle.append({
                            'bbox': plate_bbox,
                            'conf': det['conf']
                        })
            
            # Use highest confidence plate
            if plates_in_vehicle:
                best_plate = max(plates_in_vehicle, key=lambda p: p['conf'])
                px1, py1, px2, py2 = [int(c) for c in best_plate['bbox']]
                
                # Clip to image bounds
                h, w = full_image.shape[:2]
                px1, py1 = max(0, px1), max(0, py1)
                px2, py2 = min(w, px2), min(h, py2)
                
                if px2 > px1 and py2 > py1:
                    # Extend bbox by 15px left/right for better OCR context (like reference code)
                    h, w = full_image.shape[:2]
                    px1_ext = max(0, px1 - 15)
                    px2_ext = min(w, px2 + 15)
                    
                    # Crop PLATE from full image with extended context
                    plate_crop = full_image[py1:py2, px1_ext:px2_ext]
                    
                    if plate_crop.size > 0:
                        # Run OCR on plate crop WITH preprocessing for best accuracy
                        text, conf = self.ocr_engine.extract_text(plate_crop, preprocess=True)
                        logger.debug(f"OCR on plate crop: '{text}' (conf: {conf:.2%})")
                        return text, conf
            
            # Fallback: No plate detected - run OCR on vehicle crop WITH preprocessing
            logger.debug("No plate detected in vehicle, running OCR on vehicle crop as fallback")
            text, conf = self.ocr_engine.extract_text(vehicle_crop, preprocess=True)
            return text, conf
            
        except Exception as e:
            logger.warning(f"OCR Failed: {e}")
            return "", 0.0

    def _extract_color_and_grayscale(self, crop: np.ndarray) -> Tuple[np.ndarray, str, bool, float]:
        """Extract color histogram AND detect grayscale/BW (night camera)"""
        try:
            # Resize for speed
            small = cv2.resize(crop, (64, 64))
            
            # Grayscale Detection (CRITICAL for cross-modal matching)
            is_gray, gray_conf = self._is_grayscale(crop)
            
            # HSV Histogram (skip if grayscale)
            if is_gray:
                # Don't compute color histogram for grayscale images
                hist = np.zeros(64)
            else:
                hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
                hist = cv2.calcHist([hsv], [0, 1], None, [8, 8], [0, 180, 0, 256])
                cv2.normalize(hist, hist)
                hist = hist.flatten()
            
            return hist, "unknown", is_gray, gray_conf
        except:
            return np.zeros(64), "unknown", False, 0.0
    
    def _is_grayscale(self, image: np.ndarray) -> Tuple[bool, float]:
        """
        Detect if image is grayscale/BW (night camera)
        
        Returns:
            (is_grayscale, confidence)
        """
        if len(image.shape) < 3:
            return True, 1.0
        
        # Split channels
        r, g, b = image[:,:,0], image[:,:,1], image[:,:,2]
        
        # Compute channel differences
        rg_diff = np.abs(r.astype(float) - g.astype(float)).mean()
        rb_diff = np.abs(r.astype(float) - b.astype(float)).mean()
        gb_diff = np.abs(g.astype(float) - b.astype(float)).mean()
        
        avg_diff = (rg_diff + rb_diff + gb_diff) / 3.0
        
        # Under ~10 avg difference = grayscale
        confidence = 1.0 - min(avg_diff / 20.0, 1.0)
        is_gray = avg_diff < 10.0
        
        if is_gray:
            logger.debug(f"🌙 Grayscale detected: avg_diff={avg_diff:.2f}, conf={confidence:.3f}")
        
        return is_gray, confidence

    def _save_debug_image(self, img, idx):
        """Save failed detection image for debugging"""
        try:
            debug_dir = config.BASE_DIR / 'debug_failures'
            debug_dir.mkdir(exist_ok=True)
            
            # Cleanup old files (keep last 20)
            files = sorted(debug_dir.glob("*.jpg"), key=os.path.getmtime)
            if len(files) > 20:
                for f in files[:-20]:
                    try: os.remove(f)
                    except: pass
            
            timestamp = int(time.time() * 1000)
            cv2.imwrite(str(debug_dir / f"fail_{timestamp}_{idx}.jpg"), img)
            # logger.warning(f"Saved failed detection image to {debug_dir}")
        except:
            pass
            
            
# Factory
_embedding_engine = None

def get_embedding_engine():
    global _embedding_engine
    if _embedding_engine is None:
        _embedding_engine = EmbeddingEngine()
    return _embedding_engine
