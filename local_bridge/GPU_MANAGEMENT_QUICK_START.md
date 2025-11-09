# GPU Management System - Quick Start Guide

## Overview

The GPU Management System provides comprehensive monitoring, memory allocation, temperature tracking, and throttling for optimal GPU utilization in the Junmai AutoDev system.

**Requirements:** 17.1, 17.2, 17.3, 17.5

## Features

- ✅ GPU memory usage monitoring
- ✅ GPU temperature monitoring
- ✅ Memory allocation management
- ✅ Processing throttling based on temperature and load
- ✅ Multi-GPU support
- ✅ Automatic recovery from critical states
- ✅ Real-time metrics and history tracking
- ✅ Event callbacks for state changes

## Quick Start

### 1. Basic GPU Status

```python
from gpu_manager import get_gpu_manager

# Get GPU manager instance
gpu_manager = get_gpu_manager()

# Check if GPU is available
if gpu_manager.is_available():
    # Get GPU status
    status = gpu_manager.get_gpu_status()
    
    print(f"GPU: {status['name']}")
    print(f"Temperature: {status['temperature_celsius']}°C")
    print(f"Memory: {status['memory']['percent']:.1f}%")
    print(f"State: {status['state']}")
```

### 2. Memory Allocation

```python
# Allocate GPU memory
success = gpu_manager.allocate_memory("llm_model", 2048)  # 2GB

if success:
    print("Memory allocated successfully")
    
    # Check available memory
    available = gpu_manager.get_available_memory()
    print(f"Available: {available}MB")
    
    # ... use GPU memory ...
    
    # Deallocate when done
    gpu_manager.deallocate_memory("llm_model")
```

### 3. Temperature Monitoring

```python
# Start continuous monitoring
gpu_manager.start_monitoring()

# Get temperature trend
trend = gpu_manager.get_temperature_trend(duration_minutes=5)

print(f"Current: {trend['current_temp']}°C")
print(f"Average: {trend['avg_temp']:.1f}°C")
print(f"Trend: {trend['trend']}")

# Stop monitoring
gpu_manager.stop_monitoring()
```

### 4. Processing Throttling

```python
# Check if processing should be throttled
if gpu_manager.should_throttle_processing():
    # Get recommended speed
    speed = gpu_manager.get_processing_speed_multiplier()
    
    if speed == 0.0:
        print("Pause processing - GPU critical")
    elif speed == 0.5:
        print("Reduce to half speed - GPU throttled")
    else:
        print(f"Process at {speed:.0%} speed")
```

### 5. State Change Callbacks

```python
def on_throttle(metrics):
    print(f"GPU throttling! Temp: {metrics.temperature_celsius}°C")
    # Reduce processing speed

def on_critical(metrics):
    print(f"GPU CRITICAL! Temp: {metrics.temperature_celsius}°C")
    # Pause all processing

# Register callbacks
gpu_manager.register_callback('throttle', on_throttle)
gpu_manager.register_callback('critical', on_critical)

# Start monitoring
gpu_manager.start_monitoring()
```

## API Endpoints

### Get GPU Status

```bash
GET /api/gpu/status?gpu_id=0
```

Response:
```json
{
  "success": true,
  "data": {
    "available": true,
    "gpu_id": 0,
    "name": "NVIDIA GeForce RTX 4060",
    "state": "normal",
    "temperature_celsius": 68.0,
    "load_percent": 45.2,
    "memory": {
      "used_mb": 3072,
      "total_mb": 8192,
      "percent": 37.5
    },
    "throttling": {
      "is_throttled": false,
      "should_throttle": false,
      "speed_multiplier": 0.8
    }
  }
}
```

### Allocate Memory

```bash
POST /api/gpu/memory/allocate
Content-Type: application/json

{
  "allocation_id": "llm_model",
  "required_mb": 2048,
  "gpu_id": 0
}
```

### Get Temperature Trend

```bash
GET /api/gpu/temperature/trend?gpu_id=0&duration=5
```

### Start Monitoring

```bash
POST /api/gpu/monitoring/start
```

## GPU States

| State | Temperature | Memory | Action |
|-------|-------------|--------|--------|
| **OPTIMAL** | < 65°C | < 70% | Full speed (1.0x) |
| **NORMAL** | 65-75°C | 70-85% | Reduced speed (0.8x) |
| **THROTTLED** | 75-85°C | 85-95% | Half speed (0.5x) |
| **CRITICAL** | > 85°C | > 95% | Pause (0.0x) |

## Configuration

### Default Configuration

```python
config = {
    # Temperature thresholds (Celsius)
    'temp_optimal': 65,
    'temp_normal': 75,
    'temp_throttle': 85,
    'temp_critical': 90,
    
    # Memory thresholds (percent)
    'memory_optimal': 70,
    'memory_normal': 85,
    'memory_critical': 95,
    
    # Memory limits
    'memory_limit_mb': 6144,  # 6GB for RTX 4060
    'memory_reserve_mb': 512,  # Reserve 512MB
    
    # Monitoring
    'monitor_interval': 3,  # Monitor every 3 seconds
    'history_size': 200,    # Keep 200 measurements
}
```

### Update Configuration

```python
gpu_manager.update_config({
    'temp_throttle': 80,
    'memory_limit_mb': 7168
})
```

Or via API:

```bash
PUT /api/gpu/config
Content-Type: application/json

{
  "temp_throttle": 80,
  "memory_limit_mb": 7168
}
```

## Integration with Processing Pipeline

### Example: LLM Processing with GPU Management

```python
from gpu_manager import get_gpu_manager

gpu_manager = get_gpu_manager()

# Allocate memory for LLM
if gpu_manager.allocate_memory("llm_inference", 2048):
    try:
        # Check if we should throttle
        if gpu_manager.should_throttle_processing():
            speed = gpu_manager.get_processing_speed_multiplier()
            
            if speed == 0.0:
                print("Waiting for GPU to cool down...")
                time.sleep(30)
            else:
                # Adjust batch size based on speed
                batch_size = int(base_batch_size * speed)
        
        # Process with LLM
        result = process_with_llm(image, batch_size)
        
    finally:
        # Always deallocate
        gpu_manager.deallocate_memory("llm_inference")
```

### Example: Automatic Throttling

```python
def process_photos_with_gpu_management(photos):
    gpu_manager = get_gpu_manager()
    gpu_manager.start_monitoring()
    
    # Register throttle callback
    def on_throttle(metrics):
        print(f"Throttling: {metrics.temperature_celsius}°C")
        time.sleep(10)  # Cool down
    
    gpu_manager.register_callback('throttle', on_throttle)
    
    try:
        for photo in photos:
            # Check throttling before each photo
            while gpu_manager.should_throttle_processing():
                time.sleep(5)
            
            # Process photo
            process_photo(photo)
    
    finally:
        gpu_manager.stop_monitoring()
```

## Monitoring Dashboard Integration

### Real-time GPU Status Widget

```python
def get_gpu_dashboard_data():
    """Get GPU data for dashboard display"""
    gpu_manager = get_gpu_manager()
    
    if not gpu_manager.is_available():
        return {'available': False}
    
    status = gpu_manager.get_gpu_status()
    trend = gpu_manager.get_temperature_trend(duration_minutes=5)
    
    return {
        'available': True,
        'name': status['name'],
        'temperature': status['temperature_celsius'],
        'temp_trend': trend.get('trend', 'unknown'),
        'memory_percent': status['memory']['percent'],
        'state': status['state'],
        'state_color': {
            'optimal': 'green',
            'normal': 'blue',
            'throttled': 'orange',
            'critical': 'red'
        }.get(status['state'], 'gray'),
        'throttling': status['throttling']['is_throttled']
    }
```

## Troubleshooting

### GPU Not Detected

```python
gpu_manager = get_gpu_manager()

if not gpu_manager.is_available():
    print("GPU not available")
    print("Possible causes:")
    print("1. GPUtil not installed: pip install gputil")
    print("2. No NVIDIA GPU detected")
    print("3. GPU drivers not installed")
```

### Memory Allocation Failed

```python
success = gpu_manager.allocate_memory("task", 4096)

if not success:
    # Check available memory
    available = gpu_manager.get_available_memory()
    print(f"Available: {available}MB")
    
    # Check current allocations
    status = gpu_manager.get_gpu_status()
    alloc_stats = status['memory']['allocation_stats']
    print(f"Current allocations: {alloc_stats['allocations']}")
```

### High Temperature

```python
status = gpu_manager.get_gpu_status()

if status['temperature_celsius'] > 80:
    print("High GPU temperature detected!")
    print("Actions:")
    print("1. Check GPU cooling")
    print("2. Reduce processing load")
    print("3. Increase throttle cooldown")
    
    # Increase cooldown
    gpu_manager.update_config({
        'throttle_cooldown_seconds': 60
    })
```

## Best Practices

1. **Always Deallocate Memory**
   ```python
   try:
       gpu_manager.allocate_memory("task", 1024)
       # ... process ...
   finally:
       gpu_manager.deallocate_memory("task")
   ```

2. **Monitor Before Heavy Processing**
   ```python
   gpu_manager.start_monitoring()
   # ... heavy GPU work ...
   gpu_manager.stop_monitoring()
   ```

3. **Respect Throttling Signals**
   ```python
   if gpu_manager.should_throttle_processing():
       # Reduce load or wait
       time.sleep(10)
   ```

4. **Use Callbacks for Automation**
   ```python
   def auto_pause_on_critical(metrics):
       pause_all_processing()
   
   gpu_manager.register_callback('critical', auto_pause_on_critical)
   ```

5. **Reserve Memory for System**
   - Default: 512MB reserved
   - Adjust based on your needs
   - Leave headroom for OS and other apps

## Performance Tips

- **Optimal Memory Limit**: Set to 75-80% of total GPU memory
- **Monitor Interval**: 3-5 seconds for good balance
- **History Size**: 200 samples = ~10 minutes at 3s interval
- **Cooldown Period**: 30-60 seconds after throttling

## Requirements Mapping

- **17.1**: GPU memory usage monitoring and allocation management
- **17.2**: GPU temperature monitoring with trend analysis
- **17.3**: Processing throttling based on GPU state
- **17.5**: Automatic recovery and state management

## Next Steps

1. Run example: `python example_gpu_usage.py`
2. Run tests: `pytest test_gpu_manager.py -v`
3. Integrate with your processing pipeline
4. Configure thresholds for your GPU model
5. Set up monitoring dashboard

## Support

For issues or questions:
- Check logs in `logs/main.log`
- Review GPU metrics history
- Verify GPU drivers are up to date
- Ensure GPUtil is installed: `pip install gputil`
