import warnings
warnings.filterwarnings('ignore')

import torch
import torch.nn as nn
import torchvision.transforms as T

# Suppress torchreid Cython warning
import logging
logging.getLogger('torchreid').setLevel(logging.ERROR)

import torchreid
from pathlib import Path
from typing import List, Tuple
import numpy as np
import logging
import cv2
import gc
import threading

from .. import config

logger = logging.getLogger(__name__)


class GeM(nn.Module):
    """Generalized Mean Pooling for robust feature aggregation"""
    def __init__(self, p=3.0, eps=1e-6):
        super(GeM, self).__init__()
        self.p = nn.Parameter(torch.ones(1) * p)
        self.eps = eps

    def forward(self, x):
        return self.gem(x, p=self.p, eps=self.eps)
    
    def gem(self, x, p=3, eps=1e-6):
        return torch.nn.functional.avg_pool2d(x.clamp(min=eps).pow(p), (x.size(-2), x.size(-1))).pow(1./p)


class OpenVINOReIDModel:
    """OpenVINO ReID model for fast CPU inference (thread-safe with thread-local requests)"""
    
    def __init__(self):
        self.model = None
        self.compiled_model = None
        self.input_layer = None
        self.output_layer = None
        self.image_size = config.REID_IMAGE_SIZE
        self._local = threading.local()  # Thread-local storage for parallel execution
        
        self._load_model()
        logger.info(f"[OK] OpenVINO ReID model initialized (size: {self.image_size}x{self.image_size}, thread-local mode)")
    
    def _load_model(self):
        """Load OpenVINO ReID model"""
        try:
            from openvino.runtime import Core
            
            model_path = config.REID_OPENVINO_PATH
            if not model_path.exists():
                raise FileNotFoundError(f"OpenVINO model not found: {model_path}")
            
            # Initialize OpenVINO
            core = Core()
            
            # Load model
            self.model = core.read_model(model=str(model_path))
            
            # Compile model for CPU
            self.compiled_model = core.compile_model(self.model, device_name="CPU")
            
            # Get input/output layers
            self.input_layer = self.compiled_model.input(0)
            self.output_layer = self.compiled_model.output(0)
            
            logger.info(f"[OK] Loaded OpenVINO ReID model from {model_path}")
            logger.info(f"  Input shape: {self.input_layer.partial_shape}")
            logger.info(f"  Output shape: {self.output_layer.partial_shape}")
            
        except ImportError:
            logger.error("OpenVINO not installed. Install with: pip install openvino")
            raise
        except Exception as e:
            logger.error(f"Failed to load OpenVINO ReID model: {e}")
            raise
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for OpenVINO ReID model
        
        Args:
            image: BGR image (H, W, 3)
        
        Returns:
            Preprocessed image (1, 3, H, W) NCHW format
        """
        # Resize to model input size
        img_resized = cv2.resize(image, (self.image_size, self.image_size))
        
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        
        # Normalize (ImageNet stats)
        img_float = img_rgb.astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_normalized = (img_float - mean) / std
        
        # Convert to NCHW (batch, channels, height, width)
        img_transposed = img_normalized.transpose(2, 0, 1)  # HWC -> CHW
        img_batch = np.expand_dims(img_transposed, axis=0)  # Add batch dimension
        
        return img_batch
    
    def _get_infer_request(self):
        """Get thread-local inference request for parallel execution"""
        if not hasattr(self._local, 'infer_request'):
            self._local.infer_request = self.compiled_model.create_infer_request()
        return self._local.infer_request
    
    def extract_features(self, image: np.ndarray) -> np.ndarray:
        """
        Extract 512-D ReID features from vehicle image (thread-safe with parallel execution)
        
        Args:
            image: BGR image (H, W, 3)
        
        Returns:
            features: 512-D normalized feature vector
        """
        try:
            # Preprocess image
            img_input = self.preprocess(image)
            
            # Thread-local inference (enables parallel execution across threads!)
            infer_request = self._get_infer_request()
            result = infer_request.infer({self.input_layer: img_input})
            features_output = result[self.output_layer]
            
            # Extract features (flatten if needed)
            features = features_output[0]  # Remove batch dimension
            
            if len(features.shape) > 1:
                features = features.flatten()
            
            # Normalize (L2 normalization)
            norm = np.linalg.norm(features)
            if norm > 0:
                features = features / norm
            
            return features.astype(np.float32)
            
        except Exception as e:
            logger.error(f"OpenVINO feature extraction failed: {e}")
            return np.zeros(config.REID_EMBEDDING_DIM, dtype=np.float32)
    
    def extract_batch_features(self, images: List[np.ndarray]) -> np.ndarray:
        """
        Extract features for batch of images
        
        Args:
            images: List of BGR images
        
        Returns:
            features: (N, 512) feature array
        """
        if not images:
            return np.array([])
        
        features_list = []
        for img in images:
            features = self.extract_features(img)
            features_list.append(features)
        
        result = np.array(features_list, dtype=np.float32)
        
        # CRITICAL: Force memory cleanup after batch processing
        del features_list
        gc.collect()
        
        return result


class MultiScaleReIDModel:
    """Multi-scale TorchReID model with GeM pooling"""
    
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.multi_scale = config.REID_MULTI_SCALE
        self.scales = config.REID_SCALES
        
        # Image preprocessing
        self.transform = T.Compose([
            T.ToPILImage(),
            T.Resize((config.REID_IMAGE_SIZE, config.REID_IMAGE_SIZE)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        self._load_model()
        logger.info(f"[OK] TorchReID model initialized on {self.device}")
        logger.info(f"[OK] Multi-scale: {self.multi_scale}, Scales: {self.scales}")
    
    def _load_model(self):
        """Load TorchReID OSNet-AIN model with GeM pooling"""
        try:
            # Load base OSNet-AIN model
            model = torchreid.models.build_model(
                name='osnet_ain_x1_0',
                num_classes=1000,  # ImageNet classes
                loss='softmax',
                pretrained=False
            )
            
            # Load pretrained weights from custom checkpoint
            weight_path = config.REID_CHECKPOINT_PATH
            if weight_path.exists():
                logger.info(f"Loading TorchReID checkpoint from {weight_path}")
                checkpoint = torch.load(weight_path, map_location=self.device)
                if 'state_dict' in checkpoint:
                    model.load_state_dict(checkpoint['state_dict'])
                else:
                    model.load_state_dict(checkpoint)
                logger.info(f"[OK] Loaded custom-trained weights from {weight_path}")
            else:
                logger.warning(f"[WARN] Checkpoint not found: {weight_path}, using random init")
            
            # Replace GAP with GeM pooling
            model.global_avgpool = GeM(p=3.0)
            
            # Set to evaluation mode
            model.eval()
            model.to(self.device)
            
            self.model = model
            
        except Exception as e:
            logger.error(f"Failed to load TorchReID model: {e}")
            raise
    
    def extract_features(self, image: np.ndarray) -> np.ndarray:
        """
        Extract 512-D ReID features from vehicle image
        
        Args:
            image: BGR image (H, W, 3)
        
        Returns:
            features: 512-D normalized feature vector
        """
        try:
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            if self.multi_scale:
                return self._extract_multiscale_features(image_rgb)
            else:
                return self._extract_single_scale_features(image_rgb)
        
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return np.zeros(config.REID_EMBEDDING_DIM, dtype=np.float32)
    
    def _extract_single_scale_features(self, image_rgb: np.ndarray) -> np.ndarray:
        """Extract features at single scale"""
        # Preprocess
        img_tensor = self.transform(image_rgb).unsqueeze(0).to(self.device)
        
        # Extract features
        with torch.no_grad():
            features = self.model(img_tensor)
        
        # Normalize
        features = torch.nn.functional.normalize(features, p=2, dim=1)
        
        return features.cpu().numpy()[0]
    
    def _extract_multiscale_features(self, image_rgb: np.ndarray) -> np.ndarray:
        """Extract features at multiple scales and fuse"""
        all_features = []
        
        for scale in self.scales:
            # Resize image to scale
            h, w = image_rgb.shape[:2]
            new_h, new_w = int(h * scale), int(w * scale)
            scaled_img = cv2.resize(image_rgb, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            # Preprocess
            img_tensor = self.transform(scaled_img).unsqueeze(0).to(self.device)
            
            # Extract features
            with torch.no_grad():
                features = self.model(img_tensor)
            
            all_features.append(features)
        
        # Average fusion
        fused_features = torch.mean(torch.stack(all_features), dim=0)
        
        # Normalize
        fused_features = torch.nn.functional.normalize(fused_features, p=2, dim=1)
        
        return fused_features.cpu().numpy()[0]
    
    def extract_batch_features(self, images: List[np.ndarray]) -> np.ndarray:
        """
        Extract features for batch of images (faster)
        
        Args:
            images: List of BGR images
        
        Returns:
            features: (N, 512) feature array
        """
        if not images:
            return np.array([])
        
        try:
            # Convert all images to RGB and preprocess
            batch_tensors = []
            for img in images:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_tensor = self.transform(img_rgb)
                batch_tensors.append(img_tensor)
            
            # Stack into batch
            batch = torch.stack(batch_tensors).to(self.device)
            
            # Extract features
            with torch.no_grad():
                features = self.model(batch)
            
            # Normalize
            features = torch.nn.functional.normalize(features, p=2, dim=1)
            
            return features.cpu().numpy()
        
        except Exception as e:
            logger.error(f"Batch feature extraction failed: {e}")
            return np.zeros((len(images), config.REID_EMBEDDING_DIM), dtype=np.float32)


# Global model instance
_reid_model = None

def get_reid_model():
    """Get or create global ReID model instance (supports TorchReID and OpenVINO)"""
    global _reid_model
    if _reid_model is None:
        # Choose backend from config
        if config.REID_BACKEND == 'openvino':
            logger.info("Initializing OpenVINO ReID model (fast CPU inference)")
            _reid_model = OpenVINOReIDModel()
        else:
            logger.info("Initializing TorchReID model (GPU/CPU inference)")
            _reid_model = MultiScaleReIDModel()
    return _reid_model
