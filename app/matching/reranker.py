from typing import List, Dict, Tuple, Optional
import logging
import numpy as np

from .. import config
from .jaccard_reranker import compute_jaccard_reranking

logger = logging.getLogger(__name__)


class Reranker:
    """Combine and re-rank OCR + embedding matches with Jaccard re-ranking"""
    
    def __init__(self):
        self.ocr_boost_score = config.MATCHING_OCR_BOOST_SCORE
        self.enable_ocr_matching = config.MATCHING_ENABLE_OCR_MATCHING
        self.enable_jaccard = True  # NEW: Enable Jaccard re-ranking
        
        logger.info(f"[OK] Reranker initialized (OCR boost: +{self.ocr_boost_score:.2f}, Jaccard: ON)")
    
    def rerank(
        self,
        ocr_matches: List[Tuple[str, float]],
        embedding_matches: List[Dict],
        top_k: int = 10,
        query_embedding: Optional[np.ndarray] = None,
        candidate_embeddings: Optional[Dict[str, np.ndarray]] = None
    ) -> List[Dict]:
        """
        Combine OCR exact matches with embedding matches and re-rank
        
        Strategy:
        1. Apply Jaccard re-ranking if embeddings provided (15-20% accuracy boost)
        2. If OCR exact match exists, boost its score significantly
        3. Combine with embedding matches
        4. Sort by final score
        
        Args:
            ocr_matches: List of (transaction_id, ocr_score) from OCR matcher
            embedding_matches: List of dicts with:
                - transaction_id: str
                - score: float (multi-feature score)
                - distance: float (FAISS distance)
            top_k: Number of results to return
            query_embedding: Query ReID embedding (512-D) for Jaccard
            candidate_embeddings: Dict of {tx_id: embedding} for Jaccard
        
        Returns:
            Ranked list of match dicts with final scores
        """
        # STEP 1: Apply Jaccard re-ranking if embeddings provided
        if self.enable_jaccard and query_embedding is not None and candidate_embeddings:
            embedding_matches = self._apply_jaccard_reranking(
                embedding_matches,
                query_embedding,
                candidate_embeddings
            )
        
        # STEP 2: Create lookup for OCR matches
        ocr_match_dict = {tid: score for tid, score in ocr_matches}
        
        # STEP 3: Combine scores
        combined = {}
        
        # Add embedding matches
        for match in embedding_matches:
            tid = match['transaction_id']
            combined[tid] = match.copy()
        
        # STEP 4: Apply OCR boost if enabled
        if self.enable_ocr_matching:
            for tid, ocr_score in ocr_match_dict.items():
                if tid in combined:
                    # Already in embedding matches - boost score
                    original_score = combined[tid]['score']
                    boosted_score = min(1.0, original_score + self.ocr_boost_score)
                    combined[tid]['score'] = boosted_score
                    combined[tid]['has_ocr_match'] = True
                    combined[tid]['ocr_score'] = ocr_score
                    
                    logger.info(f"  OCR boost applied to {tid}: {original_score:.3f} → {boosted_score:.3f}")
                else:
                    # Not in embedding matches - add with OCR score only
                    combined[tid] = {
                        'transaction_id': tid,
                        'score': min(1.0, ocr_score * 0.5 + self.ocr_boost_score),
                        'has_ocr_match': True,
                        'ocr_score': ocr_score,
                        'distance': 0.0
                    }
        
        # STEP 5: Convert to list and sort by score descending
        ranked_results = sorted(
            combined.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        # Return top K
        final_results = ranked_results[:top_k]
        
        logger.info(f"[OK] Reranked {len(combined)} candidates, returning top {len(final_results)}")
        
        return final_results
    
    def _apply_jaccard_reranking(
        self,
        embedding_matches: List[Dict],
        query_embedding: np.ndarray,
        candidate_embeddings: Dict[str, np.ndarray]
    ) -> List[Dict]:
        """Apply Jaccard re-ranking to embedding matches"""
        if len(embedding_matches) < 2:
            return embedding_matches
        
        try:
            # Extract candidate IDs and scores
            candidate_ids = [m['transaction_id'] for m in embedding_matches]
            initial_scores = [m['score'] for m in embedding_matches]
            
            # Build embedding matrix (filter to only candidates that have embeddings)
            valid_indices = []
            valid_ids = []
            embeddings_list = []
            
            for i, tid in enumerate(candidate_ids):
                if tid in candidate_embeddings:
                    valid_indices.append(i)
                    valid_ids.append(tid)
                    embeddings_list.append(candidate_embeddings[tid])
            
            if len(embeddings_list) < 2:
                logger.debug("Not enough embeddings for Jaccard re-ranking")
                return embedding_matches
            
            candidate_emb_matrix = np.vstack(embeddings_list)
            valid_scores = [initial_scores[i] for i in valid_indices]
            
            # Compute Jaccard re-ranking
            reranked = compute_jaccard_reranking(
                query_embedding=query_embedding,
                candidate_embeddings=candidate_emb_matrix,
                candidate_ids=valid_ids,
                initial_scores=valid_scores,
                k1=20,
                lambda_value=0.3
            )
            
            # Update scores in embedding_matches
            rerank_lookup = {r['tx_id']: r['reranked_score'] for r in reranked}
            
            updated_matches = []
            for match in embedding_matches:
                tid = match['transaction_id']
                if tid in rerank_lookup:
                    match['score'] = rerank_lookup[tid]
                    match['jaccard_reranked'] = True
                updated_matches.append(match)
            
            logger.info(f"  Jaccard re-ranking applied to {len(reranked)}/{len(embedding_matches)} candidates")
            
            return updated_matches
        
        except Exception as e:
            logger.error(f"Jaccard re-ranking failed: {e}")
            return embedding_matches


# Global reranker
_reranker = None

def get_reranker() -> Reranker:
    """Get or create global reranker instance"""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker
