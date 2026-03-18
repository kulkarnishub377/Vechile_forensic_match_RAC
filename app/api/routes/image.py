"""
Image Serving API - CRITICAL Missing Endpoint

GET /api/image/{unique_id} - Serve vehicle images by ID

ISSUE: Frontend currently calls this endpoint but it doesn't exist (404 errors!)
SOLUTION: Look up image_path in metadata and serve file

This endpoint is essential for:
- Displaying search results in frontend
- Image gallery view
- Lightbox image preview
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ...storage.metadata_manager import get_metadata_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["images"])


@router.get("/image/{unique_id}")
async def get_image(unique_id: str):
    """
    Serve vehicle image by unique ID

    **CRITICAL ENDPOINT** - Frontend depends on this for image display

    Args:
        unique_id: Unique vehicle ID (e.g., "entry_20260318_143052_a1b2c3d4")

    Returns:
        Image file (JPEG/PNG) with caching headers

    Raises:
        404: Image not found (metadata missing or file missing)
    """
    try:
        # Get metadata to find image path
        metadata_manager = get_metadata_manager()
        metadata = metadata_manager.get_metadata_by_id(unique_id)

        if not metadata:
            logger.warning(f"[404] Metadata not found for {unique_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Image not found: {unique_id}"
            )

        # Get image path from metadata
        image_path_str = metadata.get('image_path')

        if not image_path_str:
            logger.warning(f"[404] No image_path in metadata for {unique_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Image path not found in metadata: {unique_id}"
            )

        image_path = Path(image_path_str)

        # Check if file exists
        if not image_path.exists():
            logger.warning(f"[404] Image file does not exist: {image_path}")
            raise HTTPException(
                status_code=404,
                detail=f"Image file not found: {image_path.name}"
            )

        # Serve file with caching headers
        return FileResponse(
            path=str(image_path),
            media_type="image/jpeg",  # Default to JPEG, browser will handle others
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "X-Vehicle-ID": unique_id
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Error serving image {unique_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.head("/image/{unique_id}")
async def check_image_exists(unique_id: str):
    """
    Check if image exists without downloading it

    Args:
        unique_id: Unique vehicle ID

    Returns:
        200: Image exists
        404: Image not found
    """
    try:
        # Get metadata
        metadata_manager = get_metadata_manager()
        metadata = metadata_manager.get_metadata_by_id(unique_id)

        if not metadata:
            raise HTTPException(status_code=404, detail="Image not found")

        # Check if file exists
        image_path_str = metadata.get('image_path')
        if not image_path_str or not Path(image_path_str).exists():
            raise HTTPException(status_code=404, detail="Image file not found")

        return {"exists": True}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error checking image {unique_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
