"""
Upload API Endpoints

New endpoints for standalone image upload workflow:
- POST /api/upload/entry - Upload entry vehicle image
- POST /api/upload/exit - Upload exit vehicle image
- POST /api/upload/batch - Batch upload multiple images
- GET /api/uploads/stats - Get upload statistics
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from ...services.upload_service import get_upload_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["upload"])


# Response models
class UploadResponse(BaseModel):
    """Response for single image upload"""
    success: bool
    unique_id: Optional[str] = None
    image_path: Optional[str] = None
    vehicle_type: Optional[str] = None
    timestamp: Optional[str] = None
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    embedding_extracted: Optional[bool] = None
    vehicle_confidence: Optional[float] = None
    processing_time_ms: Optional[float] = None
    error: Optional[str] = None


class BatchUploadResponse(BaseModel):
    """Response for batch upload"""
    uploaded: List[dict]
    failed: List[dict]
    total_uploaded: int
    total_failed: int
    processing_time_ms: float


class UploadStatsResponse(BaseModel):
    """Response for upload statistics"""
    total_images: int
    entry_count: int
    exit_count: int
    date_range: Optional[dict]
    storage_size_mb: float


@router.post("/entry", response_model=UploadResponse)
async def upload_entry_image(
    file: UploadFile = File(..., description="Entry vehicle image file"),
    timestamp: Optional[str] = Form(None, description="Vehicle timestamp (ISO format, optional)")
):
    """
    Upload entry vehicle image

    Saves image locally, extracts embeddings, stores in FAISS.

    Args:
        file: Image file (JPEG/PNG/BMP)
        timestamp: Optional ISO format timestamp (defaults to current time)

    Returns:
        UploadResponse with unique_id and processing results

    Example:
        ```
        curl -X POST http://localhost:8899/api/upload/entry \\
          -F "file=@entry_vehicle.jpg" \\
          -F "timestamp=2026-03-18T10:00:00"
        ```
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Must be an image."
            )

        # Parse timestamp
        timestamp_dt = None
        if timestamp:
            try:
                timestamp_dt = datetime.fromisoformat(timestamp)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid timestamp format: {timestamp}. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )

        # Upload and process
        upload_service = get_upload_service()
        result = await upload_service.upload_vehicle_image(
            file=file,
            vehicle_type="entry",
            timestamp=timestamp_dt
        )

        return UploadResponse(**result)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to upload entry image: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/exit", response_model=UploadResponse)
async def upload_exit_image(
    file: UploadFile = File(..., description="Exit vehicle image file"),
    timestamp: Optional[str] = Form(None, description="Vehicle timestamp (ISO format, optional)")
):
    """
    Upload exit vehicle image

    Same as /entry but for exit vehicles.

    Args:
        file: Image file (JPEG/PNG/BMP)
        timestamp: Optional ISO format timestamp (defaults to current time)

    Returns:
        UploadResponse with unique_id and processing results
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Must be an image."
            )

        # Parse timestamp
        timestamp_dt = None
        if timestamp:
            try:
                timestamp_dt = datetime.fromisoformat(timestamp)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid timestamp format: {timestamp}. Use ISO format"
                )

        # Upload and process
        upload_service = get_upload_service()
        result = await upload_service.upload_vehicle_image(
            file=file,
            vehicle_type="exit",
            timestamp=timestamp_dt
        )

        return UploadResponse(**result)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to upload exit image: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/batch", response_model=BatchUploadResponse)
async def upload_batch(
    files: List[UploadFile] = File(..., description="Multiple image files"),
    vehicle_types: List[str] = Form(..., description="Vehicle types (entry/exit) for each file"),
    timestamps: Optional[List[str]] = Form(None, description="Optional timestamps for each file")
):
    """
    Batch upload multiple vehicle images

    Processes multiple images in a single request.

    Args:
        files: List of image files
        vehicle_types: List of vehicle types ("entry" or "exit") matching files
        timestamps: Optional list of ISO format timestamps

    Returns:
        BatchUploadResponse with success/failure lists

    Example:
        ```
        curl -X POST http://localhost:8899/api/upload/batch \\
          -F "files=@img1.jpg" \\
          -F "files=@img2.jpg" \\
          -F "vehicle_types=entry" \\
          -F "vehicle_types=exit"
        ```
    """
    try:
        # Validate inputs
        if len(files) != len(vehicle_types):
            raise HTTPException(
                status_code=400,
                detail=f"Length mismatch: {len(files)} files but {len(vehicle_types)} vehicle_types"
            )

        # Validate vehicle types
        for vtype in vehicle_types:
            if vtype not in ['entry', 'exit']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid vehicle_type: {vtype}. Must be 'entry' or 'exit'"
                )

        # Parse timestamps
        timestamps_dt = None
        if timestamps:
            if len(timestamps) != len(files):
                raise HTTPException(
                    status_code=400,
                    detail=f"Length mismatch: {len(files)} files but {len(timestamps)} timestamps"
                )

            timestamps_dt = []
            for ts in timestamps:
                try:
                    timestamps_dt.append(datetime.fromisoformat(ts))
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid timestamp format: {ts}"
                    )

        # Upload batch
        upload_service = get_upload_service()
        result = await upload_service.upload_batch(
            files=files,
            vehicle_types=vehicle_types,
            timestamps=timestamps_dt
        )

        return BatchUploadResponse(**result)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to upload batch: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch upload failed: {str(e)}"
        )


@router.get("/stats", response_model=UploadStatsResponse)
async def get_upload_stats():
    """
    Get upload statistics

    Returns counts and storage info for uploaded images.

    Returns:
        UploadStatsResponse with image counts and storage size

    Example:
        ```
        curl http://localhost:8899/api/upload/stats
        ```
    """
    try:
        upload_service = get_upload_service()
        stats = upload_service.get_upload_stats()

        return UploadStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get upload stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )
