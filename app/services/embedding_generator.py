"""
Embedding Generator Service
OSNet-AIN 512-dimensional embedding generation with TorchReID auto-download
"""
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import cv2
import numpy as np
import logging
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generate 512-D embeddings using TorchReID OSNet-AIN with auto-download"""

    def __init__(self):
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.transform = None
        self.ready = False

    def initialize(self):
        """Load OSNet-AIN model with auto-download"""
        try:
            logger.info("Loading OSNet-AIN with TorchReID auto-download...")

            # Import TorchReID
            import torchreid

            # Auto-download OSNet-AIN model
            self.model = torchreid.models.build_model(
                name='osnet_ain_x1_0',
                num_classes=1000,  # ImageNet pretraining
                pretrained=True
            )

            self.model.to(self.device)
            self.model.eval()

            # Setup transforms
            self.transform = transforms.Compose([
                transforms.Resize((256, 128)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])

            self.ready = True
            logger.info("OSNet-AIN embedder ready")

        except Exception as e:
            logger.error(f"Failed to load OSNet: {str(e)}")
            self.ready = False
            raise

    def generate(self, image_id: str, vehicle_region: np.ndarray) -> Optional[np.ndarray]:
        """
        Generate 512-D embedding from vehicle region
        Returns normalized embedding
        """
        try:
            if not self.ready:
                logger.error("Model not initialized")
                return None

            if vehicle_region is None or vehicle_region.size == 0:
                logger.error(f"Invalid vehicle region: {image_id[:8]}...")
                return None

            # Convert BGR to RGB
            vehicle_rgb = cv2.cvtColor(vehicle_region, cv2.COLOR_BGR2RGB)

            # Convert to PIL
            pil_image = Image.fromarray(vehicle_rgb)

            # Transform
            tensor = self.transform(pil_image).unsqueeze(0)
            tensor = tensor.to(self.device)

            # Generate embedding
            with torch.no_grad():
                features = self.model(tensor)

            # Convert to numpy and normalize
            embedding = features.cpu().numpy()[0]
            embedding = embedding / (np.linalg.norm(embedding) + 1e-12)

            logger.info(f"Embedding generated: {image_id[:8]}... (dim: {embedding.shape[0]})")
            return embedding

        except Exception as e:
            logger.error(f"Embedding generation error: {str(e)}")
            return None