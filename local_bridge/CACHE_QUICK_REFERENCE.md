# Cache Manager Quick Reference

## Quick Commands

### Start Redis
```bash
# Windows (WSL)
wsl -d Ubuntu -e redis-server

# macOS
redis-server

# Linux
sudo systemctl start redis
```

### Test Redis
```bash
redis-cli ping  # Should return: PONG
```

## Code Snippets

### Initialize Cache
```python
from cache_manager import CacheManager
cache = CacheManager()
```

### Cache EXIF Data
```python
# Cache
cache.cache_exif('photo.jpg', exif_data)

# Retrieve
cached = cache.get_exif('photo.jpg')

# Invalidate
cache.invalidate_exif('photo.jpg')
```

### Cache AI Evaluation
```python
# Cache
cache.cache_ai_evaluation('photo.jpg', evaluation)

# Retrieve
cached = cache.get_ai_evaluation('photo.jpg')

# Invalidate
cache.invalidate_ai_evaluation('photo.jpg')
```

### Pattern: Check Cache First
```python
cached = cache.get_exif(file_path)
if cached:
    return cached

result = analyzer.analyze(file_path)
cache.cache_exif(file_path, result)
return result
```

### Get Statistics
```python
stats = cache.get_cache_stats()
print(f"EXIF: {stats['exif_count']}, AI: {stats['ai_eval_count']}")
```

### Clear Cache
```python
cache.clear_all_exif()           # Clear all EXIF
cache.clear_all_ai_evaluations() # Clear all AI
cache.clear_all()                # Clear everything
```

## Common Issues

### Redis Not Running
```bash
# Check
redis-cli ping

# Start
redis-server
```

### Cache Disabled
```python
if not cache.is_enabled():
    print("Redis not available")
```

### Clear Stuck Cache
```python
cache.clear_all()
```

## Performance

- **EXIF**: 25-50x faster with cache
- **AI Eval**: 1000-2500x faster with cache
- **TTL**: EXIF 24h, AI 7d

## Files

- `cache_manager.py` - Implementation
- `example_cache_usage.py` - Examples
- `test_cache_manager.py` - Tests
- `CACHE_IMPLEMENTATION.md` - Full docs
- `CACHE_QUICK_START.md` - Tutorial

## Key Points

✅ Always check cache first  
✅ Use global instance: `get_cache_manager()`  
✅ Invalidate on file changes  
✅ Handle disabled cache gracefully  
✅ Monitor with `get_cache_stats()`
