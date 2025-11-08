# Logging System Documentation

## Overview

The Junmai AutoDev logging system provides comprehensive structured logging with multiple log files, automatic rotation, level filtering, and API endpoints for log viewing.

**Requirements Implemented:** 14.2, 14.4

## Features

### 1. Structured Logging
- **JSON Format**: All logs are written in structured JSON format for easy parsing and analysis
- **Multiple Categories**: Separate log files for different purposes:
  - `main.log`: General application logs
  - `performance.log`: Performance metrics and timing data
  - `errors.log`: Error logs with exception details

### 2. Log Rotation
- **Automatic Rotation**: Log files automatically rotate when they reach the configured size limit (default: 10MB)
- **Backup Management**: Keeps a configurable number of backup files (default: 5)
- **No Data Loss**: Seamless rotation without losing log entries

### 3. Log Level Filtering
- **Standard Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Configurable**: Set minimum log level via configuration
- **Runtime Filtering**: Filter logs by level when reading via API

### 4. API Endpoints
- **View Logs**: Retrieve log entries with filtering
- **Statistics**: Get log file statistics
- **Download**: Download log files
- **Clear**: Clear log files (with caution)

## Architecture

```
┌─────────────────────────────────────────┐
│         Application Code                │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│      LoggingSystem                      │
│  ┌─────────────────────────────────┐   │
│  │  Main Logger                    │   │
│  │  - StructuredFormatter          │   │
│  │  - RotatingFileHandler          │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  Performance Logger             │   │
│  │  - PerformanceFormatter         │   │
│  │  - RotatingFileHandler          │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  Error Logger                   │   │
│  │  - StructuredFormatter          │   │
│  │  - RotatingFileHandler          │   │
│  └─────────────────────────────────┘   │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Log Files                       │
│  - logs/main.log                        │
│  - logs/performance.log                 │
│  - logs/errors.log                      │
│  - logs/*.log.1, *.log.2, ... (backups) │
└─────────────────────────────────────────┘
```

## Usage

### Basic Logging

```python
from logging_system import get_logging_system

# Get logging system instance
logging_system = get_logging_system(log_level="INFO")

# Log a message
logging_system.log("INFO", "Application started", version="2.0", user="admin")

# Log with different levels
logging_system.log("DEBUG", "Debug information", component="database")
logging_system.log("WARNING", "Resource usage high", cpu_percent=85)
logging_system.log("ERROR", "Operation failed", operation="import", reason="timeout")
```

### Performance Logging

```python
# Log performance metrics
logging_system.log_performance(
    operation="photo_processing",
    duration_ms=1234.56,
    status="success",
    photo_count=10,
    avg_score=4.2
)

# Using PerformanceTimer context manager
from logging_system import PerformanceTimer

with PerformanceTimer(logging_system, "batch_processing", batch_size=100):
    # Your code here
    process_photos()
# Automatically logs duration and status
```

### Error Logging

```python
# Log error with exception
try:
    risky_operation()
except Exception as e:
    logging_system.log_error(
        "Operation failed",
        exception=e,
        context="photo_import",
        photo_id="IMG_1234"
    )
```

### Convenience Functions

```python
from logging_system import log, log_performance, log_error

# Simple logging
log("INFO", "Message", field1="value1")

# Performance logging
log_performance("operation_name", 123.45, metric1=100)

# Error logging
try:
    raise ValueError("Error")
except Exception as e:
    log_error("Error occurred", exception=e)
```

## Log Format

### Main Log Entry
```json
{
  "timestamp": "2025-11-08T14:32:15.123456",
  "level": "INFO",
  "logger": "junmai.main",
  "message": "Job created successfully",
  "module": "app",
  "function": "create_job",
  "line": 45,
  "job_id": "abc123",
  "user": "admin"
}
```

### Performance Log Entry
```json
{
  "timestamp": "2025-11-08T14:32:15.123456",
  "operation": "photo_processing",
  "duration_ms": 1234.56,
  "status": "success",
  "message": "photo_processing completed",
  "metrics": {
    "photo_count": 10,
    "avg_score": 4.2
  }
}
```

### Error Log Entry
```json
{
  "timestamp": "2025-11-08T14:32:15.123456",
  "level": "ERROR",
  "logger": "junmai.error",
  "message": "Failed to process photo",
  "module": "processor",
  "function": "process_photo",
  "line": 123,
  "exception": "ValueError: Invalid photo format\n  File ...",
  "photo_id": "IMG_1234",
  "context": "import"
}
```

## API Endpoints

### GET /logs
Retrieve log entries with optional filtering.

**Query Parameters:**
- `category` (string): Log category - `main`, `performance`, or `errors` (default: `main`)
- `lines` (integer): Number of lines to return (default: 100, max: 10000)
- `level` (string): Filter by log level - `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

**Example:**
```bash
curl "http://localhost:5100/logs?category=main&lines=50&level=ERROR"
```

**Response:**
```json
{
  "category": "main",
  "count": 5,
  "entries": [
    {
      "timestamp": "2025-11-08T14:32:15.123456",
      "level": "ERROR",
      "message": "Operation failed",
      ...
    }
  ]
}
```

### GET /logs/stats
Get statistics about log files.

**Example:**
```bash
curl "http://localhost:5100/logs/stats"
```

**Response:**
```json
{
  "log_directory": "/path/to/logs",
  "categories": {
    "main": {
      "file_size_bytes": 1048576,
      "file_size_mb": 1.0,
      "line_count": 1234,
      "path": "/path/to/logs/main.log"
    },
    "performance": { ... },
    "errors": { ... }
  }
}
```

### GET /logs/files
Get list of all log files organized by category.

**Example:**
```bash
curl "http://localhost:5100/logs/files"
```

**Response:**
```json
{
  "main": [
    "/path/to/logs/main.log",
    "/path/to/logs/main.log.1",
    "/path/to/logs/main.log.2"
  ],
  "performance": [ ... ],
  "errors": [ ... ]
}
```

### GET /logs/download/{category}
Download a specific log file.

**Path Parameters:**
- `category` (string): Log category - `main`, `performance`, or `errors`

**Example:**
```bash
curl "http://localhost:5100/logs/download/main" -O
```

### POST /logs/clear
Clear log files.

**Request Body:**
```json
{
  "category": "main"  // Optional: specific category to clear
}
```

**Example:**
```bash
# Clear specific category
curl -X POST "http://localhost:5100/logs/clear" \
  -H "Content-Type: application/json" \
  -d '{"category": "main"}'

# Clear all logs
curl -X POST "http://localhost:5100/logs/clear" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Configuration

The logging system can be configured via the system configuration:

```json
{
  "system": {
    "log_level": "INFO"  // DEBUG, INFO, WARNING, ERROR, CRITICAL
  }
}
```

### Programmatic Configuration

```python
from logging_system import LoggingSystem
import pathlib

logging_system = LoggingSystem(
    log_dir=pathlib.Path("/custom/log/path"),
    max_bytes=20 * 1024 * 1024,  # 20MB per file
    backup_count=10,              # Keep 10 backup files
    log_level="DEBUG"             # Minimum log level
)
```

## Best Practices

### 1. Use Appropriate Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors that may cause system failure

### 2. Include Context
Always include relevant context in log messages:
```python
logging_system.log("INFO", "Photo processed", 
                   photo_id="IMG_1234",
                   session_id="session-abc",
                   duration_ms=123.45)
```

### 3. Use Performance Timers
For operations that need timing:
```python
with PerformanceTimer(logging_system, "operation_name", batch_size=100):
    # Your code
    pass
```

### 4. Log Errors with Exceptions
Always include exception details:
```python
try:
    risky_operation()
except Exception as e:
    logging_system.log_error("Operation failed", exception=e, context="...")
```

### 5. Monitor Log File Sizes
Regularly check log statistics to ensure rotation is working:
```python
stats = logging_system.get_log_stats()
print(f"Main log size: {stats['categories']['main']['file_size_mb']} MB")
```

## Troubleshooting

### Log Files Not Created
- Check that the log directory exists and is writable
- Verify log level is set appropriately (DEBUG logs won't appear if level is INFO)

### Log Rotation Not Working
- Check `max_bytes` configuration
- Verify disk space is available
- Check file permissions

### Performance Impact
- Use appropriate log levels (avoid DEBUG in production)
- Monitor log file sizes
- Consider increasing rotation size if files rotate too frequently

### Reading Logs Programmatically
```python
# Read recent error logs
entries = logging_system.read_logs("errors", lines=100)

for entry in entries:
    print(f"{entry['timestamp']}: {entry['message']}")
```

## Integration with Existing Code

The logging system is integrated into `app.py` and automatically logs:
- All API requests and responses
- Job creation and processing
- Configuration changes
- Errors and exceptions
- Performance metrics

Example from `app.py`:
```python
from logging_system import get_logging_system, PerformanceTimer

logging_system = get_logging_system(log_level="INFO")

@app.route("/job", methods=["POST"])
def create_job():
    with PerformanceTimer(logging_system, "create_job"):
        logging_system.log("INFO", "Received request to /job endpoint")
        # ... rest of the code
```

## Testing

Run the test suite:
```bash
cd local_bridge
python -m pytest test_logging_system.py -v
```

Or run the standalone test:
```bash
python logging_system.py
```

## Future Enhancements

Potential improvements for future versions:
- Remote log shipping (e.g., to Elasticsearch, Splunk)
- Real-time log streaming via WebSocket
- Log aggregation across multiple instances
- Advanced log analysis and alerting
- Log compression for archived files
- Configurable log retention policies

## References

- Requirements: 14.2 (構造化ログ機能), 14.4 (ログビューアーAPI)
- Design Document: `.kiro/specs/ui-ux-enhancement/design.md`
- Python logging documentation: https://docs.python.org/3/library/logging.html
