from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
from pathlib import Path

from .routes import search, health, upload, image
from .. import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOGS_DIR / 'api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vehicle Matching Service",
    description="Dual-path matching: OCR-first + embedding fusion",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router)  # /api/search endpoints
app.include_router(search.router_no_prefix)  # /search endpoints (no prefix)
app.include_router(health.router)
app.include_router(upload.router)  # NEW - /api/upload endpoints
app.include_router(image.router)   # NEW - /api/image/{unique_id} endpoint (CRITICAL!)

# Mount static files BEFORE catch-all
frontend_dir = Path(__file__).parent.parent.parent / 'frontend'
if frontend_dir.exists():
    # Mount CSS and JS as separate static directories
    css_dir = frontend_dir / 'css'
    js_dir = frontend_dir / 'js'
    
    if css_dir.exists():
        app.mount("/static/css", StaticFiles(directory=str(css_dir)), name="css")
    if js_dir.exists():
        app.mount("/static/js", StaticFiles(directory=str(js_dir)), name="js")
    
    # Mount the root HTML
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    logger.info(f"[OK] Mounted frontend from {frontend_dir}")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("=" * 60)
    logger.info("[INFO] Vehicle Matching Service Starting...")
    logger.info("=" * 60)
    
    # Pre-load models (lazy loading will happen on first request if not done here)
    try:
        from ..core.reid_models import get_reid_model
        from ..core.yolo_detector import get_vehicle_detector
        from ..core.ocr_engine import get_ocr_engine
        
        logger.info("Loading AI models...")
        reid_model = get_reid_model()
        vehicle_detector = get_vehicle_detector()
        ocr_engine = get_ocr_engine()
        
        logger.info("[OK] All models loaded successfully")
    except Exception as e:
        logger.error(f"[WARN] Model loading failed: {e}")
        logger.warning("Models will be loaded on first request")

    # NOTE: Database initialization removed - system is now standalone
    # Images are uploaded locally instead of fetched from database

    # Initialize FAISS manager
    try:
        from ..storage.faiss_manager import get_faiss_manager
        faiss_mgr = get_faiss_manager()
        logger.info("[OK] FAISS manager initialized")
    except Exception as e:
        logger.error(f"[WARN] FAISS initialization failed: {e}")
    
    logger.info("=" * 60)
    logger.info("[OK] Service ready to accept requests")
    logger.info(f"  API docs: http://localhost:{config.API_PORT}/docs")
    logger.info(f"  Frontend: http://localhost:{config.API_PORT}/")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Vehicle Matching Service...")

    # NOTE: Database cleanup removed - system is now standalone

    # Clear FAISS cache
    try:
        from ..storage.faiss_manager import get_faiss_manager
        faiss_mgr = get_faiss_manager()
        faiss_mgr.clear_cache()
        logger.info("[OK] FAISS cache cleared")
    except Exception as e:
        logger.error(f"Error clearing FAISS cache: {e}")
    
    logger.info("[OK] Service stopped")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.api.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_RELOAD,
        workers=config.API_WORKERS
    )
