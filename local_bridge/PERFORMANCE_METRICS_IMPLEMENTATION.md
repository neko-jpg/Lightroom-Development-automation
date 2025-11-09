# Performance Metrics Collection Implementation

## Overview

The Performance Metrics Collection system provides comprehensive tracking of processing times, memory usage, and GPU usage for the Junmai AutoDev system. This enables performance monitoring, optimization, and reporting.

**Requirements**: 12.1, 12.2, 15.4

## Features

### Core Capabilities

1. **Processing Time Measurement** (Requirement 12.1)
   - Context manager for automatic timing
   - Manual recording support
   - Multi-stage operation tracking
   - Success/failure tracking
   - Error message capture

2. **Memory Usage Tracking** (Requirement 12.2)
   - System memory monitoring
   - Process memory tracking
   - Background sampling
   - Historical tracking

3. **GPU Usage Tracking** (Requirement 12.2)
   - GPU load monitoring
   - GPU memory tracking
   - Temperature monitoring
   - Multi-GPU support

4. **Metrics Export** (Requirement 15.4)
   - JSON export with full data
   - CSV export by metric type
   - Automatic file naming
   - Summary statistics included

## Architecture

### Components

```
PerformanceMetricsCollector
├── Processing Time Metrics
│   ├── Operation tracking
│   ├── Duration measurement
│   └── Success/failure tracking
├── Memory Usage Metrics
│   ├── System memory
│   └── Process memory
├── GPU Usage Metrics
│   ├── Load tracking
│   ├── Memory tracking
│   └── Temperature monitoring
└── Export Functions
    ├── JSON export
    └── CSV export
```

### Data Models

#### ProcessingTimeMetric
```python
@dataclass
class ProcessingTimeMetric:
    timestamp: datetime
    operation: str
    duration_ms: float
    photo_id: Optional[int]
    job_id: Optional[str]
    stage: Optional[str]
    success: bool
    error_message: Optional[str]
```

#### MemoryUsageMetric
```python
@dataclass
class MemoryUsageMetric:
    timestamp: datetime
    total_mb: float
    used_mb: float
    available_mb: float
    percent: float
    process_memory_mb: float
    operation: Optional[str]
```

#### GPUUsageMetric
```python
@dataclass
class GPUUsageMetric:
    timestamp: datetime
    gpu_id: int
    load_percent: float
    memory_used_mb: float
    memory_total_mb: float
    memory_percent: float
    temperature_celsius: float
    operation: Optional[str]
```

## Usage

### Basic Processing Time Measurement

```python
from performance_metrics import measure_performance

# Using context manager (automatic recording)
with measure_performance("image_processing", photo_id=123):
    # Your processing code here
    process_image()

# Manual recording
from performance_metrics import record_processing_time
import time

start = time.time()
process_image()
duration_ms = (time.time() - start) * 1000
record_processing_time("image_processing", duration_ms, photo_id=123)
```

### Multi-Stage Operations

```python
photo_id = 789
job_id = "job_001"

# Stage 1: EXIF Analysis
with measure_performance("exif_analysis", photo_id=photo_id, job_id=job_id, stage="exif"):
    analyze_exif()

# Stage 2: AI Evaluation
with measure_performance("ai_evaluation", photo_id=photo_id, job_id=job_id, stage="ai"):
    evaluate_with_ai()

# Stage 3: Preset Selection
with measure_performance("preset_selection", photo_id=photo_id, job_id=job_id, stage="preset"):
    select_preset()
```

### Memory and GPU Tracking

```python
from performance_metrics import record_memory_usage, record_gpu_usage

# Record memory usage
record_memory_usage("processing_batch")

# Record GPU usage
record_gpu_usage("ai_inference")
```

### Background Monitoring

```python
from performance_metrics import get_performance_metrics_collector

collector = get_performance_metrics_collector()

# Start background monitoring
collector.start_monitoring()

# Do your work...

# Stop monitoring
collector.stop_monitoring()
```

### Getting Statistics

```python
collector = get_performance_metrics_collector()

# Processing time stats
stats = collector.get_processing_time_stats(
    operation="image_processing",  # Optional: filter by operation
    duration_minutes=60            # Optional: last 60 minutes
)

print(f"Average duration: {stats['avg_duration_ms']:.2f}ms")
print(f"Success rate: {stats['success_rate']:.1f}%")

# Memory usage stats
memory_stats = collector.get_memory_usage_stats(duration_minutes=30)
print(f"Average memory: {memory_stats['avg_used_mb']:.0f}MB")

# GPU usage stats
gpu_stats = collector.get_gpu_usage_stats(gpu_id=0, duration_minutes=30)
print(f"Average GPU load: {gpu_stats['avg_load_percent']:.1f}%")

# Operation summary
summary = collector.get_operation_summary()
for op in summary:
    print(f"{op['operation']}: {op['avg_duration_ms']:.2f}ms avg")
```

### Exporting Metrics

```python
collector = get_performance_metrics_collector()

# Export to JSON (includes all metrics and summary)
json_path = collector.export_to_json()
print(f"Exported to: {json_path}")

# Export to CSV (by metric type)
csv_path = collector.export_to_csv('processing')
print(f"Exported to: {csv_path}")
```

## API Endpoints

### GET /api/metrics/processing/stats
Get processing time statistics.

**Query Parameters:**
- `operation` (optional): Filter by operation name
- `duration_minutes` (optional): Time window in minutes

**Response:**
```json
{
  "success": true,
  "stats": {
    "count": 100,
    "avg_duration_ms": 245.5,
    "min_duration_ms": 100.0,
    "max_duration_ms": 500.0,
    "success_rate": 95.0,
    "failure_count": 5
  }
}
```

### GET /api/metrics/memory/stats
Get memory usage statistics.

**Query Parameters:**
- `duration_minutes` (optional): Time window in minutes

**Response:**
```json
{
  "success": true,
  "stats": {
    "count": 50,
    "current_used_mb": 8192.0,
    "avg_used_mb": 7500.0,
    "max_used_mb": 9000.0,
    "current_percent": 50.0
  }
}
```

### GET /api/metrics/gpu/stats
Get GPU usage statistics.

**Query Parameters:**
- `gpu_id` (optional): GPU identifier
- `duration_minutes` (optional): Time window in minutes

**Response:**
```json
{
  "success": true,
  "stats": {
    "count": 50,
    "current_load_percent": 75.0,
    "avg_load_percent": 65.0,
    "current_temperature": 68.0,
    "avg_temperature": 65.0
  }
}
```

### GET /api/metrics/operations/summary
Get summary of all operations.

**Query Parameters:**
- `duration_minutes` (optional): Time window in minutes

**Response:**
```json
{
  "success": true,
  "operations": [
    {
      "operation": "ai_evaluation",
      "count": 50,
      "avg_duration_ms": 800.0,
      "total_duration_ms": 40000.0,
      "success_rate": 98.0
    }
  ]
}
```

### POST /api/metrics/export/json
Export all metrics to JSON file.

**Response:**
```json
{
  "success": true,
  "filepath": "data/metrics/metrics_20250108_120000.json",
  "message": "Metrics exported successfully"
}
```

### POST /api/metrics/export/csv
Export specific metric type to CSV file.

**Request Body:**
```json
{
  "metric_type": "processing"
}
```

**Response:**
```json
{
  "success": true,
  "filepath": "data/metrics/processing_metrics_20250108_120000.csv",
  "metric_type": "processing",
  "message": "Metrics exported successfully"
}
```

### POST /api/metrics/monitoring/start
Start background metrics monitoring.

### POST /api/metrics/monitoring/stop
Stop background metrics monitoring.

### POST /api/metrics/clear
Clear metrics history.

**Request Body:**
```json
{
  "metric_type": "processing"  // or "memory", "gpu", or null for all
}
```

## Configuration

```python
collector = get_performance_metrics_collector()

collector.update_config({
    'max_history_size': 10000,           # Maximum metrics to keep
    'auto_export_interval': 3600,        # Auto-export interval (seconds)
    'export_directory': 'data/metrics',  # Export directory
    'enable_gpu_tracking': True,         # Enable GPU tracking
    'enable_memory_tracking': True,      # Enable memory tracking
    'memory_sample_interval': 60         # Memory sampling interval (seconds)
})
```

## Performance Considerations

### Memory Usage
- Default max history: 10,000 metrics
- Automatic trimming when limit reached
- Typical memory per metric: ~200 bytes
- Total memory for full history: ~2MB

### CPU Overhead
- Processing time recording: <0.1ms
- Memory sampling: ~1ms
- GPU sampling: ~2ms
- Background monitoring: Minimal (runs in separate thread)

### Storage
- JSON export: ~1MB per 10,000 metrics
- CSV export: ~500KB per 10,000 metrics
- Automatic file naming with timestamps

## Best Practices

### 1. Use Context Managers
```python
# Good: Automatic timing and recording
with measure_performance("operation"):
    do_work()

# Avoid: Manual timing (error-prone)
start = time.time()
do_work()
record_processing_time("operation", (time.time() - start) * 1000)
```

### 2. Include Metadata
```python
# Good: Include relevant metadata
with measure_performance("process_photo", photo_id=123, job_id="job_001"):
    process_photo()

# Avoid: Missing context
with measure_performance("process_photo"):
    process_photo()
```

### 3. Use Background Monitoring
```python
# Start monitoring at application startup
collector = get_performance_metrics_collector()
collector.start_monitoring()

# Stop at shutdown
collector.stop_monitoring()
```

### 4. Regular Exports
```python
# Export metrics periodically (e.g., daily)
import schedule

def export_daily_metrics():
    collector = get_performance_metrics_collector()
    collector.export_to_json()
    collector.clear_metrics('processing')  # Clear old data

schedule.every().day.at("00:00").do(export_daily_metrics)
```

### 5. Filter by Time Windows
```python
# Get recent stats for monitoring
recent_stats = collector.get_processing_time_stats(duration_minutes=5)

# Get longer-term stats for analysis
daily_stats = collector.get_processing_time_stats(duration_minutes=1440)
```

## Integration with Existing Systems

### With Resource Manager
```python
from resource_manager import get_resource_manager
from performance_metrics import measure_performance

resource_mgr = get_resource_manager()

with measure_performance("batch_processing"):
    if not resource_mgr.should_throttle_processing():
        process_batch()
```

### With GPU Manager
```python
from gpu_manager import get_gpu_manager
from performance_metrics import measure_performance, record_gpu_usage

gpu_mgr = get_gpu_manager()

with measure_performance("ai_inference"):
    if gpu_mgr.is_available():
        run_inference()
        record_gpu_usage("ai_inference")
```

### With Job Queue
```python
from performance_metrics import measure_performance

def process_job(job):
    with measure_performance(
        "job_processing",
        job_id=job.id,
        photo_id=job.photo_id
    ):
        # Process job
        execute_job(job)
```

## Troubleshooting

### High Memory Usage
```python
# Reduce history size
collector.update_config({'max_history_size': 5000})

# Clear old metrics
collector.clear_metrics()
```

### Missing GPU Metrics
```python
# Check GPU availability
collector = get_performance_metrics_collector()
if not collector.gpu_available:
    print("GPU monitoring not available")
    # Install GPUtil: pip install gputil
```

### Export Failures
```python
# Check export directory
import os
export_dir = collector.config['export_directory']
if not os.path.exists(export_dir):
    os.makedirs(export_dir, exist_ok=True)
```

## Testing

Run the test suite:
```bash
py test_performance_metrics.py
```

Run example usage:
```bash
py example_performance_metrics_usage.py
```

## Requirements Mapping

- **Requirement 12.1**: Processing time measurement
  - `PerformanceTimer` context manager
  - `record_processing_time()` function
  - Processing time statistics

- **Requirement 12.2**: Memory and GPU usage tracking
  - `record_memory_usage()` function
  - `record_gpu_usage()` function
  - Background monitoring
  - Usage statistics

- **Requirement 15.4**: Metrics export
  - JSON export with full data
  - CSV export by type
  - Operation summaries
  - Statistical analysis

## Future Enhancements

1. **Real-time Dashboards**
   - WebSocket streaming of metrics
   - Live charts and graphs
   - Alert thresholds

2. **Advanced Analytics**
   - Trend analysis
   - Anomaly detection
   - Performance regression detection

3. **Distributed Metrics**
   - Multi-instance aggregation
   - Centralized metrics collection
   - Cross-system correlation

4. **Custom Metrics**
   - User-defined metric types
   - Custom aggregation functions
   - Flexible export formats
