"""
Example usage of GPU Manager

Demonstrates GPU monitoring, memory allocation, temperature tracking,
and throttling management.

Requirements: 17.1, 17.2, 17.3, 17.5
"""

import time
from gpu_manager import get_gpu_manager, GPUState


def example_basic_gpu_status():
    """Example: Get basic GPU status"""
    print("=" * 60)
    print("Example 1: Basic GPU Status")
    print("=" * 60)
    
    gpu_manager = get_gpu_manager()
    
    # Check if GPU is available
    if not gpu_manager.is_available():
        print("❌ GPU not available")
        return
    
    # Get GPU status
    status = gpu_manager.get_gpu_status()
    
    print(f"✓ GPU Available: {status['name']}")
    print(f"  State: {status['state']}")
    print(f"  Temperature: {status['temperature_celsius']}°C")
    print(f"  Load: {status['load_percent']:.1f}%")
    print(f"  Memory: {status['memory']['used_mb']:.0f}MB / {status['memory']['total_mb']:.0f}MB")
    print(f"  Memory Usage: {status['memory']['percent']:.1f}%")
    print()


def example_memory_allocation():
    """Example: GPU memory allocation"""
    print("=" * 60)
    print("Example 2: GPU Memory Allocation")
    print("=" * 60)
    
    gpu_manager = get_gpu_manager()
    
    if not gpu_manager.is_available():
        print("❌ GPU not available")
        return
    
    # Check available memory
    available = gpu_manager.get_available_memory()
    print(f"Available memory: {available:.0f}MB")
    
    # Allocate memory for LLM model
    print("\nAllocating 2048MB for LLM model...")
    success = gpu_manager.allocate_memory("llm_model", 2048)
    
    if success:
        print("✓ Memory allocated successfully")
        available = gpu_manager.get_available_memory()
        print(f"  Remaining available: {available:.0f}MB")
    else:
        print("❌ Memory allocation failed")
    
    # Allocate memory for image processing
    print("\nAllocating 512MB for image processing...")
    success = gpu_manager.allocate_memory("image_proc", 512)
    
    if success:
        print("✓ Memory allocated successfully")
        available = gpu_manager.get_available_memory()
        print(f"  Remaining available: {available:.0f}MB")
    
    # Get allocation stats
    status = gpu_manager.get_gpu_status()
    alloc_stats = status['memory']['allocation_stats']
    
    print(f"\nAllocation Statistics:")
    print(f"  Total allocations: {alloc_stats['allocation_count']}")
    print(f"  Allocated: {alloc_stats['allocated_mb']:.0f}MB")
    print(f"  Available: {alloc_stats['available_mb']:.0f}MB")
    
    # Deallocate memory
    print("\nDeallocating LLM model memory...")
    gpu_manager.deallocate_memory("llm_model")
    print("✓ Memory deallocated")
    
    available = gpu_manager.get_available_memory()
    print(f"  Available after deallocation: {available:.0f}MB")
    
    # Cleanup
    gpu_manager.deallocate_memory("image_proc")
    print()


def example_temperature_monitoring():
    """Example: GPU temperature monitoring"""
    print("=" * 60)
    print("Example 3: GPU Temperature Monitoring")
    print("=" * 60)
    
    gpu_manager = get_gpu_manager()
    
    if not gpu_manager.is_available():
        print("❌ GPU not available")
        return
    
    # Start monitoring
    print("Starting GPU monitoring...")
    gpu_manager.start_monitoring()
    
    # Monitor for 15 seconds
    print("Monitoring GPU temperature for 15 seconds...\n")
    
    for i in range(5):
        time.sleep(3)
        
        metrics = gpu_manager.get_gpu_metrics()
        if metrics:
            print(f"[{i*3+3}s] Temp: {metrics.temperature_celsius}°C | "
                  f"Load: {metrics.load_percent:.1f}% | "
                  f"State: {metrics.state.value}")
    
    # Get temperature trend
    print("\nTemperature Trend Analysis:")
    trend = gpu_manager.get_temperature_trend(duration_minutes=1)
    
    if trend:
        print(f"  Current: {trend['current_temp']}°C")
        print(f"  Average: {trend['avg_temp']:.1f}°C")
        print(f"  Min: {trend['min_temp']}°C")
        print(f"  Max: {trend['max_temp']}°C")
        print(f"  Trend: {trend['trend']}")
        print(f"  Stable: {'Yes' if trend['is_stable'] else 'No'}")
    
    # Stop monitoring
    gpu_manager.stop_monitoring()
    print("\n✓ Monitoring stopped")
    print()


def example_throttling_management():
    """Example: Processing throttling based on GPU state"""
    print("=" * 60)
    print("Example 4: Processing Throttling Management")
    print("=" * 60)
    
    gpu_manager = get_gpu_manager()
    
    if not gpu_manager.is_available():
        print("❌ GPU not available")
        return
    
    # Check throttling status
    should_throttle = gpu_manager.should_throttle_processing()
    speed_multiplier = gpu_manager.get_processing_speed_multiplier()
    
    print(f"Should throttle: {should_throttle}")
    print(f"Speed multiplier: {speed_multiplier:.1f}x")
    
    # Get current state
    status = gpu_manager.get_gpu_status()
    state = status['state']
    temp = status['temperature_celsius']
    
    print(f"\nCurrent GPU State: {state}")
    print(f"Temperature: {temp}°C")
    
    # Provide recommendations based on state
    print("\nProcessing Recommendations:")
    
    if state == 'optimal':
        print("  ✓ Full speed processing (1.0x)")
        print("  ✓ All features enabled")
    elif state == 'normal':
        print("  ⚠ Reduced speed processing (0.8x)")
        print("  ⚠ Monitor temperature")
    elif state == 'throttled':
        print("  ⚠ Half speed processing (0.5x)")
        print("  ⚠ Consider pausing non-critical tasks")
    elif state == 'critical':
        print("  ❌ Pause processing (0.0x)")
        print("  ❌ Wait for GPU to cool down")
    
    # Show thresholds
    thresholds = status['thresholds']
    print(f"\nTemperature Thresholds:")
    print(f"  Optimal: < {thresholds['temp_optimal']}°C")
    print(f"  Normal: < {thresholds['temp_normal']}°C")
    print(f"  Throttle: < {thresholds['temp_throttle']}°C")
    print(f"  Critical: ≥ {thresholds['temp_critical']}°C")
    print()


def example_state_change_callbacks():
    """Example: Register callbacks for GPU state changes"""
    print("=" * 60)
    print("Example 5: GPU State Change Callbacks")
    print("=" * 60)
    
    gpu_manager = get_gpu_manager()
    
    if not gpu_manager.is_available():
        print("❌ GPU not available")
        return
    
    # Define callback functions
    def on_state_change(old_state, new_state, metrics):
        print(f"🔄 State changed: {old_state.value} → {new_state.value}")
        if metrics:
            print(f"   Temperature: {metrics.temperature_celsius}°C")
    
    def on_throttle(metrics):
        print(f"⚠️  Throttling activated!")
        if metrics:
            print(f"   Temperature: {metrics.temperature_celsius}°C")
            print(f"   Reducing processing speed...")
    
    def on_critical(metrics):
        print(f"❌ CRITICAL: GPU in critical state!")
        if metrics:
            print(f"   Temperature: {metrics.temperature_celsius}°C")
            print(f"   Pausing all processing...")
    
    def on_resume(metrics):
        print(f"✓ GPU recovered, resuming normal operation")
        if metrics:
            print(f"   Temperature: {metrics.temperature_celsius}°C")
    
    # Register callbacks
    gpu_manager.register_callback('state_change', on_state_change)
    gpu_manager.register_callback('throttle', on_throttle)
    gpu_manager.register_callback('critical', on_critical)
    gpu_manager.register_callback('resume', on_resume)
    
    print("✓ Callbacks registered")
    print("  - State change")
    print("  - Throttle")
    print("  - Critical")
    print("  - Resume")
    
    print("\nMonitoring for state changes (20 seconds)...")
    print("(Callbacks will be triggered if GPU state changes)\n")
    
    # Start monitoring
    gpu_manager.start_monitoring()
    
    # Wait for potential state changes
    time.sleep(20)
    
    # Stop monitoring
    gpu_manager.stop_monitoring()
    
    print("\n✓ Monitoring complete")
    print()


def example_multi_gpu_support():
    """Example: Multi-GPU support"""
    print("=" * 60)
    print("Example 6: Multi-GPU Support")
    print("=" * 60)
    
    gpu_manager = get_gpu_manager()
    
    if not gpu_manager.is_available():
        print("❌ GPU not available")
        return
    
    # Get all GPUs status
    all_status = gpu_manager.get_all_gpus_status()
    
    print(f"Detected GPUs: {len(all_status)}\n")
    
    for i, status in enumerate(all_status):
        print(f"GPU {i}: {status['name']}")
        print(f"  State: {status['state']}")
        print(f"  Temperature: {status['temperature_celsius']}°C")
        print(f"  Memory: {status['memory']['used_mb']:.0f}MB / {status['memory']['total_mb']:.0f}MB")
        print()


def example_metrics_history():
    """Example: GPU metrics history"""
    print("=" * 60)
    print("Example 7: GPU Metrics History")
    print("=" * 60)
    
    gpu_manager = get_gpu_manager()
    
    if not gpu_manager.is_available():
        print("❌ GPU not available")
        return
    
    # Start monitoring to collect data
    print("Collecting metrics for 10 seconds...")
    gpu_manager.start_monitoring()
    time.sleep(10)
    gpu_manager.stop_monitoring()
    
    # Get metrics history
    history = gpu_manager.get_metrics_history(limit=10)
    
    print(f"\nLast {len(history)} measurements:\n")
    
    for i, metrics in enumerate(history[-5:], 1):  # Show last 5
        print(f"{i}. {metrics['timestamp']}")
        print(f"   Temp: {metrics['temperature_celsius']}°C | "
              f"Load: {metrics['load_percent']:.1f}% | "
              f"State: {metrics['state']}")
    
    print()


def example_config_management():
    """Example: GPU manager configuration"""
    print("=" * 60)
    print("Example 8: Configuration Management")
    print("=" * 60)
    
    gpu_manager = get_gpu_manager()
    
    # Get current config
    config = gpu_manager.config
    
    print("Current Configuration:")
    print(f"  Temperature Optimal: {config['temp_optimal']}°C")
    print(f"  Temperature Normal: {config['temp_normal']}°C")
    print(f"  Temperature Throttle: {config['temp_throttle']}°C")
    print(f"  Temperature Critical: {config['temp_critical']}°C")
    print(f"  Memory Limit: {config['memory_limit_mb']}MB")
    print(f"  Memory Reserve: {config['memory_reserve_mb']}MB")
    print(f"  Monitor Interval: {config['monitor_interval']}s")
    
    # Update configuration
    print("\nUpdating temperature thresholds...")
    gpu_manager.update_config({
        'temp_optimal': 60,
        'temp_throttle': 80
    })
    
    print("✓ Configuration updated")
    print(f"  New Optimal: {gpu_manager.config['temp_optimal']}°C")
    print(f"  New Throttle: {gpu_manager.config['temp_throttle']}°C")
    print()


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("GPU Manager - Example Usage")
    print("=" * 60 + "\n")
    
    try:
        # Run examples
        example_basic_gpu_status()
        time.sleep(1)
        
        example_memory_allocation()
        time.sleep(1)
        
        example_temperature_monitoring()
        time.sleep(1)
        
        example_throttling_management()
        time.sleep(1)
        
        example_state_change_callbacks()
        time.sleep(1)
        
        example_multi_gpu_support()
        time.sleep(1)
        
        example_metrics_history()
        time.sleep(1)
        
        example_config_management()
        
        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
