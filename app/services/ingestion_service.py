import warnings
import os
import logging as _logging

warnings.filterwarnings('ignore')
os.environ['PPOCR_LOG_LEVEL'] = 'ERROR'
_logging.getLogger('ppocr').setLevel(_logging.ERROR)
_logging.getLogger('PaddleOCR').setLevel(_logging.ERROR)

import csv
import time
import signal
import sys
import shutil
import tempfile
import gc
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from contextlib import contextmanager
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app import config
from app.database.entry_queries import EntryQueries
from app.database.db_connection import get_db_connection
from app.core.embedding_engine import get_embedding_engine
from app.storage.faiss_manager import get_faiss_manager
from app.storage.metadata_manager import get_metadata_manager

# Setup logging with rotation (100 MB per file, keep 7 backups)
os.makedirs(config.LOGS_DIR, exist_ok=True)
rotating_handler = RotatingFileHandler(
    config.LOG_INGESTION,
    maxBytes=config.LOG_MAX_SIZE_MB * 1024 * 1024,
    backupCount=config.LOG_BACKUP_COUNT
)
rotating_handler.setFormatter(logging.Formatter(config.LOG_FORMAT, config.LOG_DATE_FORMAT))

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
    handlers=[
        logging.StreamHandler(),
        rotating_handler
    ]
)

logger = logging.getLogger(__name__)


@contextmanager
def LocalFileContext(file_path):
    """
    Context manager to copy file to local temp for processing.
    Minimizes random access latency on network shares.
    
    Args:
        file_path: Path to file (can be network share)
        
    Yields:
        Local temp path (or original if copy fails)
    """
    temp_path = None
    yielded_path = None
    try:
        # Create temp file with same extension
        ext = os.path.splitext(file_path)[1]
        fd, temp_path = tempfile.mkstemp(suffix=ext)
        os.close(fd)
        
        # Copy to temp (optimized for large files)
        shutil.copyfile(file_path, temp_path)
        yielded_path = temp_path
        
    except Exception as e:
        logger.debug(f"Local cache failed for {file_path}, using original: {e}")
        # Fallback: use original path
        yielded_path = file_path
    
    try:
        yield yielded_path
    finally:
        # Cleanup temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.debug(f"Failed to remove temp file {temp_path}: {e}")


class IngestionService:
    """
    ENTRY Vehicle Ingestion Service v3.0
    
    Features:
    - 12-hour lookback on first startup
    - Batch processing with OpenVINO ReID + OCR
    - Time-partitioned FAISS storage
    - Auto-save every 100 vectors
    - CSV audit trail
    - Graceful shutdown with partition save
    
    Workflow:
    1. Poll MSSQL for new ENTRY transactions
    2. Load images (with local caching for network shares)
    3. Extract ReID embeddings + OCR text + color histograms
    4. Store in FAISS vector database (daily partitions)
    5. Track metadata in separate storage
    6. Log to CSV for audit
    7. Repeat continuously
    """
    
    def __init__(self):
        """Initialize ingestion service"""
        self.running = False
        self.entry_queries = EntryQueries()
        self.embedding_engine = get_embedding_engine()
        self.faiss_manager = get_faiss_manager()
        self.metadata_manager = get_metadata_manager()
        self.last_fetched_time = self._load_last_fetched_time()
        self.total_processed = 0
        self.total_failed = 0
        
        # Track current partition date (for final shutdown save)
        self.current_partition_date = None
        
        logger.info("=" * 80)
        logger.info("ENTRY Ingestion Service v3.0 - Initialized")
        logger.info(f"Last fetched time: {self.last_fetched_time}")
        logger.info(f"Batch size: {config.INGESTION_BATCH_SIZE}")
        logger.info(f"Worker threads: {config.INGESTION_WORKER_THREADS}")
        logger.info(f"Poll interval: {config.INGESTION_POLL_INTERVAL}s")
        logger.info("=" * 80)
    
    def _load_last_fetched_time(self) -> datetime:
        """
        Load last fetched timestamp from file
        
        CRITICAL: On first run, start from configured lookback hours ago
        
        Returns:
            Last fetched datetime or (now - lookback hours) on first run
        """
        if config.LAST_FETCHED_TIME_FILE.exists():
            try:
                with open(config.LAST_FETCHED_TIME_FILE, 'r') as f:
                    timestamp_str = f.read().strip()
                    last_time = datetime.fromisoformat(timestamp_str)
                    logger.info(f"Resuming from last checkpoint: {last_time}")
                    return last_time
            except Exception as e:
                logger.warning(f"Failed to load last fetched time: {e}")
        
        # FIRST RUN: Start from lookback hours ago
        start_time = datetime.now() - timedelta(hours=config.INGESTION_LOOKBACK_HOURS)
        logger.warning(f"FIRST RUN DETECTED")
        logger.warning(f"Starting ingestion from {config.INGESTION_LOOKBACK_HOURS} hours ago: {start_time}")
        logger.warning(f"This will process all ENTRY vehicles from the last {config.INGESTION_LOOKBACK_HOURS} hours")
        
        return start_time
    
    def _save_last_fetched_time(self, timestamp: datetime):
        """
        Save last fetched timestamp to file
        
        Args:
            timestamp: Timestamp to save
        """
        try:
            config.LAST_FETCHED_TIME_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(config.LAST_FETCHED_TIME_FILE, 'w') as f:
                f.write(timestamp.isoformat())
        except Exception as e:
            logger.error(f"Failed to save last fetched time: {e}")
    
    def _append_to_entry_track_csv(
        self,
        transaction_id: str,
        timestamp: datetime,
        image_path: str,
        embedding_time: float,
        success: bool,
        ocr_text: str = "",
        ocr_conf: float = 0.0,
        error: Optional[str] = None
    ):
        """
        Append entry to tracking CSV with detailed information
        
        Args:
            transaction_id: Transaction ID
            timestamp: Entry timestamp
            image_path: Image file path
            embedding_time: Time taken to generate embedding (seconds)
            success: Whether processing succeeded
            ocr_text: Extracted OCR text (if successful)
            ocr_conf: OCR confidence score
            error: Error message if failed
        """
        date_str = timestamp.strftime('%Y-%m-%d')
        csv_file = config.ENTRY_TRACK_DIR / f"entry_track_{date_str}.csv"
        
        # Ensure directory exists
        csv_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists to write header
        file_exists = csv_file.exists()
        
        try:
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header if new file
                if not file_exists:
                    writer.writerow([
                        'entry_transaction_id',
                        'entry_timestamp',
                        'image_path',
                        'ocr_text',
                        'ocr_confidence',
                        'embedding_time_seconds',
                        'vector_partition_date',
                        'processed_at',
                        'success',
                        'error'
                    ])
                
                # Write data
                writer.writerow([
                    transaction_id,
                    timestamp.isoformat(),
                    image_path,
                    ocr_text or '***',
                    f"{ocr_conf:.4f}" if ocr_conf > 0 else "0.0000",
                    f"{embedding_time:.3f}",
                    date_str,
                    datetime.now().isoformat(),
                    'YES' if success else 'NO',
                    error or ''
                ])
        
        except Exception as e:
            logger.error(f"Failed to write to entry track CSV: {e}")
    
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
        retry=retry_if_exception_type((OSError, ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def _process_single_entry(self, entry_data: dict) -> bool:
        """
        Process a single ENTRY transaction with retry logic
        
        Args:
            entry_data: Entry transaction dictionary from database
            
        Returns:
            True if successful, False otherwise
        """
        transaction_id = entry_data.get('LOCAL_TX_ID', '')
        timestamp = entry_data.get('ANPR_READ_TIME', datetime.now())
        image_path = entry_data.get('ANPR_IMAGE_PATH', '')
        
        start_time = time.time()
        
        try:
            # Validate image path
            if not image_path:
                error_msg = "No image path in database"
                logger.warning(f"{transaction_id}: {error_msg}")
                self._append_to_entry_track_csv(
                    transaction_id, timestamp, image_path,
                    time.time() - start_time, False, error=error_msg
                )
                return False
            
            # Map database path to actual storage location
            # E.g., E:\_TrxMedia -> \\192.50.20.13\_TrxMedia
            mapped_image_path = config.map_image_path(image_path)
            
            # Check if file exists
            if not os.path.exists(mapped_image_path):
                error_msg = f"Image file not found: {mapped_image_path}"
                logger.warning(f"{transaction_id}: {error_msg}")
                self._append_to_entry_track_csv(
                    transaction_id, timestamp, image_path,
                    time.time() - start_time, False, error=error_msg
                )
                return False
            
            # Extract embedding (use local copy for network shares)
            with LocalFileContext(mapped_image_path) as local_image_path:
                # Process single image
                results = self.embedding_engine.process_batch([local_image_path])
                
                if not results or len(results) == 0:
                    error_msg = "Batch processing returned no results"
                    logger.warning(f"{transaction_id}: {error_msg}")
                    self._append_to_entry_track_csv(
                        transaction_id, timestamp, image_path,
                        time.time() - start_time, False, error=error_msg
                    )
                    return False
                
                result = results[0]
            
            # Validate result
            if result is None:
                error_msg = "No vehicle detected in image"
                logger.warning(f"{transaction_id}: {error_msg}")
                self._append_to_entry_track_csv(
                    transaction_id, timestamp, image_path,
                    time.time() - start_time, False, error=error_msg
                )
                return False
            
            if result.reid_embedding is None:
                error_msg = "Failed to extract ReID embedding"
                logger.warning(f"{transaction_id}: {error_msg}")
                self._append_to_entry_track_csv(
                    transaction_id, timestamp, image_path,
                    time.time() - start_time, False, error=error_msg
                )
                return False
            
            # Get partition key (date)
            partition_key = self.faiss_manager._get_partition_key(timestamp)
            
            # Add to FAISS (auto-saves every 100 vectors)
            self.faiss_manager.add_vectors(
                partition_key=partition_key,
                vectors=result.reid_embedding.reshape(1, -1),
                transaction_ids=[transaction_id]
            )
            
            # Save metadata (color, OCR, aspect ratio)
            self.metadata_manager.save_metadata(
                transaction_id=transaction_id,
                timestamp=timestamp,
                embedding_data={
                    'color_histogram': result.color_hist,
                    'ocr_text': result.ocr_text,
                    'ocr_confidence': result.ocr_conf,
                    'bbox': result.bbox,
                    'plate_bbox': None,
                    'aspect_ratio': result.aspect_ratio,
                    'vehicle_confidence': result.vehicle_conf
                }
            )
            
            # Track partition date for final shutdown save
            if self.current_partition_date != partition_key:
                logger.debug(f"Partition date: {partition_key}")
                self.current_partition_date = partition_key
            
            # Log success
            processing_time = time.time() - start_time
            ocr_text = result.ocr_text if result.ocr_text else '***'
            
            logger.info(
                f"[OK] {transaction_id} | "
                f"OCR: {ocr_text} | "
                f"Conf: {result.ocr_conf:.2f} | "
                f"Time: {processing_time:.2f}s"
            )
            
            self._append_to_entry_track_csv(
                transaction_id, timestamp, image_path,
                processing_time, True,
                ocr_text=result.ocr_text,
                ocr_conf=result.ocr_conf
            )
            
            # CRITICAL: Force memory cleanup after each entry
            del result
            gc.collect()
            
            return True
        
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            logger.error(f"[FAIL] {transaction_id}: {e}", exc_info=False)
            self._append_to_entry_track_csv(
                transaction_id, timestamp, image_path,
                time.time() - start_time, False, error=error_msg
            )
            
            # Force memory cleanup on error too
            gc.collect()
            
            return False
    
    def _process_batch_threaded(self, entries: List[dict]) -> Tuple[int, int]:
        """
        Process batch of entries using thread pool
        
        Args:
            entries: List of entry dictionaries
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        if not entries:
            return 0, 0
        
        success_count = 0
        failed_count = 0
        
        # CRITICAL FIX: Reduce workers to prevent memory exhaustion
        # Each worker loads ~300MB (YOLO + ResNet + OSNet + tensors)
        # 6 workers × 300MB = 1.8GB causing OOM errors
        max_workers = min(3, config.INGESTION_WORKER_THREADS)  # Max 3 parallel workers
        logger.info(f"Processing batch with {max_workers} workers (reduced from {config.INGESTION_WORKER_THREADS} to prevent OOM)")
        
        # Use thread pool for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._process_single_entry, entry): entry
                for entry in entries
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Thread execution failed: {e}")
                    failed_count += 1
        
        # CRITICAL: Aggressive memory cleanup after batch
        logger.debug(f"Forcing garbage collection after batch...")
        gc.collect()
        
        return success_count, failed_count
    
    def run(self):
        """Main ingestion loop - runs 24x7"""
        self.running = True
        logger.info("Starting ENTRY ingestion service...")
        
        # Test database connection
        try:
            db = get_db_connection()
            db.execute_query("SELECT 1")
            logger.info("Database connection OK")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return
        
        while self.running:
            try:
                logger.debug(f"Fetching new entries after {self.last_fetched_time}")
                
                # Fetch new entries from MSSQL with retry
                @retry(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
                    before_sleep=before_sleep_log(logger, logging.WARNING)
                )
                def safe_fetch(timestamp):
                    return self.entry_queries.fetch_new_entry_transactions(timestamp)
                
                entries = safe_fetch(self.last_fetched_time)
                
                if not entries:
                    logger.debug("No new entries found")
                else:
                    logger.info(f"Fetched {len(entries)} new ENTRY transactions")
                    
                    # Process in batches (configurable batch size)
                    batch_size = config.INGESTION_BATCH_SIZE
                    
                    for i in range(0, len(entries), batch_size):
                        batch = entries[i:i + batch_size]
                        batch_num = i // batch_size + 1
                        total_batches = (len(entries) + batch_size - 1) // batch_size
                        
                        logger.info(
                            f"Processing batch {batch_num}/{total_batches} "
                            f"({len(batch)} entries)"
                        )
                        
                        # Process batch with thread pool
                        success_count, failed_count = self._process_batch_threaded(batch)
                        
                        # Update totals
                        self.total_processed += success_count
                        self.total_failed += failed_count
                        
                        logger.info(
                            f"Batch {batch_num} complete: "
                            f"{success_count} success, {failed_count} failed | "
                            f"Total: {self.total_processed} success, {self.total_failed} failed"
                        )
                    
                    # Update last fetched time to latest entry
                    latest_entry = max(entries, key=lambda x: x.get('ANPR_READ_TIME', datetime.min))
                    self.last_fetched_time = latest_entry.get('ANPR_READ_TIME', self.last_fetched_time)
                    self._save_last_fetched_time(self.last_fetched_time)
                    
                    logger.info(f"Updated last fetched time: {self.last_fetched_time}")
                
                # Sleep before next poll
                logger.debug(f"Sleeping for {config.INGESTION_POLL_INTERVAL} seconds...")
                time.sleep(config.INGESTION_POLL_INTERVAL)
            
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                break
            except Exception as e:
                logger.error(f"Ingestion loop error: {e}", exc_info=True)
                logger.info("Retrying in 30 seconds...")
                time.sleep(30)
        
        # Cleanup and final save
        logger.info("Shutting down ingestion service...")
        
        # Force final save of current partition
        # (FAISS already auto-saved every 100 vectors, but this ensures last batch is saved)
        if self.current_partition_date:
            logger.info(f"Final partition save: {self.current_partition_date}")
            try:
                self.faiss_manager.save_partition(self.current_partition_date)
                logger.info(f"Partition {self.current_partition_date} saved successfully")
            except Exception as e:
                logger.error(f"Failed to save final partition: {e}")
        
        logger.info(
            f"Ingestion service stopped | "
            f"Total processed: {self.total_processed} | "
            f"Total failed: {self.total_failed}"
        )
    
    def stop(self):
        """Stop the ingestion service gracefully"""
        logger.info("Stopping ingestion service...")
        self.running = False


# Global service instance for signal handler
_service_instance = None


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    global _service_instance
    logger.info(f"Received shutdown signal {sig}")
    
    if _service_instance:
        logger.info("Initiating graceful shutdown...")
        _service_instance.stop()
    else:
        logger.warning("No service instance to stop")
        sys.exit(0)


def get_ingestion_service():
    """Get singleton ingestion service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = IngestionService()
    return _service_instance


def main():
    """Main entry point for ingestion service"""
    global _service_instance
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run service
    service = IngestionService()
    _service_instance = service
    
    try:
        service.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected")
        service.stop()
    except Exception as e:
        logger.error(f"Service crashed: {e}", exc_info=True)
    finally:
        logger.info("Service shutdown complete")
        sys.exit(0)


if __name__ == "__main__":
    main()
