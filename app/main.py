"""
🚗 Vehicle Re-Identification System
Single Unified Service - Image Upload + Real-time Matching
No Database Required - All In-Memory Processing
"""

from fastapi import FastAPI, UploadFile, File, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
import uuid
import time
import logging
from datetime import datetime
from pathlib import Path
import os

from app.services.session_manager import SessionManager
from app.services.image_storage import ImageStorage
from app.services.vehicle_detector import VehicleDetector
from app.services.embedding_generator import EmbeddingGenerator
from app.services.search_engine import SearchEngine
from app.config import LOG_LEVEL

# ═══════════════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════════════

# Logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI(
    title="🚗 Vehicle Re-Identification System",
    description="Image-Based Vehicle Matching (No Database)",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZIP Compression
app.add_middleware(GZIPMiddleware, minimum_size=1000)

# Static Files (Frontend)
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

# ═══════════════════════════════════════════════════════════════════
# SERVICES (Separated Concerns)
# ═══════════════════════════════════════════════════════════════════

session_manager = SessionManager()
image_storage = ImageStorage()
vehicle_detector = VehicleDetector()
embedding_generator = EmbeddingGenerator()
search_engine = SearchEngine()

app_start_time = time.time()

# ═══════════════════════════════════════════════════════════════════
# ROOT
# ═══════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main frontend"""
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        with open(index_path) as f:
            return f.read()
    return "<h1>Frontend not found</h1>"

# ═══════════════════════════════════════════════════════════════════
# FILE UPLOAD - (Image Storage Service)
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/upload")
async def upload_image(
    file: UploadFile = File(...),
    session_id: str = Query(None)
):
    """
    Upload vehicle image to session
    - Service: ImageStorage (handles upload)
    - Service: VehicleDetector (detects vehicle)
    - Service: EmbeddingGenerator (generates 512-D vector)
    """
    try:
        # Create session if needed
        if not session_id:
            session_id = session_manager.create_session()
        
        # Read file
        file_content = await file.read()
        
        # Store image (ImageStorage Service)
        image_id = image_storage.save_image(
            session_id=session_id,
            filename=file.filename,
            content=file_content
        )
        
        # Detect vehicle (VehicleDetector Service)
        detection_result = vehicle_detector.detect(
            image_id=image_id,
            image_data=file_content
        )
        
        if not detection_result["success"]:
            return JSONResponse({
                "error": "No vehicle detected in image",
                "image_id": image_id,
                "session_id": session_id
            }, status_code=400)
        
        # Generate embedding (EmbeddingGenerator Service)
        embedding = embedding_generator.generate(
            image_id=image_id,
            vehicle_region=detection_result["vehicle_region"]
        )
        
        if embedding is None:
            return JSONResponse({
                "error": "Failed to generate embedding",
                "image_id": image_id
            }, status_code=500)
        
        # Update storage with embedding
        image_storage.add_embedding(image_id, embedding)
        
        # Add to search index (SearchEngine Service)
        search_engine.add_to_index(image_id, embedding)
        
        logger.info(f"✓ Image uploaded: {image_id} | Session: {session_id[:8]}...")
        
        return {
            "success": True,
            "session_id": session_id,
            "image_id": image_id,
            "filename": file.filename,
            "vehicle_detected": True,
            "embedding_ready": True,
            "confidence": detection_result["confidence"]
        }
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return JSONResponse({
            "error": str(e)
        }, status_code=500)

# ═══════════════════════════════════════════════════════════════════
# IMAGE SEARCH - (Search Engine Service)
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/search")
async def search_vehicle(
    file: UploadFile = File(...),
    session_id: str = Query(...),
    threshold: float = Query(0.85, ge=0.0, le=1.0)
):
    """
    Search for similar vehicles in uploaded images
    - Service: VehicleDetector (detects in search image)
    - Service: EmbeddingGenerator (generates query embedding)
    - Service: SearchEngine (FAISS search)
    """
    try:
        # Validate session
        if not session_manager.session_exists(session_id):
            return JSONResponse({
                "error": "Session not found"
            }, status_code=404)
        
        if image_storage.get_image_count(session_id) == 0:
            return JSONResponse({
                "error": "No images in session for search"
            }, status_code=400)
        
        # Read search file
        file_content = await file.read()
        
        # Detect vehicle in search image (VehicleDetector Service)
        detection = vehicle_detector.detect(
            image_id="search_temp",
            image_data=file_content
        )
        
        if not detection["success"]:
            return JSONResponse({
                "error": "No vehicle detected in search image"
            }, status_code=400)
        
        # Generate search embedding (EmbeddingGenerator Service)
        query_embedding = embedding_generator.generate(
            image_id="search_query",
            vehicle_region=detection["vehicle_region"]
        )
        
        # Search index (SearchEngine Service)
        start_time = time.time()
        matches = search_engine.search(
            query_embedding=query_embedding,
            threshold=threshold,
            top_k=50
        )
        search_time = (time.time() - start_time) * 1000  # ms
        
        # Enrich with metadata
        results = []
        for match in matches:
            image_info = image_storage.get_image_info(match["image_id"])
            if image_info:
                results.append({
                    "image_id": match["image_id"],
                    "filename": image_info["filename"],
                    "match_score": round(match["score"], 3),
                    "match_type": "confident" if match["score"] >= 0.92 else "probable",
                    "upload_time": image_info["upload_time"]
                })
        
        results = sorted(results, key=lambda x: x["match_score"], reverse=True)
        
        logger.info(f"✓ Search completed: {len(results)} matches in {search_time:.1f}ms")
        
        return {
            "success": True,
            "matches": results,
            "total_matches": len(results),
            "search_time_ms": search_time,
            "threshold_used": threshold
        }
    
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return JSONResponse({
            "error": str(e)
        }, status_code=500)

# ═══════════════════════════════════════════════════════════════════
# RESULTS - Get session images
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/results/{session_id}")
async def get_results(session_id: str):
    """Get all images in session"""
    try:
        if not session_manager.session_exists(session_id):
            return JSONResponse({
                "error": "Session not found"
            }, status_code=404)
        
        images = image_storage.get_session_images(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "total_images": len(images),
            "images": images
        }
    
    except Exception as e:
        logger.error(f"Results error: {str(e)}")
        return JSONResponse({
            "error": str(e)
        }, status_code=500)

# ═══════════════════════════════════════════════════════════════════
# CLEAR SESSION
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/clear/{session_id}")
async def clear_session(session_id: str):
    """Clear all images in session"""
    try:
        image_storage.clear_session(session_id)
        session_manager.clear_session(session_id)
        search_engine.clear_session_index(session_id)
        
        logger.info(f"✓ Session cleared: {session_id[:8]}...")
        
        return {
            "success": True,
            "message": "Session cleared"
        }
    
    except Exception as e:
        logger.error(f"Clear error: {str(e)}")
        return JSONResponse({
            "error": str(e)
        }, status_code=500)

# ═══════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    """System health check"""
    uptime = int(time.time() - app_start_time)
    
    return {
        "status": "healthy",
        "uptime_seconds": uptime,
        "models_ready": vehicle_detector.ready and embedding_generator.ready,
        "active_sessions": session_manager.get_active_count(),
        "total_images_indexed": search_engine.get_index_size(),
        "version": "2.0.0"
    }

# ═══════════════════════════════════════════════════════════════════
# STARTUP / SHUTDOWN
# ═══════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup():
    """Initialize all services on startup"""
    logger.info("=" * 60)
    logger.info("🚗 Vehicle Re-ID System Starting (No Database Mode)")
    logger.info("=" * 60)
    
    try:
        logger.info("Loading YOLO detector...")
        vehicle_detector.initialize()
        logger.info("✓ YOLO detector ready")
        
        logger.info("Loading OSNet-AIN embedder...")
        embedding_generator.initialize()
        logger.info("✓ OSNet-AIN embedder ready")
        
        logger.info("Initializing FAISS search...")
        search_engine.initialize()
        logger.info("✓ FAISS search ready")
        
        logger.info("=" * 60)
        logger.info("✓ All services initialized successfully")
        logger.info("🌐 API available at: http://localhost:8000")
        logger.info("📖 Documentation at: http://localhost:8000/docs")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("Shutting down services...")
    image_storage.cleanup()
    search_engine.cleanup()
    logger.info("✓ All services shutdown")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
