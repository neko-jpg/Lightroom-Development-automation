# Performance Metrics Quick Reference

## Import

```python
from performance_metrics import (
    measure_performance,
    record_processing_time,
    record_memory_usage,
    record_gpu_usage,
    get_performance_metrics_collector
)
```

## Basic Usage

### Measure Processing Time
```python
# Automatic timing with context manager
with measure_performance("operation_name"):
    do_work()

# With metadata
with measure_performance("operation", photo_id=123, job_id="job_001"):
    do_work()

# Manual recording
record_processing_time("operation", duration_ms=100.5, photo_id=123)
```

### Track Memory
```python
record_memory_usage("operation_name")
```

### Track GPU
```python
record_gpu_usage("operation_name")
```

## Statistics

```python
collector = get_performance_metrics_collector()

# Processing stats
stats = collector.get_processing_time_stats()
# Returns: count, avg_duration_ms, min, max, median, success_rate

# Memory stats
mem_stats = collector.get_memory_usage_stats()
# Returns: current_used_mb, avg_used_mb, max_used_mb, percent

# GPU stats
gpu_stats = collector.get_gpu_usage_stats()
# Returns: current_load_percent, avg_load_percent, temperature

# Operation summary
summary = collector.get_operation_summary()
# Returns: list of {operation, count, avg_duration_ms, success_rate}
```

## Time Windows

```python
# Last 5 minutes
recent = collector.get_processing_time_stats(duration_minutes=5)

# Last hour
hourly = collector.get_processing_time_stats(duration_minutes=60)

# Specific operation
op_stats = collector.get_processing_time_stats(operation="ai_evaluation")
```

## Export

```python
# Export to JSON (all metrics + summary)
json_path = collector.export_to_json()

# Export to CSV (specific type)
csv_path = collector.export_to_csv('processing')  # or 'memory', 'gpu'
```

## Background Monitoring

```python
# Start monitoring (at app startup)
collector.start_monitoring()

# Stop monitoring (at app shutdown)
collector.stop_monitoring()
```

## Configuration

```python
collector.update_config({
    'max_history_size': 10000,
    'memory_sample_interval': 60,
    'export_directory': 'data/metrics'
})
```

## API Endpoints

### Statistics
```bash
# Processing stats
GET /api/metrics/processing/stats?operation=ai_eval&duration_minutes=60

# Memory stats
GET /api/metrics/memory/stats?duration_minutes=30

# GPU stats
GET /api/metrics/gpu/stats?gpu_id=0&duration_minutes=30

# Operations summary
GET /api/metrics/operations/summary
```

### Export
```bash
# Export to JSON
POST /api/metrics/export/json

# Export to CSV
POST /api/metrics/export/csv
Content-Type: application/json
{"metric_type": "processing"}

# Download export
GET /api/metrics/export/download/<filename>
```

### Management
```bash
# Start monitoring
POST /api/metrics/monitoring/start

# Stop monitoring
POST /api/metrics/monitoring/stop

# Clear metrics
POST /api/metrics/clear
Content-Type: application/json
{"metric_type": "processing"}  # or null for all

# Get counts
GET /api/metrics/count

# Get/update config
GET /api/metrics/config
PUT /api/metrics/config
Content-Type: application/json
{"max_history_size": 5000}
```

## Common Patterns

### Pattern 1: Multi-Stage Operation
```python
photo_id = 123
job_id = "job_001"

with measure_performance("exif", photo_id=photo_id, job_id=job_id, stage="exif"):
    analyze_exif()

with measure_performance("ai", photo_id=photo_id, job_id=job_id, stage="ai"):
    evaluate_with_ai()
```

### Pattern 2: Error Tracking
```python
try:
    with measure_performance("risky_operation"):
        do_risky_work()
except Exception as e:
    # Error automatically recorded
    handle_error(e)
```

### Pattern 3: Conditional Tracking
```python
if should_track_performance:
    with measure_performance("operation"):
        do_work()
else:
    do_work()
```

### Pattern 4: Batch Processing
```python
for item in batch:
    with measure_performance("process_item", photo_id=item.id):
        process_item(item)

# Get batch stats
stats = collector.get_processing_time_stats(operation="process_item")
print(f"Processed {stats['count']} items in {stats['total_duration_ms']:.0f}ms")
```

## Data Classes

### ProcessingTimeMetric
```python
timestamp: datetime
operation: str
duration_ms: float
photo_id: Optional[int]
job_id: Optional[str]
stage: Optional[str]
success: bool
error_message: Optional[str]
```

### MemoryUsageMetric
```python
timestamp: datetime
total_mb: float
used_mb: float
available_mb: float
percent: float
process_memory_mb: float
operation: Optional[str]
```

### GPUUsageMetric
```python
timestamp: datetime
gpu_id: int
load_percent: float
memory_used_mb: float
memory_total_mb: float
memory_percent: float
temperature_celsius: float
operation: Optional[str]
```

## Tips

1. **Always use context managers** for automatic timing
2. **Include metadata** (photo_id, job_id) for better tracking
3. **Start monitoring at startup** for continuous tracking
4. **Export regularly** to avoid memory buildup
5. **Use time windows** for recent analysis
6. **Filter by operation** for specific insights
7. **Check success rates** to identify problematic operations
8. **Monitor GPU temperature** to prevent overheating

## Examples

Run examples:
```bash
py example_performance_metrics_usage.py
```

Run tests:
```bash
py test_performance_metrics.py
```

## Documentation

- [PERFORMANCE_METRICS_IMPLEMENTATION.md](PERFORMANCE_METRICS_IMPLEMENTATION.md) - Full documentation
- [PERFORMANCE_METRICS_QUICK_START.md](PERFORMANCE_METRICS_QUICK_START.md) - Getting started guide
- [TASK_42_COMPLETION_SUMMARY.md](TASK_42_COMPLETION_SUMMARY.md) - Implementation summary
