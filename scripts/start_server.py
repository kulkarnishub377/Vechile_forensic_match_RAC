#!/usr/bin/env python3
"""
Vehicle Re-Identification System - Startup Script
Simple launcher for the FastAPI application
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("Vehicle Re-Identification System v2.0")
    print("=" * 60)
    print("Starting server on http://localhost:8000")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
