"""
Tests for Performance Metrics Collection System

Requirements: 12.1, 12.2, 15.4
"""

import unittest
import time
import tempfile
import os
import json
import csv
from datetime import datetime, timedelta
from performance_metrics import (
    PerformanceMetricsCollector,
    PerformanceTimer,
    ProcessingTimeMetric,
    MemoryUsageMetric,
    GPUUsageMetric,
    measure_performance,
    record_processing_time,
    record_memory_usage,
    record_gpu_usage
)


class TestPerformanceTimer(unittest.TestCase):
    """Test PerformanceTimer context manager"""
    
    def test_timer_basic(self):
        """Test basic timer functionality"""
        with PerformanceTimer("test_op", auto_record=False) as timer:
            time.sleep(0.1)
        
        self.assertIsNotNone(timer.duration_ms)
        self.assertGreater(timer.duration_ms, 90)  # At least 90ms
        self.assertTrue(timer.success)
        self.assertIsNone(timer.error_message)
    
    def test_timer_with_error(self):
        """Test timer with exception"""
        try:
            with PerformanceTimer("test_op", auto_record=False) as timer:
                raise ValueError("Test error")
        except ValueError:
            pass
        
        self.assertFalse(timer.success)
        self.assertIsNotNone(timer.error_message)
        self.assertIn("Test error", timer.error_message)
    
    def test_timer_with_metadata(self):
        """Test timer with metadata"""
        with PerformanceTimer(
            "test_op",
            photo_id=123,
            job_id="job_001",
            stage="test",
            auto_record=False
        ) as timer:
            time.sleep(0.05)
        
        self.assertEqual(timer.photo_id, 123)
        self.assertEqual(timer.job_id, "job_001")
        self.assertEqual(timer.stage, "test")


class TestPerformanceMetricsCollector(unittest.TestCase):
    """Test PerformanceMetricsCollector"""
    
    def setUp(self):
        """Set up test collector"""
        self.collector = PerformanceMetricsCollector()
        self.collector.clear_metrics()
    
    def tearDown(self):
        """Clean up"""
        self.collector.stop_monitoring()
        self.collector.clear_metrics()
    
    def test_record_processing_time(self):
        """Test recording processing time"""
        self.collector.record_processing_time(
            operation="test_op",
            duration_ms=100.5,
            photo_id=123,
            success=True
        )
        
        self.assertEqual(len(self.collector.processing_times), 1)
        
        metric = self.collector.processing_times[0]
        self.assertEqual(metric.operation, "test_op")
        self.assertEqual(metric.duration_ms, 100.5)
        self.assertEqual(metric.photo_id, 123)
        self.assertTrue(metric.success)
    
    def test_record_memory_usage(self):
        """Test recording memory usage"""
        self.collector.record_memory_usage("test_op")
        
        self.assertEqual(len(self.collector.memory_usage), 1)
        
        metric = self.collector.memory_usage[0]
        self.assertEqual(metric.operation, "test_op")
        self.assertGreater(metric.total_mb, 0)
        self.assertGreater(metric.used_mb, 0)
        self.assertGreater(metric.percent, 0)
    
    def test_record_gpu_usage(self):
        """Test recording GPU usage"""
        self.collector.record_gpu_usage("test_op")
        
        # GPU may not be available
        if self.collector.gpu_available:
            self.assertGreater(len(self.collector.gpu_usage), 0)
    
    def test_processing_time_stats(self):
        """Test processing time statistics"""
        # Record multiple operations
        for i in range(10):
            self.collector.record_processing_time(
                operation="test_op",
                duration_ms=100 + i * 10,
                success=True
            )
        
        stats = self.collector.get_processing_time_stats()
        
        self.assertEqual(stats['count'], 10)
        self.assertEqual(stats['success_count'], 10)
        self.assertEqual(stats['failure_count'], 0)
        self.assertAlmostEqual(stats['avg_duration_ms'], 145.0, places=1)
        self.assertEqual(stats['min_duration_ms'], 100)
        self.assertEqual(stats['max_duration_ms'], 190)
    
    def test_processing_time_stats_with_failures(self):
        """Test stats with failures"""
        # Record successes and failures
        for i in range(5):
            self.collector.record_processing_time(
                operation="test_op",
                duration_ms=100,
                success=True
            )
        
        for i in range(3):
            self.collector.record_processing_time(
                operation="test_op",
                duration_ms=100,
                success=False,
                error_message="Test error"
            )
        
        stats = self.collector.get_processing_time_stats()
        
        self.assertEqual(stats['count'], 8)
        self.assertEqual(stats['success_count'], 5)
        self.assertEqual(stats['failure_count'], 3)
        self.assertAlmostEqual(stats['success_rate'], 62.5, places=1)
    
    def test_processing_time_stats_by_operation(self):
        """Test stats filtered by operation"""
        # Record different operations
        self.collector.record_processing_time("op1", 100, success=True)
        self.collector.record_processing_time("op1", 200, success=True)
        self.collector.record_processing_time("op2", 300, success=True)
        
        stats_op1 = self.collector.get_processing_time_stats(operation="op1")
        stats_op2 = self.collector.get_processing_time_stats(operation="op2")
        
        self.assertEqual(stats_op1['count'], 2)
        self.assertEqual(stats_op2['count'], 1)
        self.assertAlmostEqual(stats_op1['avg_duration_ms'], 150.0)
        self.assertAlmostEqual(stats_op2['avg_duration_ms'], 300.0)
    
    def test_memory_usage_stats(self):
        """Test memory usage statistics"""
        # Record multiple samples
        for i in range(5):
            self.collector.record_memory_usage()
            time.sleep(0.01)
        
        stats = self.collector.get_memory_usage_stats()
        
        self.assertEqual(stats['count'], 5)
        self.assertGreater(stats['current_used_mb'], 0)
        self.assertGreater(stats['avg_used_mb'], 0)
        self.assertGreater(stats['max_used_mb'], 0)
    
    def test_operation_summary(self):
        """Test operation summary"""
        # Record various operations
        operations = {
            'op1': [100, 150, 200],
            'op2': [50, 75],
            'op3': [300, 350, 400, 450]
        }
        
        for op, durations in operations.items():
            for duration in durations:
                self.collector.record_processing_time(op, duration, success=True)
        
        summary = self.collector.get_operation_summary()
        
        self.assertEqual(len(summary), 3)
        
        # Should be sorted by total duration (descending)
        self.assertEqual(summary[0]['operation'], 'op3')  # Total: 1500ms
        self.assertEqual(summary[1]['operation'], 'op1')  # Total: 450ms
        self.assertEqual(summary[2]['operation'], 'op2')  # Total: 125ms
    
    def test_time_window_filtering(self):
        """Test filtering by time window"""
        # Record old metric
        old_metric = ProcessingTimeMetric(
            timestamp=datetime.now() - timedelta(minutes=10),
            operation="old_op",
            duration_ms=100,
            success=True
        )
        self.collector.processing_times.append(old_metric)
        
        # Record recent metric
        self.collector.record_processing_time("recent_op", 200, success=True)
        
        # Get stats for last 5 minutes
        stats = self.collector.get_processing_time_stats(duration_minutes=5)
        
        # Should only include recent metric
        self.assertEqual(stats['count'], 1)
    
    def test_export_to_json(self):
        """Test JSON export"""
        # Record some metrics
        self.collector.record_processing_time("test_op", 100, success=True)
        self.collector.record_memory_usage("test_op")
        
        # Export
        with tempfile.TemporaryDirectory() as tmpdir:
            self.collector.config['export_directory'] = tmpdir
            filepath = self.collector.export_to_json()
            
            # Verify file exists
            self.assertTrue(os.path.exists(filepath))
            
            # Verify content
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.assertIn('export_timestamp', data)
            self.assertIn('processing_times', data)
            self.assertIn('memory_usage', data)
            self.assertIn('summary', data)
            
            self.assertEqual(len(data['processing_times']), 1)
            self.assertEqual(len(data['memory_usage']), 1)
    
    def test_export_to_csv(self):
        """Test CSV export"""
        # Record some metrics
        self.collector.record_processing_time("test_op", 100, photo_id=123, success=True)
        self.collector.record_processing_time("test_op", 200, photo_id=456, success=True)
        
        # Export
        with tempfile.TemporaryDirectory() as tmpdir:
            self.collector.config['export_directory'] = tmpdir
            filepath = self.collector.export_to_csv('processing')
            
            # Verify file exists
            self.assertTrue(os.path.exists(filepath))
            
            # Verify content
            with open(filepath, 'r', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['operation'], 'test_op')
            self.assertEqual(rows[0]['photo_id'], '123')
    
    def test_clear_metrics(self):
        """Test clearing metrics"""
        # Record metrics
        self.collector.record_processing_time("test_op", 100, success=True)
        self.collector.record_memory_usage()
        
        # Clear specific type
        self.collector.clear_metrics('processing')
        self.assertEqual(len(self.collector.processing_times), 0)
        self.assertGreater(len(self.collector.memory_usage), 0)
        
        # Clear all
        self.collector.clear_metrics()
        self.assertEqual(len(self.collector.processing_times), 0)
        self.assertEqual(len(self.collector.memory_usage), 0)
    
    def test_metrics_count(self):
        """Test getting metrics count"""
        self.collector.record_processing_time("test_op", 100, success=True)
        self.collector.record_memory_usage()
        
        counts = self.collector.get_metrics_count()
        
        self.assertEqual(counts['processing_times'], 1)
        self.assertEqual(counts['memory_usage'], 1)
        self.assertEqual(counts['total'], 2)
    
    def test_history_trimming(self):
        """Test automatic history trimming"""
        # Set small max size
        self.collector.config['max_history_size'] = 10
        
        # Record more than max
        for i in range(15):
            self.collector.record_processing_time("test_op", 100, success=True)
        
        # Should be trimmed to max
        self.assertEqual(len(self.collector.processing_times), 10)
    
    def test_background_monitoring(self):
        """Test background monitoring"""
        # Configure fast sampling
        self.collector.config['memory_sample_interval'] = 0.5
        
        # Start monitoring
        self.collector.start_monitoring()
        self.assertTrue(self.collector.is_monitoring)
        
        # Wait for some samples
        time.sleep(1.5)
        
        # Stop monitoring
        self.collector.stop_monitoring()
        self.assertFalse(self.collector.is_monitoring)
        
        # Should have collected some samples
        self.assertGreater(len(self.collector.memory_usage), 0)
    
    def test_config_update(self):
        """Test configuration update"""
        original_size = self.collector.config['max_history_size']
        
        success = self.collector.update_config({
            'max_history_size': 5000
        })
        
        self.assertTrue(success)
        self.assertEqual(self.collector.config['max_history_size'], 5000)
        self.assertNotEqual(self.collector.config['max_history_size'], original_size)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions"""
    
    def setUp(self):
        """Set up"""
        from performance_metrics import get_performance_metrics_collector
        self.collector = get_performance_metrics_collector()
        self.collector.clear_metrics()
    
    def tearDown(self):
        """Clean up"""
        self.collector.clear_metrics()
    
    def test_measure_performance(self):
        """Test measure_performance function"""
        with measure_performance("test_op", photo_id=123):
            time.sleep(0.05)
        
        self.assertEqual(len(self.collector.processing_times), 1)
        metric = self.collector.processing_times[0]
        self.assertEqual(metric.operation, "test_op")
        self.assertEqual(metric.photo_id, 123)
    
    def test_record_processing_time_function(self):
        """Test record_processing_time function"""
        record_processing_time("test_op", 100.5, photo_id=456)
        
        self.assertEqual(len(self.collector.processing_times), 1)
        metric = self.collector.processing_times[0]
        self.assertEqual(metric.operation, "test_op")
        self.assertEqual(metric.duration_ms, 100.5)
    
    def test_record_memory_usage_function(self):
        """Test record_memory_usage function"""
        record_memory_usage("test_op")
        
        self.assertEqual(len(self.collector.memory_usage), 1)
    
    def test_record_gpu_usage_function(self):
        """Test record_gpu_usage function"""
        record_gpu_usage("test_op")
        
        # GPU may not be available
        if self.collector.gpu_available:
            self.assertGreater(len(self.collector.gpu_usage), 0)


class TestMetricDataClasses(unittest.TestCase):
    """Test metric data classes"""
    
    def test_processing_time_metric_to_dict(self):
        """Test ProcessingTimeMetric to_dict"""
        metric = ProcessingTimeMetric(
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            operation="test_op",
            duration_ms=100.5,
            photo_id=123,
            job_id="job_001",
            stage="test",
            success=True,
            error_message=None
        )
        
        d = metric.to_dict()
        
        self.assertEqual(d['operation'], "test_op")
        self.assertEqual(d['duration_ms'], 100.5)
        self.assertEqual(d['photo_id'], 123)
        self.assertEqual(d['job_id'], "job_001")
        self.assertTrue(d['success'])
    
    def test_memory_usage_metric_to_dict(self):
        """Test MemoryUsageMetric to_dict"""
        metric = MemoryUsageMetric(
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            total_mb=16384.0,
            used_mb=8192.0,
            available_mb=8192.0,
            percent=50.0,
            process_memory_mb=512.0,
            operation="test_op"
        )
        
        d = metric.to_dict()
        
        self.assertEqual(d['total_mb'], 16384.0)
        self.assertEqual(d['used_mb'], 8192.0)
        self.assertEqual(d['percent'], 50.0)
        self.assertEqual(d['operation'], "test_op")
    
    def test_gpu_usage_metric_to_dict(self):
        """Test GPUUsageMetric to_dict"""
        metric = GPUUsageMetric(
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            gpu_id=0,
            load_percent=75.0,
            memory_used_mb=4096.0,
            memory_total_mb=8192.0,
            memory_percent=50.0,
            temperature_celsius=65.0,
            operation="test_op"
        )
        
        d = metric.to_dict()
        
        self.assertEqual(d['gpu_id'], 0)
        self.assertEqual(d['load_percent'], 75.0)
        self.assertEqual(d['temperature_celsius'], 65.0)
        self.assertEqual(d['operation'], "test_op")


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
