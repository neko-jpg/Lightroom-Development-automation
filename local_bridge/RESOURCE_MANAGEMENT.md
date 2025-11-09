# Resource Management System

## Overview

The Resource Management System provides comprehensive monitoring and dynamic adjustment of system resources (CPU, GPU, memory) to optimize photo processing performance while preventing system overload.

**Requirements**: 4.3, 12.4, 17.3

## Features

### 1. CPU Usage Monitoring
- Real-time CPU usage tracking (overall and per-core)
- Configurable usage thresholds
- Automatic detection of high CPU load
- CPU frequency monitoring

### 2. GPU Temperature Monitoring
- Real-time GPU temperature tracking
- Configurable temperature limits (normal: 75°C, critical: 85°C)
- GPU memory usage monitoring
- GPU load percentage tracking
- Automatic throttling on overheating

### 3. System Idle Detection
- Automatic detection of system idle time
- Configurable idle threshold (default: 5 minutes)
- CPU-based idle detection (< 15% usage)
- Idle duration tracking

### 4. Dynamic Processing Speed Adjustment
- Automatic speed adjustment based on resource state
- Four resource states:
  - **IDLE**: Full speed (1.0x)
  - **NORMAL**: 80% speed (0.8x)
  - **BUSY**: 50% speed (0.5x)
  - **CRITICAL**: Paused (0.0x)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Resource Manager                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ CPU Monitor  │  │ GPU Monitor  │  │ Idle Detector│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Resource State Determination              │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Resource-Aware Queue                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │      Automatic Speed Adjustment                   │  │
│  │  • Pause on critical                              │  │
│  │  • Throttle on busy                               │  │
│  │  • Full speed on idle                             │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Job Queue Manager                       │
│              (Celery + Redis)                            │
└─────────────────────────────────────────────────────────┘
```

## Configuration

### Default Configuration

```python
{
    # CPU thresholds
    'cpu_limit_percent': 80,
    'cpu_critical_percent': 95,
    'cpu_idle_percent': 20,
    
    # GPU thresholds
    'gpu_temp_limit_celsius': 75,
    'gpu_temp_critical_celsius': 85,
    'gpu_memory_limit_percent': 90,
    
    # Memory thresholds
    'memory_limit_percent': 85,
    'memory_critical_percent': 95,
    
    # Idle detection
    'idle_threshold_seconds': 300,  # 5 minutes
    'idle_cpu_threshold': 15,
    'idle_check_interval': 60,  # Check every minute
    
    # Monitoring
    'monitor_interval': 5,  # Monitor every 5 seconds
    'history_size': 100,  # Keep last 100 measurements
}
```

### Updating Configuration

```python
from resource_manager import get_resource_manager

manager = get_resource_manager()
manager.update_config({
    'cpu_limit_percent': 85,
    'gpu_temp_limit_celsius': 80
})
```

## API Endpoints

### Get System Status
```http
GET /resources/status
```

Returns comprehensive system resource status including CPU, GPU, memory, and idle state.

**Response:**
```json
{
    "success": true,
    "status": {
        "timestamp": "2025-11-08T14:30:00",
        "state": "normal",
        "cpu": {
            "usage_percent": 45.5,
            "per_core_percent": [42.0, 48.0, 44.0, 47.0],
            "core_count": 4,
            "frequency_mhz": 3600.0,
            "is_busy": false,
            "is_critical": false
        },
        "memory": {
            "total_mb": 16384,
            "available_mb": 8192,
            "used_mb": 8192,
            "percent": 50.0,
            "is_busy": false,
            "is_critical": false
        },
        "gpu": {
            "available": true,
            "name": "NVIDIA RTX 4060",
            "load": 35.0,
            "memory_used_mb": 2048,
            "memory_total_mb": 8192,
            "memory_percent": 25.0,
            "temperature": 65.0,
            "is_overheating": false,
            "is_critical": false
        },
        "disk_usage_percent": 70.0,
        "is_idle": false,
        "idle_duration_seconds": 0.0,
        "should_throttle": false,
        "recommended_speed": 0.8
    }
}
```

### Get CPU Status
```http
GET /resources/cpu
```

Returns detailed CPU status.

### Get GPU Status
```http
GET /resources/gpu
```

Returns detailed GPU status including temperature and memory.

### Get Idle Status
```http
GET /resources/idle
```

Returns system idle state and duration.

### Start Resource Monitoring
```http
POST /resources/monitoring/start
```

Starts continuous resource monitoring in background thread.

### Stop Resource Monitoring
```http
POST /resources/monitoring/stop
```

Stops resource monitoring.

### Update Configuration
```http
PUT /resources/config
Content-Type: application/json

{
    "cpu_limit_percent": 85,
    "gpu_temp_limit_celsius": 80
}
```

Updates resource manager configuration.

## Resource-Aware Queue

### Start Resource-Aware Queue
```http
POST /resources/queue/start
```

Starts automatic resource-aware queue control.

### Get Queue Status
```http
GET /resources/queue/status
```

Returns resource-aware queue status.

**Response:**
```json
{
    "success": true,
    "status": {
        "is_running": true,
        "is_paused": false,
        "current_speed": 0.8,
        "auto_adjust": true,
        "system": { /* system status */ },
        "queue": { /* queue stats */ }
    }
}
```

### Enable/Disable Auto-Adjustment
```http
PUT /resources/queue/auto-adjust
Content-Type: application/json

{
    "enabled": true
}
```

### Get Recommended Concurrency
```http
GET /resources/queue/concurrency
```

Returns recommended number of concurrent jobs based on current resources.

## Usage Examples

### Python Usage

```python
from resource_manager import get_resource_manager
from resource_aware_queue import get_resource_aware_queue

# Initialize
resource_manager = get_resource_manager()
resource_aware_queue = get_resource_aware_queue()

# Start monitoring
resource_manager.start_monitoring()

# Start resource-aware queue control
resource_aware_queue.start()

# Check system status
status = resource_manager.get_system_status()
print(f"CPU: {status['cpu']['usage_percent']}%")
print(f"GPU Temp: {status['gpu']['temperature']}°C")
print(f"State: {status['state']}")

# Check if should throttle
if resource_manager.should_throttle_processing():
    print("System busy, throttling recommended")

# Get recommended speed
speed = resource_manager.get_recommended_speed_multiplier()
print(f"Recommended speed: {speed}x")

# Check if system is idle
if resource_manager.is_system_idle():
    print("System idle, can run at full speed")
```

### Register Callbacks

```python
def on_critical_state(state):
    print(f"CRITICAL: System resources critical!")
    # Pause processing, send alert, etc.

def on_throttle(state):
    print(f"WARNING: System busy, throttling")

def on_resume(state):
    print(f"INFO: System recovered, resuming")

# Register callbacks
resource_manager.register_callback('critical', on_critical_state)
resource_manager.register_callback('throttle', on_throttle)
resource_manager.register_callback('resume', on_resume)
```

### Integration with Job Queue

```python
from job_queue_manager import get_job_queue_manager
from resource_aware_queue import get_resource_aware_queue

job_queue = get_job_queue_manager()
resource_queue = get_resource_aware_queue()

# Start resource-aware control
resource_queue.start()

# Check if should accept new jobs
if resource_queue.should_accept_new_jobs():
    # Get recommended concurrency
    concurrency = resource_queue.get_recommended_concurrency()
    print(f"Can accept jobs, recommended concurrency: {concurrency}")
    
    # Submit jobs
    job_queue.submit_photo_processing(photo_id=123)
else:
    print("System busy, not accepting new jobs")
    
    # Get recommended delay
    delay = resource_queue.get_processing_delay()
    print(f"Retry after {delay} seconds")
```

## Resource States

### IDLE
- CPU usage < 20%
- System has been idle for > 5 minutes
- **Action**: Run at full speed (1.0x)

### NORMAL
- CPU usage 20-80%
- Memory usage < 85%
- GPU temperature < 75°C
- **Action**: Run at 80% speed (0.8x)

### BUSY
- CPU usage 80-95%
- Memory usage 85-95%
- GPU temperature 75-85°C
- **Action**: Throttle to 50% speed (0.5x)

### CRITICAL
- CPU usage > 95%
- Memory usage > 95%
- GPU temperature > 85°C
- **Action**: Pause processing (0.0x)

## Performance Metrics

### Metrics Tracked
- CPU usage (overall and per-core)
- Memory usage and availability
- GPU load, memory, and temperature
- Disk usage
- Resource state history
- Idle time duration

### Historical Data
```python
# Get last 50 measurements
history = resource_manager.get_metrics_history(limit=50)

# Get average over last 10 minutes
averages = resource_manager.get_average_metrics(duration_minutes=10)
print(f"Avg CPU: {averages['avg_cpu_percent']}%")
print(f"Avg GPU Temp: {averages['avg_gpu_temperature']}°C")
```

## Best Practices

1. **Start monitoring early**: Start resource monitoring when the application starts
2. **Use resource-aware queue**: Enable automatic queue adjustment for optimal performance
3. **Monitor GPU temperature**: Especially important for RTX 4060 with 8GB VRAM
4. **Configure thresholds**: Adjust thresholds based on your hardware and workload
5. **Use callbacks**: Register callbacks for critical events to take immediate action
6. **Check idle state**: Maximize processing speed during idle periods
7. **Respect throttling**: When throttling is recommended, reduce concurrent jobs

## Troubleshooting

### GPU Not Detected
- Install GPUtil: `pip install gputil`
- Check GPU drivers are installed
- Verify GPU is accessible: `nvidia-smi`

### High CPU Usage
- Reduce concurrent jobs
- Increase `cpu_limit_percent` threshold
- Check for other running applications

### GPU Overheating
- Lower `gpu_temp_limit_celsius` threshold
- Improve system cooling
- Reduce GPU-intensive operations
- Enable model quantization

### System Not Detecting Idle
- Check `idle_cpu_threshold` setting
- Verify `idle_threshold_seconds` is appropriate
- Check for background processes

## Requirements Mapping

- **Requirement 4.3**: CPU usage monitoring, idle detection, dynamic adjustment
- **Requirement 12.4**: Performance optimization, resource management
- **Requirement 17.3**: GPU temperature monitoring, GPU resource management

## See Also

- [Job Queue Implementation](JOB_QUEUE_IMPLEMENTATION.md)
- [Priority Management](PRIORITY_MANAGEMENT.md)
- [Celery Queue Quick Start](CELERY_QUICK_START.md)
