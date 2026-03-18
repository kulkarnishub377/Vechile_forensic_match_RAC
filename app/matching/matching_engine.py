from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import time

from .ocr_matcher import get_ocr_matcher
from .embedding_matcher import get_embedding_matcher
from .feature_scorer import get_feature_scorer
from .reranker import get_reranker
from .confidence_analyzer import analyze_match_confidence
from ..core.embedding_engine import get_embedding_engine
# NOTE: Database import removed - system is now standalone
from ..storage.metadata_manager import get_metadata_manager
from .. import config

logger = logging.getLogger(__name__)


class MatchingEngine:
    """Dual-path matching with advanced features from reference system"""
    
    MAX_ALLOWED_TOP_K = 100
    MAX_TIMESTAMP_FUTURE_HOURS = 1
    MAX_TIMESTAMP_PAST_DAYS = 365
    OCR_CANDIDATE_MULTIPLIER = 5
    EMBEDDING_CANDIDATE_MULTIPLIER = 3
    
    def __init__(self):
        self.ocr_matcher = get_ocr_matcher()
        self.embedding_matcher = get_embedding_matcher()
        self.feature_scorer = get_feature_scorer()
        self.reranker = get_reranker()
        self.embedding_engine = get_embedding_engine()
        # NOTE: entry_queries removed - no longer using database
        self.metadata_manager = get_metadata_manager()
        
        self.total_matches = 0
        self.total_errors = 0
        self.total_processing_time = 0.0
        
        logger.info("Matching engine initialized with FULL reference system features")
        logger.info("  ✓ Structure-aware OCR matching")
        logger.info("  ✓ Cross-modal matching (day/night)")
        logger.info("  ✓ Optimized weights (0.45 emb, 0.10 color)")
        logger.info("  ✓ Jaccard re-ranking")
        logger.info("  ✓ Confidence analysis")
    
    def find_matches(
        self,
        exit_image_path: str,
        exit_timestamp: datetime,
        top_k: int = 10
    ) -> List[Dict]:
        """Find matching ENTRY vehicles for EXIT vehicle"""
        start_time = time.time()
        
        try:
            self._validate_inputs(exit_image_path, exit_timestamp, top_k)
            logger.info(f"Finding matches: {Path(exit_image_path).name}")
            
            exit_data = self._process_exit_vehicle(exit_image_path)
            if exit_data is None:
                logger.warning("Failed to process exit vehicle")
                return []
            
            embedding_candidates = self._fetch_embedding_candidates(
                exit_data['reid_embedding'],
                exit_timestamp,
                top_k
            )
            
            if not embedding_candidates:
                logger.info("No embedding candidates found")
                return []
            
            ocr_matches = self._find_ocr_matches(exit_data, embedding_candidates)
            scored_matches = self._score_matches(exit_data, exit_timestamp, embedding_candidates)
            final_matches = self._rerank_matches(ocr_matches, scored_matches, top_k)
            
            self.total_matches += 1
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            
            logger.info(f"Returned {len(final_matches)} matches ({processing_time:.2f}s)")
            if final_matches:
                logger.debug(f"Top: tx_id={final_matches[0].get('tx_id')} score={final_matches[0].get('score', 0):.3f}")
            
            return final_matches
        
        except Exception as e:
            self.total_errors += 1
            logger.error(f"Matching failed: {e}")
            raise
    
    def _validate_inputs(
        self,
        exit_image_path: str,
        exit_timestamp: datetime,
        top_k: int
    ) -> None:
        """Validate all inputs before processing"""
        if not exit_image_path:
            raise ValueError("exit_image_path cannot be empty")
        
        image_path = Path(exit_image_path)
        if not image_path.exists():
            raise ValueError(f"Image file does not exist: {exit_image_path}")
        
        if not image_path.is_file():
            raise ValueError(f"Image path is not a file: {exit_image_path}")
        
        if not isinstance(exit_timestamp, datetime):
            raise ValueError("exit_timestamp must be a datetime object")
        
        now = datetime.now()
        max_future = now + timedelta(hours=self.MAX_TIMESTAMP_FUTURE_HOURS)
        min_past = now - timedelta(days=self.MAX_TIMESTAMP_PAST_DAYS)
        
        if exit_timestamp > max_future:
            raise ValueError(f"exit_timestamp is too far in future: {exit_timestamp}")
        
        if exit_timestamp < min_past:
            raise ValueError(f"exit_timestamp is too old: {exit_timestamp}")
        
        if not isinstance(top_k, int):
            raise ValueError("top_k must be an integer")
        
        if top_k < 1:
            raise ValueError(f"top_k must be >= 1, got {top_k}")
        
        if top_k > self.MAX_ALLOWED_TOP_K:
            raise ValueError(f"top_k exceeds maximum allowed ({self.MAX_ALLOWED_TOP_K}), got {top_k}")
    
    def _process_exit_vehicle(self, exit_image_path: str) -> Optional[Dict]:
        """
        Process exit vehicle image to extract features
        
        Returns:
            Dict with features or None if processing fails
        """
        try:
            embedding_data = self.embedding_engine.process_image(exit_image_path)
            
            if embedding_data is None:
                return None
            
            # Extract and validate features (use correct attribute names from VehicleEmbedding)
            exit_data = {
                'reid_embedding': embedding_data.reid_embedding,
                'ocr_text': embedding_data.ocr_text or '',
                'ocr_confidence': embedding_data.ocr_conf or 0.0,  # Note: VehicleEmbedding uses ocr_conf
                'color_histogram': embedding_data.color_hist,  # Note: VehicleEmbedding uses color_hist
                'aspect_ratio': embedding_data.aspect_ratio or 1.0,
                'is_grayscale': embedding_data.is_grayscale,
                'bbox': embedding_data.bbox
            }
            
            # Log grayscale detection
            if exit_data['is_grayscale']:
                logger.info(f"  🌙 Night/BW camera detected (cross-modal matching enabled)")
            else:
                logger.info(f"  🎨 Color camera detected")
            
            # Log OCR with masking for privacy
            ocr_masked = self._mask_ocr(exit_data['ocr_text'])
            logger.info(
                f"  Exit OCR: '{ocr_masked}' (conf: {exit_data['ocr_confidence']:.2f})"
            )
            
            return exit_data
            
        except Exception as e:
            logger.error(f"Exit vehicle processing failed: {e}", exc_info=True)
            return None
    
    def _fetch_embedding_candidates(
        self,
        query_embedding: np.ndarray,
        exit_timestamp: datetime,
        top_k: int
    ) -> List[tuple]:
        """
        Fetch embedding candidates from FAISS (single search for both paths)
        
        CRITICAL: Only searches UNCOMBINED entries (PROCESS_FLAG <> 'C')
        
        Returns:
            List of (transaction_id, distance) tuples
        """
        # Calculate how many candidates we need
        # For OCR: need more candidates to filter
        # For embedding: need extra for re-ranking
        ocr_needs = top_k * self.OCR_CANDIDATE_MULTIPLIER if config.MATCHING_ENABLE_OCR_MATCHING else 0
        embedding_needs = top_k * self.EMBEDDING_CANDIDATE_MULTIPLIER
        
        # Take the maximum of both needs
        fetch_k = max(ocr_needs, embedding_needs)
        
        logger.info(f"  Fetching {fetch_k} embedding candidates (top_k={top_k})")
        
        try:
            # NOTE: Database filtering removed - search all indexed images
            # Previously filtered by UNCOMBINED entries (PROCESS_FLAG <> 'C')
            # Now searches all uploaded images in FAISS index
            logger.info("  Searching all indexed images (no database filtering)...")

            # Search FAISS for all matching vectors (no pre-filtering)
            embedding_results = self.embedding_matcher.find_embedding_matches(
                query_embedding=query_embedding,
                exit_timestamp=exit_timestamp,
top_k=fetch_k,
                uncombined_ids=None  # Search all, no filtering
            )

            logger.info(f"  Found {len(embedding_results)} embedding candidates")
            return embedding_results
            
        except Exception as e:
            logger.error(f"Embedding search failed: {e}", exc_info=True)
            return []
    
    def _find_ocr_matches(
        self,
        exit_data: Dict,
        embedding_candidates: List[tuple]
    ) -> List[tuple]:
        """
        Find OCR exact matches among embedding candidates
        
        Returns:
            List of (transaction_id, match_score) tuples
        """
        if not config.MATCHING_ENABLE_OCR_MATCHING:
            return []
        
        if not exit_data['ocr_text']:
            return []
        
        try:
            logger.info("  Path 1: OCR exact matching...")
            
            # Extract transaction IDs from candidates
            entry_ids = [tid for tid, _ in embedding_candidates]
            
            # Batch fetch entry records (FIX: N+1 query problem)
            entry_records = self._batch_get_entries(entry_ids)
            
            # Extract timestamps
            entry_timestamps = [
                rec['Timestamp'] if rec else datetime.now()
                for rec in entry_records
            ]
            
            # Find OCR matches
            ocr_matches = self.ocr_matcher.find_ocr_matches(
                query_ocr_text=exit_data['ocr_text'],
                query_ocr_confidence=exit_data['ocr_confidence'],
                entry_transaction_ids=entry_ids,
                entry_timestamps=entry_timestamps
            )
            
            logger.info(f"  Found {len(ocr_matches)} OCR exact matches")
            return ocr_matches
            
        except Exception as e:
            logger.error(f"OCR matching failed: {e}", exc_info=True)
            return []
    
    def _batch_get_entries(self, entry_ids: List[str]) -> List[Optional[Dict]]:
        """
        Batch fetch entry records to avoid N+1 queries
        
        Returns:
            List of entry records (same order as entry_ids)
        """
        try:
            # Check if entry_queries supports batch operations
            if hasattr(self.entry_queries, 'get_entries_batch'):
                return self.entry_queries.get_entries_batch(entry_ids)
            else:
                # Fallback: individual queries (still better than in loop)
                return [self.entry_queries.get_entry_by_id(tid) for tid in entry_ids]
        except Exception as e:
            logger.error(f"Batch entry fetch failed: {e}", exc_info=True)
            return [None] * len(entry_ids)
    
    def _score_matches(
        self,
        exit_data: Dict,
        exit_timestamp: datetime,
        embedding_candidates: List[tuple]
    ) -> List[Dict]:
        """
        Compute multi-feature scores for all candidates
        
        Returns:
            List of scored match dicts
        """
        logger.info("  Path 2: Multi-feature scoring...")
        
        try:
            # Batch fetch entry records once for all candidates
            entry_ids = [tid for tid, _ in embedding_candidates]
            entry_records = self._batch_get_entries(entry_ids)
            
            # Prepare exit data for scoring (with grayscale info)
            exit_scoring_data = {
                'color_histogram': exit_data['color_histogram'],
                'timestamp': exit_timestamp,
                'aspect_ratio': exit_data['aspect_ratio'],
                'is_grayscale': exit_data.get('is_grayscale', False),
                'bbox': exit_data.get('bbox', [0, 0, 100, 100])
            }
            
            scored_matches = []
            
            for (entry_tid, distance), entry_record in zip(embedding_candidates, entry_records):
                # Skip if entry record not found
                if entry_record is None:
                    logger.warning(f"  Skipping {entry_tid}: entry record not found")
                    continue
                
                # Validate required fields
                if 'Timestamp' not in entry_record:
                    logger.warning(f"  Skipping {entry_tid}: missing timestamp")
                    continue
                
                entry_timestamp = entry_record['Timestamp']
                
                # Convert distance to similarity
                embedding_similarity = self.embedding_matcher.convert_distance_to_similarity(distance)
                
                # Compute multi-feature score
                try:
                    total_score = self.feature_scorer.compute_score(
                        exit_data=exit_scoring_data,
                        entry_transaction_id=entry_tid,
                        entry_timestamp=entry_timestamp,
                        embedding_similarity=embedding_similarity
                    )
                    
                    scored_matches.append({
                        'transaction_id': entry_tid,
                        'score': total_score,
                        'distance': distance,
                        'has_ocr_match': False,
                        'entry_timestamp': entry_timestamp.isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"  Scoring failed for {entry_tid}: {e}")
                    continue
            
            logger.info(f"  Scored {len(scored_matches)}/{len(embedding_candidates)} candidates")
            return scored_matches
            
        except Exception as e:
            logger.error(f"Match scoring failed: {e}", exc_info=True)
            return []
    
    def _rerank_matches(
        self,
        ocr_matches: List[tuple],
        scored_matches: List[Dict],
        top_k: int
    ) -> List[Dict]:
        """Re-rank matches using OCR boost + Jaccard + confidence analysis"""
        logger.info("  Re-ranking with OCR boost + Jaccard + confidence analysis...")
        
        try:
            # Apply confidence analysis FIRST (adaptive result count)
            filtered_matches, confidence = analyze_match_confidence(scored_matches, top_k)
            
            logger.info(f"  Match confidence: {confidence.upper()}")
            
            # Then apply final re-ranking
            final_matches = self.reranker.rerank(
                ocr_matches=ocr_matches,
                embedding_matches=filtered_matches,
                top_k=top_k
            )
            return final_matches
        except Exception as e:
            logger.error(f"Re-ranking failed: {e}")
            return sorted(scored_matches, key=lambda x: x['score'], reverse=True)[:top_k]
    
    # Privacy/Security helpers
    
    @staticmethod
    def _mask_ocr(ocr_text: str) -> str:
        """Mask OCR text for logging (privacy protection)"""
        if not ocr_text or len(ocr_text) < 3:
            return "***"
        # Show first 2 and last 1 character
        return f"{ocr_text[:2]}***{ocr_text[-1]}"
    
    @staticmethod
    def _mask_path(path: str) -> str:
        """Mask sensitive parts of file path"""
        try:
            p = Path(path)
            return f".../{p.parent.name}/{p.name}"
        except:
            return "***"
    
    @staticmethod
    def _mask_transaction_id(tid: str) -> str:
        """Mask transaction ID for logging"""
        if not tid or len(tid) < 6:
            return "***"
        return f"{tid[:3]}***{tid[-3:]}"
    
    def get_metrics(self) -> Dict[str, float]:
        """
        Get performance metrics
        
        Returns:
            Dict with metrics
        """
        return {
            'total_matches': self.total_matches,
            'total_errors': self.total_errors,
            'error_rate': self.total_errors / max(1, self.total_matches),
            'avg_processing_time': self.total_processing_time / max(1, self.total_matches),
            'total_processing_time': self.total_processing_time
        }
    
    def reset_metrics(self) -> None:
        """Reset performance metrics"""
        self.total_matches = 0
        self.total_errors = 0
        self.total_processing_time = 0.0


# Global matching engine with proper lifecycle management
_matching_engine: Optional[MatchingEngine] = None


def get_matching_engine() -> MatchingEngine:
    """
    Get or create global matching engine instance
    
    Returns:
        Singleton MatchingEngine instance
    """
    global _matching_engine
    if _matching_engine is None:
        _matching_engine = MatchingEngine()
    return _matching_engine


def reset_matching_engine() -> None:
    """
    Reset global matching engine (for testing/cleanup)
    """
    global _matching_engine
    _matching_engine = None
