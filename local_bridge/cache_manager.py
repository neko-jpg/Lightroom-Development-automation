"""
Cache Manager for Junmai AutoDev System

Provides Redis-based caching for EXIF data and AI evaluation results
to improve performance and reduce redundant processing.

Features:
- EXIF data caching (24-hour TTL)
- AI evaluation result caching (7-day TTL)
- Cache invalidation logic
- Automatic cache key generation
- Connection pooling and error handling

Requirements: 12.5
"""

import redis
import json
import hashlib
import logging
from typing import Dict, Optional, Any
from datetime import timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Redis-based cache manager for EXIF and AI evaluation data.
    
    Provides efficient caching with automatic key generation,
    TTL management, and graceful fallback when Redis is unavailable.
    """
    
    # Cache TTL settings
    EXIF_CACHE_TTL = timedelta(hours=24)  # 24 hours
    AI_EVAL_CACHE_TTL = timedelta(days=7)  # 7 days
    
    # Cache key prefixes
    EXIF_PREFIX = "exif"
    AI_EVAL_PREFIX = "ai_eval"
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = True,
        max_connections: int = 10
    ):
        """
        Initialize cache manager with Redis connection.
        
        Args:
            host: Redis server host (default: localhost)
            port: Redis server port (default: 6379)
            db: Redis database number (default: 0)
            password: Redis password (optional)
            decode_responses: Decode responses to strings (default: True)
            max_connections: Maximum connection pool size (default: 10)
        """
        self.host = host
        self.port = port
        self.db = db
        self.redis_client = None
        self.enabled = False
        
        try:
            # Create connection pool
            pool = redis.ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=decode_responses,
                max_connections=max_connections
            )
            
            # Initialize Redis client
            self.redis_client = redis.Redis(connection_pool=pool)
            
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            
            logger.info(f"Cache manager initialized: {host}:{port} (db={db})")
            
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize cache manager: {e}")
            self.enabled = False
    
    def _generate_cache_key(self, prefix: str, file_path: str) -> str:
        """
        Generate cache key from file path.
        
        Uses MD5 hash of absolute file path for consistent key generation.
        
        Args:
            prefix: Cache key prefix (e.g., 'exif', 'ai_eval')
            file_path: File path to generate key for
            
        Returns:
            Cache key string
        """
        # Normalize path and generate hash
        abs_path = str(Path(file_path).resolve())
        path_hash = hashlib.md5(abs_path.encode()).hexdigest()
        
        return f"{prefix}:{path_hash}"
    
    def cache_exif(self, file_path: str, data: Dict) -> bool:
        """
        Cache EXIF data for a photo file.
        
        Args:
            file_path: Photo file path
            data: EXIF data dictionary to cache
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            key = self._generate_cache_key(self.EXIF_PREFIX, file_path)
            
            # Serialize data to JSON
            json_data = json.dumps(data)
            
            # Store with TTL
            self.redis_client.setex(
                key,
                self.EXIF_CACHE_TTL,
                json_data
            )
            
            logger.debug(f"Cached EXIF data: {Path(file_path).name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache EXIF data: {e}")
            return False
    
    def get_exif(self, file_path: str) -> Optional[Dict]:
        """
        Retrieve cached EXIF data for a photo file.
        
        Args:
            file_path: Photo file path
            
        Returns:
            Cached EXIF data dictionary, or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            key = self._generate_cache_key(self.EXIF_PREFIX, file_path)
            
            # Retrieve from cache
            json_data = self.redis_client.get(key)
            
            if json_data:
                data = json.loads(json_data)
                logger.debug(f"Cache hit (EXIF): {Path(file_path).name}")
                return data
            else:
                logger.debug(f"Cache miss (EXIF): {Path(file_path).name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve EXIF cache: {e}")
            return None
    
    def cache_ai_evaluation(self, file_path: str, data: Dict) -> bool:
        """
        Cache AI evaluation result for a photo file.
        
        Args:
            file_path: Photo file path
            data: AI evaluation result dictionary to cache
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            key = self._generate_cache_key(self.AI_EVAL_PREFIX, file_path)
            
            # Serialize data to JSON
            json_data = json.dumps(data)
            
            # Store with TTL
            self.redis_client.setex(
                key,
                self.AI_EVAL_CACHE_TTL,
                json_data
            )
            
            logger.debug(f"Cached AI evaluation: {Path(file_path).name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache AI evaluation: {e}")
            return False
    
    def get_ai_evaluation(self, file_path: str) -> Optional[Dict]:
        """
        Retrieve cached AI evaluation result for a photo file.
        
        Args:
            file_path: Photo file path
            
        Returns:
            Cached AI evaluation dictionary, or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            key = self._generate_cache_key(self.AI_EVAL_PREFIX, file_path)
            
            # Retrieve from cache
            json_data = self.redis_client.get(key)
            
            if json_data:
                data = json.loads(json_data)
                logger.debug(f"Cache hit (AI eval): {Path(file_path).name}")
                return data
            else:
                logger.debug(f"Cache miss (AI eval): {Path(file_path).name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve AI evaluation cache: {e}")
            return None
    
    def invalidate_exif(self, file_path: str) -> bool:
        """
        Invalidate cached EXIF data for a photo file.
        
        Args:
            file_path: Photo file path
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            key = self._generate_cache_key(self.EXIF_PREFIX, file_path)
            deleted = self.redis_client.delete(key)
            
            if deleted:
                logger.debug(f"Invalidated EXIF cache: {Path(file_path).name}")
            
            return bool(deleted)
            
        except Exception as e:
            logger.error(f"Failed to invalidate EXIF cache: {e}")
            return False
    
    def invalidate_ai_evaluation(self, file_path: str) -> bool:
        """
        Invalidate cached AI evaluation for a photo file.
        
        Args:
            file_path: Photo file path
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            key = self._generate_cache_key(self.AI_EVAL_PREFIX, file_path)
            deleted = self.redis_client.delete(key)
            
            if deleted:
                logger.debug(f"Invalidated AI eval cache: {Path(file_path).name}")
            
            return bool(deleted)
            
        except Exception as e:
            logger.error(f"Failed to invalidate AI evaluation cache: {e}")
            return False
    
    def invalidate_all(self, file_path: str) -> bool:
        """
        Invalidate all cached data for a photo file.
        
        Args:
            file_path: Photo file path
            
        Returns:
            True if all caches invalidated successfully, False otherwise
        """
        exif_result = self.invalidate_exif(file_path)
        ai_result = self.invalidate_ai_evaluation(file_path)
        
        return exif_result or ai_result
    
    def clear_all_exif(self) -> int:
        """
        Clear all cached EXIF data.
        
        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0
        
        try:
            pattern = f"{self.EXIF_PREFIX}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} EXIF cache entries")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to clear EXIF cache: {e}")
            return 0
    
    def clear_all_ai_evaluations(self) -> int:
        """
        Clear all cached AI evaluation results.
        
        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0
        
        try:
            pattern = f"{self.AI_EVAL_PREFIX}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} AI evaluation cache entries")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to clear AI evaluation cache: {e}")
            return 0
    
    def clear_all(self) -> int:
        """
        Clear all cached data.
        
        Returns:
            Total number of keys deleted
        """
        exif_count = self.clear_all_exif()
        ai_count = self.clear_all_ai_evaluations()
        
        total = exif_count + ai_count
        logger.info(f"Cleared total {total} cache entries")
        
        return total
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics:
            {
                'enabled': bool,
                'exif_count': int,
                'ai_eval_count': int,
                'total_keys': int,
                'memory_used': str,
                'connected': bool
            }
        """
        stats = {
            'enabled': self.enabled,
            'exif_count': 0,
            'ai_eval_count': 0,
            'total_keys': 0,
            'memory_used': 'N/A',
            'connected': False
        }
        
        if not self.enabled:
            return stats
        
        try:
            # Test connection
            self.redis_client.ping()
            stats['connected'] = True
            
            # Count keys by prefix
            exif_keys = self.redis_client.keys(f"{self.EXIF_PREFIX}:*")
            ai_keys = self.redis_client.keys(f"{self.AI_EVAL_PREFIX}:*")
            
            stats['exif_count'] = len(exif_keys)
            stats['ai_eval_count'] = len(ai_keys)
            stats['total_keys'] = stats['exif_count'] + stats['ai_eval_count']
            
            # Get memory info
            info = self.redis_client.info('memory')
            memory_bytes = info.get('used_memory', 0)
            stats['memory_used'] = self._format_bytes(memory_bytes)
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            stats['connected'] = False
        
        return stats
    
    def _format_bytes(self, bytes_value: int) -> str:
        """
        Format bytes to human-readable string.
        
        Args:
            bytes_value: Number of bytes
            
        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        
        return f"{bytes_value:.2f} TB"
    
    def is_enabled(self) -> bool:
        """
        Check if caching is enabled.
        
        Returns:
            True if caching is enabled and Redis is connected
        """
        return self.enabled
    
    def close(self):
        """Close Redis connection."""
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Cache manager connection closed")
            except Exception as e:
                logger.error(f"Error closing cache manager: {e}")


# Global cache manager instance
_cache_manager = None


def get_cache_manager(
    host: str = 'localhost',
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None
) -> CacheManager:
    """
    Get or create global cache manager instance.
    
    Args:
        host: Redis server host
        port: Redis server port
        db: Redis database number
        password: Redis password (optional)
        
    Returns:
        CacheManager instance
    """
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CacheManager(
            host=host,
            port=port,
            db=db,
            password=password
        )
    
    return _cache_manager


def main():
    """Example usage of cache manager."""
    import sys
    
    # Initialize cache manager
    cache = CacheManager()
    
    if not cache.is_enabled():
        print("Cache is not enabled. Make sure Redis is running.")
        sys.exit(1)
    
    # Example EXIF data
    test_file = "test_photo.jpg"
    exif_data = {
        'camera': {'make': 'Canon', 'model': 'EOS R5'},
        'settings': {'iso': 800, 'aperture': 2.8},
        'location': {'latitude': 35.6762, 'longitude': 139.6503}
    }
    
    # Cache EXIF data
    print(f"Caching EXIF data for: {test_file}")
    cache.cache_exif(test_file, exif_data)
    
    # Retrieve EXIF data
    print(f"Retrieving EXIF data for: {test_file}")
    cached_data = cache.get_exif(test_file)
    print(f"Cached data: {cached_data}")
    
    # Get cache stats
    print("\nCache Statistics:")
    stats = cache.get_cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Invalidate cache
    print(f"\nInvalidating cache for: {test_file}")
    cache.invalidate_all(test_file)
    
    # Try to retrieve again (should be None)
    cached_data = cache.get_exif(test_file)
    print(f"After invalidation: {cached_data}")
    
    # Close connection
    cache.close()


if __name__ == '__main__':
    main()
