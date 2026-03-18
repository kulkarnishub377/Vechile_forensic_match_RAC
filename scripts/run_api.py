"""
Run API server
FastAPI application for vehicle matching
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from app import config

if __name__ == "__main__":
    uvicorn.run(
        "app.api.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_RELOAD,
        workers=config.API_WORKERS,
        log_level="info"
    )
