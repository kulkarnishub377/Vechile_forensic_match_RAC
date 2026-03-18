from typing import List, Tuple
import logging
from datetime import datetime, timedelta
import numpy as np

from ..storage.faiss_manager import get_faiss_manager
from .. import config

logger = logging.getLogger(__name__)


class EmbeddingMatcher:
    """FAISS-based embedding similarity search"""
    
    def __init__(self):
        self.faiss_manager = get_faiss_manager()
        self.search_window_hours = config.MATCHING_SEARCH_WINDOW_HOURS
        
        logger.info("[OK] Embedding matcher initialized")
    
    def find_embedding_matches(
        self,
        query_embedding: np.ndarray,
        exit_timestamp: datetime,
        top_k: int = 100,
        uncombined_ids: List[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Find similar vehicles using FAISS
        
        Args:
            query_embedding: (512,) ReID embedding
            exit_timestamp: Exit transaction timestamp
            top_k: Number of results to return
            uncombined_ids: Optional list of UNCOMBINED entry IDs to filter results
                           If provided, only returns matches from this set
        
        Returns:
            List of (transaction_id, distance) tuples
        """
        try:
            # Define search window (look back from exit time)
            search_start = exit_timestamp - timedelta(hours=self.search_window_hours)
            search_end = exit_timestamp
            
            # Get partition keys to search
            partition_keys = self.faiss_manager.get_partition_keys_in_window(
                search_start,
                search_end
            )
            
            if not partition_keys:
                logger.warning(f"No partitions found in search window")
                return []
            
            # Search across partitions (get more results if filtering)
            search_k = top_k * 3 if uncombined_ids else top_k
            
            results = self.faiss_manager.search_partitions(
                query_vector=query_embedding,
                partition_keys=partition_keys,
                top_k=search_k
            )
            
            # FILTER: If uncombined_ids provided, only keep those entries
            if uncombined_ids:
                uncombined_set = set(uncombined_ids)
                filtered_results = [
                    (tid, dist) for tid, dist in results
                    if tid in uncombined_set
                ]
                logger.info(
                    f"[OK] Found {len(results)} total, "
                    f"filtered to {len(filtered_results)} UNCOMBINED matches"
                )
                results = filtered_results[:top_k]
            else:
                logger.info(f"[OK] Found {len(results)} embedding matches (no filter)")
            
            return results[:top_k]
        
        except Exception as e:
            logger.error(f"Embedding search failed: {e}")
            return []
    
    def convert_distance_to_similarity(self, distance: float) -> float:
        """
        Convert FAISS result to similarity score [0, 1]
        
        NOTE: We now use Inner Product (IP) index for normalized vectors.
        IP for normalized vectors = cosine similarity = [-1, 1], typically [0, 1] for ReID
        
        Args:
            distance: Inner Product score from FAISS (higher = more similar)
        
        Returns:
            similarity: Score in [0, 1]
        """
        # For Inner Product with normalized vectors:
        # - Score is already in [-1, 1] range (cosine similarity)
        # - Higher values mean MORE similar (unlike L2 where lower = better)
        # - Clamp to [0, 1] for practical use
        similarity = max(0.0, min(1.0, distance))
        return similarity


# Global embedding matcher
_embedding_matcher = None

def get_embedding_matcher() -> EmbeddingMatcher:
    """Get or create global embedding matcher instance"""
    global _embedding_matcher
    if _embedding_matcher is None:
        _embedding_matcher = EmbeddingMatcher()
    return _embedding_matcher
