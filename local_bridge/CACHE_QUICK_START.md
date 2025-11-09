# Cache Manager Quick Start Guide

## 5-Minute Setup

### 1. Start Redis

**Windows (WSL):**
```powershell
wsl -d Ubuntu -e redis-server
```

**macOS:**
```bash
redis-server
```

**Linux:**
```bash
sudo systemctl start redis
```

### 2. Verify Redis

```bash
redis-cli ping
# Should return: PONG
```

### 3. Use Cache Manager

```python
from cache_manager import CacheManager

# Initialize
cache = CacheManager()

# Cache EXIF data
exif_data = {'camera': {'make': 'Canon'}}
cache.cache_exif('photo.jpg', exif_data)

# Retrieve from cache
cached = cache.get_exif('photo.jpg')
print(cached)  # {'camera': {'make': 'Canon'}}
```

## Common Use Cases

### Use Case 1: Cache EXIF Analysis

```python
from cache_manager import get_cache_manager
from exif_analyzer import EXIFAnalyzer

cache = get_cache_manager()
analyzer = EXIFAnalyzer()

def analyze_with_cache(file_path):
    # Try cache first
    cached = cache.get_exif(file_path)
    if cached:
        return cached
    
    # Cache miss - analyze
    result = analyzer.analyze(file_path)
    cache.cache_exif(file_path, result)
    return result

# Use it
exif = analyze_with_cache('photo.jpg')
```

### Use Case 2: Cache AI Evaluation

```python
from cache_manager import get_cache_manager
from ai_selector import AISelector

cache = get_cache_manager()
selector = AISelector()

def evaluate_with_cache(file_path):
    # Try cache first
    cached = cache.get_ai_evaluation(file_path)
    if cached:
        return cached
    
    # Cache miss - evaluate
    result = selector.evaluate(file_path)
    cache.cache_ai_evaluation(file_path, result)
    return result

# Use it
evaluation = evaluate_with_cache('photo.jpg')
print(f"Score: {evaluation['overall_score']}")
```

### Use Case 3: Batch Processing with Cache

```python
from cache_manager import get_cache_manager

cache = get_cache_manager()

def process_batch(photo_files):
    results = []
    
    for file_path in photo_files:
        # Try cache
        cached = cache.get_ai_evaluation(file_path)
        
        if cached:
            results.append(cached)
        else:
            # Process and cache
            result = process_photo(file_path)
            cache.cache_ai_evaluation(file_path, result)
            results.append(result)
    
    return results
```

### Use Case 4: Invalidate on File Change

```python
from cache_manager import get_cache_manager

cache = get_cache_manager()

def reprocess_photo(file_path):
    # Invalidate old cache
    cache.invalidate_all(file_path)
    
    # Process fresh
    exif = analyzer.analyze(file_path)
    evaluation = selector.evaluate(file_path)
    
    # Cache new results
    cache.cache_exif(file_path, exif)
    cache.cache_ai_evaluation(file_path, evaluation)
    
    return evaluation
```

## Cache Statistics

```python
from cache_manager import get_cache_manager

cache = get_cache_manager()

# Get stats
stats = cache.get_cache_stats()

print(f"EXIF entries: {stats['exif_count']}")
print(f"AI eval entries: {stats['ai_eval_count']}")
print(f"Memory used: {stats['memory_used']}")
```

## Cache Maintenance

```python
from cache_manager import get_cache_manager

cache = get_cache_manager()

# Clear all EXIF cache
cache.clear_all_exif()

# Clear all AI evaluation cache
cache.clear_all_ai_evaluations()

# Clear everything
cache.clear_all()
```

## Performance Tips

### 1. Always Check Cache First

```python
# ✓ Fast
cached = cache.get_exif(file_path)
if not cached:
    cached = analyzer.analyze(file_path)
    cache.cache_exif(file_path, cached)

# ✗ Slow
result = analyzer.analyze(file_path)  # Always processes
```

### 2. Use Global Instance

```python
# ✓ Efficient
from cache_manager import get_cache_manager
cache = get_cache_manager()

# ✗ Wasteful
cache = CacheManager()  # Creates new connection each time
```

### 3. Batch Operations

```python
# ✓ Efficient
for file in files:
    cached = cache.get_exif(file)
    if not cached:
        # Process only cache misses
        pass

# ✗ Inefficient
for file in files:
    # Always processes
    result = analyzer.analyze(file)
```

## Troubleshooting

### Redis Not Running

```bash
# Check if Redis is running
redis-cli ping

# If not, start it
redis-server
```

### Cache Not Working

```python
cache = CacheManager()

if not cache.is_enabled():
    print("Cache is disabled - check Redis connection")
```

### Clear Stuck Cache

```python
# Clear all cache
cache.clear_all()

# Or clear specific type
cache.clear_all_exif()
cache.clear_all_ai_evaluations()
```

## Next Steps

- Read [CACHE_IMPLEMENTATION.md](CACHE_IMPLEMENTATION.md) for detailed documentation
- Run `py example_cache_usage.py` for more examples
- Run `py test_cache_manager.py` to verify installation

## Key Points

- ✅ Cache speeds up processing by 25-2500x
- ✅ EXIF cache: 24-hour TTL
- ✅ AI evaluation cache: 7-day TTL
- ✅ Automatic cache key generation
- ✅ Graceful fallback when Redis unavailable
- ✅ Thread-safe connection pooling
