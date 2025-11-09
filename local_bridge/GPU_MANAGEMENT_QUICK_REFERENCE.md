# GPU Management System - Quick Reference

## Quick Commands

### Get GPU Status
```python
from gpu_manager import get_gpu_manager

gpu = get_gpu_manager()
status = gpu.get_gpu_status()
```

### Allocate Memory
```python
gpu.allocate_memory("task_id", 2048)  # 2GB
```

### Deallocate Memory
```python
gpu.deallocate_memory("task_id")
```

### Check Throttling
```python
if gpu.should_throttle_processing():
    speed = gpu.get_processing_speed_multiplier()
```

### Start Monitoring
```python
gpu.start_monitoring()
```

### Stop Monitoring
```python
gpu.stop_monitoring()
```

## API Endpoints

### Status
```bash
GET /api/gpu/status?gpu_id=0
GET /api/gpu/status/all
```

### Metrics
```bash
GET /api/gpu/metrics?gpu_id=0
GET /api/gpu/metrics/history?limit=100
GET /api/gpu/temperature/trend?duration=5
```

### Memory
```bash
POST /api/gpu/memory/allocate
{
  "allocation_id": "task",
  "required_mb": 2048
}

POST /api/gpu/memory/deallocate
{
  "allocation_id": "task"
}

GET /api/gpu/memory/available?gpu_id=0
```

### Throttling
```bash
GET /api/gpu/throttle/status
```

### Monitoring
```bash
POST /api/gpu/monitoring/start
POST /api/gpu/monitoring/stop
```

### Configuration
```bash
GET /api/gpu/config
PUT /api/gpu/config
{
  "temp_throttle": 80
}
```

## GPU States

| State | Temperature | Memory | Speed |
|-------|-------------|--------|-------|
| OPTIMAL | < 65°C | < 70% | 1.0x |
| NORMAL | 65-75°C | 70-85% | 0.8x |
| THROTTLED | 75-85°C | 85-95% | 0.5x |
| CRITICAL | > 85°C | > 95% | 0.0x |

## Event Callbacks

```python
def on_throttle(metrics):
    print(f"Throttling: {metrics.temperature_celsius}°C")

def on_critical(metrics):
    print(f"CRITICAL: {metrics.temperature_celsius}°C")

gpu.register_callback('throttle', on_throttle)
gpu.register_callback('critical', on_critical)
```

**Available Events:**
- `state_change` - GPU state changed
- `throttle` - Throttling activated
- `resume` - Normal operation resumed
- `critical` - Critical state entered
- `overheat` - Temperature exceeds throttle threshold

## Configuration

```python
gpu.update_config({
    'temp_optimal': 65,
    'temp_throttle': 85,
    'memory_limit_mb': 6144
})
```

## Common Patterns

### Safe Memory Allocation
```python
if gpu.allocate_memory("task", 2048):
    try:
        # Use GPU
        process()
    finally:
        gpu.deallocate_memory("task")
```

### Throttle-Aware Processing
```python
while gpu.should_throttle_processing():
    time.sleep(5)
process()
```

### Temperature Monitoring
```python
gpu.start_monitoring()
trend = gpu.get_temperature_trend(duration_minutes=5)
print(f"Temp: {trend['current_temp']}°C")
gpu.stop_monitoring()
```

## Troubleshooting

### GPU Not Available
```python
if not gpu.is_available():
    # Install: pip install gputil
    # Check: nvidia-smi
```

### Allocation Failed
```python
available = gpu.get_available_memory()
print(f"Available: {available}MB")
```

### High Temperature
```python
status = gpu.get_gpu_status()
if status['temperature_celsius'] > 80:
    # Reduce load or wait
    time.sleep(30)
```

## Testing

```bash
# Run all tests
pytest test_gpu_manager.py -v

# Run specific test
pytest test_gpu_manager.py::TestGPUManager::test_gpu_status -v

# Run with coverage
pytest test_gpu_manager.py --cov=gpu_manager
```

## Examples

```bash
# Run examples
python example_gpu_usage.py
```

## Requirements

- **17.1**: GPU memory monitoring ✅
- **17.2**: GPU temperature monitoring ✅
- **17.3**: Processing throttling ✅
- **17.5**: Memory allocation management ✅

## Files

- `gpu_manager.py` - Core system
- `api_gpu.py` - REST API
- `test_gpu_manager.py` - Tests
- `example_gpu_usage.py` - Examples
- `GPU_MANAGEMENT_QUICK_START.md` - Full guide
- `GPU_MANAGEMENT_IMPLEMENTATION.md` - Details
