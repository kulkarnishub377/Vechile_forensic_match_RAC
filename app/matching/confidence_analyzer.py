import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


def analyze_match_confidence(results: List[Dict], top_k: int) -> Tuple[List[Dict], str]:
    """
    Analyze match confidence and adapt result count
    
    This is the same confidence analysis from the reference system
    that provides adaptive result filtering based on match quality
    
    Args:
        results: List of match dicts with 'score' field
        top_k: Base number of results requested
    
    Returns:
        (filtered_results, confidence_level)
    """
    if not results:
        logger.debug("analyze_match_confidence: No results to analyze")
        return [], "no_results"
    
    # Sort by similarity score
    results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
    
    top_score = results[0].get('score', 0)
    second_score = results[1].get('score', 0) if len(results) > 1 else 0
    
    logger.debug(f"Confidence analysis: top_score={top_score:.3f}, second_score={second_score:.3f}, total_results={len(results)}")
    
    # Confidence analysis
    if top_score >= 0.80:
        confidence = "very_high"
        if top_score - second_score < 0.05:
            confidence = "high"  # Close competition
    elif top_score >= 0.60:
        confidence = "high"
    elif top_score >= 0.40:
        confidence = "moderate"
    else:
        confidence = "low"
    
    logger.debug(f"Confidence level: {confidence}")
    
    # Adaptive filtering based on confidence
    if confidence == "very_high":
        filtered = results[:top_k]
    elif confidence == "high":
        # Return 2x more candidates for close matches
        filtered = results[:min(top_k * 2, len(results))]
    elif confidence == "moderate":
        # Return 3x more candidates for uncertain matches
        filtered = results[:min(top_k * 3, len(results))]
    else:
        # Return 4x more candidates for low confidence
        filtered = results[:min(top_k * 4, len(results))]
    
    logger.info(f"Confidence: {confidence} - Filtered {len(results)} → {len(filtered)} candidates")
    return filtered, confidence
