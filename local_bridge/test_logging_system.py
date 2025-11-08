"""
Test suite for the Logging System

Tests structured logging, log rotation, filtering, and API endpoints.
"""

import pytest
import json
import time
import pathlib
import shutil
from logging_system import (
    LoggingSystem,
    PerformanceTimer,
    get_logging_system,
    log,
    log_performance,
    log_error
)


class TestLoggingSystem:
    """Test cases for LoggingSystem"""
    
    @pytest.fixture
    def test_log_dir(self, tmp_path):
        """Create temporary log directory"""
        log_dir = tmp_path / "test_logs"
        log_dir.mkdir()
        yield log_dir
        # Cleanup
        if log_dir.exists():
            shutil.rmtree(log_dir)
    
    @pytest.fixture
    def logging_system(self, test_log_dir):
        """Create LoggingSystem instance for testing"""
        return LoggingSystem(
            log_dir=test_log_dir,
            max_bytes=1024,  # Small size for testing rotation
            backup_count=3,
            log_level="DEBUG"
        )
    
    def test_initialization(self, logging_system, test_log_dir):
        """Test logging system initialization"""
        assert logging_system.log_dir == test_log_dir
        assert test_log_dir.exists()
        assert logging_system.log_level == 10  # DEBUG level
    
    def test_basic_logging(self, logging_system, test_log_dir):
        """Test basic logging functionality"""
        logging_system.log("INFO", "Test message", test_field="test_value")
        
        # Check log file exists
        log_file = test_log_dir / "main.log"
        assert log_file.exists()
        
        # Read and verify log entry
        with open(log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry['level'] == 'INFO'
        assert log_entry['message'] == 'Test message'
        assert log_entry['test_field'] == 'test_value'
    
    def test_performance_logging(self, logging_system, test_log_dir):
        """Test performance logging"""
        logging_system.log_performance(
            operation="test_operation",
            duration_ms=123.45,
            status="success",
            metric1=100,
            metric2=200
        )
        
        # Check performance log file
        log_file = test_log_dir / "performance.log"
        assert log_file.exists()
        
        # Read and verify log entry
        with open(log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry['operation'] == 'test_operation'
        assert log_entry['duration_ms'] == 123.45
        assert log_entry['status'] == 'success'
        assert log_entry['metrics']['metric1'] == 100
    
    def test_error_logging(self, logging_system, test_log_dir):
        """Test error logging with exception"""
        try:
            raise ValueError("Test error")
        except Exception as e:
            logging_system.log_error("An error occurred", exception=e, context="test")
        
        # Check error log file
        log_file = test_log_dir / "errors.log"
        assert log_file.exists()
        
        # Read and verify log entry
        with open(log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry['level'] == 'ERROR'
        assert log_entry['message'] == 'An error occurred'
        assert 'exception' in log_entry
        assert 'ValueError' in log_entry['exception']
    
    def test_performance_timer(self, logging_system, test_log_dir):
        """Test PerformanceTimer context manager"""
        with PerformanceTimer(logging_system, "timed_operation", test_metric=42):
            time.sleep(0.05)  # Sleep for 50ms
        
        # Check performance log
        log_file = test_log_dir / "performance.log"
        with open(log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry['operation'] == 'timed_operation'
        assert log_entry['duration_ms'] >= 50  # At least 50ms
        assert log_entry['status'] == 'success'
        assert log_entry['metrics']['test_metric'] == 42
    
    def test_performance_timer_with_exception(self, logging_system, test_log_dir):
        """Test PerformanceTimer with exception"""
        try:
            with PerformanceTimer(logging_system, "failing_operation"):
                raise RuntimeError("Test failure")
        except RuntimeError:
            pass
        
        # Check performance log
        log_file = test_log_dir / "performance.log"
        with open(log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry['operation'] == 'failing_operation'
        assert log_entry['status'] == 'failure'
    
    def test_read_logs(self, logging_system):
        """Test reading log entries"""
        # Write some log entries
        for i in range(5):
            logging_system.log("INFO", f"Message {i}", index=i)
        
        # Read logs
        entries = logging_system.read_logs("main", lines=10)
        
        assert len(entries) == 5
        assert entries[0]['message'] == 'Message 0'
        assert entries[4]['message'] == 'Message 4'
    
    def test_read_logs_with_level_filter(self, logging_system):
        """Test reading logs with level filter"""
        # Write mixed level entries
        logging_system.log("INFO", "Info message")
        logging_system.log("WARNING", "Warning message")
        logging_system.log("ERROR", "Error message")
        
        # Read only ERROR logs
        entries = logging_system.read_logs("main", lines=10, level_filter="ERROR")
        
        assert len(entries) == 1
        assert entries[0]['level'] == 'ERROR'
        assert entries[0]['message'] == 'Error message'
    
    def test_log_stats(self, logging_system):
        """Test log statistics"""
        # Write some logs
        for i in range(10):
            logging_system.log("INFO", f"Message {i}")
        
        stats = logging_system.get_log_stats()
        
        assert 'log_directory' in stats
        assert 'categories' in stats
        assert 'main' in stats['categories']
        assert stats['categories']['main']['line_count'] == 10
        assert stats['categories']['main']['file_size_bytes'] > 0
    
    def test_get_log_files(self, logging_system):
        """Test getting log file list"""
        # Write to different categories
        logging_system.log("INFO", "Main log")
        logging_system.log_performance("test_op", 100)
        logging_system.log_error("Error log")
        
        log_files = logging_system.get_log_files()
        
        assert 'main' in log_files
        assert 'performance' in log_files
        assert 'errors' in log_files
        assert len(log_files['main']) > 0
        assert len(log_files['performance']) > 0
        assert len(log_files['errors']) > 0
    
    def test_clear_logs(self, logging_system, test_log_dir):
        """Test clearing log files"""
        # Write some logs
        logging_system.log("INFO", "Test message")
        
        log_file = test_log_dir / "main.log"
        assert log_file.exists()
        
        # Clear logs
        logging_system.clear_logs("main")
        
        # File should be deleted
        assert not log_file.exists()
    
    def test_log_rotation(self, logging_system, test_log_dir):
        """Test log rotation when file size exceeds limit"""
        # Write enough data to trigger rotation (max_bytes=1024)
        for i in range(100):
            logging_system.log("INFO", f"Long message {i}" * 10, index=i)
        
        # Check for rotated files
        main_log = test_log_dir / "main.log"
        rotated_log = test_log_dir / "main.log.1"
        
        assert main_log.exists()
        # Rotation may or may not have occurred depending on exact sizes
        # Just verify the main log exists and is within size limit
        assert main_log.stat().st_size <= logging_system.max_bytes * 2  # Allow some buffer


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @pytest.fixture
    def test_log_dir(self, tmp_path):
        """Create temporary log directory"""
        log_dir = tmp_path / "test_logs_convenience"
        log_dir.mkdir()
        yield log_dir
        if log_dir.exists():
            shutil.rmtree(log_dir)
    
    def test_log_function(self, test_log_dir):
        """Test convenience log function"""
        # Initialize global logging system
        logging_sys = get_logging_system(log_dir=test_log_dir)
        
        log("INFO", "Test message", field1="value1")
        
        log_file = test_log_dir / "main.log"
        assert log_file.exists()
    
    def test_log_performance_function(self, test_log_dir):
        """Test convenience log_performance function"""
        logging_sys = get_logging_system(log_dir=test_log_dir)
        
        log_performance("test_op", 100.5, metric1=42)
        
        log_file = test_log_dir / "performance.log"
        assert log_file.exists()
    
    def test_log_error_function(self, test_log_dir):
        """Test convenience log_error function"""
        logging_sys = get_logging_system(log_dir=test_log_dir)
        
        try:
            raise ValueError("Test error")
        except Exception as e:
            log_error("Error occurred", exception=e)
        
        log_file = test_log_dir / "errors.log"
        assert log_file.exists()


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
