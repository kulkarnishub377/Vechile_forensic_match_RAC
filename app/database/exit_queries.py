from datetime import datetime
from typing import List, Dict, Optional
import logging

from .db_connection import get_db_connection
from .. import config

logger = logging.getLogger(__name__)


class ExitQueries:
    """Query EXIT vehicles from database (matches old system structure)"""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def fetch_exit_transactions(self, time_window_start: datetime, time_window_end: datetime) -> List[Dict]:
        """
        Fetch EXIT transactions within time window
        
        Args:
            time_window_start: Start of time window
            time_window_end: End of time window
        
        Returns:
            List of exit records (simplified for user - OCR generates VRN)
        """
        query = """
        SELECT
            PT.LOCAL_TX_ID,
            PT.ANPR_READ_TIME,
            PT.ANPR_IMAGE_PATH
        FROM TBL_PLAZA_TRANSACTION PT
        INNER JOIN TBL_PLAZA_LANE PL
            ON PT.PLAZA_ID = PL.PLAZA_ID
            AND PT.LANE_ID = PL.LANE_NAME
        WHERE PL.LANE_MODE = 'EXIT'
            AND PT.ANPR_READ_TIME BETWEEN ? AND ?
            AND PT.ANPR_IMAGE_PATH IS NOT NULL
        ORDER BY PT.ANPR_READ_TIME ASC
        """
        
        try:
            rows = self.db.execute_query(query, (time_window_start, time_window_end))
            
            exits = []
            for row in rows:
                # Map image path from E:\_TrxMedia to \\192.50.20.13\_TrxMedia
                image_path = config.map_image_path(row.ANPR_IMAGE_PATH) if row.ANPR_IMAGE_PATH else None
                
                # Only essential fields - OCR generates VRN
                exit_rec = {
                    'LOCAL_TX_ID': row.LOCAL_TX_ID,
                    'ANPR_READ_TIME': row.ANPR_READ_TIME,
                    'ANPR_IMAGE_PATH': image_path
                }
                exits.append(exit_rec)
            
            logger.info(f"[OK] Fetched {len(exits)} EXIT transactions in window")
            return exits
        
        except Exception as e:
            logger.error(f"Failed to fetch exit transactions: {e}")
            return []
    
    def get_exit_by_id(self, transaction_id: str) -> Optional[Dict]:
        """
        Get single EXIT transaction by ID
        
        Args:
            transaction_id: LOCAL_TX_ID
        
        Returns:
            Exit record dict or None (simplified for user - OCR generates VRN)
        """
        query = """
        SELECT
            PT.LOCAL_TX_ID,
            PT.ANPR_READ_TIME,
            PT.ANPR_IMAGE_PATH
        FROM TBL_PLAZA_TRANSACTION PT
        INNER JOIN TBL_PLAZA_LANE PL
            ON PT.PLAZA_ID = PL.PLAZA_ID
            AND PT.LANE_ID = PL.LANE_NAME
        WHERE PL.LANE_MODE = 'EXIT'
            AND PT.LOCAL_TX_ID = ?
            AND PT.ANPR_IMAGE_PATH IS NOT NULL
        """
        
        try:
            rows = self.db.execute_query(query, (transaction_id,))
            
            if not rows:
                logger.warning(f"EXIT transaction not found: {transaction_id}")
                return None
            
            row = rows[0]
            
            # Map image path from E:\_TrxMedia to \\192.50.20.13\_TrxMedia
            image_path = config.map_image_path(row.ANPR_IMAGE_PATH) if row.ANPR_IMAGE_PATH else None
            
            # Only essential fields - OCR generates VRN
            exit_rec = {
                'LOCAL_TX_ID': row.LOCAL_TX_ID,
                'ANPR_READ_TIME': row.ANPR_READ_TIME,
                'ANPR_IMAGE_PATH': image_path
            }
            
            logger.info(f"[OK] Fetched EXIT transaction: {transaction_id}")
            return exit_rec
        
        except Exception as e:
            logger.error(f"Failed to get exit by ID {transaction_id}: {e}")
            return None


# Global instance
_exit_queries = None

def get_exit_queries() -> ExitQueries:
    """Get or create global ExitQueries instance"""
    global _exit_queries
    if _exit_queries is None:
        _exit_queries = ExitQueries()
    return _exit_queries
