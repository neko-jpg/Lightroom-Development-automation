# Performance Metrics Quick Start Guide

## Installation

No additional dependencies required beyond the base system.

Optional for GPU tracking:
```bash
pip install gputil
```

## Quick Start

### 1. Basic Timing

```python
from performance_metrics import measure_performance

# Measure any operation
with measure_performance("my_operation"):
    # Your code here
    process_data()
```

### 2. Track Memory and GPU

```python
from performance_metrics import record_memory_usage, record_gpu_usage

# Record current memory usage
record_memory_usage("batch_processing")

# Record current GPU usage
record_gpu_usage("ai_inference")
```

### 3. Get Statistics

```python
from performance_metrics import get_performance_metrics_collector

collector = get_performance_metrics_collector()

# Get processing stats
stats = collector.get_processing_time_stats()
print(f"Average: {stats['avg_duration_ms']:.2f}ms")
print(f"Success rate: {stats['success_rate']:.1f}%")

# Get operation summary
summary = collector.get_operation_summary()
for op in summary:
    print(f"{op['operation']}: {op['avg_duration_ms']:.2f}ms")
```

### 4. Export Metrics

```python
# Export to JSON
json_path = collector.export_to_json()

# Export to CSV
csv_path = collector.export_to_csv('processing')
```

## Common Patterns

### Pattern 1: Multi-Stage Processing

```python
photo_id = 123
job_id = "job_001"

with measure_performance("exif_analysis", photo_id=photo_id, job_id=job_id, stage="exif"):
    analyze_exif()

with measure_performance("ai_evaluation", photo_id=photo_id, job_id=job_id, stage="ai"):
    evaluate_with_ai()

with measure_performance("preset_selection", photo_id=photo_id, job_id=job_id, stage="preset"):
    select_preset()
```

### Pattern 2: Background Monitoring

```python
# At application startup
collector = get_performance_metrics_collector()
collector.start_monitoring()

# At application shutdown
collector.stop_monitoring()
```

### Pattern 3: Error Tracking

```python
try:
    with measure_performance("risky_operation"):
        do_risky_work()
except Exception as e:
    # Error is automatically recorded
    pass
```

### Pattern 4: Time Window Analysis

```python
# Last 5 minutes
recent = collector.get_processing_time_stats(duration_minutes=5)

# Last hour
hourly = collector.get_processing_time_stats(duration_minutes=60)

# All time
all_time = collector.get_processing_time_stats()
```

## API Usage

### Start Monitoring
```bash
curl -X POST http://localhost:5100/api/metrics/monitoring/start
```

### Get Processing Stats
```bash
curl "http://localhost:5100/api/metrics/processing/stats?duration_minutes=60"
```

### Get Operation Summary
```bash
curl http://localhost:5100/api/metrics/operations/summary
```

### Export to JSON
```bash
curl -X POST http://localhost:5100/api/metrics/export/json
```

### Export to CSV
```bash
curl -X POST http://localhost:5100/api/metrics/export/csv \
  -H "Content-Type: application/json" \
  -d '{"metric_type": "processing"}'
```

## Configuration

```python
collector.update_config({
    'max_history_size': 10000,
    'memory_sample_interval': 60,
    'export_directory': 'data/metrics'
})
```

## Tips

1. **Use context managers** for automatic timing
2. **Include metadata** (photo_id, job_id) for better tracking
3. **Start background monitoring** at application startup
4. **Export regularly** to avoid memory buildup
5. **Filter by time windows** for recent analysis

## Examples

Run the example script:
```bash
py example_performance_metrics_usage.py
```

Run tests:
```bash
py test_performance_metrics.py
```

## Next Steps

- Read [PERFORMANCE_METRICS_IMPLEMENTATION.md](PERFORMANCE_METRICS_IMPLEMENTATION.md) for detailed documentation
- Integrate with your existing code
- Set up regular exports
- Monitor performance trends
