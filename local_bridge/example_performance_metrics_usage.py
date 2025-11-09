"""
Example usage of Performance Metrics Collection System

This script demonstrates how to use the performance metrics collector
for tracking processing times, memory usage, and GPU usage.

Requirements: 12.1, 12.2, 15.4
"""

import time
import random
from performance_metrics import (
    get_performance_metrics_collector,
    measure_performance,
    record_processing_time,
    record_memory_usage,
    record_gpu_usage
)


def example_basic_timing():
    """Example: Basic processing time measurement"""
    print("=" * 60)
    print("Example 1: Basic Processing Time Measurement")
    print("=" * 60)
    
    collector = get_performance_metrics_collector()
    
    # Method 1: Using context manager
    print("\n1. Using context manager:")
    with measure_performance("image_processing", photo_id=123):
        time.sleep(0.5)  # Simulate processing
        print("   Processing image...")
    
    # Method 2: Manual recording
    print("\n2. Manual recording:")
    start = time.time()
    time.sleep(0.3)  # Simulate processing
    duration_ms = (time.time() - start) * 1000
    record_processing_time("manual_operation", duration_ms, photo_id=456)
    print(f"   Recorded: {duration_ms:.2f}ms")
    
    # Get stats
    stats = collector.get_processing_time_stats()
    print(f"\n📊 Total operations recorded: {stats['count']}")
    print(f"   Average duration: {stats['avg_duration_ms']:.2f}ms")


def example_operation_stages():
    """Example: Tracking multi-stage operations"""
    print("\n" + "=" * 60)
    print("Example 2: Multi-Stage Operation Tracking")
    print("=" * 60)
    
    photo_id = 789
    job_id = "job_001"
    
    # Stage 1: EXIF Analysis
    with measure_performance("exif_analysis", photo_id=photo_id, job_id=job_id, stage="exif"):
        time.sleep(0.1)
        print("   ✓ EXIF analysis completed")
    
    # Stage 2: AI Evaluation
    with measure_performance("ai_evaluation", photo_id=photo_id, job_id=job_id, stage="ai"):
        time.sleep(0.8)
        print("   ✓ AI evaluation completed")
    
    # Stage 3: Preset Selection
    with measure_performance("preset_selection", photo_id=photo_id, job_id=job_id, stage="preset"):
        time.sleep(0.2)
        print("   ✓ Preset selection completed")
    
    # Get operation summary
    collector = get_performance_metrics_collector()
    summary = collector.get_operation_summary()
    
    print("\n📊 Operation Summary:")
    for op in summary:
        print(f"   {op['operation']}: {op['avg_duration_ms']:.2f}ms avg, {op['count']} times")


def example_error_tracking():
    """Example: Tracking operations with errors"""
    print("\n" + "=" * 60)
    print("Example 3: Error Tracking")
    print("=" * 60)
    
    # Successful operation
    with measure_performance("successful_op", photo_id=100):
        time.sleep(0.1)
        print("   ✓ Operation succeeded")
    
    # Failed operation
    try:
        with measure_performance("failed_op", photo_id=101):
            time.sleep(0.1)
            raise ValueError("Simulated error")
    except ValueError:
        print("   ✗ Operation failed (error tracked)")
    
    # Get stats
    collector = get_performance_metrics_collector()
    stats = collector.get_processing_time_stats()
    
    print(f"\n📊 Success rate: {stats['success_rate']:.1f}%")
    print(f"   Successes: {stats['success_count']}")
    print(f"   Failures: {stats['failure_count']}")


def example_memory_tracking():
    """Example: Memory usage tracking"""
    print("\n" + "=" * 60)
    print("Example 4: Memory Usage Tracking")
    print("=" * 60)
    
    collector = get_performance_metrics_collector()
    
    # Record memory at different points
    print("\n1. Initial memory state:")
    record_memory_usage("startup")
    stats = collector.get_memory_usage_stats()
    print(f"   System memory: {stats['current_used_mb']:.0f}MB ({stats['current_percent']:.1f}%)")
    print(f"   Process memory: {stats['current_process_mb']:.0f}MB")
    
    # Simulate memory-intensive operation
    print("\n2. During processing:")
    data = [0] * 10000000  # Allocate some memory
    record_memory_usage("processing")
    stats = collector.get_memory_usage_stats()
    print(f"   System memory: {stats['current_used_mb']:.0f}MB ({stats['current_percent']:.1f}%)")
    print(f"   Process memory: {stats['current_process_mb']:.0f}MB")
    
    # Clean up
    del data
    print("\n3. After cleanup:")
    record_memory_usage("cleanup")
    stats = collector.get_memory_usage_stats()
    print(f"   System memory: {stats['current_used_mb']:.0f}MB ({stats['current_percent']:.1f}%)")
    print(f"   Process memory: {stats['current_process_mb']:.0f}MB")


def example_gpu_tracking():
    """Example: GPU usage tracking"""
    print("\n" + "=" * 60)
    print("Example 5: GPU Usage Tracking")
    print("=" * 60)
    
    collector = get_performance_metrics_collector()
    
    if not collector.gpu_available:
        print("\n⚠️  GPU not available - skipping GPU tracking example")
        return
    
    # Record GPU usage
    print("\n1. Recording GPU usage:")
    record_gpu_usage("ai_inference")
    
    stats = collector.get_gpu_usage_stats()
    
    if stats['count'] > 0:
        print(f"   GPU Load: {stats['current_load_percent']:.1f}%")
        print(f"   GPU Memory: {stats['current_memory_percent']:.1f}%")
        print(f"   GPU Temperature: {stats['current_temperature']:.1f}°C")
    else:
        print("   No GPU metrics recorded yet")


def example_background_monitoring():
    """Example: Background monitoring"""
    print("\n" + "=" * 60)
    print("Example 6: Background Monitoring")
    print("=" * 60)
    
    collector = get_performance_metrics_collector()
    
    # Configure monitoring
    collector.update_config({
        'memory_sample_interval': 2  # Sample every 2 seconds
    })
    
    print("\n1. Starting background monitoring...")
    collector.start_monitoring()
    
    # Do some work
    print("2. Performing operations (monitoring in background)...")
    for i in range(3):
        with measure_performance(f"batch_operation_{i}"):
            time.sleep(1)
        print(f"   ✓ Operation {i+1} completed")
    
    # Stop monitoring
    print("\n3. Stopping monitoring...")
    collector.stop_monitoring()
    
    # Check collected metrics
    counts = collector.get_metrics_count()
    print(f"\n📊 Metrics collected:")
    print(f"   Processing times: {counts['processing_times']}")
    print(f"   Memory samples: {counts['memory_usage']}")
    print(f"   GPU samples: {counts['gpu_usage']}")


def example_statistics():
    """Example: Getting detailed statistics"""
    print("\n" + "=" * 60)
    print("Example 7: Detailed Statistics")
    print("=" * 60)
    
    collector = get_performance_metrics_collector()
    
    # Simulate various operations
    operations = ["exif_analysis", "ai_evaluation", "preset_selection", "export"]
    
    print("\n1. Simulating operations...")
    for _ in range(20):
        op = random.choice(operations)
        duration = random.uniform(100, 1000)
        
        with measure_performance(op):
            time.sleep(duration / 1000)
    
    # Get overall stats
    print("\n2. Overall statistics:")
    stats = collector.get_processing_time_stats()
    print(f"   Total operations: {stats['count']}")
    print(f"   Average duration: {stats['avg_duration_ms']:.2f}ms")
    print(f"   Min duration: {stats['min_duration_ms']:.2f}ms")
    print(f"   Max duration: {stats['max_duration_ms']:.2f}ms")
    print(f"   Median duration: {stats['median_duration_ms']:.2f}ms")
    
    # Get per-operation stats
    print("\n3. Per-operation statistics:")
    summary = collector.get_operation_summary()
    for op in summary:
        print(f"   {op['operation']}:")
        print(f"      Count: {op['count']}")
        print(f"      Avg: {op['avg_duration_ms']:.2f}ms")
        print(f"      Total: {op['total_duration_ms']:.2f}ms")


def example_export():
    """Example: Exporting metrics"""
    print("\n" + "=" * 60)
    print("Example 8: Exporting Metrics")
    print("=" * 60)
    
    collector = get_performance_metrics_collector()
    
    # Generate some metrics
    print("\n1. Generating sample metrics...")
    for i in range(10):
        with measure_performance("sample_operation", photo_id=i):
            time.sleep(0.05)
    
    record_memory_usage("export_test")
    
    # Export to JSON
    print("\n2. Exporting to JSON...")
    json_path = collector.export_to_json()
    print(f"   ✓ Exported to: {json_path}")
    
    # Export to CSV
    print("\n3. Exporting to CSV...")
    csv_path = collector.export_to_csv('processing')
    print(f"   ✓ Exported to: {csv_path}")
    
    print("\n📁 Export files created successfully!")


def example_time_windows():
    """Example: Time window filtering"""
    print("\n" + "=" * 60)
    print("Example 9: Time Window Filtering")
    print("=" * 60)
    
    collector = get_performance_metrics_collector()
    
    # Generate metrics over time
    print("\n1. Generating metrics over time...")
    for i in range(5):
        with measure_performance("timed_operation"):
            time.sleep(0.1)
        time.sleep(0.5)  # Wait between operations
    
    # Get stats for different time windows
    print("\n2. Statistics by time window:")
    
    # Last 1 minute
    stats_1min = collector.get_processing_time_stats(duration_minutes=1)
    print(f"   Last 1 minute: {stats_1min['count']} operations")
    
    # Last 5 minutes
    stats_5min = collector.get_processing_time_stats(duration_minutes=5)
    print(f"   Last 5 minutes: {stats_5min['count']} operations")
    
    # All time
    stats_all = collector.get_processing_time_stats()
    print(f"   All time: {stats_all['count']} operations")


def example_cleanup():
    """Example: Cleaning up metrics"""
    print("\n" + "=" * 60)
    print("Example 10: Cleanup")
    print("=" * 60)
    
    collector = get_performance_metrics_collector()
    
    # Check current counts
    counts_before = collector.get_metrics_count()
    print(f"\n1. Metrics before cleanup:")
    print(f"   Processing: {counts_before['processing_times']}")
    print(f"   Memory: {counts_before['memory_usage']}")
    print(f"   GPU: {counts_before['gpu_usage']}")
    
    # Clear specific type
    print("\n2. Clearing processing metrics...")
    collector.clear_metrics('processing')
    
    # Clear all
    print("3. Clearing all metrics...")
    collector.clear_metrics()
    
    # Check after cleanup
    counts_after = collector.get_metrics_count()
    print(f"\n4. Metrics after cleanup:")
    print(f"   Processing: {counts_after['processing_times']}")
    print(f"   Memory: {counts_after['memory_usage']}")
    print(f"   GPU: {counts_after['gpu_usage']}")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("PERFORMANCE METRICS COLLECTION EXAMPLES")
    print("=" * 60)
    
    try:
        example_basic_timing()
        example_operation_stages()
        example_error_tracking()
        example_memory_tracking()
        example_gpu_tracking()
        example_background_monitoring()
        example_statistics()
        example_export()
        example_time_windows()
        example_cleanup()
        
        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
