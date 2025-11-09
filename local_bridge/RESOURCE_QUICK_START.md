# Resource Management Quick Start Guide

## Installation

### 1. Install Dependencies

```bash
pip install psutil gputil
```

**Note**: GPUtil is optional but recommended for GPU monitoring.

### 2. Verify Installation

```python
import psutil
print(f"CPU cores: {psutil.cpu_count()}")
print(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")

try:
    import GPUtil
    gpus = GPUtil.getGPUs()
    if gpus:
        print(f"GPU: {gpus[0].name}")
    else:
        print("No GPU detected")
except ImportError:
    print("GPUtil not installed (GPU monitoring disabled)")
```

## Basic Usage

### Start Resource Monitoring

```python
from resource_manager import get_resource_manager

# Get manager instance
manager = get_resource_manager()

# Start monitoring
manager.start_monitoring()

print("Resource monitoring started")
```

### Check System Status

```python
# Get current status
status = manager.get_system_status()

print(f"State: {status['state']}")
print(f"CPU: {status['cpu']['usage_percent']}%")
print(f"Memory: {status['memory']['percent']}%")

if status['gpu']['available']:
    print(f"GPU Temp: {status['gpu']['temperature']}°C")
    print(f"GPU Load: {status['gpu']['load']}%")
```

### Check if Should Throttle

```python
if manager.should_throttle_processing():
    print("⚠️  System busy - throttling recommended")
    speed = manager.get_recommended_speed_multiplier()
    print(f"Recommended speed: {speed}x")
else:
    print("✓ System resources OK")
```

### Check Idle State

```python
if manager.is_system_idle():
    idle_duration = manager.get_idle_duration()
    print(f"System idle for {idle_duration:.0f} seconds")
    print("Can run at full speed!")
else:
    print("System active")
```

## Resource-Aware Queue

### Start Automatic Control

```python
from resource_aware_queue import get_resource_aware_queue

# Get queue controller
queue = get_resource_aware_queue()

# Start automatic resource-aware control
queue.start()

print("Resource-aware queue control started")
```

### Check Queue Status

```python
status = queue.get_status()

print(f"Running: {status['is_running']}")
print(f"Paused: {status['is_paused']}")
print(f"Current speed: {status['current_speed']}x")
print(f"Auto-adjust: {status['auto_adjust']}")
```

### Get Recommendations

```python
# Check if should accept new jobs
if queue.should_accept_new_jobs():
    # Get recommended concurrency
    concurrency = queue.get_recommended_concurrency()
    print(f"✓ Can accept jobs (concurrency: {concurrency})")
else:
    # Get recommended delay
    delay = queue.get_processing_delay()
    print(f"⚠️  Wait {delay} seconds before submitting")
```

## API Usage

### Get System Status

```bash
curl http://localhost:5100/resources/status
```

### Start Monitoring

```bash
curl -X POST http://localhost:5100/resources/monitoring/start
```

### Get CPU Status

```bash
curl http://localhost:5100/resources/cpu
```

### Get GPU Status

```bash
curl http://localhost:5100/resources/gpu
```

### Check Idle State

```bash
curl http://localhost:5100/resources/idle
```

### Start Resource-Aware Queue

```bash
curl -X POST http://localhost:5100/resources/queue/start
```

### Get Queue Status

```bash
curl http://localhost:5100/resources/queue/status
```

### Enable Auto-Adjustment

```bash
curl -X PUT http://localhost:5100/resources/queue/auto-adjust \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

### Get Recommended Concurrency

```bash
curl http://localhost:5100/resources/queue/concurrency
```

## Configuration

### Update Thresholds

```python
manager.update_config({
    'cpu_limit_percent': 85,
    'gpu_temp_limit_celsius': 80,
    'idle_threshold_seconds': 600  # 10 minutes
})
```

### Via API

```bash
curl -X PUT http://localhost:5100/resources/config \
  -H "Content-Type: application/json" \
  -d '{
    "cpu_limit_percent": 85,
    "gpu_temp_limit_celsius": 80
  }'
```

## Integration with Job Queue

### Complete Example

```python
from resource_manager import get_resource_manager
from resource_aware_queue import get_resource_aware_queue
from job_queue_manager import get_job_queue_manager

# Initialize
resource_manager = get_resource_manager()
resource_queue = get_resource_aware_queue()
job_queue = get_job_queue_manager()

# Start monitoring and control
resource_manager.start_monitoring()
resource_queue.start()

# Submit jobs with resource awareness
photo_ids = [1, 2, 3, 4, 5]

for photo_id in photo_ids:
    # Check if should accept
    if resource_queue.should_accept_new_jobs():
        # Get recommended concurrency
        concurrency = resource_queue.get_recommended_concurrency()
        
        # Submit job
        task_id = job_queue.submit_photo_processing(photo_id)
        print(f"Submitted photo {photo_id}: {task_id}")
        
        # Get recommended delay
        delay = resource_queue.get_processing_delay()
        if delay > 0:
            import time
            time.sleep(delay)
    else:
        print(f"Skipping photo {photo_id} - system busy")
```

## Callbacks

### Register Event Handlers

```python
def on_critical(state):
    print(f"🚨 CRITICAL: {state}")
    # Send alert, pause processing, etc.

def on_throttle(state):
    print(f"⚠️  THROTTLE: {state}")
    # Reduce speed, log warning, etc.

def on_resume(state):
    print(f"✓ RESUME: {state}")
    # Resume normal speed, log info, etc.

# Register callbacks
manager.register_callback('critical', on_critical)
manager.register_callback('throttle', on_throttle)
manager.register_callback('resume', on_resume)
```

## Monitoring Dashboard

### Simple Status Display

```python
import time

def display_status():
    while True:
        status = manager.get_system_status()
        
        print("\n" + "="*50)
        print(f"State: {status['state'].upper()}")
        print(f"CPU: {status['cpu']['usage_percent']:.1f}%")
        print(f"Memory: {status['memory']['percent']:.1f}%")
        
        if status['gpu']['available']:
            print(f"GPU: {status['gpu']['temperature']:.1f}°C "
                  f"({status['gpu']['load']:.1f}%)")
        
        print(f"Idle: {status['is_idle']}")
        print(f"Speed: {status['recommended_speed']}x")
        print("="*50)
        
        time.sleep(5)

# Run dashboard
display_status()
```

## Common Scenarios

### Scenario 1: High CPU Usage

```python
# Check CPU status
cpu = manager.get_cpu_status()

if cpu['is_busy']:
    print("CPU busy, reducing load...")
    
    # Reduce concurrent jobs
    concurrency = queue.get_recommended_concurrency()
    print(f"Recommended concurrency: {concurrency}")
    
    # Or pause queue
    queue.force_pause()
```

### Scenario 2: GPU Overheating

```python
# Check GPU status
gpu = manager.get_gpu_status()

if gpu['is_overheating']:
    print(f"GPU overheating: {gpu['temperature']}°C")
    
    # Pause processing
    queue.force_pause()
    
    # Wait for cooldown
    import time
    time.sleep(60)
    
    # Resume when cooled
    if not manager.get_gpu_status()['is_overheating']:
        queue.force_resume()
```

### Scenario 3: Maximize Idle Time Processing

```python
import time

while True:
    if manager.is_system_idle():
        print("System idle - processing at full speed")
        
        # Submit batch of jobs
        job_queue.submit_batch_processing(photo_ids, priority=5)
        
        # Process until no longer idle
        while manager.is_system_idle():
            time.sleep(10)
    else:
        print("System active - waiting for idle")
        time.sleep(60)
```

## Testing

### Run Tests

```bash
# Run all tests
pytest test_resource_manager.py -v

# Run specific test
pytest test_resource_manager.py::TestResourceManager::test_get_current_metrics -v

# Run with coverage
pytest test_resource_manager.py --cov=resource_manager --cov-report=html
```

### Manual Testing

```python
# Test CPU monitoring
import psutil
print(f"CPU: {psutil.cpu_percent(interval=1)}%")

# Test GPU monitoring
try:
    import GPUtil
    gpus = GPUtil.getGPUs()
    if gpus:
        gpu = gpus[0]
        print(f"GPU: {gpu.name}")
        print(f"Temp: {gpu.temperature}°C")
        print(f"Load: {gpu.load * 100}%")
except Exception as e:
    print(f"GPU test failed: {e}")

# Test idle detection
manager = get_resource_manager()
manager.config['idle_threshold_seconds'] = 5
manager.start_monitoring()

import time
time.sleep(6)

print(f"Idle: {manager.is_system_idle()}")
```

## Troubleshooting

### Issue: GPU Not Detected

```python
# Check GPU availability
manager = get_resource_manager()
print(f"GPU available: {manager.gpu_available}")

# Try manual check
try:
    import GPUtil
    gpus = GPUtil.getGPUs()
    print(f"GPUs found: {len(gpus)}")
    for gpu in gpus:
        print(f"  - {gpu.name}")
except Exception as e:
    print(f"Error: {e}")
```

### Issue: Monitoring Not Starting

```python
# Check if already running
if manager.is_monitoring:
    print("Already monitoring")
    manager.stop_monitoring()

# Start fresh
manager.start_monitoring()
print(f"Monitoring: {manager.is_monitoring}")
```

### Issue: Incorrect Thresholds

```python
# Check current config
print(manager.config)

# Reset to defaults
manager.config = {
    'cpu_limit_percent': 80,
    'gpu_temp_limit_celsius': 75,
    'idle_threshold_seconds': 300
}
```

## Next Steps

1. Read [Resource Management Documentation](RESOURCE_MANAGEMENT.md)
2. Integrate with [Job Queue System](JOB_QUEUE_IMPLEMENTATION.md)
3. Configure [Priority Management](PRIORITY_MANAGEMENT.md)
4. Set up [Celery Workers](CELERY_QUICK_START.md)

## Support

For issues or questions:
1. Check logs in `logs/main.log`
2. Review [Resource Management Documentation](RESOURCE_MANAGEMENT.md)
3. Run diagnostic tests: `pytest test_resource_manager.py -v`
