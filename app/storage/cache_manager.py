"""
Cache manager with Redis/LRU fallback
"""
import json
from typing import Optional, Any
import logging
from functools import lru_cache

from .. import config

logger = logging.getLogger(__name__)


class CacheManager:
    """Cache manager with Redis backend and LRU fallback"""
    
    def __init__(self):
        self.redis_client = None
        self.use_redis = config.CACHE_REDIS_ENABLED
        
        if self.use_redis:
            self._init_redis()
        
        # In-memory LRU cache as fallback
        self.memory_cache = {}
        self.max_memory_cache_size = 1000
        
        logger.info(f"[OK] Cache manager initialized (Redis: {self.use_redis})")
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            import redis
            
            self.redis_client = redis.Redis(
                host=config.CACHE_REDIS_HOST,
                port=config.CACHE_REDIS_PORT,
                db=config.CACHE_REDIS_DB,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"[OK] Connected to Redis at {config.CACHE_REDIS_HOST}:{config.CACHE_REDIS_PORT}")
        
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}, using in-memory cache")
            self.redis_client = None
            self.use_redis = False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        try:
            # Try Redis first
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            
            # Fallback to memory cache
            return self.memory_cache.get(key)
        
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (None = no expiration)
        """
        try:
            serialized = json.dumps(value)
            
            # Set in Redis
            if self.redis_client:
                if ttl:
                    self.redis_client.setex(key, ttl, serialized)
                else:
                    self.redis_client.set(key, serialized)
            
            # Also set in memory cache
            self.memory_cache[key] = value
            
            # Limit memory cache size
            if len(self.memory_cache) > self.max_memory_cache_size:
                # Remove oldest entries (simple FIFO)
                keys_to_remove = list(self.memory_cache.keys())[:100]
                for k in keys_to_remove:
                    del self.memory_cache[k]
        
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
    
    def delete(self, key: str):
        """Delete key from cache"""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            
            if key in self.memory_cache:
                del self.memory_cache[key]
        
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {e}")
    
    def clear(self):
        """Clear all cache"""
        try:
            if self.redis_client:
                self.redis_client.flushdb()
            
            self.memory_cache.clear()
            logger.info("[OK] Cache cleared")
        
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")


# Global cache manager
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
