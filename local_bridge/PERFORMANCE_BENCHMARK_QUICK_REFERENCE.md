# Performance Benchmark Tests - Quick Reference

## Overview

Comprehensive performance testing suite for Junmai AutoDev system covering:
- **1000 photos processing benchmark** (Requirement 12.1)
- **Memory leak detection** (Requirement 12.3)
- **GPU usage monitoring** (Requirement 12.2)
- **Sustained load stress testing**

## Requirements Coverage

| Requirement | Description | Test Coverage |
|-------------|-------------|---------------|
| 12.1 | Process 1 photo in average 5 seconds | ✅ Single photo, batch, and 1000 photo tests |
| 12.2 | Hold max 20 jobs in queue | ✅ Concurrent job queue capacity test |
| 12.3 | Memory usage under 1GB | ✅ Memory leak detection and monitoring |

## Performance Thresholds

```python
THRESHOLDS = {
    'avg_processing_time_ms': 5000,  # 5 seconds per photo
    'max_concurrent_jobs': 20,        # Max 20 jobs in queue
    'max_memory_mb': 1024,            # Max 1GB memory usage
    'throughput_photos_per_minute': 12,  # At least 12 photos/min
}
```

## Running Tests

### Run All Benchmark Tests
```bash
cd local_bridge
py test_performance_benchmark.py
```

### Run Specific Test
```bash
# Single photo processing
py test_performance_benchmark.py PerformanceBenchmarkTests.test_01_single_photo_processing_time

# 1000 photos benchmark
py test_performance_benchmark.py PerformanceBenchmarkTests.test_03_large_batch_1000_photos_benchmark

# Memory leak detection
py test_performance_benchmark.py PerformanceBenchmarkTests.test_04_memory_leak_detection

# GPU usage monitoring
py test_performance_benchmark.py PerformanceBenchmarkTests.test_05_gpu_usage_monitoring
```

## Test Descriptions

### Test 01: Single Photo Processing Time
**Purpose**: Verify single photo processing meets 5-second requirement  
**Duration**: ~5 seconds  
**Validates**: Basic processing performance

### Test 02: Batch 100 Photos Processing
**Purpose**: Test batch processing efficiency  
**Duration**: ~5-8 minutes  
**Validates**: Sustained performance over medium batch

### Test 03: Large Batch 1000 Photos Benchmark ⭐
**Purpose**: **MAIN BENCHMARK** - Full system performance test  
**Duration**: ~50-80 minutes  
**Validates**:
- Average processing time per photo
- Memory usage stays under 1GB
- Throughput meets minimum 12 photos/min
- System stability over large batch

**Expected Output**:
```
BENCHMARK RESULTS - 1000 Photos
======================================================================

Processing Statistics:
  Total photos: 1000
  Total time: 4166.67s (69.44 minutes)
  Average time per photo: 4166.67ms (4.17s)
  Min time: 2000.00ms
  Max time: 6000.00ms
  Median time: 4000.00ms
  Throughput: 0.24 photos/sec
  Throughput: 14.40 photos/min
  Success rate: 100.00%

Memory Statistics:
  Initial memory: 150.00MB
  Final memory: 850.00MB
  Memory increase: 700.00MB
  Peak memory: 900.00MB
  Average memory: 500.00MB

Threshold Compliance:
  Avg processing time: 4166.67ms / 5000ms (PASS)
  Peak memory: 900.00MB / 1024MB (PASS)
  Throughput: 14.40 / 12 photos/min (PASS)
```

### Test 04: Memory Leak Detection
**Purpose**: Detect memory leaks over repeated processing  
**Duration**: ~5-10 minutes  
**Validates**:
- Memory growth rate < 0.5MB per iteration
- Final memory < 1GB
- No unbounded memory growth

**Methodology**:
- Processes 50 iterations of 10 photos each (500 total)
- Forces garbage collection between iterations
- Uses `tracemalloc` for detailed memory profiling
- Calculates linear regression to detect leak trend

### Test 05: GPU Usage Monitoring
**Purpose**: Monitor GPU usage and temperature  
**Duration**: ~3-5 minutes  
**Validates**:
- GPU temperature stays below 85°C
- GPU memory usage tracking
- GPU load monitoring

**Note**: Requires GPU and GPUtil library. Skips if not available.

### Test 06: Concurrent Job Queue Capacity
**Purpose**: Verify queue never exceeds 20 jobs  
**Duration**: ~2-3 minutes  
**Validates**:
- Queue management
- Concurrent job handling
- Capacity limits

### Test 07: Sustained Load Stress Test
**Purpose**: Test system stability under sustained load  
**Duration**: 2 minutes  
**Validates**:
- Performance doesn't degrade > 20%
- Memory remains stable
- Success rate stays > 95%

## Interpreting Results

### ✅ PASS Criteria
- All processing times ≤ 5000ms average
- Memory usage ≤ 1024MB peak
- Throughput ≥ 12 photos/min
- No memory leaks detected
- GPU temperature < 85°C
- Success rate ≥ 95%

### ❌ FAIL Indicators
- Processing time exceeds 5 seconds average
- Memory usage exceeds 1GB
- Throughput below 12 photos/min
- Memory leak detected (growth > 0.5MB/iteration)
- GPU overheating (> 85°C)
- Success rate drops below 95%

## Metrics Export

After tests complete, metrics are automatically exported to:
```
data/metrics/metrics_YYYYMMDD_HHMMSS.json
```

Contains:
- All processing time measurements
- Memory usage samples
- GPU usage data (if available)
- Statistical summaries
- Operation breakdowns

## Performance Optimization Tips

### If Processing Time Exceeds Threshold:
1. Check CPU/GPU utilization
2. Review AI model complexity
3. Optimize EXIF parsing
4. Consider parallel processing

### If Memory Usage Exceeds Threshold:
1. Check for memory leaks in loops
2. Ensure proper garbage collection
3. Review cache sizes
4. Optimize data structures

### If Throughput Below Target:
1. Increase concurrent workers
2. Optimize I/O operations
3. Review resource throttling
4. Check disk performance

## Troubleshooting

### Test Hangs or Times Out
- Check system resources (CPU, memory, disk)
- Verify no other heavy processes running
- Increase timeout values if needed

### GPU Tests Fail
- Ensure GPU drivers installed
- Install GPUtil: `pip install gputil`
- Check GPU is not in use by other applications

### Memory Leak False Positives
- Run test multiple times to confirm
- Check if OS is caching data
- Verify garbage collection is working

## Integration with CI/CD

### Recommended Test Schedule
- **Every commit**: Test 01 (single photo)
- **Daily**: Tests 01-02, 04, 06 (fast tests)
- **Weekly**: Test 03 (1000 photos benchmark)
- **Pre-release**: All tests including stress test

### Performance Regression Detection
Monitor these metrics over time:
- Average processing time trend
- Memory usage trend
- Throughput trend
- Success rate trend

Alert if:
- Processing time increases > 10%
- Memory usage increases > 15%
- Throughput decreases > 10%
- Success rate drops > 2%

## Related Files

- `test_performance_benchmark.py` - Main benchmark test suite
- `performance_metrics.py` - Metrics collection system
- `test_performance_metrics.py` - Metrics system unit tests
- `resource_manager.py` - Resource monitoring
- `test_resource_manager.py` - Resource manager tests

## Requirements

```
psutil>=5.9.0
GPUtil>=1.4.0  # Optional, for GPU tests
```

## Contact

For performance issues or questions:
- Review logs in `data/metrics/`
- Check system resource usage
- Consult PERFORMANCE_METRICS_IMPLEMENTATION.md
