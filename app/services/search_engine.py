"""
Search Engine Service
FAISS in-memory vector search for vehicle matching
"""
import faiss
import numpy as np
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SearchEngine:
    """FAISS-based in-memory search for vehicle matching"""
    
    def __init__(self, dimension: int = 512):
        self.dimension = dimension
        self.index = None
        self.id_map = {}  # faiss_id → image_id
        self.reverse_map = {}  # image_id → faiss_id
        self.embeddings = {}  # image_id → embedding
        self.session_indices = {}  # session_id → set of image_ids in index
    
    def initialize(self):
        """Initialize FAISS index"""
        try:
            # Create L2 distance index
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info("✓ FAISS index initialized")
        except Exception as e:
            logger.error(f"FAISS initialization error: {str(e)}")
            raise
    
    def add_to_index(self, image_id: str, embedding: np.ndarray, session_id: str = None):
        """
        Add embedding to FAISS index
        """
        try:
            if self.index is None:
                self.initialize()
            
            # Ensure float32
            embedding = embedding.astype(np.float32).reshape(1, -1)
            
            # Add to index
            idx = self.index.ntotal
            self.index.add(embedding)
            
            # Map IDs
            self.id_map[idx] = image_id
            self.reverse_map[image_id] = idx
            self.embeddings[image_id] = embedding[0]
            
            # Track session
            if session_id:
                if session_id not in self.session_indices:
                    self.session_indices[session_id] = set()
                self.session_indices[session_id].add(image_id)
            
            logger.info(f"Added to index: {image_id[:8]}... (total: {self.index.ntotal})")
        
        except Exception as e:
            logger.error(f"Add to index error: {str(e)}")
    
    def search(
        self,
        query_embedding: np.ndarray,
        threshold: float = 0.85,
        top_k: int = 50
    ) -> List[Dict]:
        """
        Search for similar embeddings
        Returns list of (image_id, similarity_score)
        """
        try:
            if self.index is None or self.index.ntotal == 0:
                logger.warning("Index is empty")
                return []
            
            # Prepare query
            query = query_embedding.astype(np.float32).reshape(1, -1)
            
            # Search FAISS
            k = min(top_k, self.index.ntotal)
            distances, indices = self.index.search(query, k)
            
            # Convert L2 distances to similarity scores (0-1)
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx >= 0 and idx in self.id_map:
                    # Convert L2 distance to cosine similarity approximation
                    # similarity = 1 / (1 + distance)
                    similarity = 1.0 / (1.0 + float(dist))
                    
                    if similarity >= threshold:
                        results.append({
                            "image_id": self.id_map[idx],
                            "distance": float(dist),
                            "score": similarity
                        })
            
            logger.info(f"Search found: {len(results)} results above threshold {threshold}")
            return results
        
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []
    
    def clear_session_index(self, session_id: str):
        """Remove images from specific session from index"""
        try:
            if session_id not in self.session_indices:
                return
            
            # Rebuild index without session images
            image_ids_to_keep = []
            for image_id, embedding in self.embeddings.items():
                if image_id not in self.session_indices.get(session_id, set()):
                    image_ids_to_keep.append(image_id)
            
            # Rebuild index
            self._rebuild_index(image_ids_to_keep)
            
            # Remove from session tracking
            del self.session_indices[session_id]
            
            logger.info(f"Session index cleared: {session_id[:8]}...")
        
        except Exception as e:
            logger.error(f"Clear session error: {str(e)}")
    
    def _rebuild_index(self, image_ids: List[str]):
        """Rebuild FAISS index with specified images"""
        try:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.id_map = {}
            self.reverse_map = {}
            
            for idx, image_id in enumerate(image_ids):
                if image_id in self.embeddings:
                    embedding = self.embeddings[image_id].astype(np.float32).reshape(1, -1)
                    self.index.add(embedding)
                    self.id_map[idx] = image_id
                    self.reverse_map[image_id] = idx
            
            logger.info(f"Index rebuilt: {self.index.ntotal} entries")
        
        except Exception as e:
            logger.error(f"Rebuild index error: {str(e)}")
    
    def get_index_size(self) -> int:
        """Get total vectors in index"""
        return self.index.ntotal if self.index else 0
    
    def cleanup(self):
        """Clear all data"""
        self.index = None
        self.id_map.clear()
        self.reverse_map.clear()
        self.embeddings.clear()
        self.session_indices.clear()
        logger.info("Search engine cleanup complete")
