"""
Unit tests for Cache Manager

Tests Redis-based caching functionality for EXIF data and AI evaluations.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from cache_manager import CacheManager, get_cache_manager


class TestCacheManager:
    """Test suite for CacheManager class."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        with patch('cache_manager.redis.Redis') as mock_redis_class:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_redis_class.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def cache_manager(self, mock_redis):
        """Create CacheManager instance with mocked Redis."""
        with patch('cache_manager.redis.ConnectionPool'):
            cache = CacheManager()
            cache.redis_client = mock_redis
            cache.enabled = True
            return cache
    
    def test_initialization_success(self, mock_redis):
        """Test successful cache manager initialization."""
        with patch('cache_manager.redis.ConnectionPool'):
            cache = CacheManager()
            assert cache.enabled is True
            mock_redis.ping.assert_called_once()
    
    def test_initialization_failure(self):
        """Test cache manager initialization failure."""
        with patch('cache_manager.redis.ConnectionPool') as mock_pool:
            mock_pool.side_effect = Exception("Connection failed")
            cache = CacheManager()
            assert cache.enabled is False
    
    def test_generate_cache_key(self, cache_manager):
        """Test cache key generation."""
        file_path = "/path/to/photo.jpg"
        key = cache_manager._generate_cache_key("test", file_path)
        
        assert key.startswith("test:")
        assert len(key) > len("test:")
    
    def test_cache_exif_success(self, cache_manager, mock_redis):
        """Test successful EXIF data caching."""
        file_path = "test_photo.jpg"
        exif_data = {
            'camera': {'make': 'Canon', 'model': 'EOS R5'},
            'settings': {'iso': 800}
        }
        
        result = cache_manager.cache_exif(file_path, exif_data)
        
        assert result is True
        mock_redis.setex.assert_called_once()
        
        # Verify the data was serialized correctly
        call_args = mock_redis.setex.call_args
        assert call_args[0][0].startswith("exif:")
        assert isinstance(call_args[0][2], str)  # JSON string
    
    def test_cache_exif_disabled(self):
        """Test EXIF caching when cache is disabled."""
        cache = CacheManager()
        cache.enabled = False
        
        result = cache.cache_exif("test.jpg", {})
        assert result is False
    
    def test_get_exif_hit(self, cache_manager, mock_redis):
        """Test retrieving cached EXIF data (cache hit)."""
        file_path = "test_photo.jpg"
        exif_data = {'camera': {'make': 'Canon'}}
        
        # Mock Redis to return cached data
        mock_redis.get.return_value = json.dumps(exif_data)
        
        result = cache_manager.get_exif(file_path)
        
        assert result == exif_data
        mock_redis.get.assert_called_once()
    
    def test_get_exif_miss(self, cache_manager, mock_redis):
        """Test retrieving EXIF data when not cached (cache miss)."""
        file_path = "test_photo.jpg"
        
        # Mock Redis to return None (cache miss)
        mock_redis.get.return_value = None
        
        result = cache_manager.get_exif(file_path)
        
        assert result is None
        mock_redis.get.assert_called_once()
    
    def test_cache_ai_evaluation_success(self, cache_manager, mock_redis):
        """Test successful AI evaluation caching."""
        file_path = "test_photo.jpg"
        ai_eval = {
            'overall_score': 4.5,
            'recommendation': 'approve',
            'tags': ['portrait', 'high_quality']
        }
        
        result = cache_manager.cache_ai_evaluation(file_path, ai_eval)
        
        assert result is True
        mock_redis.setex.assert_called_once()
        
        # Verify the key prefix
        call_args = mock_redis.setex.call_args
        assert call_args[0][0].startswith("ai_eval:")
    
    def test_get_ai_evaluation_hit(self, cache_manager, mock_redis):
        """Test retrieving cached AI evaluation (cache hit)."""
        file_path = "test_photo.jpg"
        ai_eval = {'overall_score': 4.5}
        
        # Mock Redis to return cached data
        mock_redis.get.return_value = json.dumps(ai_eval)
        
        result = cache_manager.get_ai_evaluation(file_path)
        
        assert result == ai_eval
        mock_redis.get.assert_called_once()
    
    def test_invalidate_exif(self, cache_manager, mock_redis):
        """Test EXIF cache invalidation."""
        file_path = "test_photo.jpg"
        
        # Mock successful deletion
        mock_redis.delete.return_value = 1
        
        result = cache_manager.invalidate_exif(file_path)
        
        assert result is True
        mock_redis.delete.assert_called_once()
    
    def test_invalidate_ai_evaluation(self, cache_manager, mock_redis):
        """Test AI evaluation cache invalidation."""
        file_path = "test_photo.jpg"
        
        # Mock successful deletion
        mock_redis.delete.return_value = 1
        
        result = cache_manager.invalidate_ai_evaluation(file_path)
        
        assert result is True
        mock_redis.delete.assert_called_once()
    
    def test_invalidate_all(self, cache_manager, mock_redis):
        """Test invalidating all cache for a file."""
        file_path = "test_photo.jpg"
        
        # Mock successful deletions
        mock_redis.delete.return_value = 1
        
        result = cache_manager.invalidate_all(file_path)
        
        assert result is True
        assert mock_redis.delete.call_count == 2  # EXIF + AI eval
    
    def test_clear_all_exif(self, cache_manager, mock_redis):
        """Test clearing all EXIF cache entries."""
        # Mock keys and delete
        mock_redis.keys.return_value = ['exif:key1', 'exif:key2', 'exif:key3']
        mock_redis.delete.return_value = 3
        
        result = cache_manager.clear_all_exif()
        
        assert result == 3
        mock_redis.keys.assert_called_once_with("exif:*")
        mock_redis.delete.assert_called_once()
    
    def test_clear_all_ai_evaluations(self, cache_manager, mock_redis):
        """Test clearing all AI evaluation cache entries."""
        # Mock keys and delete
        mock_redis.keys.return_value = ['ai_eval:key1', 'ai_eval:key2']
        mock_redis.delete.return_value = 2
        
        result = cache_manager.clear_all_ai_evaluations()
        
        assert result == 2
        mock_redis.keys.assert_called_once_with("ai_eval:*")
    
    def test_clear_all(self, cache_manager, mock_redis):
        """Test clearing all cache entries."""
        # Mock keys and delete for both prefixes
        def keys_side_effect(pattern):
            if pattern == "exif:*":
                return ['exif:key1', 'exif:key2']
            elif pattern == "ai_eval:*":
                return ['ai_eval:key1']
            return []
        
        mock_redis.keys.side_effect = keys_side_effect
        mock_redis.delete.side_effect = [2, 1]  # EXIF count, AI eval count
        
        result = cache_manager.clear_all()
        
        assert result == 3  # Total
        assert mock_redis.keys.call_count == 2
        assert mock_redis.delete.call_count == 2
    
    def test_get_cache_stats(self, cache_manager, mock_redis):
        """Test getting cache statistics."""
        # Mock Redis info and keys
        mock_redis.ping.return_value = True
        mock_redis.keys.side_effect = [
            ['exif:1', 'exif:2'],  # EXIF keys
            ['ai_eval:1']  # AI eval keys
        ]
        mock_redis.info.return_value = {'used_memory': 1024 * 1024}  # 1 MB
        
        stats = cache_manager.get_cache_stats()
        
        assert stats['enabled'] is True
        assert stats['connected'] is True
        assert stats['exif_count'] == 2
        assert stats['ai_eval_count'] == 1
        assert stats['total_keys'] == 3
        assert 'MB' in stats['memory_used']
    
    def test_get_cache_stats_disabled(self):
        """Test getting stats when cache is disabled."""
        cache = CacheManager()
        cache.enabled = False
        
        stats = cache.get_cache_stats()
        
        assert stats['enabled'] is False
        assert stats['connected'] is False
        assert stats['total_keys'] == 0
    
    def test_format_bytes(self, cache_manager):
        """Test byte formatting."""
        assert "B" in cache_manager._format_bytes(500)
        assert "KB" in cache_manager._format_bytes(1024)
        assert "MB" in cache_manager._format_bytes(1024 * 1024)
        assert "GB" in cache_manager._format_bytes(1024 * 1024 * 1024)
    
    def test_is_enabled(self, cache_manager):
        """Test checking if cache is enabled."""
        assert cache_manager.is_enabled() is True
        
        cache_manager.enabled = False
        assert cache_manager.is_enabled() is False
    
    def test_close(self, cache_manager, mock_redis):
        """Test closing cache connection."""
        cache_manager.close()
        mock_redis.close.assert_called_once()


class TestGlobalCacheManager:
    """Test suite for global cache manager instance."""
    
    def test_get_cache_manager_singleton(self):
        """Test that get_cache_manager returns singleton instance."""
        with patch('cache_manager.CacheManager') as mock_cache_class:
            mock_instance = Mock()
            mock_cache_class.return_value = mock_instance
            
            # Reset global instance
            import cache_manager as cm
            cm._cache_manager = None
            
            # Get instance twice
            cache1 = get_cache_manager()
            cache2 = get_cache_manager()
            
            # Should be the same instance
            assert cache1 is cache2
            # CacheManager should only be instantiated once
            assert mock_cache_class.call_count == 1


class TestCacheIntegration:
    """Integration tests for cache manager (requires Redis)."""
    
    @pytest.fixture
    def real_cache(self):
        """Create real cache manager (skipped if Redis not available)."""
        cache = CacheManager()
        if not cache.is_enabled():
            pytest.skip("Redis not available")
        
        # Clear any existing test data
        cache.clear_all()
        
        yield cache
        
        # Cleanup
        cache.clear_all()
        cache.close()
    
    def test_real_exif_caching(self, real_cache):
        """Test real EXIF caching with Redis."""
        file_path = "integration_test.jpg"
        exif_data = {
            'camera': {'make': 'Canon', 'model': 'EOS R5'},
            'settings': {'iso': 800, 'aperture': 2.8}
        }
        
        # Cache data
        assert real_cache.cache_exif(file_path, exif_data) is True
        
        # Retrieve data
        cached = real_cache.get_exif(file_path)
        assert cached is not None
        assert cached['camera']['make'] == 'Canon'
        assert cached['settings']['iso'] == 800
        
        # Invalidate
        assert real_cache.invalidate_exif(file_path) is True
        
        # Should be gone
        assert real_cache.get_exif(file_path) is None
    
    def test_real_ai_evaluation_caching(self, real_cache):
        """Test real AI evaluation caching with Redis."""
        file_path = "integration_test.jpg"
        ai_eval = {
            'overall_score': 4.5,
            'recommendation': 'approve',
            'tags': ['portrait', 'high_quality']
        }
        
        # Cache data
        assert real_cache.cache_ai_evaluation(file_path, ai_eval) is True
        
        # Retrieve data
        cached = real_cache.get_ai_evaluation(file_path)
        assert cached is not None
        assert cached['overall_score'] == 4.5
        assert 'portrait' in cached['tags']
        
        # Invalidate
        assert real_cache.invalidate_ai_evaluation(file_path) is True
        
        # Should be gone
        assert real_cache.get_ai_evaluation(file_path) is None


def main():
    """Run tests."""
    pytest.main([__file__, '-v'])


if __name__ == '__main__':
    main()
