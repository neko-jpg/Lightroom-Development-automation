"""
Structured Logging System for Junmai AutoDev

This module provides comprehensive logging functionality including:
- Structured logging to multiple log files (main.log, performance.log, errors.log)
- Log rotation with configurable size and backup count
- Log level filtering
- JSON-formatted structured logs
- Performance metrics tracking

Requirements: 14.2, 14.4
"""

import logging
import logging.handlers
import json
import pathlib
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


class LogCategory(Enum):
    """Log categories for structured logging"""
    MAIN = "main"
    PERFORMANCE = "performance"
    ERROR = "error"


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured JSON
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class PerformanceFormatter(logging.Formatter):
    """
    Formatter for performance logs with metrics
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format performance log record
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted performance log
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "operation": getattr(record, 'operation', 'unknown'),
            "duration_ms": getattr(record, 'duration_ms', 0),
            "status": getattr(record, 'status', 'unknown'),
            "message": record.getMessage()
        }
        
        # Add metrics if present
        if hasattr(record, 'metrics'):
            log_data["metrics"] = record.metrics
        
        return json.dumps(log_data, ensure_ascii=False)


class LoggingSystem:
    """
    Centralized logging system for Junmai AutoDev
    
    Manages multiple log files with rotation, filtering, and structured output.
    """
    
    def __init__(
        self,
        log_dir: Optional[pathlib.Path] = None,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        log_level: str = "INFO"
    ):
        """
        Initialize logging system
        
        Args:
            log_dir: Directory for log files. If None, uses default location.
            max_bytes: Maximum size of each log file before rotation
            backup_count: Number of backup files to keep
            log_level: Default logging level
        """
        if log_dir is None:
            log_dir = pathlib.Path(__file__).parent / "logs"
        
        self.log_dir = pathlib.Path(log_dir)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize loggers
        self.main_logger = self._setup_logger(
            "junmai.main",
            "main.log",
            StructuredFormatter()
        )
        
        self.performance_logger = self._setup_logger(
            "junmai.performance",
            "performance.log",
            PerformanceFormatter()
        )
        
        self.error_logger = self._setup_logger(
            "junmai.error",
            "errors.log",
            StructuredFormatter(),
            level=logging.ERROR
        )
        
        # Console handler for development
        self._setup_console_handler()
    
    def _setup_logger(
        self,
        name: str,
        filename: str,
        formatter: logging.Formatter,
        level: Optional[int] = None
    ) -> logging.Logger:
        """
        Setup a logger with rotating file handler
        
        Args:
            name: Logger name
            filename: Log file name
            formatter: Log formatter
            level: Logging level (uses default if None)
            
        Returns:
            Configured logger
        """
        logger = logging.getLogger(name)
        logger.setLevel(level if level is not None else self.log_level)
        logger.propagate = False
        
        # Remove existing handlers
        logger.handlers.clear()
        
        # Create rotating file handler
        log_path = self.log_dir / filename
        handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _setup_console_handler(self) -> None:
        """Setup console handler for main logger"""
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(self.log_level)
        self.main_logger.addHandler(console_handler)
    
    def log(
        self,
        level: str,
        message: str,
        category: LogCategory = LogCategory.MAIN,
        **extra_fields
    ) -> None:
        """
        Log a message with optional extra fields
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            category: Log category
            **extra_fields: Additional fields to include in structured log
        """
        logger = self._get_logger(category)
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # Create log record with extra fields
        extra = {'extra_fields': extra_fields} if extra_fields else {}
        logger.log(log_level, message, extra=extra)
        
        # Also log errors to error logger
        if log_level >= logging.ERROR and category != LogCategory.ERROR:
            self.error_logger.log(log_level, message, extra=extra)
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        status: str = "success",
        message: str = "",
        **metrics
    ) -> None:
        """
        Log performance metrics
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            status: Operation status (success, failure, etc.)
            message: Optional message
            **metrics: Additional metrics to log
        """
        extra = {
            'operation': operation,
            'duration_ms': duration_ms,
            'status': status,
            'metrics': metrics
        }
        
        self.performance_logger.info(message or f"{operation} completed", extra=extra)
    
    def log_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        **extra_fields
    ) -> None:
        """
        Log an error with optional exception
        
        Args:
            message: Error message
            exception: Exception object
            **extra_fields: Additional fields
        """
        extra = {'extra_fields': extra_fields} if extra_fields else {}
        
        if exception:
            self.error_logger.error(message, exc_info=exception, extra=extra)
        else:
            self.error_logger.error(message, extra=extra)
    
    def _get_logger(self, category: LogCategory) -> logging.Logger:
        """Get logger for specified category"""
        if category == LogCategory.PERFORMANCE:
            return self.performance_logger
        elif category == LogCategory.ERROR:
            return self.error_logger
        else:
            return self.main_logger
    
    def get_log_files(self) -> Dict[str, List[pathlib.Path]]:
        """
        Get all log files organized by category
        
        Returns:
            Dictionary mapping category to list of log file paths
        """
        log_files = {
            "main": [],
            "performance": [],
            "errors": []
        }
        
        for category, base_name in [
            ("main", "main.log"),
            ("performance", "performance.log"),
            ("errors", "errors.log")
        ]:
            # Main log file
            main_file = self.log_dir / base_name
            if main_file.exists():
                log_files[category].append(main_file)
            
            # Rotated log files
            for i in range(1, self.backup_count + 1):
                rotated_file = self.log_dir / f"{base_name}.{i}"
                if rotated_file.exists():
                    log_files[category].append(rotated_file)
        
        return log_files
    
    def read_logs(
        self,
        category: str = "main",
        lines: int = 100,
        level_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Read and parse log entries
        
        Args:
            category: Log category (main, performance, errors)
            lines: Number of lines to read (from end)
            level_filter: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            List of parsed log entries
        """
        log_file = self.log_dir / f"{category}.log"
        
        if not log_file.exists():
            return []
        
        entries = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                # Read all lines
                all_lines = f.readlines()
                
                # Get last N lines
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                for line in recent_lines:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Apply level filter if specified
                        if level_filter and entry.get('level') != level_filter.upper():
                            continue
                        
                        entries.append(entry)
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue
        
        except Exception as e:
            self.log_error(f"Failed to read logs: {e}", exception=e)
        
        return entries
    
    def clear_logs(self, category: Optional[str] = None) -> None:
        """
        Clear log files
        
        Args:
            category: Specific category to clear, or None to clear all
        """
        categories = [category] if category else ["main", "performance", "errors"]
        
        for cat in categories:
            log_file = self.log_dir / f"{cat}.log"
            if log_file.exists():
                log_file.unlink()
                self.log("INFO", f"Cleared {cat} logs")
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get statistics about log files
        
        Returns:
            Dictionary with log statistics
        """
        stats = {
            "log_directory": str(self.log_dir),
            "categories": {}
        }
        
        for category in ["main", "performance", "errors"]:
            log_file = self.log_dir / f"{category}.log"
            
            if log_file.exists():
                file_size = log_file.stat().st_size
                
                # Count lines
                with open(log_file, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
                
                stats["categories"][category] = {
                    "file_size_bytes": file_size,
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                    "line_count": line_count,
                    "path": str(log_file)
                }
            else:
                stats["categories"][category] = {
                    "file_size_bytes": 0,
                    "file_size_mb": 0,
                    "line_count": 0,
                    "path": str(log_file)
                }
        
        return stats


class PerformanceTimer:
    """
    Context manager for timing operations and logging performance
    """
    
    def __init__(
        self,
        logging_system: LoggingSystem,
        operation: str,
        **metrics
    ):
        """
        Initialize performance timer
        
        Args:
            logging_system: LoggingSystem instance
            operation: Operation name
            **metrics: Additional metrics to log
        """
        self.logging_system = logging_system
        self.operation = operation
        self.metrics = metrics
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        """Start timing"""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log performance"""
        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000
        
        status = "failure" if exc_type else "success"
        
        self.logging_system.log_performance(
            operation=self.operation,
            duration_ms=duration_ms,
            status=status,
            **self.metrics
        )
        
        # Don't suppress exceptions
        return False


# Global logging system instance
_logging_system: Optional[LoggingSystem] = None


def get_logging_system(
    log_dir: Optional[pathlib.Path] = None,
    log_level: str = "INFO"
) -> LoggingSystem:
    """
    Get or create global logging system instance
    
    Args:
        log_dir: Log directory path
        log_level: Logging level
        
    Returns:
        LoggingSystem instance
    """
    global _logging_system
    
    if _logging_system is None:
        _logging_system = LoggingSystem(log_dir=log_dir, log_level=log_level)
    
    return _logging_system


def log(level: str, message: str, **extra_fields) -> None:
    """
    Convenience function for logging
    
    Args:
        level: Log level
        message: Log message
        **extra_fields: Additional fields
    """
    logging_system = get_logging_system()
    logging_system.log(level, message, **extra_fields)


def log_performance(operation: str, duration_ms: float, **metrics) -> None:
    """
    Convenience function for performance logging
    
    Args:
        operation: Operation name
        duration_ms: Duration in milliseconds
        **metrics: Additional metrics
    """
    logging_system = get_logging_system()
    logging_system.log_performance(operation, duration_ms, **metrics)


def log_error(message: str, exception: Optional[Exception] = None, **extra_fields) -> None:
    """
    Convenience function for error logging
    
    Args:
        message: Error message
        exception: Exception object
        **extra_fields: Additional fields
    """
    logging_system = get_logging_system()
    logging_system.log_error(message, exception, **extra_fields)


if __name__ == '__main__':
    # Test the logging system
    print("=== Testing Logging System ===\n")
    
    # Initialize logging system
    log_sys = LoggingSystem(log_dir=pathlib.Path("test_logs"), log_level="DEBUG")
    
    # Test 1: Basic logging
    print("Test 1: Basic logging")
    log_sys.log("INFO", "System started", job_id="test-123", user="admin")
    log_sys.log("DEBUG", "Debug message", component="test")
    log_sys.log("WARNING", "Warning message", severity="medium")
    print("✓ Basic logs written\n")
    
    # Test 2: Performance logging
    print("Test 2: Performance logging")
    log_sys.log_performance(
        operation="photo_processing",
        duration_ms=1234.56,
        status="success",
        photo_count=10,
        avg_score=4.2
    )
    print("✓ Performance log written\n")
    
    # Test 3: Error logging
    print("Test 3: Error logging")
    try:
        raise ValueError("Test error")
    except Exception as e:
        log_sys.log_error("An error occurred", exception=e, context="test")
    print("✓ Error log written\n")
    
    # Test 4: Performance timer
    print("Test 4: Performance timer")
    with PerformanceTimer(log_sys, "test_operation", test_metric=42):
        time.sleep(0.1)
    print("✓ Performance timer logged\n")
    
    # Test 5: Read logs
    print("Test 5: Read logs")
    main_logs = log_sys.read_logs("main", lines=10)
    print(f"✓ Read {len(main_logs)} main log entries\n")
    
    # Test 6: Log statistics
    print("Test 6: Log statistics")
    stats = log_sys.get_log_stats()
    print(f"✓ Log stats: {json.dumps(stats, indent=2)}\n")
    
    # Cleanup - close loggers first to release file handles
    import shutil
    import logging
    
    # Close all handlers to release file locks
    for logger_name in ['junmai.main', 'junmai.performance', 'junmai.error']:
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
    
    # Now we can safely remove the directory
    if pathlib.Path("test_logs").exists():
        try:
            shutil.rmtree("test_logs")
            print("✓ Test logs cleaned up\n")
        except PermissionError:
            print("⚠ Could not clean up test logs (files in use)\n")
    
    print("=== All tests passed! ===")
