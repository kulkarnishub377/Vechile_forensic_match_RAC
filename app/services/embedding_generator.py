"""
Embedding Generator Service
OSNet-AIN 512-dimensional embedding generation with sophisticated core implementation
"""
import cv2
import numpy as np
import logging
from typing import Optional

from app.core.reid_models import get_reid_model

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generate 512-D embeddings using sophisticated OSNet-AIN implementation"""

    def __init__(self):
        self.model = None
        self.ready = False

    def initialize(self):
        """Load OSNet-AIN model using sophisticated core implementation"""
        try:
            logger.info("Loading OSNet-AIN with core implementation (supports TorchReID + OpenVINO)...")
            self.model = get_reid_model()
            self.ready = True
            logger.info("✓ OSNet-AIN loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load OSNet: {str(e)}")
            self.ready = False
            raise

    def generate(self, image_id: str, vehicle_region: np.ndarray) -> Optional[np.ndarray]:
        """
        Generate 512-D embedding from vehicle region using sophisticated core model
        Returns normalized embedding
        """
        try:
            if not self.ready:
                logger.error("Model not initialized")
                return None

            if vehicle_region is None or vehicle_region.size == 0:
                logger.error(f"Invalid vehicle region: {image_id[:8]}...")
                return None

            # Use sophisticated core model to extract features
            embedding = self.model.extract_features(vehicle_region)

            if embedding is None or len(embedding) == 0:
                logger.error(f"Failed to generate embedding for {image_id[:8]}...")
                return None

            # Ensure normalized
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            logger.info(f"✓ Embedding generated: {image_id[:8]}... (dim: {embedding.shape[0]})")
            return embedding

        except Exception as e:
            logger.error(f"Embedding generation error: {str(e)}")
            return None
