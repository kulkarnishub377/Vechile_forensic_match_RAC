import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging
import numpy as np
import threading

from .. import config

logger = logging.getLogger(__name__)


class MetadataManager:
    """Manage vehicle metadata storage (thread-safe)"""
    
    def __init__(self):
        self.metadata_dir = config.DATA_DIR / 'metadata'
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self.cache = {}
        
        # Thread-safe file writes
        self._write_locks = {}  # One lock per partition file
        self._locks_lock = threading.Lock()  # Lock to create locks
        
        logger.info("[OK] Metadata manager initialized")
    
    def _get_partition_key(self, timestamp: datetime) -> str:
        """Get partition key from timestamp (YYYY-MM-DD)"""
        return timestamp.strftime('%Y-%m-%d')
    
    def _get_metadata_path(self, partition_key: str) -> Path:
        """Get metadata file path for partition"""
        return self.metadata_dir / f"{partition_key}.json"
    
    def _get_partition_lock(self, partition_key: str) -> threading.Lock:
        """Get or create lock for partition file (thread-safe)"""
        with self._locks_lock:
            if partition_key not in self._write_locks:
                self._write_locks[partition_key] = threading.Lock()
            return self._write_locks[partition_key]
    
    def save_metadata(
        self,
        transaction_id: str,
        timestamp: datetime,
        embedding_data: Dict,
        image_path: Optional[str] = None,
        original_filename: Optional[str] = None,
        vehicle_type: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        image_dimensions: Optional[tuple] = None
    ):
        """
        Save metadata for single vehicle (thread-safe)

        Args:
            transaction_id: Transaction ID (or unique_id for uploads)
            timestamp: Transaction timestamp
            embedding_data: Dict with keys:
                - color_histogram: 2048-D array (saved as list)
                - ocr_text: str
                - ocr_confidence: float
                - bbox: [x1, y1, x2, y2]
                - plate_bbox: [x1, y1, x2, y2] or None
                - aspect_ratio: float
                - vehicle_confidence: float
            image_path: Local path to image file (NEW - for uploads)
            original_filename: Original uploaded filename (NEW)
            vehicle_type: "entry" or "exit" (NEW)
            file_size_bytes: Image file size in bytes (NEW)
            image_dimensions: [width, height] (NEW)
        """
        try:
            partition_key = self._get_partition_key(timestamp)
            metadata_path = self._get_metadata_path(partition_key)
            
            # Get partition-specific lock
            partition_lock = self._get_partition_lock(partition_key)
            
            # Thread-safe file read/modify/write
            with partition_lock:
                # Load existing metadata with corruption recovery
                partition_data = {}
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            partition_data = json.load(f)
                    except json.JSONDecodeError as e:
                        # JSON is corrupted - backup and start fresh
                        backup_path = metadata_path.with_suffix(f'.corrupted_{int(timestamp.timestamp())}.bak')
                        metadata_path.rename(backup_path)
                        logger.warning(f"[RECOVERED] Corrupted metadata file backed up to {backup_path.name}, starting fresh")
                        partition_data = {}
                    except Exception as e:
                        logger.error(f"Failed to load metadata: {e}, starting fresh")
                        partition_data = {}
                
                # Convert numpy arrays to lists for JSON serialization
                serializable_data = {
                    'transaction_id': transaction_id,
                    'timestamp': timestamp.isoformat(),
                    'color_histogram': embedding_data['color_histogram'].tolist() if isinstance(embedding_data['color_histogram'], np.ndarray) else embedding_data['color_histogram'],
                    'ocr_text': embedding_data['ocr_text'],
                    'ocr_confidence': embedding_data['ocr_confidence'],
                    'bbox': embedding_data['bbox'],
                    'plate_bbox': embedding_data['plate_bbox'],
                    'aspect_ratio': embedding_data['aspect_ratio'],
                    'vehicle_confidence': embedding_data['vehicle_confidence']
                }
                
                # Add to partition
                partition_data[transaction_id] = serializable_data
                
                # Save atomically (write to temp, then rename)
                temp_path = metadata_path.with_suffix('.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(partition_data, f, indent=2)
                
                # Atomic rename (works on Windows when target doesn't exist or is not open)
                if metadata_path.exists():
                    metadata_path.unlink()  # Delete first on Windows
                temp_path.rename(metadata_path)
            
            # Update cache outside lock
            if partition_key not in self.cache:
                self.cache[partition_key] = {}
            self.cache[partition_key][transaction_id] = serializable_data
        
        except Exception as e:
            logger.error(f"Failed to save metadata for {transaction_id}: {e}")
    
    def save_batch_metadata(
        self,
        transaction_ids: List[str],
        timestamps: List[datetime],
        embedding_data_list: List[Dict]
    ):
        """
        Save metadata for batch of vehicles
        
        Args:
            transaction_ids: List of transaction IDs
            timestamps: List of timestamps
            embedding_data_list: List of embedding data dicts
        """
        # Group by partition
        partitions = {}
        
        for tid, ts, data in zip(transaction_ids, timestamps, embedding_data_list):
            partition_key = self._get_partition_key(ts)
            
            if partition_key not in partitions:
                partitions[partition_key] = []
            
            partitions[partition_key].append((tid, ts, data))
        
        # Save each partition (thread-safe)
        for partition_key, items in partitions.items():
            try:
                metadata_path = self._get_metadata_path(partition_key)
                partition_lock = self._get_partition_lock(partition_key)
                
                # Thread-safe file read/modify/write
                with partition_lock:
                    # Load existing with corruption recovery
                    partition_data = {}
                    if metadata_path.exists():
                        try:
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                partition_data = json.load(f)
                        except json.JSONDecodeError as e:
                            # JSON is corrupted - backup and start fresh
                            backup_path = metadata_path.with_suffix(f'.corrupted_{int(datetime.now().timestamp())}.bak')
                            metadata_path.rename(backup_path)
                            logger.warning(f"[RECOVERED] Corrupted metadata file backed up to {backup_path.name}, starting fresh")
                            partition_data = {}
                        except Exception as e:
                            logger.error(f"Failed to load metadata: {e}, starting fresh")
                            partition_data = {}
                    
                    # Add new items
                    for tid, ts, data in items:
                        serializable_data = {
                            'transaction_id': tid,
                            'timestamp': ts.isoformat(),
                            'color_histogram': data['color_histogram'].tolist() if isinstance(data['color_histogram'], np.ndarray) else data['color_histogram'],
                            'ocr_text': data['ocr_text'],
                            'ocr_confidence': data['ocr_confidence'],
                            'bbox': data['bbox'],
                            'plate_bbox': data['plate_bbox'],
                            'aspect_ratio': data['aspect_ratio'],
                            'vehicle_confidence': data['vehicle_confidence']
                        }
                        
                        partition_data[tid] = serializable_data
                    
                    # Save atomically (write to temp, then rename)
                    temp_path = metadata_path.with_suffix('.tmp')
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        json.dump(partition_data, f, indent=2)
                    
                    # Atomic rename (works on Windows when target doesn't exist or is not open)
                    if metadata_path.exists():
                        metadata_path.unlink()  # Delete first on Windows
                    temp_path.rename(metadata_path)
                
                logger.info(f"[OK] Saved {len(items)} metadata items to partition {partition_key}")
            
            except Exception as e:
                logger.error(f"Failed to save batch metadata for partition {partition_key}: {e}")
    
    def get_metadata(self, transaction_id: str, timestamp: datetime) -> Optional[Dict]:
        """
        Get metadata for transaction
        
        Args:
            transaction_id: Transaction ID
            timestamp: Transaction timestamp (to find partition)
        
        Returns:
            Metadata dict or None
        """
        try:
            partition_key = self._get_partition_key(timestamp)
            
            # Check cache
            if partition_key in self.cache and transaction_id in self.cache[partition_key]:
                return self.cache[partition_key][transaction_id]
            
            # Load from disk
            metadata_path = self._get_metadata_path(partition_key)
            if not metadata_path.exists():
                return None
            
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    partition_data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Corrupted metadata file for partition {partition_key}: {e}")
                return None
            
            # Cache partition
            self.cache[partition_key] = partition_data
            
            return partition_data.get(transaction_id)
        
        except Exception as e:
            logger.error(f"Failed to get metadata for {transaction_id}: {e}")
            return None
    
    def get_batch_metadata(self, transaction_ids: List[str], timestamps: List[datetime]) -> List[Optional[Dict]]:
        """
        Get metadata for batch of transactions
        
        Args:
            transaction_ids: List of transaction IDs
            timestamps: List of timestamps
        
        Returns:
            List of metadata dicts (None for missing)
        """
        results = []
        
        for tid, ts in zip(transaction_ids, timestamps):
            metadata = self.get_metadata(tid, ts)
            results.append(metadata)
        
        return results


# Global metadata manager
_metadata_manager = None

def get_metadata_manager() -> MetadataManager:
    """Get or create global metadata manager instance"""
    global _metadata_manager
    if _metadata_manager is None:
        _metadata_manager = MetadataManager()
    return _metadata_manager
