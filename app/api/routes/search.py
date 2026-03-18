"""
Search endpoint for vehicle matching
"""
from fastapi import APIRouter, HTTPException, Query, Body
from datetime import datetime
from typing import Optional
from pathlib import Path
import time
import logging

from ..models.responses import SearchRequest, SearchResponse, MatchResult
from ...matching.matching_engine import get_matching_engine
from ... import config

logger = logging.getLogger(__name__)

# Router WITH prefix for /api/search endpoints
router = APIRouter(prefix="/api", tags=["search"])

# Additional router WITHOUT prefix for /search endpoint
router_no_prefix = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
@router_no_prefix.post("/search", response_model=SearchResponse)
async def search_matches(request: SearchRequest):
    """
    Search for matching ENTRY vehicles given EXIT transaction ID
    
    **Workflow:**
    1. Fetch EXIT transaction data from database by ID
    2. Extract features from exit vehicle image (ReID, OCR, color)
    3. OCR exact matching (if license plate detected)
    4. Embedding similarity search using FAISS
    5. Multi-feature scoring (embedding, color, time, scale)
    6. Re-rank with OCR boost
    7. Return matched ENTRY transaction IDs
    
    **Request:**
    - `exit_transaction_id`: EXIT transaction ID (required)
    - `top_k`: Number of matches to return (optional, default: 10)
    
    **Response:**
    - `exit_transaction_id`: EXIT transaction ID
    - `exit_timestamp`: EXIT transaction timestamp
    - `matched_entry_transaction_ids`: List of matched ENTRY IDs
    - `matches_found`: Count of matches
    - `processing_time_seconds`: Processing time in seconds
    - `error`: Error message if failed
    """
    start_time = time.time()
    
    try:
        logger.info(f"[SEARCH] POST request for exit_transaction_id: {request.exit_transaction_id}")
        
        # Fetch EXIT transaction from database
        from ...database.exit_queries import get_exit_queries
        
        exit_queries = get_exit_queries()
        exit_tx = exit_queries.get_exit_by_id(request.exit_transaction_id)
        
        if not exit_tx:
            logger.error(f"EXIT transaction not found: {request.exit_transaction_id}")
            processing_time = time.time() - start_time
            return SearchResponse(
                exit_transaction_id=request.exit_transaction_id,
                exit_timestamp="",
                matched_entry_transaction_ids=[],
                matches_found=0,
                processing_time_seconds=round(processing_time, 3),
                error=f"EXIT transaction {request.exit_transaction_id} not found in database"
            )
        
        # Extract data
        exit_image_path = exit_tx.get('ANPR_IMAGE_PATH')
        exit_timestamp = exit_tx.get('ANPR_READ_TIME')
        
        if not exit_image_path:
            logger.error(f"No image path for transaction: {request.exit_transaction_id}")
            processing_time = time.time() - start_time
            return SearchResponse(
                exit_transaction_id=request.exit_transaction_id,
                exit_timestamp=exit_timestamp.isoformat() if exit_timestamp else "",
                matched_entry_transaction_ids=[],
                matches_found=0,
                processing_time_seconds=round(processing_time, 3),
                error="EXIT transaction has no image path"
            )
        
        if not exit_timestamp:
            logger.error(f"No timestamp for transaction: {request.exit_transaction_id}")
            processing_time = time.time() - start_time
            return SearchResponse(
                exit_transaction_id=request.exit_transaction_id,
                exit_timestamp="",
                matched_entry_transaction_ids=[],
                matches_found=0,
                processing_time_seconds=round(processing_time, 3),
                error="EXIT transaction has no timestamp"
            )
        
        # Validate image exists
        image_path = Path(exit_image_path)
        if not image_path.exists():
            logger.error(f"Image file not found: {exit_image_path}")
            processing_time = time.time() - start_time
            return SearchResponse(
                exit_transaction_id=request.exit_transaction_id,
                exit_timestamp=exit_timestamp.isoformat(),
                matched_entry_transaction_ids=[],
                matches_found=0,
                processing_time_seconds=round(processing_time, 3),
                error=f"Image file not found at: {exit_image_path}"
            )
        
        logger.info(f"  Image path: {exit_image_path}")
        logger.info(f"  Timestamp: {exit_timestamp}")
        logger.info(f"  Top K: {request.top_k}")
        
        # Get matching engine and find matches
        matching_engine = get_matching_engine()
        
        matches = matching_engine.find_matches(
            exit_image_path=exit_image_path,
            exit_timestamp=exit_timestamp,
            top_k=request.top_k
        )
        
        # Extract transaction IDs
        matched_ids = [m['transaction_id'] for m in matches]
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        logger.info(f"[OK] Search completed in {processing_time:.3f}s, {len(matched_ids)} matches")
        
        return SearchResponse(
            exit_transaction_id=request.exit_transaction_id,
            exit_timestamp=exit_timestamp.isoformat(),
            matched_entry_transaction_ids=matched_ids,
            matches_found=len(matched_ids),
            processing_time_seconds=round(processing_time, 3),
            error=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        
        processing_time = time.time() - start_time
        
        return SearchResponse(
            exit_transaction_id=request.exit_transaction_id,
            exit_timestamp="",
            matched_entry_transaction_ids=[],
            matches_found=0,
            processing_time_seconds=round(processing_time, 3),
            error=str(e)
        )


@router.get("/search/match", response_model=SearchResponse)
@router_no_prefix.get("/search/match", response_model=SearchResponse)
async def search_matches_get(
    exit_transaction_id: str = Query(..., description="EXIT transaction ID"),
    matching_method: str = Query("both", description="Matching method: both, ocr, embedding"),
    top_k: int = Query(10, description="Number of top matches to return"),
    time_window_hours: int = Query(12, description="Time window in hours to search"),
    min_score: float = Query(0.3, description="Minimum score threshold")
):
    """
    GET endpoint for vehicle matching (for frontend)
    
    Fetches EXIT transaction data from database then performs matching
    """
    start_time = time.time()
    
    try:
        logger.info(f"[SEARCH] GET request for exit_transaction_id: {exit_transaction_id}")
        
        # Fetch EXIT transaction from database
        from ...database.exit_queries import get_exit_queries
        
        exit_queries = get_exit_queries()
        exit_tx = exit_queries.get_exit_by_id(exit_transaction_id)
        
        if not exit_tx:
            logger.error(f"EXIT transaction not found: {exit_transaction_id}")
            raise HTTPException(
                status_code=404,
                detail=f"EXIT transaction {exit_transaction_id} not found in database"
            )
        
        # Extract data with correct field names
        exit_image_path = exit_tx.get('ANPR_IMAGE_PATH')
        exit_timestamp = exit_tx.get('ANPR_READ_TIME')
        
        if not exit_image_path:
            logger.error(f"No image path for transaction: {exit_transaction_id}")
            raise HTTPException(
                status_code=400,
                detail=f"EXIT transaction {exit_transaction_id} has no image path"
            )
        
        if not exit_timestamp:
            logger.error(f"No timestamp for transaction: {exit_transaction_id}")
            raise HTTPException(
                status_code=400,
                detail=f"EXIT transaction {exit_transaction_id} has no timestamp"
            )
        
        # Validate image path exists
        image_path = Path(exit_image_path)
        if not image_path.exists():
            logger.error(f"Image file not found: {exit_image_path}")
            raise HTTPException(
                status_code=404,
                detail=f"Image file not found at: {exit_image_path}"
            )
        
        logger.info(f"  Image path: {exit_image_path}")
        logger.info(f"  Timestamp: {exit_timestamp}")
        logger.info(f"  Top K: {top_k}")
        
        # Create search request with NEW format (transaction ID based)
        request = SearchRequest(
            exit_transaction_id=exit_transaction_id,
            top_k=top_k
        )
        
        # Perform search
        return await search_matches(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET search failed: {e}", exc_info=True)
        processing_time = (time.time() - start_time)
        
        # Return error response in NEW format
        return SearchResponse(
            exit_transaction_id=exit_transaction_id,
            exit_timestamp=exit_timestamp.isoformat() if exit_timestamp else "",
            matched_entry_transaction_ids=[],
            matches_found=0,
            processing_time_seconds=processing_time,
            error=str(e)
        )
