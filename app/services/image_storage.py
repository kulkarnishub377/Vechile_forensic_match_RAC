"""
Image Storage Service
Handles image storage and metadata management (in-memory)
"""
import uuid
import cv2
import numpy as np
from datetime import datetime
import logging
from typing import Dict, Optional, List
from io import BytesIO

logger = logging.getLogger(__name__)

class ImageStorage:
    """Store and manage images in-memory (no database)"""
    
    def __init__(self):
        self.storage: Dict[str, dict] = {}  # image_id → image data
        self.sessions: Dict[str, list] = {}  # session_id → [image_ids]
    
    def save_image(self, session_id: str, filename: str, content: bytes) -> str:
        """
        Save image to memory
        Returns: image_id
        """
        try:
            image_id = str(uuid.uuid4())
            
            # Decode image
            nparr = np.frombuffer(content, np.uint8)
            image_data = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image_data is None:
                logger.error(f"Failed to decode image: {filename}")
                return None
            
            # Store image and metadata
            self.storage[image_id] = {
                "session_id": session_id,
                "filename": filename,
                "image": image_data,
                "upload_time": datetime.now().isoformat(),
                "embedding": None,
                "vehicle_region": None
            }
            
            # Track in session
            if session_id not in self.sessions:
                self.sessions[session_id] = []
            self.sessions[session_id].append(image_id)
            
            logger.info(f"Image saved: {image_id[:8]}... ({filename})")
            return image_id
        
        except Exception as e:
            logger.error(f"Save image error: {str(e)}")
            return None
    
    def add_embedding(self, image_id: str, embedding: np.ndarray):
        """Add embedding to image"""
        if image_id in self.storage:
            self.storage[image_id]["embedding"] = embedding
            logger.info(f"Embedding added to image: {image_id[:8]}...")
    
    def add_vehicle_region(self, image_id: str, region: np.ndarray):
        """Store vehicle cropped region"""
        if image_id in self.storage:
            self.storage[image_id]["vehicle_region"] = region
    
    def get_image_info(self, image_id: str) -> Optional[dict]:
        """Get image metadata (without raw image data)"""
        if image_id in self.storage:
            img = self.storage[image_id]
            return {
                "image_id": image_id,
                "filename": img["filename"],
                "upload_time": img["upload_time"],
                "embedding_ready": img["embedding"] is not None
            }
        return None
    
    def get_embedding(self, image_id: str) -> Optional[np.ndarray]:
        """Get image embedding"""
        if image_id in self.storage:
            return self.storage[image_id]["embedding"]
        return None
    
    def get_session_images(self, session_id: str) -> list:
        """Get all image info in session"""
        if session_id not in self.sessions:
            return []
        
        images = []
        for image_id in self.sessions[session_id]:
            info = self.get_image_info(image_id)
            if info:
                images.append(info)
        
        return images
    
    def get_image_count(self, session_id: str) -> int:
        """Get count of images in session"""
        return len(self.sessions.get(session_id, []))
    
    def clear_session(self, session_id: str):
        """Remove all images in session"""
        if session_id in self.sessions:
            for image_id in self.sessions[session_id]:
                if image_id in self.storage:
                    del self.storage[image_id]
            del self.sessions[session_id]
            logger.info(f"Session cleared: {session_id[:8]}...")
    
    def cleanup(self):
        """Cleanup all storage"""
        self.storage.clear()
        self.sessions.clear()
        logger.info("Storage cleanup complete")
