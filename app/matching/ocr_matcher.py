from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime
import difflib

from ..database.entry_queries import get_entry_queries
from ..storage.metadata_manager import get_metadata_manager
from .. import config

logger = logging.getLogger(__name__)


# Indian state codes for validation
STATE_CODES = {
    "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD", "DL", "DN",
    "GA", "GJ", "HP", "HR", "JH", "JK", "KA", "KL", "LA", "LD",
    "MH", "ML", "MN", "MP", "MZ", "NL", "OD", "OR", "PB", "PY",
    "RJ", "SK", "TN", "TR", "TS", "TG", "UK", "UA", "UP", "WB"
}


def normalize_ocr_confusions(plate: str) -> str:
    """Normalize common OCR confusions for comparison"""
    if not plate:
        return ""
    
    confusion_map = {
        '0': 'O', 'O': 'O', 'Q': 'O', 'D': 'O',
        '1': 'I', 'I': 'I', 'L': 'I', 'T': 'I',
        '5': 'S', 'S': 'S',
        '8': 'B', 'B': 'B',
        '2': 'Z', 'Z': 'Z', '7': 'Z',
        '6': 'G', 'G': 'G',
        '4': 'A',
    }
    
    normalized = ""
    for c in plate.upper():
        normalized += confusion_map.get(c, c)
    
    return normalized


def extract_plate_parts(plate: str) -> Dict[str, str]:
    """Extract structured parts from an Indian plate number"""
    parts = {
        'format': 'unknown',
        'state': '',
        'district': '',
        'series': '',
        'number': '',
        'raw': plate
    }
    
    if not plate or len(plate) < 4:
        return parts
    
    plate = plate.upper().strip()
    
    # Bharat series (22BH1234AB)
    if len(plate) >= 8 and plate[2:4] == 'BH':
        parts['format'] = 'bharat_series'
        parts['state'] = 'BH'
        parts['district'] = plate[:2]
        parts['number'] = plate[4:8] if len(plate) >= 8 else plate[4:]
        parts['series'] = plate[8:] if len(plate) > 8 else ''
        return parts
    
    # Standard format
    potential_state = plate[:2]
    if potential_state.isalpha():
        parts['state'] = potential_state
        remaining = plate[2:]
        
        # District (1-2 digits)
        district = ""
        i = 0
        while i < len(remaining) and remaining[i].isdigit() and len(district) < 2:
            district += remaining[i]
            i += 1
        parts['district'] = district
        remaining = remaining[len(district):]
        
        # Series (0-3 letters)
        series = ""
        i = 0
        while i < len(remaining) and remaining[i].isalpha() and len(series) < 3:
            series += remaining[i]
            i += 1
        parts['series'] = series
        remaining = remaining[len(series):]
        
        # Number
        number = ""
        for c in remaining:
            if c.isdigit():
                number += c
        parts['number'] = number
        
        if parts['state'] in STATE_CODES:
            parts['format'] = 'standard'
        else:
            parts['format'] = 'standard_unverified'
        
        return parts
    
    # Fallback
    number = ""
    for c in reversed(plate):
        if c.isdigit():
            number = c + number
        else:
            break
    parts['number'] = number
    
    return parts


def calculate_plate_similarity(plate1: str, plate2: str) -> Tuple[float, bool, str]:
    """
    Structure-aware plate similarity matching
    
    Returns:
        (similarity_ratio, is_likely_same_vehicle, match_type)
    """
    if not plate1 or not plate2:
        return 0.0, False, 'none'
    
    plate1 = plate1.upper().strip()
    plate2 = plate2.upper().strip()
    
    # Exact match
    if plate1 == plate2:
        return 1.0, True, 'exact'
    
    # Normalized match (OCR confusions)
    normalized1 = normalize_ocr_confusions(plate1)
    normalized2 = normalize_ocr_confusions(plate2)
    
    if normalized1 == normalized2:
        return 0.98, True, 'normalized'
    
    base_ratio = difflib.SequenceMatcher(None, plate1, plate2).ratio()
    normalized_ratio = difflib.SequenceMatcher(None, normalized1, normalized2).ratio()
    
    # Structure-aware comparison
    parts1 = extract_plate_parts(plate1)
    parts2 = extract_plate_parts(plate2)
    
    # Both Bharat series
    if parts1['format'] == 'bharat_series' and parts2['format'] == 'bharat_series':
        num_match = parts1['number'] == parts2['number']
        series_match = parts1['series'] == parts2['series']
        
        if num_match and series_match:
            year_match = parts1['district'] == parts2['district']
            return 0.98 if year_match else 0.90, True, 'fuzzy_high'
        elif normalize_ocr_confusions(parts1['number']) == normalize_ocr_confusions(parts2['number']):
            return 0.95, True, 'normalized'
        else:
            return base_ratio, False, 'prefix_only'
    
    # Both standard format
    if parts1['format'] in ['standard', 'standard_unverified'] and \
       parts2['format'] in ['standard', 'standard_unverified']:
        
        same_state = parts1['state'] == parts2['state'] or \
                    normalize_ocr_confusions(parts1['state']) == normalize_ocr_confusions(parts2['state'])
        same_district = parts1['district'] == parts2['district']
        series_match = parts1['series'] == parts2['series'] or \
                      normalize_ocr_confusions(parts1['series']) == normalize_ocr_confusions(parts2['series'])
        
        num1, num2 = parts1['number'], parts2['number']
        
        if num1 and num2:
            if num1 == num2:
                num_similarity = 1.0
            else:
                norm_num1 = normalize_ocr_confusions(num1)
                norm_num2 = normalize_ocr_confusions(num2)
                if norm_num1 == norm_num2:
                    num_similarity = 0.95
                else:
                    num_similarity = difflib.SequenceMatcher(None, num1, num2).ratio()
        else:
            num_similarity = 0.0 if (num1 or num2) else 1.0
        
        if same_state and same_district and series_match:
            if num_similarity >= 0.9:
                return max(base_ratio, normalized_ratio), True, 'fuzzy_high'
            elif num_similarity >= 0.5:
                if normalized_ratio >= 0.90:
                    return normalized_ratio, True, 'fuzzy_high'
                else:
                    return base_ratio, False, 'fuzzy_low'
            else:
                return base_ratio, False, 'prefix_only'
        
        elif same_state and same_district and num_similarity >= 0.9:
            return max(base_ratio, 0.7), True, 'fuzzy_medium'
    
    # Generic fuzzy
    if normalized_ratio >= 0.90:
        return normalized_ratio, True, 'fuzzy_high'
    elif normalized_ratio >= 0.75:
        return normalized_ratio, False, 'fuzzy_medium'
    else:
        return base_ratio, False, 'fuzzy_low'


class OCRMatcher:
    """OCR exact match for license plates"""
    
    def __init__(self):
        self.entry_queries = get_entry_queries()
        self.metadata_manager = get_metadata_manager()
        self.min_ocr_confidence = config.MATCHING_MIN_OCR_CONFIDENCE
        
        logger.info("[OK] OCR matcher initialized")
    
    def find_ocr_matches(
        self,
        query_ocr_text: str,
        query_ocr_confidence: float,
        entry_transaction_ids: List[str],
        entry_timestamps: List[datetime]
    ) -> List[Tuple[str, float]]:
        """
        Find exact OCR matches from candidates
        
        Args:
            query_ocr_text: Exit vehicle OCR text
            query_ocr_confidence: Exit OCR confidence
            entry_transaction_ids: Candidate entry transaction IDs
            entry_timestamps: Candidate entry timestamps
        
        Returns:
            List of (transaction_id, match_score) tuples
        """
        if not query_ocr_text or query_ocr_confidence < self.min_ocr_confidence:
            return []
        
        matches = []
        
        # Get metadata for all candidates
        metadata_list = self.metadata_manager.get_batch_metadata(
            entry_transaction_ids,
            entry_timestamps
        )
        
        for tid, metadata in zip(entry_transaction_ids, metadata_list):
            if metadata is None:
                continue
            
            entry_ocr_text = metadata.get('ocr_text', '')
            entry_ocr_confidence = metadata.get('ocr_confidence', 0.0)
            
            if not entry_ocr_text or entry_ocr_confidence < self.min_ocr_confidence:
                continue
            
            # Structure-aware similarity matching
            similarity, is_likely_same, match_type = calculate_plate_similarity(
                query_ocr_text, entry_ocr_text
            )
            
            if is_likely_same and similarity >= 0.70:
                # Calculate score based on similarity and confidence
                base_score = query_ocr_confidence * entry_ocr_confidence
                match_score = base_score * similarity
                matches.append((tid, match_score))
                
                if match_type != 'exact':
                    logger.info(f"  {match_type.upper()} match: '{query_ocr_text}' ~ '{entry_ocr_text}' (sim={similarity:.3f})")
        
        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"[OK] Found {len(matches)} OCR exact matches for '{query_ocr_text}'")
        
        return matches
    
    def build_ocr_index(self, partition_key: str):
        """
        Build OCR text index for partition (for faster lookup)
        This is a placeholder for future optimization
        
        Args:
            partition_key: Partition key (YYYY-MM-DD)
        """
        # TODO: Implement inverted index for OCR text
        # For now, we use linear scan which is fast enough for daily partitions
        pass


# Global OCR matcher
_ocr_matcher = None

def get_ocr_matcher() -> OCRMatcher:
    """Get or create global OCR matcher instance"""
    global _ocr_matcher
    if _ocr_matcher is None:
        _ocr_matcher = OCRMatcher()
    return _ocr_matcher
