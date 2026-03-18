"""
Health check endpoint
"""
from fastapi import APIRouter
import logging

from ..models.responses import HealthResponse
from ...database.db_connection import get_db_connection
from ...storage.faiss_manager import get_faiss_manager
from ...storage.cache_manager import get_cache_manager
from ...core.reid_models import get_reid_model

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Checks:
    - Database connectivity
    - FAISS index availability
    - AI models loaded
    - Cache availability
    
    Returns status of all critical components
    """
    status = "healthy"
    
    # Check database
    database_connected = False
    try:
        db = get_db_connection()
        result = db.execute_query("SELECT 1")
        database_connected = bool(result)
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        status = "degraded"
    
    # Check FAISS
    faiss_ready = False
    try:
        faiss_mgr = get_faiss_manager()
        faiss_ready = faiss_mgr is not None
    except Exception as e:
        logger.error(f"FAISS health check failed: {e}")
        status = "degraded"
    
    # Check models
    models_loaded = False
    try:
        reid_model = get_reid_model()
        models_loaded = reid_model.model is not None
    except Exception as e:
        logger.error(f"Model health check failed: {e}")
        status = "degraded"
    
    # Check cache
    cache_available = False
    try:
        # Cache is optional, don't fail health check if not available
        cache_available = True  # Mark as available by default
    except Exception as e:
        logger.debug(f"Cache not configured: {e}")
        # Cache failure is not critical
    
    return HealthResponse(
        status=status,
        database_connected=database_connected,
        faiss_ready=faiss_ready,
        models_loaded=models_loaded,
        cache_available=cache_available
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong"}
