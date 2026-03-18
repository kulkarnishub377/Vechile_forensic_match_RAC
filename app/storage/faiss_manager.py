"""
FAISS vector storage manager with time partitioning
OPTIMIZED: Uses IndexFlatIP (no training), batch adds, lazy saving
"""
import faiss
import pickle
import logging
import threading
import numpy as np
from typing import List, Tuple, Dict
from pathlib import Path
from datetime import datetime

from .. import config

logger = logging.getLogger(__name__)


class FAISSManager:
    """
    Time-partitioned FAISS manager for ReID embeddings
    
    OPTIMIZED for speed:
    - Uses IndexFlatIP (no training needed!) 
    - Keeps indexes in memory, saves periodically
    - Batch operations for efficiency
    """
    
    MAX_CACHE_SIZE = 7  # Maximum partitions to keep in memory
    SAVE_INTERVAL = 50  # Save after every N vectors (not every 1!)
    
    def __init__(self):
        self.index_dir = Path(config.VECTOR_DB_DIR)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.embedding_dim = config.REID_EMBEDDING_DIM
        
        # In-memory cache of partitions
        self.index_cache = {}  # partition_key -> index
        self.metadata_cache = {}  # partition_key -> metadata
        self._cache_access_order = []  # LRU tracking
        self._pending_saves = {}  # partition_key -> count of unsaved adds
        
        self.lock = threading.RLock()
        
        logger.info(f"[OK] FAISS manager initialized (FlatIP, max_cache: {self.MAX_CACHE_SIZE})")
    
    def _get_partition_key(self, timestamp: datetime) -> str:
        """Get partition key from timestamp (daily partitions)"""
        return timestamp.strftime('%Y-%m-%d')
    
    def _get_index_path(self, partition_key: str) -> Path:
        """Get file path for partition index"""
        partition_dir = self.index_dir / partition_key
        partition_dir.mkdir(parents=True, exist_ok=True)
        return partition_dir / "index.faiss"
    
    def _get_metadata_path(self, partition_key: str) -> Path:
        """Get file path for partition metadata"""
        partition_dir = self.index_dir / partition_key
        partition_dir.mkdir(parents=True, exist_ok=True)
        return partition_dir / "ids.pkl"
    
    def _create_index(self) -> faiss.Index:
        """Create new FAISS index - FLAT only for speed (NO IVF training!)"""
        # IndexFlatIP = cosine similarity for normalized vectors
        # NO training needed = instant creation!
        index = faiss.IndexFlatIP(self.embedding_dim)
        logger.debug(f"Created FlatIP index (dim={self.embedding_dim})")
        return index
    
    def _get_or_create_partition(self, partition_key: str) -> Tuple[faiss.Index, Dict]:
        """Get partition from cache or load/create it"""
        with self.lock:
            # Check cache first
            if partition_key in self.index_cache:
                # Update LRU order
                if partition_key in self._cache_access_order:
                    self._cache_access_order.remove(partition_key)
                self._cache_access_order.append(partition_key)
                return self.index_cache[partition_key], self.metadata_cache[partition_key]
            
            # Try to load from disk
            index_path = self._get_index_path(partition_key)
            meta_path = self._get_metadata_path(partition_key)
            
            if index_path.exists():
                try:
                    index = faiss.read_index(str(index_path))
                    with open(meta_path, 'rb') as f:
                        metadata = pickle.load(f)
                    logger.debug(f"Loaded partition {partition_key} from disk ({index.ntotal} vectors)")
                except Exception as e:
                    logger.warning(f"Failed to load partition {partition_key}: {e}")
                    index = self._create_index()
                    metadata = {'transaction_ids': []}
            else:
                # Create new
                index = self._create_index()
                metadata = {'transaction_ids': []}
            
            # Add to cache
            self.index_cache[partition_key] = index
            self.metadata_cache[partition_key] = metadata
            self._cache_access_order.append(partition_key)
            self._pending_saves[partition_key] = 0
            
            # Evict old partitions if needed
            self._evict_if_needed()
            
            return index, metadata
    
    def _evict_if_needed(self):
        """Evict oldest partitions from cache if over limit"""
        while len(self.index_cache) > self.MAX_CACHE_SIZE:
            oldest_key = self._cache_access_order.pop(0)
            if oldest_key in self.index_cache:
                # Save before evicting
                self._save_partition(oldest_key)
                del self.index_cache[oldest_key]
                del self.metadata_cache[oldest_key]
                if oldest_key in self._pending_saves:
                    del self._pending_saves[oldest_key]
                logger.debug(f"Evicted partition from cache: {oldest_key}")
    
    def _save_partition(self, partition_key: str):
        """Save a single partition to disk"""
        if partition_key not in self.index_cache:
            return
        
        try:
            index = self.index_cache[partition_key]
            metadata = self.metadata_cache[partition_key]
            
            index_path = self._get_index_path(partition_key)
            meta_path = self._get_metadata_path(partition_key)
            
            faiss.write_index(index, str(index_path))
            with open(meta_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            self._pending_saves[partition_key] = 0
            logger.debug(f"Saved partition {partition_key} ({index.ntotal} vectors)")
        except Exception as e:
            logger.error(f"Failed to save partition {partition_key}: {e}")
    
    def add_vectors(self, partition_key: str, vectors: np.ndarray, transaction_ids: List[str]):
        """
        Add vectors to partition - FAST (in-memory, lazy save)
        
        Args:
            partition_key: Partition key (YYYY-MM-DD)
            vectors: (N, 512) embedding array
            transaction_ids: List of transaction IDs
        """
        with self.lock:
            try:
                index, metadata = self._get_or_create_partition(partition_key)
                
                # Normalize and add vectors
                vectors = vectors.astype('float32')
                norm = np.linalg.norm(vectors, axis=1, keepdims=True)
                vectors = np.where(norm > 0, vectors / norm, vectors)
                
                index.add(vectors)
                metadata['transaction_ids'].extend(transaction_ids)
                
                # Track pending saves
                self._pending_saves[partition_key] = self._pending_saves.get(partition_key, 0) + len(vectors)
                
                total_vectors = index.ntotal
                logger.info(f"[OK] Added {len(vectors)} vectors to partition {partition_key} (total: {total_vectors})")
                
                # Save periodically (not every time!)
                if self._pending_saves[partition_key] >= self.SAVE_INTERVAL:
                    self._save_partition(partition_key)
                    logger.info(f"     Auto-saved partition {partition_key}")
            
            except Exception as e:
                logger.error(f"Failed to add vectors to partition {partition_key}: {e}")
    
    def search_partitions(
        self,
        query_vector: np.ndarray,
        partition_keys: List[str],
        top_k: int = 100
    ) -> List[Tuple[str, float]]:
        """
        Search across multiple partitions
        
        Args:
            query_vector: (512,) query embedding
            partition_keys: List of partition keys to search
            top_k: Number of results per partition
        
        Returns:
            List of (transaction_id, similarity) tuples - sorted by similarity DESC
        """
        all_results = []
        
        query_vector = query_vector.reshape(1, -1).astype('float32')
        # Normalize query
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm
        
        with self.lock:
            for partition_key in partition_keys:
                try:
                    index, metadata = self._get_or_create_partition(partition_key)
                    
                    if index.ntotal == 0:
                        continue
                    
                    # Search
                    k = min(top_k, index.ntotal)
                    distances, indices = index.search(query_vector, k)
                    
                    # Map indices to transaction IDs
                    tx_ids = metadata['transaction_ids']
                    for dist, idx in zip(distances[0], indices[0]):
                        if idx >= 0 and idx < len(tx_ids):
                            all_results.append((tx_ids[idx], float(dist)))
                
                except Exception as e:
                    logger.error(f"Search failed for partition {partition_key}: {e}")
        
        # Sort by similarity (Inner Product: higher = better)
        all_results.sort(key=lambda x: x[1], reverse=True)
        
        return all_results[:top_k]
    
    def get_partition_keys_in_window(self, start_time: datetime, end_time: datetime) -> List[str]:
        """Get all partition keys within time window"""
        from datetime import timedelta
        
        keys = []
        current = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        while current <= end:
            keys.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        
        return keys
    
    def save_partition(self, partition_key: str):
        """Force save a specific partition to disk"""
        with self.lock:
            self._save_partition(partition_key)
    
    def save_all(self):
        """Save all cached partitions to disk"""
        with self.lock:
            saved = 0
            for partition_key in list(self.index_cache.keys()):
                try:
                    self._save_partition(partition_key)
                    saved += 1
                except Exception as e:
                    logger.error(f"Failed to save {partition_key}: {e}")
            logger.info(f"[OK] Saved {saved} partitions to disk")
    
    def clear_cache(self):
        """Clear in-memory cache (after saving)"""
        with self.lock:
            self.save_all()
            self.index_cache.clear()
            self.metadata_cache.clear()
            self._cache_access_order.clear()
            self._pending_saves.clear()
            logger.info("[OK] Cache cleared")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics for monitoring"""
        with self.lock:
            total_vectors = sum(
                idx.ntotal for idx in self.index_cache.values()
            )
            return {
                'cached_partitions': len(self.index_cache),
                'max_cache_size': self.MAX_CACHE_SIZE,
                'total_vectors_in_cache': total_vectors,
                'cache_order': self._cache_access_order.copy(),
                'pending_saves': dict(self._pending_saves)
            }


# Singleton instance
_faiss_manager = None


def get_faiss_manager() -> FAISSManager:
    """Get or create global FAISS manager instance"""
    global _faiss_manager
    if _faiss_manager is None:
        _faiss_manager = FAISSManager()
    return _faiss_manager
