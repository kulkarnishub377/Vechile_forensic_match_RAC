"""
Embedding Generator Service
OSNet-AIN 512-dimensional embedding generation
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
    """Generate 512-D embeddings using OSNet-AIN"""
    
    def __init__(self):
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.transform = None
        self.ready = False
    
    def initialize(self):
        """Load OSNet-AIN model"""
        try:
            logger.info(f"Loading OSNet-AIN on device: {self.device}")
            
            # Simple OSNet implementation
            # In production, you'd load the actual pretrained model
            self.model = self._create_simple_osnet()
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
            logger.info("✓ OSNet-AIN loaded successfully")
        
        except Exception as e:
            logger.error(f"Failed to load OSNet: {str(e)}")
            self.ready = False
            raise
    
    def _create_simple_osnet(self) -> nn.Module:
        """
        Create a simple OSNet-like model for demo
        In production, load actual pretrained weights
        """
        class SimpleOSNet(nn.Module):
            def __init__(self):
                super().__init__()
                self.backbone = nn.Sequential(
                    nn.Conv2d(3, 64, 3, padding=1),
                    nn.ReLU(),
                    nn.Conv2d(64, 128, 3, padding=1),
                    nn.ReLU(),
                    nn.AdaptiveAvgPool2d((1, 1))
                )
                self.feat_bn = nn.BatchNorm1d(128)
                self.feat_bn.bias.requires_grad_(False)
                self.embedding = nn.Linear(128, 512)
            
            def forward(self, x):
                x = self.backbone(x)
                x = x.view(x.size(0), -1)
                x = self.feat_bn(x)
                x = self.embedding(x)
                # L2 normalization
                x = x / (torch.norm(x, p=2, dim=1, keepdim=True) + 1e-12)
                return x
        
        return SimpleOSNet()
    
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
                embedding = self.model(tensor)
            
            # Convert to numpy and normalize
            embedding_np = embedding.cpu().numpy()[0]
            embedding_np = embedding_np / (np.linalg.norm(embedding_np) + 1e-12)
            
            logger.info(f"✓ Embedding generated: {image_id[:8]}... (dim: {embedding_np.shape[0]})")
            return embedding_np
        
        except Exception as e:
            logger.error(f"Embedding generation error: {str(e)}")
            return None
