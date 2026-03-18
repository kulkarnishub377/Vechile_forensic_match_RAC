"""Core module initialization - Lazy imports to avoid slow startup"""

# Do NOT import heavy modules here - use lazy imports via get_* functions
# This prevents 8-9 minute startup times

# Only export the factory functions and classes
__all__ = [
    'get_reid_model',
    'get_vehicle_detector',
    'get_plate_detector',
    'get_ocr_engine',
    'get_embedding_engine',
]


def get_reid_model():
    """Get ReID model (lazy load)"""
    from .reid_models import get_reid_model as _get
    return _get()


def get_vehicle_detector():
    """Get vehicle detector (lazy load)"""
    from .yolo_detector import get_vehicle_detector as _get
    return _get()


def get_plate_detector():
    """Get plate detector (lazy load)"""
    from .yolo_detector import get_plate_detector as _get
    return _get()


def get_ocr_engine():
    """Get OCR engine (lazy load)"""
    from .ocr_engine import get_ocr_engine as _get
    return _get()


def get_embedding_engine():
    """Get embedding engine (lazy load)"""
    from .embedding_engine import get_embedding_engine as _get
    return _get()
