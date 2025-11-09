"""
Example usage of Cache Manager for Junmai AutoDev System

Demonstrates how to use the cache manager to improve performance
by caching EXIF data and AI evaluation results.
"""

import logging
from pathlib import Path
from cache_manager import CacheManager, get_cache_manager
from exif_analyzer import EXIFAnalyzer
from ai_selector import AISelector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_basic_caching():
    """Basic caching example."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Caching")
    print("=" * 60)
    
    # Initialize cache manager
    cache = CacheManager()
    
    if not cache.is_enabled():
        print("⚠️  Cache is not enabled. Make sure Redis is running.")
        print("   Start Redis: redis-server")
        return
    
    print("✓ Cache manager initialized\n")
    
    # Example data
    test_file = "sample_photo.jpg"
    exif_data = {
        'camera': {
            'make': 'Canon',
            'model': 'EOS R5',
            'lens': 'RF 24-70mm F2.8 L IS USM'
        },
        'settings': {
            'iso': 800,
            'aperture': 2.8,
            'shutter_speed': '1/250',
            'focal_length': 50.0
        },
        'location': {
            'latitude': 35.6762,
            'longitude': 139.6503,
            'location_type': 'outdoor'
        }
    }
    
    # Cache EXIF data
    print(f"1. Caching EXIF data for: {test_file}")
    success = cache.cache_exif(test_file, exif_data)
    print(f"   Result: {'✓ Success' if success else '✗ Failed'}\n")
    
    # Retrieve from cache
    print(f"2. Retrieving EXIF data from cache")
    cached_data = cache.get_exif(test_file)
    if cached_data:
        print(f"   ✓ Cache hit!")
        print(f"   Camera: {cached_data['camera']['make']} {cached_data['camera']['model']}")
        print(f"   ISO: {cached_data['settings']['iso']}")
    else:
        print(f"   ✗ Cache miss")
    
    print()


def example_with_exif_analyzer():
    """Example using cache with EXIF analyzer."""
    print("=" * 60)
    print("EXAMPLE 2: Cache with EXIF Analyzer")
    print("=" * 60)
    
    # Initialize components
    cache = CacheManager()
    analyzer = EXIFAnalyzer()
    
    if not cache.is_enabled():
        print("⚠️  Cache is not enabled. Continuing without cache.")
    
    # Test file (replace with actual photo path)
    test_file = "test_photo.jpg"
    
    if not Path(test_file).exists():
        print(f"⚠️  Test file not found: {test_file}")
        print("   Please provide a valid photo file path.")
        return
    
    print(f"Analyzing: {test_file}\n")
    
    # First attempt - will analyze and cache
    print("1. First analysis (cache miss expected)")
    cached_exif = cache.get_exif(test_file)
    
    if cached_exif:
        print("   ✓ Using cached EXIF data")
        exif_data = cached_exif
    else:
        print("   ✗ Cache miss - analyzing EXIF...")
        exif_data = analyzer.analyze(test_file)
        cache.cache_exif(test_file, exif_data)
        print("   ✓ EXIF data cached")
    
    print(f"   Camera: {exif_data.get('camera', {}).get('make', 'Unknown')}")
    print()
    
    # Second attempt - should use cache
    print("2. Second analysis (cache hit expected)")
    cached_exif = cache.get_exif(test_file)
    
    if cached_exif:
        print("   ✓ Using cached EXIF data (fast!)")
    else:
        print("   ✗ Cache miss - analyzing EXIF...")
        exif_data = analyzer.analyze(test_file)
        cache.cache_exif(test_file, exif_data)
    
    print()


def example_with_ai_selector():
    """Example using cache with AI selector."""
    print("=" * 60)
    print("EXAMPLE 3: Cache with AI Selector")
    print("=" * 60)
    
    # Initialize components
    cache = CacheManager()
    selector = AISelector(enable_llm=False)  # Disable LLM for faster testing
    
    if not cache.is_enabled():
        print("⚠️  Cache is not enabled. Continuing without cache.")
    
    # Test file (replace with actual photo path)
    test_file = "test_photo.jpg"
    
    if not Path(test_file).exists():
        print(f"⚠️  Test file not found: {test_file}")
        print("   Please provide a valid photo file path.")
        return
    
    print(f"Evaluating: {test_file}\n")
    
    # First evaluation - will process and cache
    print("1. First evaluation (cache miss expected)")
    cached_eval = cache.get_ai_evaluation(test_file)
    
    if cached_eval:
        print("   ✓ Using cached AI evaluation")
        evaluation = cached_eval
    else:
        print("   ✗ Cache miss - running AI evaluation...")
        evaluation = selector.evaluate(test_file)
        cache.cache_ai_evaluation(test_file, evaluation)
        print("   ✓ AI evaluation cached")
    
    print(f"   Score: {evaluation.get('overall_score', 0):.2f} / 5.0")
    print(f"   Recommendation: {evaluation.get('recommendation', 'unknown')}")
    print()
    
    # Second evaluation - should use cache
    print("2. Second evaluation (cache hit expected)")
    cached_eval = cache.get_ai_evaluation(test_file)
    
    if cached_eval:
        print("   ✓ Using cached AI evaluation (fast!)")
        print(f"   Score: {cached_eval.get('overall_score', 0):.2f} / 5.0")
    else:
        print("   ✗ Cache miss - running AI evaluation...")
        evaluation = selector.evaluate(test_file)
        cache.cache_ai_evaluation(test_file, evaluation)
    
    print()


def example_cache_invalidation():
    """Example of cache invalidation."""
    print("=" * 60)
    print("EXAMPLE 4: Cache Invalidation")
    print("=" * 60)
    
    cache = CacheManager()
    
    if not cache.is_enabled():
        print("⚠️  Cache is not enabled.")
        return
    
    test_file = "test_photo.jpg"
    
    # Cache some data
    print("1. Caching test data")
    exif_data = {'camera': {'make': 'Canon'}}
    ai_eval = {'overall_score': 4.5}
    
    cache.cache_exif(test_file, exif_data)
    cache.cache_ai_evaluation(test_file, ai_eval)
    print("   ✓ Data cached\n")
    
    # Verify cache
    print("2. Verifying cache")
    print(f"   EXIF cached: {cache.get_exif(test_file) is not None}")
    print(f"   AI eval cached: {cache.get_ai_evaluation(test_file) is not None}")
    print()
    
    # Invalidate EXIF only
    print("3. Invalidating EXIF cache")
    cache.invalidate_exif(test_file)
    print(f"   EXIF cached: {cache.get_exif(test_file) is not None}")
    print(f"   AI eval cached: {cache.get_ai_evaluation(test_file) is not None}")
    print()
    
    # Invalidate all
    print("4. Invalidating all cache for file")
    cache.invalidate_all(test_file)
    print(f"   EXIF cached: {cache.get_exif(test_file) is not None}")
    print(f"   AI eval cached: {cache.get_ai_evaluation(test_file) is not None}")
    print()


def example_cache_statistics():
    """Example of cache statistics."""
    print("=" * 60)
    print("EXAMPLE 5: Cache Statistics")
    print("=" * 60)
    
    cache = CacheManager()
    
    if not cache.is_enabled():
        print("⚠️  Cache is not enabled.")
        return
    
    # Get statistics
    stats = cache.get_cache_stats()
    
    print("Cache Statistics:")
    print(f"  Enabled: {stats['enabled']}")
    print(f"  Connected: {stats['connected']}")
    print(f"  EXIF entries: {stats['exif_count']}")
    print(f"  AI eval entries: {stats['ai_eval_count']}")
    print(f"  Total keys: {stats['total_keys']}")
    print(f"  Memory used: {stats['memory_used']}")
    print()


def example_global_cache_manager():
    """Example using global cache manager instance."""
    print("=" * 60)
    print("EXAMPLE 6: Global Cache Manager")
    print("=" * 60)
    
    # Get global cache manager instance
    cache1 = get_cache_manager()
    cache2 = get_cache_manager()
    
    # Both should be the same instance
    print(f"Same instance: {cache1 is cache2}")
    print(f"Cache enabled: {cache1.is_enabled()}")
    print()


def example_performance_comparison():
    """Compare performance with and without cache."""
    print("=" * 60)
    print("EXAMPLE 7: Performance Comparison")
    print("=" * 60)
    
    import time
    
    cache = CacheManager()
    analyzer = EXIFAnalyzer()
    
    if not cache.is_enabled():
        print("⚠️  Cache is not enabled.")
        return
    
    test_file = "test_photo.jpg"
    
    if not Path(test_file).exists():
        print(f"⚠️  Test file not found: {test_file}")
        return
    
    # Clear cache first
    cache.invalidate_all(test_file)
    
    # Without cache
    print("1. Without cache (first run)")
    start = time.time()
    exif_data = analyzer.analyze(test_file)
    duration_no_cache = time.time() - start
    print(f"   Time: {duration_no_cache*1000:.2f} ms")
    
    # Cache the data
    cache.cache_exif(test_file, exif_data)
    
    # With cache
    print("\n2. With cache (second run)")
    start = time.time()
    cached_data = cache.get_exif(test_file)
    duration_with_cache = time.time() - start
    print(f"   Time: {duration_with_cache*1000:.2f} ms")
    
    # Calculate speedup
    if duration_with_cache > 0:
        speedup = duration_no_cache / duration_with_cache
        print(f"\n   Speedup: {speedup:.1f}x faster with cache!")
    
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("CACHE MANAGER EXAMPLES")
    print("=" * 60 + "\n")
    
    try:
        # Run examples
        example_basic_caching()
        example_cache_statistics()
        example_cache_invalidation()
        example_global_cache_manager()
        
        # These require actual photo files
        # example_with_exif_analyzer()
        # example_with_ai_selector()
        # example_performance_comparison()
        
        print("=" * 60)
        print("Examples completed!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Error running examples: {e}")
        raise


if __name__ == '__main__':
    main()
