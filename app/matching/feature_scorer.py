from typing import Dict, List
import logging
from datetime import datetime
import numpy as np
import cv2

from ..storage.metadata_manager import get_metadata_manager
from .. import config

logger = logging.getLogger(__name__)


class FeatureScorer:
    """Multi-feature scoring engine with cross-modal support"""
    
    # Optimized weights from reference system
    WEIGHT_EMBEDDING = 0.45  # ReID embedding (45%)
    WEIGHT_COLOR = 0.10      # Color histogram (10%)
    # Remaining 45% for boosts: scale, cross-modal, OCR
    
    def __init__(self):
        self.metadata_manager = get_metadata_manager()
        
        logger.info(f"[OK] Feature scorer initialized")
        logger.info(f"  Weights - Embedding:{self.WEIGHT_EMBEDDING:.2f} Color:{self.WEIGHT_COLOR:.2f} Boosts:0.45")
    
    def compute_score(
        self,
        exit_data: Dict,
        entry_transaction_id: str,
        entry_timestamp: datetime,
        embedding_similarity: float
    ) -> float:
        """
        Compute multi-feature match score with cross-modal support
        
        Args:
            exit_data: Exit vehicle data with:
                - color_histogram: 2048-D array
                - timestamp: datetime
                - aspect_ratio: float
                - is_grayscale: bool (NEW)
                - bbox: list [x1, y1, x2, y2]
            entry_transaction_id: Entry transaction ID
            entry_timestamp: Entry timestamp
            embedding_similarity: Pre-computed embedding similarity [0, 1]
        
        Returns:
            total_score: Combined score [0, 1]
        """
        # Get entry metadata
        entry_metadata = self.metadata_manager.get_metadata(
            entry_transaction_id,
            entry_timestamp
        )
        
        if entry_metadata is None:
            return embedding_similarity * self.WEIGHT_EMBEDDING
        
        # 1. Embedding score (already computed)
        score_embedding = embedding_similarity
        
        # Check cross-modal (day vs night)
        query_is_gray = exit_data.get('is_grayscale', False)
        db_is_grayscale = entry_metadata.get('is_grayscale', False)
        is_cross_modal = (query_is_gray != db_is_grayscale)
        
        # 2. Color histogram similarity (DISABLED for cross-modal)
        if is_cross_modal:
            score_color = 0.0
            logger.debug(f"  Cross-modal: color disabled (query_gray={query_is_gray}, db_gray={db_is_grayscale})")
        else:
            score_color = self._compute_color_similarity(
                exit_data.get('color_histogram'),
                entry_metadata.get('color_histogram')
            )
        
        # 3. Scale-aware boost
        scale_boost = self._compute_scale_boost(
            exit_data.get('bbox'),
            entry_metadata.get('bbox')
        )
        
        # 4. Cross-modal boost (compensate for disabled color matching)
        cross_modal_boost = 0.0
        if is_cross_modal and score_embedding >= 0.45:
            if score_embedding >= 0.70:
                cross_modal_boost = 0.18 + 0.05 * (score_embedding - 0.70) / 0.30
            elif score_embedding >= 0.55:
                cross_modal_boost = 0.08 + 0.10 * (score_embedding - 0.55) / 0.15
            else:
                cross_modal_boost = 0.03 + 0.05 * (score_embedding - 0.45) / 0.10
            
            logger.debug(f"  Cross-modal boost: {cross_modal_boost:.3f} (emb_sim={score_embedding:.3f})")
        
        # Weighted combination
        total_score = (
            self.WEIGHT_EMBEDDING * score_embedding +
            self.WEIGHT_COLOR * score_color +
            scale_boost +
            cross_modal_boost
        )
        
        return float(total_score)
    
    def _compute_color_similarity(
        self,
        hist1: np.ndarray,
        hist2: np.ndarray
    ) -> float:
        """Compute color histogram similarity using correlation"""
        if hist1 is None or hist2 is None:
            return 0.5  # Neutral
        
        try:
            # Convert to numpy arrays
            if not isinstance(hist1, np.ndarray):
                hist1 = np.array(hist1)
            if not isinstance(hist2, np.ndarray):
                hist2 = np.array(hist2)
            
            # Normalize histograms
            hist1 = hist1 / (np.sum(hist1) + 1e-6)
            hist2 = hist2 / (np.sum(hist2) + 1e-6)
            
            # Compute correlation
            correlation = np.corrcoef(hist1, hist2)[0, 1]
            
            # Map to [0, 1]
            similarity = (correlation + 1) / 2
            
            return float(similarity)
        
        except Exception as e:
            logger.error(f"Color similarity computation failed: {e}")
            return 0.5
    
    
    def _compute_scale_boost(
        self,
        bbox1: List[int],
        bbox2: List[int]
    ) -> float:
        """
        Compute scale-aware boost from bbox similarity
        
        Similar size/aspect = boost score
        """
        if not bbox1 or not bbox2:
            return 0.0
        
        try:
            # Calculate areas
            w1 = bbox1[2] - bbox1[0]
            h1 = bbox1[3] - bbox1[1]
            area1 = w1 * h1
            
            w2 = bbox2[2] - bbox2[0]
            h2 = bbox2[3] - bbox2[1]
            area2 = w2 * h2
            
            if area1 <= 0 or area2 <= 0:
                return 0.0
            
            # Area ratio
            area_ratio = min(area1, area2) / max(area1, area2)
            
            # Aspect ratio similarity
            aspect1 = w1 / (h1 + 1e-7)
            aspect2 = w2 / (h2 + 1e-7)
            aspect_diff = abs(aspect1 - aspect2) / max(aspect1, aspect2, 0.1)
            aspect_similarity = 1.0 - min(aspect_diff, 1.0)
            
            # Combined boost (up to 5% of total score)
            if area_ratio > 0.3 and aspect_similarity > 0.6:
                boost = 0.05 * area_ratio * aspect_similarity
                return float(boost)
            
            return 0.0
        
        except Exception as e:
            logger.error(f"Scale boost computation failed: {e}")
            return 0.0


# Global feature scorer
_feature_scorer = None

def get_feature_scorer() -> FeatureScorer:
    """Get or create global feature scorer instance"""
    global _feature_scorer
    if _feature_scorer is None:
        _feature_scorer = FeatureScorer()
    return _feature_scorer
