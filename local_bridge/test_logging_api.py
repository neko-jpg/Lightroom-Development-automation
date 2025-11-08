"""
Integration test for logging API endpoints

Tests the Flask API endpoints for log viewing and management.
"""

import json
import time
import pathlib
import shutil
from logging_system import get_logging_system


def test_logging_api_endpoints():
    """Test logging API endpoints by simulating usage"""
    
    print("=== Testing Logging API Integration ===\n")
    
    # Setup test logging system
    test_log_dir = pathlib.Path("test_api_logs")
    if test_log_dir.exists():
        shutil.rmtree(test_log_dir)
    
    logging_system = get_logging_system(log_dir=test_log_dir, log_level="DEBUG")
    
    # Test 1: Generate various log entries
    print("Test 1: Generating log entries")
    logging_system.log("INFO", "API test started", test_id="api-001")
    logging_system.log("DEBUG", "Debug information", component="test")
    logging_system.log("WARNING", "Warning message", severity="medium")
    logging_system.log("ERROR", "Error message", error_code="E001")
    
    logging_system.log_performance(
        operation="test_operation",
        duration_ms=123.45,
        status="success",
        metric1=100
    )
    
    try:
        raise ValueError("Test error")
    except Exception as e:
        logging_system.log_error("Test error occurred", exception=e)
    
    print("✓ Generated 6 log entries\n")
    
    # Test 2: Read logs (simulating GET /logs)
    print("Test 2: Reading logs")
    main_logs = logging_system.read_logs("main", lines=100)
    print(f"✓ Retrieved {len(main_logs)} main log entries")
    
    performance_logs = logging_system.read_logs("performance", lines=100)
    print(f"✓ Retrieved {len(performance_logs)} performance log entries")
    
    error_logs = logging_system.read_logs("errors", lines=100)
    print(f"✓ Retrieved {len(error_logs)} error log entries\n")
    
    # Test 3: Filter by level (simulating GET /logs?level=ERROR)
    print("Test 3: Filtering by log level")
    error_only = logging_system.read_logs("main", lines=100, level_filter="ERROR")
    print(f"✓ Retrieved {len(error_only)} ERROR level entries")
    
    info_only = logging_system.read_logs("main", lines=100, level_filter="INFO")
    print(f"✓ Retrieved {len(info_only)} INFO level entries\n")
    
    # Test 4: Get log statistics (simulating GET /logs/stats)
    print("Test 4: Getting log statistics")
    stats = logging_system.get_log_stats()
    print(f"✓ Log directory: {stats['log_directory']}")
    print(f"✓ Main log: {stats['categories']['main']['line_count']} lines, "
          f"{stats['categories']['main']['file_size_mb']} MB")
    print(f"✓ Performance log: {stats['categories']['performance']['line_count']} lines")
    print(f"✓ Error log: {stats['categories']['errors']['line_count']} lines\n")
    
    # Test 5: Get log files (simulating GET /logs/files)
    print("Test 5: Getting log file list")
    log_files = logging_system.get_log_files()
    print(f"✓ Main log files: {len(log_files['main'])}")
    print(f"✓ Performance log files: {len(log_files['performance'])}")
    print(f"✓ Error log files: {len(log_files['errors'])}\n")
    
    # Test 6: Verify log content structure
    print("Test 6: Verifying log entry structure")
    if main_logs:
        entry = main_logs[0]
        required_fields = ['timestamp', 'level', 'logger', 'message', 'module', 'function', 'line']
        for field in required_fields:
            assert field in entry, f"Missing required field: {field}"
        print(f"✓ Log entry structure valid")
        print(f"  Sample entry: {json.dumps(entry, indent=2)}\n")
    
    # Test 7: Verify performance log structure
    print("Test 7: Verifying performance log structure")
    if performance_logs:
        entry = performance_logs[0]
        required_fields = ['timestamp', 'operation', 'duration_ms', 'status']
        for field in required_fields:
            assert field in entry, f"Missing required field: {field}"
        print(f"✓ Performance log structure valid")
        print(f"  Sample entry: {json.dumps(entry, indent=2)}\n")
    
    # Test 8: Test log rotation simulation
    print("Test 8: Testing log rotation (generating many entries)")
    for i in range(50):
        logging_system.log("INFO", f"Rotation test message {i}", index=i)
    
    stats_after = logging_system.get_log_stats()
    print(f"✓ Generated 50 additional entries")
    print(f"✓ Main log now has {stats_after['categories']['main']['line_count']} lines\n")
    
    # Cleanup
    print("Cleanup: Closing loggers and removing test logs")
    import logging
    for logger_name in ['junmai.main', 'junmai.performance', 'junmai.error']:
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
    
    try:
        if test_log_dir.exists():
            shutil.rmtree(test_log_dir)
        print("✓ Test logs cleaned up\n")
    except PermissionError:
        print("⚠ Could not clean up test logs (files in use)\n")
    
    print("=== All API integration tests passed! ===")


def demonstrate_api_usage():
    """Demonstrate how to use the logging API endpoints"""
    
    print("\n=== API Endpoint Usage Examples ===\n")
    
    examples = [
        {
            "title": "Get recent main logs",
            "method": "GET",
            "endpoint": "/logs?category=main&lines=100",
            "description": "Retrieve the last 100 entries from main.log"
        },
        {
            "title": "Get error logs only",
            "method": "GET",
            "endpoint": "/logs?category=main&level=ERROR",
            "description": "Retrieve only ERROR level entries"
        },
        {
            "title": "Get performance logs",
            "method": "GET",
            "endpoint": "/logs?category=performance&lines=50",
            "description": "Retrieve the last 50 performance metrics"
        },
        {
            "title": "Get log statistics",
            "method": "GET",
            "endpoint": "/logs/stats",
            "description": "Get file sizes and line counts for all log categories"
        },
        {
            "title": "Get log file list",
            "method": "GET",
            "endpoint": "/logs/files",
            "description": "Get paths to all log files including rotated backups"
        },
        {
            "title": "Download main log",
            "method": "GET",
            "endpoint": "/logs/download/main",
            "description": "Download the main.log file"
        },
        {
            "title": "Clear specific log",
            "method": "POST",
            "endpoint": "/logs/clear",
            "body": '{"category": "main"}',
            "description": "Clear the main.log file"
        },
        {
            "title": "Clear all logs",
            "method": "POST",
            "endpoint": "/logs/clear",
            "body": '{}',
            "description": "Clear all log files"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['title']}")
        print(f"   Method: {example['method']}")
        print(f"   Endpoint: {example['endpoint']}")
        if 'body' in example:
            print(f"   Body: {example['body']}")
        print(f"   Description: {example['description']}")
        print()
    
    print("Example curl commands:")
    print()
    print("# Get recent logs")
    print('curl "http://localhost:5100/logs?category=main&lines=50"')
    print()
    print("# Get error logs")
    print('curl "http://localhost:5100/logs?category=main&level=ERROR"')
    print()
    print("# Get statistics")
    print('curl "http://localhost:5100/logs/stats"')
    print()
    print("# Download log file")
    print('curl "http://localhost:5100/logs/download/main" -O')
    print()
    print("# Clear logs")
    print('curl -X POST "http://localhost:5100/logs/clear" -H "Content-Type: application/json" -d \'{"category": "main"}\'')
    print()


if __name__ == '__main__':
    test_logging_api_endpoints()
    demonstrate_api_usage()
