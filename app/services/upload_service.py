"""
Upload Service - Standalone Image Upload and Processing

Replaces ingestion_service.py with upload-based system.
No database dependencies - all images stored locally.

Features:
- Accept image uploads (File, UploadFile, or path)
- Generate UUID-based unique IDs
- Save to local date-partitioned directories
- Extract embeddings using existing embedding_engine
- Store vectors in FAISS
- Save enhanced metadata with image paths
"""

import uuid
import logging
import shutil
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from PIL import Image
import numpy as np

from fastapi import UploadFile

from .. import config
from ..core.embedding_engine import get_embedding_engine
from ..storage.faiss_manager import get_faiss_manager
from ..storage.metadata_manager import get_metadata_manager

logger = logging.getLogger(__name__)


class UploadService:
    """Service for uploading and processing vehicle images"""

    def __init__(self):
        self.embedding_engine = get_embedding_engine()
        self.faiss_manager = get_faiss_manager()
        self.metadata_manager = get_metadata_manager()

        # Upload directories
        self.upload_dir = config.DATA_DIR / 'uploads'
        self.entry_dir = self.upload_dir / 'entry'
        self.exit_dir = self.upload_dir / 'exit'

        # Create directories if they don't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.entry_dir.mkdir(parents=True, exist_ok=True)
        self.exit_dir.mkdir(parents=True, exist_ok=True)

        logger.info("[OK] Upload service initialized")

    def generate_unique_id(self, vehicle_type: str, timestamp: Optional[datetime] = None) -> str:
        """
        Generate unique vehicle ID

        Format: {type}_{timestamp}_{uuid}
        Example: entry_20260318_143052_a1b2c3d4

        Args:
            vehicle_type: "entry" or "exit"
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Unique ID string
        """
        if timestamp is None:
            timestamp = datetime.now()

        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        short_uuid = str(uuid.uuid4())[:8]

        return f"{vehicle_type}_{timestamp_str}_{short_uuid}"

    def _get_upload_directory(self, vehicle_type: str, timestamp: datetime) -> Path:
        """
        Get date-partitioned upload directory

        Args:
            vehicle_type: "entry" or "exit"
            timestamp: Upload timestamp

        Returns:
            Path to directory (e.g., data/uploads/entry/2026-03-18/)
        """
        base_dir = self.entry_dir if vehicle_type == "entry" else self.exit_dir
        date_str = timestamp.strftime('%Y-%m-%d')
        date_dir = base_dir / date_str

        # Create if doesn't exist
        date_dir.mkdir(parents=True, exist_ok=True)

        return date_dir

    def _get_image_extension(self, filename: str) -> str:
        """
        Get image extension from filename

        Args:
            filename: Original filename

        Returns:
            Extension (e.g., '.jpg')
        """
        ext = Path(filename).suffix.lower()

        # Default to .jpg if no extension
        if not ext or ext not in ['.jpg', '.jpeg', '.png', '.bmp']:
            ext = '.jpg'

        return ext

    async def save_uploaded_file(
        self,
        file: UploadFile,
        unique_id: str,
        vehicle_type: str,
        timestamp: datetime
    ) -> Path:
        """
        Save uploaded file to local storage

        Args:
            file: FastAPI UploadFile object
            unique_id: Generated unique ID
            vehicle_type: "entry" or "exit"
            timestamp: Upload timestamp

        Returns:
            Path to saved image file
        """
        try:
            # Get upload directory
            upload_dir = self._get_upload_directory(vehicle_type, timestamp)

            # Get file extension
            ext = self._get_image_extension(file.filename)

            # Create filename: entry_20260318_143052_a1b2c3d4.jpg
            filename = f"{unique_id}{ext}"
            file_path = upload_dir / filename

            # Save file
            with open(file_path, 'wb') as f:
                # Read in chunks to handle large files
                content = await file.read()
                f.write(content)

            logger.info(f"[OK] Saved image to {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}")
            raise

    def _get_image_info(self, image_path: Path) -> Dict[str, Any]:
        """
        Get image metadata (size, dimensions)

        Args:
            image_path: Path to image file

        Returns:
            Dict with file_size_bytes and image_dimensions
        """
        try:
            # File size
            file_size_bytes = image_path.stat().st_size

            # Image dimensions
            with Image.open(image_path) as img:
                image_dimensions = (img.width, img.height)

            return {
                'file_size_bytes': file_size_bytes,
                'image_dimensions': image_dimensions
            }

        except Exception as e:
            logger.warning(f"Could not get image info for {image_path}: {e}")
            return {
                'file_size_bytes': 0,
                'image_dimensions': (0, 0)
            }

    async def upload_vehicle_image(
        self,
        file: UploadFile,
        vehicle_type: str,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Upload and process vehicle image

        Main entry point for image upload workflow.

        Args:
            file: FastAPI UploadFile object
            vehicle_type: "entry" or "exit"
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Dict containing:
                - unique_id: Generated ID
                - image_path: Local path to saved image
                - vehicle_type: Vehicle type
                - timestamp: ISO timestamp
                - ocr_text: Extracted license plate text
                - ocr_confidence: OCR confidence score
                - embedding_extracted: Whether ReID embedding was extracted
                - processing_time_ms: Processing time in milliseconds
                - success: Boolean success flag
                - error: Error message if failed
        """
        start_time = time.time()
        result = {
            'success': False,
            'error': None
        }

        try:
            # Validate vehicle type
            if vehicle_type not in ['entry', 'exit']:
                raise ValueError(f"Invalid vehicle_type: {vehicle_type}. Must be 'entry' or 'exit'")

            # Default timestamp to now
            if timestamp is None:
                timestamp = datetime.now()

            # Generate unique ID
            unique_id = self.generate_unique_id(vehicle_type, timestamp)
            result['unique_id'] = unique_id
            result['vehicle_type'] = vehicle_type
            result['timestamp'] = timestamp.isoformat()

            # Save uploaded file
            image_path = await self.save_uploaded_file(file, unique_id, vehicle_type, timestamp)
            result['image_path'] = str(image_path)

            # Get image info
            image_info = self._get_image_info(image_path)

            # Extract embeddings using existing embedding_engine
            logger.info(f"[PROCESS] Extracting embeddings for {unique_id}")
            embedding_data = self.embedding_engine.process_image(str(image_path))

            if embedding_data is None:
                raise Exception("Failed to extract embeddings")

            # Store in FAISS
            partition_key = self.faiss_manager._get_partition_key(timestamp)
            embedding_vector = embedding_data.reid_embedding.reshape(1, -1)

            self.faiss_manager.add_vectors(
                partition_key=partition_key,
                vectors=embedding_vector,
                transaction_ids=[unique_id]
            )

            logger.info(f"[OK] Added vector to FAISS partition {partition_key}")

            # Prepare metadata
            metadata_dict = {
                'color_histogram': embedding_data.color_hist,
                'ocr_text': embedding_data.ocr_text or '',
                'ocr_confidence': embedding_data.ocr_conf,
                'bbox': embedding_data.bbox,
                'plate_bbox': None,  # Not extracted separately yet
                'aspect_ratio': embedding_data.aspect_ratio,
                'vehicle_confidence': embedding_data.vehicle_conf
            }

            # Save enhanced metadata with image path
            self.metadata_manager.save_metadata(
                transaction_id=unique_id,
                timestamp=timestamp,
                embedding_data=metadata_dict,
                image_path=str(image_path),
                original_filename=file.filename,
                vehicle_type=vehicle_type,
                file_size_bytes=image_info['file_size_bytes'],
                image_dimensions=image_info['image_dimensions']
            )

            logger.info(f"[OK] Saved metadata for {unique_id}")

            # Build result
            result.update({
                'success': True,
                'ocr_text': embedding_data.ocr_text or '',
                'ocr_confidence': float(embedding_data.ocr_conf),
                'embedding_extracted': True,
                'vehicle_confidence': float(embedding_data.vehicle_conf),
                'bbox': embedding_data.bbox,
                'aspect_ratio': float(embedding_data.aspect_ratio),
                'file_size_bytes': image_info['file_size_bytes'],
                'image_dimensions': list(image_info['image_dimensions']),
                'original_filename': file.filename
            })

        except Exception as e:
            logger.error(f"Failed to process upload: {e}")
            result['success'] = False
            result['error'] = str(e)

        finally:
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            result['processing_time_ms'] = round(processing_time_ms, 2)

        return result

    async def upload_batch(
        self,
        files: List[UploadFile],
        vehicle_types: List[str],
        timestamps: Optional[List[datetime]] = None
    ) -> Dict[str, Any]:
        """
        Upload and process batch of vehicle images

        Args:
            files: List of UploadFile objects
            vehicle_types: List of vehicle types ("entry" or "exit")
            timestamps: Optional list of timestamps

        Returns:
            Dict containing:
                - uploaded: List of successful upload results
                - failed: List of failed uploads with errors
                - total_uploaded: Count of successful uploads
                - total_failed: Count of failed uploads
                - processing_time_ms: Total processing time
        """
        start_time = time.time()

        # Validate inputs
        if len(files) != len(vehicle_types):
            raise ValueError("Length of files and vehicle_types must match")

        if timestamps is None:
            timestamps = [datetime.now() for _ in files]
        elif len(timestamps) != len(files):
            raise ValueError("Length of timestamps must match files")

        uploaded = []
        failed = []

        # Process each file
        for file, vehicle_type, timestamp in zip(files, vehicle_types, timestamps):
            try:
                result = await self.upload_vehicle_image(file, vehicle_type, timestamp)

                if result['success']:
                    uploaded.append(result)
                else:
                    failed.append({
                        'filename': file.filename,
                        'vehicle_type': vehicle_type,
                        'error': result.get('error', 'Unknown error')
                    })

            except Exception as e:
                failed.append({
                    'filename': file.filename,
                    'vehicle_type': vehicle_type,
                    'error': str(e)
                })

        # Calculate total processing time
        processing_time_ms = (time.time() - start_time) * 1000

        return {
            'uploaded': uploaded,
            'failed': failed,
            'total_uploaded': len(uploaded),
            'total_failed': len(failed),
            'processing_time_ms': round(processing_time_ms, 2)
        }

    def get_upload_stats(self) -> Dict[str, Any]:
        """
        Get upload statistics

        Returns:
            Dict containing:
                - total_images: Total uploaded images
                - entry_count: Entry vehicle count
                - exit_count: Exit vehicle count
                - date_range: Earliest and latest upload dates
                - storage_size_mb: Total storage used in MB
        """
        try:
            # Get all unique IDs from metadata
            all_entry_ids = self.metadata_manager.get_all_ids(vehicle_type='entry')
            all_exit_ids = self.metadata_manager.get_all_ids(vehicle_type='exit')

            # Calculate storage size
            storage_size_bytes = 0
            for directory in [self.entry_dir, self.exit_dir]:
                for file_path in directory.rglob('*'):
                    if file_path.is_file():
                        storage_size_bytes += file_path.stat().st_size

            storage_size_mb = storage_size_bytes / (1024 * 1024)

            # Get date range from directory structure
            date_dirs = []
            for directory in [self.entry_dir, self.exit_dir]:
                date_dirs.extend([d.name for d in directory.iterdir() if d.is_dir()])

            date_range = None
            if date_dirs:
                sorted_dates = sorted(date_dirs)
                date_range = {
                    'earliest': sorted_dates[0],
                    'latest': sorted_dates[-1]
                }

            return {
                'total_images': len(all_entry_ids) + len(all_exit_ids),
                'entry_count': len(all_entry_ids),
                'exit_count': len(all_exit_ids),
                'date_range': date_range,
                'storage_size_mb': round(storage_size_mb, 2)
            }

        except Exception as e:
            logger.error(f"Failed to get upload stats: {e}")
            return {
                'total_images': 0,
                'entry_count': 0,
                'exit_count': 0,
                'date_range': None,
                'storage_size_mb': 0
            }


# Global upload service singleton
_upload_service = None


def get_upload_service() -> UploadService:
    """Get or create global upload service instance"""
    global _upload_service
    if _upload_service is None:
        _upload_service = UploadService()
    return _upload_service
