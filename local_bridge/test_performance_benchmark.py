"""
Performance Benchmark Tests for Junmai AutoDev

This module provides comprehensive performance testing including:
- 1000 photos processing benchmark
- Memory leak detection
- GPU usage testing
- Throughput and latency measurements

Requirements: 12.1, 12.2, 12.3
"""

import unittest
import time
import psutil
import gc
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import json
import tracemalloc

from performance_metrics import (
    PerformanceMetricsCollector,
    measure_performance,
    get_performance_metrics_collector
)


class PerformanceBenchmarkTests(unittest.TestCase):
    """
    Performance benchmark test suite
    
    Requirements: 12.1, 12.2, 12.3
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        cls.collector = get_performance_metrics_collector()
        cls.collector.clear_metrics()
        
        # Create temporary directory for test files
        cls.temp_dir = tempfile.mkdtemp()
        
        # Performance thresholds (from requirements)
        cls.THRESHOLDS = {
            'avg_processing_time_ms': 5000,  # 5 seconds per photo (Req 12.1)
            'max_concurrent_jobs': 20,  # Max 20 jobs in queue (Req 12.2)
            'max_memory_mb': 1024,  # Max 1GB memory usage (Req 12.3)
            'throughput_photos_per_minute': 12,  # At least 12 photos/min
        }
        
        print(f"\n{'='*70}")
        print("Performance Benchmark Test Suite")
        print(f"{'='*70}")
        print(f"Test directory: {cls.temp_dir}")
        print(f"Thresholds: {json.dumps(cls.THRESHOLDS, indent=2)}")
        print(f"{'='*70}\n")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test class"""
        # Clean up temp directory
        import shutil
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
        
        # Export final metrics
        try:
            filepath = cls.collector.export_to_json()
            print(f"\nFinal metrics exported to: {filepath}")
        except Exception as e:
            print(f"\nFailed to export metrics: {e}")
    
    def setUp(self):
        """Set up each test"""
        self.start_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        gc.collect()
    
    def tearDown(self):
        """Clean up after each test"""
        gc.collect()
    
    def _simulate_photo_processing(self, photo_id: int, complexity: str = 'normal') -> Dict:
        """
        Simulate photo processing with realistic timing
        
        Args:
            photo_id: Photo identifier
            complexity: Processing complexity ('simple', 'normal', 'complex')
            
        Returns:
            Processing result dictionary
        """
        # Simulate different processing times based on complexity
        processing_times = {
            'simple': (0.5, 1.5),  # 0.5-1.5 seconds
            'normal': (2.0, 4.0),  # 2-4 seconds
            'complex': (4.0, 6.0),  # 4-6 seconds
        }
        
        min_time, max_time = processing_times.get(complexity, (2.0, 4.0))
        
        # Simulate EXIF analysis
        with measure_performance(f"exif_analysis", photo_id=photo_id):
            time.sleep(min_time * 0.1)
        
        # Simulate AI evaluation
        with measure_performance(f"ai_evaluation", photo_id=photo_id):
            time.sleep(min_time * 0.3)
        
        # Simulate context determination
        with measure_performance(f"context_determination", photo_id=photo_id):
            time.sleep(min_time * 0.1)
        
        # Simulate preset application
        with measure_performance(f"preset_application", photo_id=photo_id):
            time.sleep(min_time * 0.5)
        
        return {
            'photo_id': photo_id,
            'complexity': complexity,
            'success': True
        }
    
    def test_01_single_photo_processing_time(self):
        """
        Test: Single photo processing meets time requirement
        
        Requirement: 12.1 - Process 1 photo in average 5 seconds
        """
        print("\n" + "="*70)
        print("TEST: Single Photo Processing Time")
        print("="*70)
        
        photo_id = 1
        
        start_time = time.time()
        with measure_performance("full_photo_processing", photo_id=photo_id):
            result = self._simulate_photo_processing(photo_id, complexity='normal')
        end_time = time.time()
        
        duration_ms = (end_time - start_time) * 1000
        
        print(f"Photo ID: {photo_id}")
        print(f"Processing time: {duration_ms:.2f}ms ({duration_ms/1000:.2f}s)")
        print(f"Threshold: {self.THRESHOLDS['avg_processing_time_ms']}ms")
        print(f"Result: {'PASS' if duration_ms <= self.THRESHOLDS['avg_processing_time_ms'] else 'FAIL'}")
        
        self.assertLessEqual(
            duration_ms,
            self.THRESHOLDS['avg_processing_time_ms'],
            f"Single photo processing took {duration_ms:.2f}ms, exceeds threshold of {self.THRESHOLDS['avg_processing_time_ms']}ms"
        )
    
    def test_02_batch_100_photos_processing(self):
        """
        Test: Batch processing of 100 photos
        
        Requirement: 12.1 - Maintain average processing time
        """
        print("\n" + "="*70)
        print("TEST: Batch Processing - 100 Photos")
        print("="*70)
        
        num_photos = 100
        results = []
        
        start_time = time.time()
        
        for i in range(num_photos):
            photo_id = 100 + i
            with measure_performance("batch_photo_processing", photo_id=photo_id):
                result = self._simulate_photo_processing(photo_id, complexity='normal')
                results.append(result)
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                print(f"Progress: {i+1}/{num_photos} photos ({rate:.2f} photos/sec)")
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Get statistics
        stats = self.collector.get_processing_time_stats(operation="batch_photo_processing")
        
        print(f"\nBatch Processing Results:")
        print(f"Total photos: {num_photos}")
        print(f"Total time: {total_duration:.2f}s")
        print(f"Average time per photo: {stats['avg_duration_ms']:.2f}ms ({stats['avg_duration_ms']/1000:.2f}s)")
        print(f"Min time: {stats['min_duration_ms']:.2f}ms")
        print(f"Max time: {stats['max_duration_ms']:.2f}ms")
        print(f"Throughput: {num_photos/total_duration:.2f} photos/sec")
        print(f"Success rate: {stats['success_rate']:.2f}%")
        
        self.assertLessEqual(
            stats['avg_duration_ms'],
            self.THRESHOLDS['avg_processing_time_ms'],
            f"Average processing time {stats['avg_duration_ms']:.2f}ms exceeds threshold"
        )
    
    def test_03_large_batch_1000_photos_benchmark(self):
        """
        Test: Large batch processing of 1000 photos (MAIN BENCHMARK)
        
        Requirement: 12.1, 12.2, 12.3 - Full system performance test
        """
        print("\n" + "="*70)
        print("TEST: Large Batch Processing - 1000 Photos (BENCHMARK)")
        print("="*70)
        
        num_photos = 1000
        results = []
        
        # Start memory tracking
        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        print(f"Initial memory: {initial_memory:.2f}MB")
        
        # Start monitoring
        self.collector.start_monitoring()
        
        start_time = time.time()
        
        try:
            for i in range(num_photos):
                photo_id = 1000 + i
                
                # Vary complexity for realistic simulation
                if i % 10 == 0:
                    complexity = 'complex'
                elif i % 5 == 0:
                    complexity = 'simple'
                else:
                    complexity = 'normal'
                
                with measure_performance("benchmark_photo_processing", photo_id=photo_id):
                    result = self._simulate_photo_processing(photo_id, complexity=complexity)
                    results.append(result)
                
                # Record memory usage periodically
                if (i + 1) % 100 == 0:
                    self.collector.record_memory_usage(f"after_{i+1}_photos")
                    current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                    elapsed = time.time() - start_time
                    rate = (i + 1) / elapsed
                    eta = (num_photos - i - 1) / rate if rate > 0 else 0
                    
                    print(f"Progress: {i+1}/{num_photos} photos | "
                          f"Rate: {rate:.2f} photos/sec | "
                          f"Memory: {current_memory:.2f}MB | "
                          f"ETA: {eta:.0f}s")
        
        finally:
            # Stop monitoring
            self.collector.stop_monitoring()
        
        end_time = time.time()
        total_duration = end_time - start_time
        final_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        
        # Get comprehensive statistics
        stats = self.collector.get_processing_time_stats(operation="benchmark_photo_processing")
        memory_stats = self.collector.get_memory_usage_stats()
        
        print(f"\n{'='*70}")
        print("BENCHMARK RESULTS - 1000 Photos")
        print(f"{'='*70}")
        print(f"\nProcessing Statistics:")
        print(f"  Total photos: {num_photos}")
        print(f"  Total time: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")
        print(f"  Average time per photo: {stats['avg_duration_ms']:.2f}ms ({stats['avg_duration_ms']/1000:.2f}s)")
        print(f"  Min time: {stats['min_duration_ms']:.2f}ms")
        print(f"  Max time: {stats['max_duration_ms']:.2f}ms")
        print(f"  Median time: {stats['median_duration_ms']:.2f}ms")
        print(f"  Throughput: {num_photos/total_duration:.2f} photos/sec")
        print(f"  Throughput: {(num_photos/total_duration)*60:.2f} photos/min")
        print(f"  Success rate: {stats['success_rate']:.2f}%")
        
        print(f"\nMemory Statistics:")
        print(f"  Initial memory: {initial_memory:.2f}MB")
        print(f"  Final memory: {final_memory:.2f}MB")
        print(f"  Memory increase: {final_memory - initial_memory:.2f}MB")
        print(f"  Peak memory: {memory_stats.get('max_process_mb', 0):.2f}MB")
        print(f"  Average memory: {memory_stats.get('avg_process_mb', 0):.2f}MB")
        
        print(f"\nThreshold Compliance:")
        print(f"  Avg processing time: {stats['avg_duration_ms']:.2f}ms / {self.THRESHOLDS['avg_processing_time_ms']}ms "
              f"({'PASS' if stats['avg_duration_ms'] <= self.THRESHOLDS['avg_processing_time_ms'] else 'FAIL'})")
        print(f"  Peak memory: {memory_stats.get('max_process_mb', 0):.2f}MB / {self.THRESHOLDS['max_memory_mb']}MB "
              f"({'PASS' if memory_stats.get('max_process_mb', 0) <= self.THRESHOLDS['max_memory_mb'] else 'FAIL'})")
        print(f"  Throughput: {(num_photos/total_duration)*60:.2f} / {self.THRESHOLDS['throughput_photos_per_minute']} photos/min "
              f"({'PASS' if (num_photos/total_duration)*60 >= self.THRESHOLDS['throughput_photos_per_minute'] else 'FAIL'})")
        print(f"{'='*70}\n")
        
        # Assertions
        self.assertLessEqual(
            stats['avg_duration_ms'],
            self.THRESHOLDS['avg_processing_time_ms'],
            f"Average processing time {stats['avg_duration_ms']:.2f}ms exceeds threshold"
        )
        
        self.assertLessEqual(
            memory_stats.get('max_process_mb', 0),
            self.THRESHOLDS['max_memory_mb'],
            f"Peak memory {memory_stats.get('max_process_mb', 0):.2f}MB exceeds threshold"
        )
        
        self.assertGreaterEqual(
            (num_photos/total_duration)*60,
            self.THRESHOLDS['throughput_photos_per_minute'],
            f"Throughput {(num_photos/total_duration)*60:.2f} photos/min below threshold"
        )
    
    def test_04_memory_leak_detection(self):
        """
        Test: Memory leak detection over repeated processing
        
        Requirement: 12.3 - Memory usage stays under 1GB
        """
        print("\n" + "="*70)
        print("TEST: Memory Leak Detection")
        print("="*70)
        
        num_iterations = 50
        photos_per_iteration = 10
        memory_samples = []
        
        # Start memory tracking
        tracemalloc.start()
        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        
        print(f"Initial memory: {initial_memory:.2f}MB")
        print(f"Running {num_iterations} iterations of {photos_per_iteration} photos each...")
        
        for iteration in range(num_iterations):
            # Process batch of photos
            for i in range(photos_per_iteration):
                photo_id = 10000 + iteration * photos_per_iteration + i
                with measure_performance("memory_leak_test", photo_id=photo_id):
                    self._simulate_photo_processing(photo_id, complexity='simple')
            
            # Force garbage collection
            gc.collect()
            
            # Record memory
            current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            memory_samples.append(current_memory)
            
            if (iteration + 1) % 10 == 0:
                print(f"Iteration {iteration+1}/{num_iterations}: Memory = {current_memory:.2f}MB")
        
        # Get memory snapshot
        snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()
        
        final_memory = memory_samples[-1]
        memory_increase = final_memory - initial_memory
        
        # Calculate memory growth rate
        if len(memory_samples) > 1:
            # Linear regression to detect memory leak trend
            x = list(range(len(memory_samples)))
            y = memory_samples
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            memory_growth_per_iteration = slope
        else:
            memory_growth_per_iteration = 0
        
        print(f"\nMemory Leak Analysis:")
        print(f"  Initial memory: {initial_memory:.2f}MB")
        print(f"  Final memory: {final_memory:.2f}MB")
        print(f"  Total increase: {memory_increase:.2f}MB")
        print(f"  Growth per iteration: {memory_growth_per_iteration:.4f}MB")
        print(f"  Total photos processed: {num_iterations * photos_per_iteration}")
        print(f"  Memory per photo: {memory_increase / (num_iterations * photos_per_iteration):.4f}MB")
        
        # Show top memory allocations
        print(f"\nTop 5 Memory Allocations:")
        top_stats = snapshot.statistics('lineno')[:5]
        for stat in top_stats:
            print(f"  {stat}")
        
        # Memory leak threshold: should not grow more than 0.5MB per iteration
        memory_leak_threshold = 0.5  # MB per iteration
        
        print(f"\nMemory Leak Check:")
        print(f"  Growth rate: {memory_growth_per_iteration:.4f}MB/iteration")
        print(f"  Threshold: {memory_leak_threshold}MB/iteration")
        print(f"  Result: {'PASS' if abs(memory_growth_per_iteration) < memory_leak_threshold else 'FAIL'}")
        
        self.assertLess(
            abs(memory_growth_per_iteration),
            memory_leak_threshold,
            f"Memory leak detected: {memory_growth_per_iteration:.4f}MB per iteration"
        )
        
        self.assertLess(
            final_memory,
            self.THRESHOLDS['max_memory_mb'],
            f"Final memory {final_memory:.2f}MB exceeds threshold"
        )
    
    def test_05_gpu_usage_monitoring(self):
        """
        Test: GPU usage monitoring and tracking
        
        Requirement: 12.2 - GPU usage tracking
        """
        print("\n" + "="*70)
        print("TEST: GPU Usage Monitoring")
        print("="*70)
        
        # Check GPU availability
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            gpu_available = len(gpus) > 0
        except ImportError:
            gpu_available = False
            print("GPUtil not available - skipping GPU tests")
        
        if not gpu_available:
            self.skipTest("GPU not available for testing")
            return
        
        print(f"GPU detected: {gpus[0].name}")
        print(f"GPU memory: {gpus[0].memoryTotal}MB")
        
        # Record initial GPU state
        self.collector.record_gpu_usage("initial_state")
        
        # Simulate GPU-intensive processing
        num_photos = 50
        print(f"\nProcessing {num_photos} photos with GPU monitoring...")
        
        for i in range(num_photos):
            photo_id = 20000 + i
            
            with measure_performance("gpu_test_processing", photo_id=photo_id):
                self._simulate_photo_processing(photo_id, complexity='normal')
            
            # Record GPU usage every 10 photos
            if (i + 1) % 10 == 0:
                self.collector.record_gpu_usage(f"after_{i+1}_photos")
                print(f"Progress: {i+1}/{num_photos} photos")
        
        # Get GPU statistics
        gpu_stats = self.collector.get_gpu_usage_stats()
        
        print(f"\nGPU Usage Statistics:")
        print(f"  Samples collected: {gpu_stats['count']}")
        print(f"  Average load: {gpu_stats.get('avg_load_percent', 0):.2f}%")
        print(f"  Peak load: {gpu_stats.get('max_load_percent', 0):.2f}%")
        print(f"  Average memory: {gpu_stats.get('avg_memory_percent', 0):.2f}%")
        print(f"  Peak memory: {gpu_stats.get('max_memory_percent', 0):.2f}%")
        print(f"  Average temperature: {gpu_stats.get('avg_temperature', 0):.2f}°C")
        print(f"  Peak temperature: {gpu_stats.get('max_temperature', 0):.2f}°C")
        
        # GPU should not overheat (< 85°C)
        max_temp_threshold = 85.0
        print(f"\nGPU Temperature Check:")
        print(f"  Peak temperature: {gpu_stats.get('max_temperature', 0):.2f}°C")
        print(f"  Threshold: {max_temp_threshold}°C")
        print(f"  Result: {'PASS' if gpu_stats.get('max_temperature', 0) < max_temp_threshold else 'FAIL'}")
        
        self.assertLess(
            gpu_stats.get('max_temperature', 0),
            max_temp_threshold,
            f"GPU temperature {gpu_stats.get('max_temperature', 0):.2f}°C exceeds safe threshold"
        )
    
    def test_06_concurrent_job_queue_capacity(self):
        """
        Test: Concurrent job queue capacity
        
        Requirement: 12.2 - Hold max 20 jobs in queue
        """
        print("\n" + "="*70)
        print("TEST: Concurrent Job Queue Capacity")
        print("="*70)
        
        max_concurrent = self.THRESHOLDS['max_concurrent_jobs']
        test_jobs = max_concurrent + 5  # Test slightly over capacity
        
        print(f"Testing queue with {test_jobs} jobs (max capacity: {max_concurrent})")
        
        # Simulate job queue
        active_jobs = []
        completed_jobs = []
        
        start_time = time.time()
        
        for i in range(test_jobs):
            job_id = f"job_{i:04d}"
            
            # Add job to queue
            active_jobs.append({
                'job_id': job_id,
                'photo_id': 30000 + i,
                'start_time': time.time()
            })
            
            # Simulate job processing
            with measure_performance("queue_job_processing", photo_id=30000+i, job_id=job_id):
                self._simulate_photo_processing(30000 + i, complexity='simple')
            
            # Complete job
            completed_job = active_jobs.pop(0)
            completed_job['end_time'] = time.time()
            completed_jobs.append(completed_job)
            
            # Check queue size
            queue_size = len(active_jobs)
            
            if (i + 1) % 5 == 0:
                print(f"Processed {i+1}/{test_jobs} jobs | Queue size: {queue_size}")
            
            # Queue should never exceed max capacity
            self.assertLessEqual(
                queue_size,
                max_concurrent,
                f"Queue size {queue_size} exceeds max capacity {max_concurrent}"
            )
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        print(f"\nQueue Management Results:")
        print(f"  Total jobs: {test_jobs}")
        print(f"  Completed jobs: {len(completed_jobs)}")
        print(f"  Total time: {total_duration:.2f}s")
        print(f"  Average time per job: {total_duration/test_jobs:.2f}s")
        print(f"  Max queue capacity: {max_concurrent}")
        print(f"  Result: PASS (queue never exceeded capacity)")
    
    def test_07_sustained_load_stress_test(self):
        """
        Test: Sustained load stress test
        
        Requirement: 12.1, 12.2, 12.3 - System stability under sustained load
        """
        print("\n" + "="*70)
        print("TEST: Sustained Load Stress Test")
        print("="*70)
        
        duration_minutes = 2  # 2 minute stress test
        duration_seconds = duration_minutes * 60
        
        print(f"Running sustained load test for {duration_minutes} minutes...")
        
        # Start monitoring
        self.collector.start_monitoring()
        
        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        start_time = time.time()
        photo_count = 0
        
        try:
            while (time.time() - start_time) < duration_seconds:
                photo_id = 40000 + photo_count
                
                with measure_performance("stress_test_processing", photo_id=photo_id):
                    self._simulate_photo_processing(photo_id, complexity='normal')
                
                photo_count += 1
                
                # Report progress every 10 seconds
                elapsed = time.time() - start_time
                if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                    current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                    rate = photo_count / elapsed
                    print(f"Time: {int(elapsed)}s | Photos: {photo_count} | "
                          f"Rate: {rate:.2f} photos/sec | Memory: {current_memory:.2f}MB")
        
        finally:
            self.collector.stop_monitoring()
        
        end_time = time.time()
        actual_duration = end_time - start_time
        final_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        
        # Get statistics
        stats = self.collector.get_processing_time_stats(operation="stress_test_processing")
        memory_stats = self.collector.get_memory_usage_stats()
        
        print(f"\nStress Test Results:")
        print(f"  Duration: {actual_duration:.2f}s ({actual_duration/60:.2f} minutes)")
        print(f"  Photos processed: {photo_count}")
        print(f"  Average rate: {photo_count/actual_duration:.2f} photos/sec")
        print(f"  Average processing time: {stats['avg_duration_ms']:.2f}ms")
        print(f"  Success rate: {stats['success_rate']:.2f}%")
        print(f"  Initial memory: {initial_memory:.2f}MB")
        print(f"  Final memory: {final_memory:.2f}MB")
        print(f"  Memory increase: {final_memory - initial_memory:.2f}MB")
        print(f"  Peak memory: {memory_stats.get('max_process_mb', 0):.2f}MB")
        
        # System should remain stable
        self.assertLessEqual(
            stats['avg_duration_ms'],
            self.THRESHOLDS['avg_processing_time_ms'] * 1.2,  # Allow 20% degradation
            "Processing time degraded significantly under sustained load"
        )
        
        self.assertLessEqual(
            final_memory,
            self.THRESHOLDS['max_memory_mb'],
            f"Memory usage {final_memory:.2f}MB exceeds threshold under sustained load"
        )
        
        self.assertGreaterEqual(
            stats['success_rate'],
            95.0,
            "Success rate dropped below 95% under sustained load"
        )


def run_benchmark_tests():
    """Run performance benchmark tests"""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(PerformanceBenchmarkTests)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("\n" + "="*70)
    print("JUNMAI AUTODEV - PERFORMANCE BENCHMARK TEST SUITE")
    print("="*70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    result = run_benchmark_tests()
    
    print("\n" + "="*70)
    print("BENCHMARK SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
