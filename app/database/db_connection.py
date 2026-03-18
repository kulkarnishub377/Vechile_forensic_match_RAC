import pyodbc
from typing import Optional
import logging
from contextlib import contextmanager
import time

from .. import config
from ..utils.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Database connection pool manager"""
    
    def __init__(self):
        self.connection_string = self._build_connection_string()
        self.pool = []
        self.pool_size = config.DB_POOL_SIZE
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=pyodbc.Error
        )
        
        # Initialize connection pool
        self._initialize_pool()
        logger.info(f"[OK] Database connection pool initialized (size: {self.pool_size})")
    
    def _build_connection_string(self) -> str:
        """Build MSSQL connection string"""
        conn_str = (
            f"DRIVER={{{config.DB_DRIVER}}};"
            f"SERVER={config.DB_HOST},{config.DB_PORT};"
            f"DATABASE={config.DB_NAME};"
            f"UID={config.DB_USER};"
            f"PWD={config.DB_PASSWORD};"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout={config.DB_CONNECTION_TIMEOUT};"
        )
        return conn_str
    
    def _initialize_pool(self):
        """Create initial connection pool"""
        for i in range(self.pool_size):
            try:
                conn = pyodbc.connect(self.connection_string)
                self.pool.append(conn)
            except Exception as e:
                logger.error(f"Failed to create connection {i}: {e}")
    
    @contextmanager
    def get_connection(self):
        """
        Get connection from pool (context manager)
        
        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ...")
        """
        conn = None
        try:
            # Get connection from pool
            if self.pool:
                conn = self.pool.pop()
            else:
                # Pool exhausted, create new connection
                conn = pyodbc.connect(self.connection_string)
            
            yield conn
        
        except pyodbc.Error as e:
            logger.error(f"Database error: {e}")
            self.circuit_breaker.record_failure()
            raise
        
        finally:
            # Return connection to pool
            if conn:
                try:
                    if len(self.pool) < self.pool_size:
                        self.pool.append(conn)
                    else:
                        conn.close()
                except:
                    pass
    
    def execute_query(self, query: str, params: tuple = None):
        """
        Execute SELECT query with circuit breaker protection
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            rows: List of result rows
        """
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            logger.warning("Circuit breaker OPEN - database unavailable")
            return []
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                rows = cursor.fetchall()
                cursor.close()
                
                self.circuit_breaker.record_success()
                return rows
        
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            self.circuit_breaker.record_failure()
            return []
    
    def close_all(self):
        """Close all connections in pool"""
        for conn in self.pool:
            try:
                conn.close()
            except:
                pass
        self.pool.clear()
        logger.info("[OK] All database connections closed")


# Global database instance
_db_connection = None

def get_db_connection() -> DatabaseConnection:
    """Get or create global database connection instance"""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection
