from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from .db_connection import get_db_connection
from .. import config

logger = logging.getLogger(__name__)


class EntryQueries:
    """
    Query ENTRY vehicles from database with optimizations:
    - Connection pooling
    - Retry logic for transient failures
    - Batch operations
    - Parameterized queries (SQL injection safe)
    """
    
    def __init__(self):
        self.db = get_db_connection()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    def fetch_new_entry_transactions(
        self, 
        after_timestamp: datetime, 
        limit: int = 1000
    ) -> List[Dict]:
        """
        Fetch new ENTRY transactions after given timestamp (with retry logic)
        
        Args:
            after_timestamp: Fetch entries after this time
            limit: Maximum number of records to fetch (default 1000)
        
        Returns:
            List of entry records with essential fields:
                - tx_id: Transaction ID (LOCAL_TX_ID)
                - read_time: Timestamp (ANPR_READ_TIME)
                - image_path: Mapped image path
        """
        query = f"""
        SELECT TOP {limit}
            PT.LOCAL_TX_ID,
            PT.ANPR_READ_TIME,
            PT.ANPR_IMAGE_PATH
        FROM TBL_PLAZA_TRANSACTION PT
        INNER JOIN TBL_PLAZA_LANE PL
            ON PT.PLAZA_ID = PL.PLAZA_ID
            AND PT.LANE_ID = PL.LANE_NAME
        WHERE PL.LANE_MODE = 'ENTRY'
            AND PT.ANPR_READ_TIME > ?
            AND PT.ANPR_IMAGE_PATH IS NOT NULL
        ORDER BY PT.ANPR_READ_TIME ASC
        """
        
        try:
            rows = self.db.execute_query(query, (after_timestamp,))
            
            entries = []
            for row in rows:
                # Map image path from E:\\_TrxMedia to \\192.50.20.13\\_TrxMedia
                image_path = config.map_image_path(row.ANPR_IMAGE_PATH) if row.ANPR_IMAGE_PATH else None
                
                if not image_path:
                    continue
                
                # Simplified structure - OCR generates VRN dynamically
                entry = {
                    'tx_id': row.LOCAL_TX_ID,
                    'read_time': row.ANPR_READ_TIME,
                    'image_path': image_path,
                    # Legacy aliases for compatibility
                    'LOCAL_TX_ID': row.LOCAL_TX_ID,
                    'ANPR_READ_TIME': row.ANPR_READ_TIME,
                    'ANPR_IMAGE_PATH': image_path
                }
                entries.append(entry)
            
            logger.info(f"[OK] Fetched {len(entries)} ENTRY transactions after {after_timestamp}")
            return entries
        
        except Exception as e:
            logger.error(f"Failed to fetch entry transactions: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    def get_entry_by_id(self, transaction_id: str) -> Optional[Dict]:
        """
        Get single ENTRY transaction by ID (with retry logic)
        
        Args:
            transaction_id: LOCAL_TX_ID to fetch
        
        Returns:
            Entry record dict or None if not found
        """
        query = """
        SELECT 
            PT.LOCAL_TX_ID,
            PT.ANPR_READ_TIME,
            PT.ANPR_IMAGE_PATH
        FROM TBL_PLAZA_TRANSACTION PT
        WHERE PT.LOCAL_TX_ID = ?
        """
        
        try:
            rows = self.db.execute_query(query, (transaction_id,))
            
            if not rows:
                return None
            
            row = rows[0]
            
            # Map image path from E:\_TrxMedia to \\192.50.20.13\_TrxMedia
            image_path = config.map_image_path(row.ANPR_IMAGE_PATH) if row.ANPR_IMAGE_PATH else None
            
            # Only essential fields - OCR generates VRN
            # Include both legacy field names and new aliases for compatibility
            entry = {
                'LOCAL_TX_ID': row.LOCAL_TX_ID,
                'ANPR_READ_TIME': row.ANPR_READ_TIME,
                'ANPR_IMAGE_PATH': image_path,
                # Aliases for matching engine compatibility
                'Timestamp': row.ANPR_READ_TIME,
                'ImagePath': image_path
            }
            
            return entry
        
        except Exception as e:
            logger.error(f"Failed to get entry by ID {transaction_id}: {e}")
            return None
    
    def count_entries_after(self, after_timestamp: datetime) -> int:
        """
        Count ENTRY transactions after timestamp
        
        Args:
            after_timestamp: Count entries after this time
        
        Returns:
            Count of entries
        """
        query = """
        SELECT COUNT(*) as count
        FROM TBL_PLAZA_TRANSACTION PT
        INNER JOIN TBL_PLAZA_LANE PL
            ON PT.PLAZA_ID = PL.PLAZA_ID
            AND PT.LANE_ID = PL.LANE_NAME
        WHERE PL.LANE_MODE = 'ENTRY'
            AND PT.ANPR_READ_TIME > ?
        """
        
        try:
            rows = self.db.execute_query(query, (after_timestamp,))
            if rows:
                return rows[0].count
            return 0
        
        except Exception as e:
            logger.error(f"Failed to count entries: {e}")
            return 0
    
    def fetch_transaction_image_path(self, transaction_id: str) -> Optional[str]:
        """
        Fetch image path for a specific transaction ID
        (matches old system function)
        
        Args:
            transaction_id: LOCAL_TX_ID
        
        Returns:
            Image path string (mapped to network) or None if not found
        """
        query = """
        SELECT ANPR_IMAGE_PATH
        FROM TBL_PLAZA_TRANSACTION
        WHERE LOCAL_TX_ID = ?
        """
        
        try:
            rows = self.db.execute_query(query, (transaction_id,))
            if rows:
                image_path = rows[0].ANPR_IMAGE_PATH
                # Map path from E:\\_TrxMedia to \\192.50.20.13\\_TrxMedia
                return config.map_image_path(image_path) if image_path else None
            return None
        except Exception as e:
            logger.error(f"Failed to fetch image path for {transaction_id}: {e}")
            return None
    
    def fetch_multiple_image_paths(self, transaction_ids: List[str]) -> Dict[str, str]:
        """
        Fetch image paths for multiple transaction IDs (batch operation)
        (matches old system function)
        
        Args:
            transaction_ids: List of LOCAL_TX_ID values
        
        Returns:
            Dictionary mapping transaction_id -> mapped image_path
        """
        if not transaction_ids:
            return {}
        
        # Build IN clause with placeholders
        placeholders = ','.join(['?' for _ in transaction_ids])
        query = f"""
        SELECT LOCAL_TX_ID, ANPR_IMAGE_PATH
        FROM TBL_PLAZA_TRANSACTION
        WHERE LOCAL_TX_ID IN ({placeholders})
        """
        
        try:
            rows = self.db.execute_query(query, tuple(transaction_ids))
            result = {}
            for row in rows:
                tx_id = str(row.LOCAL_TX_ID)
                image_path = row.ANPR_IMAGE_PATH
                # Map path from E:\\_TrxMedia to \\192.50.20.13\\_TrxMedia
                result[tx_id] = config.map_image_path(image_path) if image_path else None
            return result
        except Exception as e:
            logger.error(f"Failed to fetch image paths: {e}")
            return {}
    
    def get_entries_batch(self, transaction_ids: List[str]) -> List[Optional[Dict]]:
        """
        Batch fetch ENTRY records by IDs (for matching engine optimization)
        
        Args:
            transaction_ids: List of transaction IDs to fetch
        
        Returns:
            List of entry dicts in SAME ORDER as input IDs
            (None for IDs not found)
        """
        if not transaction_ids:
            return []
        
        # Fetch all at once
        data_dict = self.fetch_multiple_transaction_data(transaction_ids)
        
        # Return in same order as input
        results = []
        for tid in transaction_ids:
            if tid in data_dict:
                # Convert to simplified format matching get_entry_by_id
                entry_data = data_dict[tid]
                results.append({
                    'LOCAL_TX_ID': tid,
                    'ANPR_READ_TIME': entry_data['timestamp'],
                    'ANPR_IMAGE_PATH': entry_data['image_path'],
                    'Timestamp': entry_data['timestamp']  # Alias for matching engine
                })
            else:
                results.append(None)
        
        return results
    
    def fetch_multiple_transaction_data(self, transaction_ids: List[str]) -> Dict[str, Dict]:
        """
        Fetch comprehensive transaction data for multiple IDs
        (matches old system PRO version function)
        
        Returns image paths, VRN (license plate), and timestamps for use in
        matching engine's VRN verification.
        
        CRITICAL: Does NOT filter by LANE_MODE - FAISS index contains ENTRY IDs
        and we need to fetch those transaction records regardless of lane mode.
        
        Args:
            transaction_ids: List of LOCAL_TX_ID values
        
        Returns:
            Dictionary mapping transaction_id -> {
                'image_path': str (mapped to network),
                'vrn': Optional[str],
                'timestamp': datetime,
                'plaza_id': str,
                'lane_id': str
            }
        """
        if not transaction_ids:
            return {}
        
        # Build IN clause with placeholders
        placeholders = ','.join(['?' for _ in transaction_ids])
        query = f"""
        SELECT
            PT.LOCAL_TX_ID,
            PT.ANPR_IMAGE_PATH,
            PT.ANPR_VRN,
            PT.ANPR_READ_TIME,
            PT.PLAZA_ID,
            PT.LANE_ID
        FROM TBL_PLAZA_TRANSACTION PT
        WHERE PT.LOCAL_TX_ID IN ({placeholders})
        """
        
        try:
            rows = self.db.execute_query(query, tuple(transaction_ids))
            
            data = {}
            for row in rows:
                tx_id = str(row.LOCAL_TX_ID)
                image_path = row.ANPR_IMAGE_PATH
                # Map path from E:\\_TrxMedia to \\192.50.20.13\\_TrxMedia
                mapped_path = config.map_image_path(image_path) if image_path else None
                
                data[tx_id] = {
                    'image_path': mapped_path,
                    'vrn': row.ANPR_VRN if hasattr(row, 'ANPR_VRN') else None,
                    'timestamp': row.ANPR_READ_TIME,
                    'plaza_id': row.PLAZA_ID,
                    'lane_id': row.LANE_ID
                }
            
            logger.debug(f"[OK] Fetched transaction data for {len(data)} entries")
            return data
        
        except Exception as e:
            logger.error(f"Failed to fetch transaction data: {e}")
            return {}
    
    def fetch_uncombined_entry_ids(
        self,
        exit_timestamp: datetime,
        time_window_hours: int = 8
    ) -> List[str]:
        """
        Fetch UNCOMBINED ENTRY transaction IDs within time window
        
        CRITICAL: Only returns entries where PROCESS_FLAG != 'C'
        These are entries that haven't been matched yet
        
        Args:
            exit_timestamp: EXIT transaction timestamp
            time_window_hours: Hours to look back (default 8)
        
        Returns:
            List of LOCAL_TX_ID strings that are uncombined
        
        Query Logic (from user's SQL):
            - LANE_MODE = 'ENTRY' (join with TBL_PLAZA_LANE)
            - ANPR_READ_TIME between (exit_time - window) and exit_time
            - PROCESS_FLAG <> 'C' (not combined yet)
        """
        # Calculate time window
        start_time = exit_timestamp - timedelta(hours=time_window_hours)
        end_time = exit_timestamp
        
        query = """
        SELECT PT.LOCAL_TX_ID
        FROM TBL_PLAZA_TRANSACTION PT WITH(NOLOCK)
        LEFT JOIN TBL_PLAZA_LANE PL WITH(NOLOCK) 
            ON PT.PLAZA_ID = PL.PLAZA_ID 
            AND PT.LANE_ID = PL.LANE_NAME
        WHERE 
            PT.ANPR_READ_TIME BETWEEN ? AND ?
            AND PL.LANE_MODE = 'ENTRY'
            AND PT.PROCESS_FLAG <> 'C'
            AND PT.ANPR_IMAGE_PATH IS NOT NULL
        ORDER BY PT.ANPR_READ_TIME DESC
        """
        
        try:
            rows = self.db.execute_query(query, (start_time, end_time))
            
            uncombined_ids = [str(row.LOCAL_TX_ID) for row in rows]
            
            logger.info(
                f"[OK] Fetched {len(uncombined_ids)} UNCOMBINED ENTRY transactions "
                f"between {start_time} and {end_time}"
            )
            return uncombined_ids
        
        except Exception as e:
            logger.error(f"Failed to fetch uncombined entries: {e}")
            return []


# Global instance
_entry_queries = None

def get_entry_queries() -> EntryQueries:
    """Get or create global EntryQueries instance"""
    global _entry_queries
    if _entry_queries is None:
        _entry_queries = EntryQueries()
    return _entry_queries
