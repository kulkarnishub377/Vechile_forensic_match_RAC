"""
Combined queries for ENTRY vehicles (matches old system)
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

from .db_connection import get_db_connection
from .. import config

logger = logging.getLogger(__name__)


class CombinedQueries:
    """Query uncombined ENTRY vehicles (uses PROCESS_FLAG from old system)"""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def fetch_uncombined_entries(self, lookback_hours: int = 10) -> List[str]:
        """
        Fetch uncombined ENTRY transaction IDs from last N hours
        CRITICAL: Only returns PROCESS_FLAG <> 'C' (uncombined entries)
        Only fetches IDs - VRN comes from FAISS metadata (optimization from old system)
        
        Args:
            lookback_hours: How many hours to look back (default 10 hours)
        
        Returns:
            List of LOCAL_TX_ID strings (uncombined ENTRY transactions only)
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=lookback_hours)
        
        # Only fetch transaction IDs - VRN comes from FAISS metadata (old system optimization)
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
        ORDER BY PT.ANPR_READ_TIME DESC
        """
        
        try:
            rows = self.db.execute_query(query, (start_time, end_time))
            transaction_ids = [row.LOCAL_TX_ID for row in rows]
            
            logger.info(
                f"[OK] Fetched {len(transaction_ids)} uncombined ENTRY IDs (last {lookback_hours}h) "
                f"- VRN from FAISS metadata"
            )
            return transaction_ids
        
        except Exception as e:
            logger.error(f"Failed to fetch uncombined entries: {e}")
            return []
    
    def fetch_combined_entries_24h(self, hours: int = 24) -> List[str]:
        """
        Fetch all combined ENTRY transaction IDs from the last N hours
        Used for primary cache refresh (matches old system)
        
        Args:
            hours: Number of hours to look back (default 24)
        
        Returns:
            List of ENTRY LOCAL_TX_ID values that have been combined (PROCESS_FLAG='C')
        """
        query = """
        SELECT DISTINCT LOCAL_TX_ID
        FROM TBL_PLAZA_TRANSACTION
        WHERE PROCESS_FLAG = 'C'
            AND ANPR_READ_TIME >= DATEADD(hour, ?, GETDATE())
            AND LOCAL_TX_ID IS NOT NULL
        """
        
        try:
            rows = self.db.execute_query(query, (-hours,))
            entry_ids = [row.LOCAL_TX_ID for row in rows]
            logger.debug(
                f"[OK] Fetched {len(entry_ids)} combined entry IDs (PROCESS_FLAG='C') "
                f"from last {hours} hours"
            )
            return entry_ids
        
        except Exception as e:
            logger.error(f"Failed to fetch 24h combined entries: {e}")
            return []
    
    def fetch_combined_entries_window(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[str]:
        """
        Fetch combined ENTRY transaction IDs within a specific time window
        Used for temporary cache creation for old searches (matches old system)
        
        Args:
            start_time: Window start timestamp
            end_time: Window end timestamp
        
        Returns:
            List of ENTRY LOCAL_TX_ID values that have been combined (PROCESS_FLAG='C')
        """
        query = """
        SELECT DISTINCT LOCAL_TX_ID
        FROM TBL_PLAZA_TRANSACTION
        WHERE PROCESS_FLAG = 'C'
            AND ANPR_READ_TIME BETWEEN ? AND ?
            AND LOCAL_TX_ID IS NOT NULL
        """
        
        try:
            rows = self.db.execute_query(query, (start_time, end_time))
            entry_ids = [row.LOCAL_TX_ID for row in rows]
            logger.debug(
                f"[OK] Fetched {len(entry_ids)} combined entry IDs (PROCESS_FLAG='C') "
                f"from {start_time.strftime('%Y-%m-%d %H:%M')} "
                f"to {end_time.strftime('%Y-%m-%d %H:%M')}"
            )
            return entry_ids
        
        except Exception as e:
            logger.error(f"Failed to fetch windowed combined entries: {e}")
            return []
    
    def check_if_combined(self, entry_transaction_id: str) -> bool:
        """
        Check if ENTRY transaction has been combined with EXIT
        Uses PROCESS_FLAG='C' from TBL_PLAZA_TRANSACTION (old system logic)
        
        Args:
            entry_transaction_id: Entry LOCAL_TX_ID
        
        Returns:
            True if combined (PROCESS_FLAG='C'), False otherwise
        """
        query = """
        SELECT PROCESS_FLAG
        FROM TBL_PLAZA_TRANSACTION
        WHERE LOCAL_TX_ID = ?
        """
        
        try:
            rows = self.db.execute_query(query, (entry_transaction_id,))
            if rows:
                return rows[0].PROCESS_FLAG == 'C'
            return False
        
        except Exception as e:
            logger.error(f"Failed to check combined status: {e}")
            return False


# Global instance
_combined_queries = None

def get_combined_queries() -> CombinedQueries:
    """Get or create global CombinedQueries instance"""
    global _combined_queries
    if _combined_queries is None:
        _combined_queries = CombinedQueries()
    return _combined_queries
