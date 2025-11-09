"""
Performance Metrics Collection System for Junmai AutoDev

This module provides comprehensive performance metrics collection including:
- Processing time measurement
- Memory usage tracking
- GPU usage tracking
- Metrics export functionality

Requirements: 12.1, 12.2, 15.4
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import csv
from pathlib import Path
from logging_system import get_logging_system

logging_system = get_logging_system()


class MetricType(Enum):
    """Types of performance metrics"""
    PROCESSING_TIME = "processing_time"
    MEMORY_USAGE = "memory_usage"
    GPU_USAGE = "gpu_usage"
    SYSTEM_RESOURCE = "system_resource"
    OPERATION = "operation"


@dataclass
class ProcessingTimeMetric:
    """Processing time metric"""
    timestamp: datetime
    operation: str
    duration_ms: float
    photo_id: Optional[int] = None
    job_id: Optional[str] = None
    stage: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'operation': self.operation,
            'duration_ms': self.duration_ms,
            'photo_id': self.photo_id,
            'job_id': self.job_id,
            'stage': self.stage,
            'success': self.success,
            'error_message': self.error_message
        }


@dataclass
class MemoryUsageMetric:
    """Memory usage metric"""
    timestamp: datetime
    total_mb: float
    used_mb: float
    available_mb: float
    percent: float
    process_memory_mb: float
    operation: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_mb': self.total_mb,
            'used_mb': self.used_mb,
            'available_mb': self.available_mb,
            'percent': self.percent,
            'process_memory_mb': self.process_memory_mb,
            'operation': self.operation
        }


@dataclass
class GPUUsageMetric:
    """GPU usage metric"""
    timestamp: datetime
    gpu_id: int
    load_percent: float
    memory_used_mb: float
    memory_total_mb: float
    memory_percent: float
    temperature_celsius: float
    operation: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'gpu_id': self.gpu_id,
            'load_percent': self.load_percent,
            'memory_used_mb': self.memory_used_mb,
            'memory_total_mb': self.memory_total_mb,
            'memory_percent': self.memory_percent,
            'temperature_celsius': self.temperature_celsius,
            'operation': self.operation
        }


class PerformanceTimer:
    """
    Context manager for measuring operation performance
    
    Usage:
        with PerformanceTimer("operation_name") as timer:
            # do work
            pass
        print(f"Duration: {timer.duration_ms}ms")
    """
    
    def __init__(
        self,
        operation: str,
        photo_id: Optional[int] = None,
        job_id: Optional[str] = None,
        stage: Optional[str] = None,
        auto_record: bool = True
    ):
        """
        Initialize performance timer
        
        Args:
            operation: Operation name
            photo_id: Associated photo ID
            job_id: Associated job ID
            stage: Processing stage
            auto_record: Automatically record metric on exit
        """
        self.operation = operation
        self.photo_id = photo_id
        self.job_id = job_id
        self.stage = stage
        self.auto_record = auto_record
        
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration_ms: Optional[float] = None
        self.success = True
        self.error_message: Optional[str] = None
    
    def __enter__(self):
        """Start timer"""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and record metric"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        
        if exc_type is not None:
            self.success = False
            self.error_message = str(exc_val)
        
        if self.auto_record:
            metrics_collector = get_performance_metrics_collector()
            metrics_collector.record_processing_time(
                operation=self.operation,
                duration_ms=self.duration_ms,
                photo_id=self.photo_id,
                job_id=self.job_id,
                stage=self.stage,
                success=self.success,
                error_message=self.error_message
            )
        
        return False  # Don't suppress exceptions


class PerformanceMetricsCollector:
    """
    Comprehensive performance metrics collection system
    
    Features:
    - Processing time measurement
    - Memory usage tracking
    - GPU usage tracking
    - Metrics aggregation and analysis
    - Export to JSON/CSV
    
    Requirements: 12.1, 12.2, 15.4
    """
    
    def __init__(self):
        """Initialize metrics collector"""
        self.config = {
            'max_history_size': 10000,  # Keep last 10000 metrics
            'auto_export_interval': 3600,  # Auto-export every hour
            'export_directory': 'data/metrics',
            'enable_gpu_tracking': True,
            'enable_memory_tracking': True,
            'memory_sample_interval': 60,  # Sample memory every 60 seconds
        }
        
        # Metrics storage
        self.processing_times: List[ProcessingTimeMetric] = []
        self.memory_usage: List[MemoryUsageMetric] = []
        self.gpu_usage: List[GPUUsageMetric] = []
        
        # Locks for thread safety
        self.processing_lock = threading.Lock()
        self.memory_lock = threading.Lock()
        self.gpu_lock = threading.Lock()
        
        # Background monitoring
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Process handle for memory tracking
        self.process = psutil.Process()
        
        # GPU availability
        self.gpu_available = self._check_gpu_availability()
        
        # Create export directory
        Path(self.config['export_directory']).mkdir(parents=True, exist_ok=True)
        
        logging_system.log("INFO", "Performance metrics collector initialized",
                          gpu_available=self.gpu_available)
    
    def _check_gpu_availability(self) -> bool:
        """Check if GPU monitoring is available"""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            return len(gpus) > 0
        except ImportError:
            return False
        except Exception:
            return False
    
    def record_processing_time(
        self,
        operation: str,
        duration_ms: float,
        photo_id: Optional[int] = None,
        job_id: Optional[str] = None,
        stage: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Record processing time metric
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            photo_id: Associated photo ID
            job_id: Associated job ID
            stage: Processing stage
            success: Whether operation succeeded
            error_message: Error message if failed
            
        Requirements: 12.1
        """
        metric = ProcessingTimeMetric(
            timestamp=datetime.now(),
            operation=operation,
            duration_ms=duration_ms,
            photo_id=photo_id,
            job_id=job_id,
            stage=stage,
            success=success,
            error_message=error_message
        )
        
        with self.processing_lock:
            self.processing_times.append(metric)
            self._trim_history(self.processing_times)
        
        # Log performance
        logging_system.log(
            "INFO" if success else "WARNING",
            "Processing time recorded",
            operation=operation,
            duration_ms=duration_ms,
            success=success
        )
    
    def record_memory_usage(self, operation: Optional[str] = None):
        """
        Record current memory usage
        
        Args:
            operation: Associated operation name
            
        Requirements: 12.2
        """
        if not self.config['enable_memory_tracking']:
            return
        
        try:
            # System memory
            memory = psutil.virtual_memory()
            
            # Process memory
            process_memory = self.process.memory_info().rss / (1024 * 1024)  # MB
            
            metric = MemoryUsageMetric(
                timestamp=datetime.now(),
                total_mb=memory.total / (1024 * 1024),
                used_mb=memory.used / (1024 * 1024),
                available_mb=memory.available / (1024 * 1024),
                percent=memory.percent,
                process_memory_mb=process_memory,
                operation=operation
            )
            
            with self.memory_lock:
                self.memory_usage.append(metric)
                self._trim_history(self.memory_usage)
            
        except Exception as e:
            logging_system.log_error("Failed to record memory usage", exception=e)
    
    def record_gpu_usage(self, operation: Optional[str] = None):
        """
        Record current GPU usage
        
        Args:
            operation: Associated operation name
            
        Requirements: 12.2
        """
        if not self.config['enable_gpu_tracking'] or not self.gpu_available:
            return
        
        try:
            import GPUtil
            
            gpus = GPUtil.getGPUs()
            
            for gpu in gpus:
                metric = GPUUsageMetric(
                    timestamp=datetime.now(),
                    gpu_id=gpu.id,
                    load_percent=gpu.load * 100,
                    memory_used_mb=gpu.memoryUsed,
                    memory_total_mb=gpu.memoryTotal,
                    memory_percent=(gpu.memoryUsed / gpu.memoryTotal * 100) if gpu.memoryTotal > 0 else 0,
                    temperature_celsius=gpu.temperature,
                    operation=operation
                )
                
                with self.gpu_lock:
                    self.gpu_usage.append(metric)
                    self._trim_history(self.gpu_usage)
            
        except Exception as e:
            logging_system.log_error("Failed to record GPU usage", exception=e)
    
    def _trim_history(self, history: List):
        """Trim history to max size"""
        max_size = self.config['max_history_size']
        if len(history) > max_size:
            del history[:len(history) - max_size]
    
    def start_monitoring(self):
        """
        Start background monitoring of memory and GPU
        
        Requirements: 12.2
        """
        if self.is_monitoring:
            logging_system.log("WARNING", "Metrics monitoring already running")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logging_system.log("INFO", "Performance metrics monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        logging_system.log("INFO", "Performance metrics monitoring stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.is_monitoring:
            try:
                # Record memory usage
                self.record_memory_usage(operation="background_monitoring")
                
                # Record GPU usage
                self.record_gpu_usage(operation="background_monitoring")
                
            except Exception as e:
                logging_system.log_error("Error in metrics monitoring loop", exception=e)
            
            time.sleep(self.config['memory_sample_interval'])
    
    def get_processing_time_stats(
        self,
        operation: Optional[str] = None,
        duration_minutes: Optional[int] = None
    ) -> Dict:
        """
        Get processing time statistics
        
        Args:
            operation: Filter by operation name
            duration_minutes: Only include metrics from last N minutes
            
        Returns:
            Statistics dictionary
            
        Requirements: 12.1, 15.4
        """
        with self.processing_lock:
            metrics = self.processing_times.copy()
        
        # Filter by operation
        if operation:
            metrics = [m for m in metrics if m.operation == operation]
        
        # Filter by duration
        if duration_minutes:
            cutoff = datetime.now() - timedelta(minutes=duration_minutes)
            metrics = [m for m in metrics if m.timestamp >= cutoff]
        
        if not metrics:
            return {
                'count': 0,
                'operation': operation
            }
        
        durations = [m.duration_ms for m in metrics]
        successes = [m for m in metrics if m.success]
        failures = [m for m in metrics if not m.success]
        
        return {
            'count': len(metrics),
            'operation': operation,
            'duration_minutes': duration_minutes,
            'total_duration_ms': sum(durations),
            'avg_duration_ms': sum(durations) / len(durations),
            'min_duration_ms': min(durations),
            'max_duration_ms': max(durations),
            'median_duration_ms': sorted(durations)[len(durations) // 2],
            'success_count': len(successes),
            'failure_count': len(failures),
            'success_rate': len(successes) / len(metrics) * 100 if metrics else 0,
            'first_timestamp': metrics[0].timestamp.isoformat(),
            'last_timestamp': metrics[-1].timestamp.isoformat()
        }
    
    def get_memory_usage_stats(self, duration_minutes: Optional[int] = None) -> Dict:
        """
        Get memory usage statistics
        
        Args:
            duration_minutes: Only include metrics from last N minutes
            
        Returns:
            Statistics dictionary
            
        Requirements: 12.2, 15.4
        """
        with self.memory_lock:
            metrics = self.memory_usage.copy()
        
        # Filter by duration
        if duration_minutes:
            cutoff = datetime.now() - timedelta(minutes=duration_minutes)
            metrics = [m for m in metrics if m.timestamp >= cutoff]
        
        if not metrics:
            return {'count': 0}
        
        return {
            'count': len(metrics),
            'duration_minutes': duration_minutes,
            'current_used_mb': metrics[-1].used_mb,
            'current_percent': metrics[-1].percent,
            'current_process_mb': metrics[-1].process_memory_mb,
            'avg_used_mb': sum(m.used_mb for m in metrics) / len(metrics),
            'avg_percent': sum(m.percent for m in metrics) / len(metrics),
            'avg_process_mb': sum(m.process_memory_mb for m in metrics) / len(metrics),
            'max_used_mb': max(m.used_mb for m in metrics),
            'max_percent': max(m.percent for m in metrics),
            'max_process_mb': max(m.process_memory_mb for m in metrics),
            'first_timestamp': metrics[0].timestamp.isoformat(),
            'last_timestamp': metrics[-1].timestamp.isoformat()
        }
    
    def get_gpu_usage_stats(
        self,
        gpu_id: Optional[int] = None,
        duration_minutes: Optional[int] = None
    ) -> Dict:
        """
        Get GPU usage statistics
        
        Args:
            gpu_id: Filter by GPU ID
            duration_minutes: Only include metrics from last N minutes
            
        Returns:
            Statistics dictionary
            
        Requirements: 12.2, 15.4
        """
        with self.gpu_lock:
            metrics = self.gpu_usage.copy()
        
        # Filter by GPU ID
        if gpu_id is not None:
            metrics = [m for m in metrics if m.gpu_id == gpu_id]
        
        # Filter by duration
        if duration_minutes:
            cutoff = datetime.now() - timedelta(minutes=duration_minutes)
            metrics = [m for m in metrics if m.timestamp >= cutoff]
        
        if not metrics:
            return {'count': 0, 'gpu_id': gpu_id}
        
        return {
            'count': len(metrics),
            'gpu_id': gpu_id,
            'duration_minutes': duration_minutes,
            'current_load_percent': metrics[-1].load_percent,
            'current_memory_percent': metrics[-1].memory_percent,
            'current_temperature': metrics[-1].temperature_celsius,
            'avg_load_percent': sum(m.load_percent for m in metrics) / len(metrics),
            'avg_memory_percent': sum(m.memory_percent for m in metrics) / len(metrics),
            'avg_temperature': sum(m.temperature_celsius for m in metrics) / len(metrics),
            'max_load_percent': max(m.load_percent for m in metrics),
            'max_memory_percent': max(m.memory_percent for m in metrics),
            'max_temperature': max(m.temperature_celsius for m in metrics),
            'first_timestamp': metrics[0].timestamp.isoformat(),
            'last_timestamp': metrics[-1].timestamp.isoformat()
        }
    
    def get_operation_summary(self, duration_minutes: Optional[int] = None) -> List[Dict]:
        """
        Get summary of all operations
        
        Args:
            duration_minutes: Only include metrics from last N minutes
            
        Returns:
            List of operation summaries
            
        Requirements: 15.4
        """
        with self.processing_lock:
            metrics = self.processing_times.copy()
        
        # Filter by duration
        if duration_minutes:
            cutoff = datetime.now() - timedelta(minutes=duration_minutes)
            metrics = [m for m in metrics if m.timestamp >= cutoff]
        
        # Group by operation
        operations = {}
        for metric in metrics:
            if metric.operation not in operations:
                operations[metric.operation] = []
            operations[metric.operation].append(metric)
        
        # Calculate stats for each operation
        summaries = []
        for operation, op_metrics in operations.items():
            durations = [m.duration_ms for m in op_metrics]
            successes = [m for m in op_metrics if m.success]
            
            summaries.append({
                'operation': operation,
                'count': len(op_metrics),
                'avg_duration_ms': sum(durations) / len(durations),
                'total_duration_ms': sum(durations),
                'success_rate': len(successes) / len(op_metrics) * 100,
                'failure_count': len(op_metrics) - len(successes)
            })
        
        # Sort by total duration (descending)
        summaries.sort(key=lambda x: x['total_duration_ms'], reverse=True)
        
        return summaries
    
    def export_to_json(self, filepath: Optional[str] = None) -> str:
        """
        Export all metrics to JSON file
        
        Args:
            filepath: Output file path (auto-generated if None)
            
        Returns:
            Path to exported file
            
        Requirements: 15.4
        """
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"{self.config['export_directory']}/metrics_{timestamp}.json"
        
        try:
            # Copy metrics first to avoid holding locks during stats calculation
            with self.processing_lock:
                processing_copy = [m.to_dict() for m in self.processing_times]
            
            with self.memory_lock:
                memory_copy = [m.to_dict() for m in self.memory_usage]
            
            with self.gpu_lock:
                gpu_copy = [m.to_dict() for m in self.gpu_usage]
            
            # Calculate stats without holding locks
            data = {
                'export_timestamp': datetime.now().isoformat(),
                'processing_times': processing_copy,
                'memory_usage': memory_copy,
                'gpu_usage': gpu_copy,
                'summary': {
                    'processing_time_stats': self.get_processing_time_stats(),
                    'memory_usage_stats': self.get_memory_usage_stats(),
                    'gpu_usage_stats': self.get_gpu_usage_stats(),
                    'operation_summary': self.get_operation_summary()
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logging_system.log("INFO", "Metrics exported to JSON",
                              filepath=filepath,
                              processing_count=len(self.processing_times),
                              memory_count=len(self.memory_usage),
                              gpu_count=len(self.gpu_usage))
            
            return filepath
            
        except Exception as e:
            logging_system.log_error("Failed to export metrics to JSON",
                                    filepath=filepath,
                                    exception=e)
            raise
    
    def export_to_csv(self, metric_type: str, filepath: Optional[str] = None) -> str:
        """
        Export specific metric type to CSV file
        
        Args:
            metric_type: Type of metric ('processing', 'memory', 'gpu')
            filepath: Output file path (auto-generated if None)
            
        Returns:
            Path to exported file
            
        Requirements: 15.4
        """
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"{self.config['export_directory']}/{metric_type}_metrics_{timestamp}.csv"
        
        try:
            if metric_type == 'processing':
                with self.processing_lock:
                    metrics = self.processing_times.copy()
                
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    if metrics:
                        writer = csv.DictWriter(f, fieldnames=metrics[0].to_dict().keys())
                        writer.writeheader()
                        for metric in metrics:
                            writer.writerow(metric.to_dict())
            
            elif metric_type == 'memory':
                with self.memory_lock:
                    metrics = self.memory_usage.copy()
                
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    if metrics:
                        writer = csv.DictWriter(f, fieldnames=metrics[0].to_dict().keys())
                        writer.writeheader()
                        for metric in metrics:
                            writer.writerow(metric.to_dict())
            
            elif metric_type == 'gpu':
                with self.gpu_lock:
                    metrics = self.gpu_usage.copy()
                
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    if metrics:
                        writer = csv.DictWriter(f, fieldnames=metrics[0].to_dict().keys())
                        writer.writeheader()
                        for metric in metrics:
                            writer.writerow(metric.to_dict())
            
            else:
                raise ValueError(f"Invalid metric type: {metric_type}")
            
            logging_system.log("INFO", "Metrics exported to CSV",
                              metric_type=metric_type,
                              filepath=filepath,
                              count=len(metrics))
            
            return filepath
            
        except Exception as e:
            logging_system.log_error("Failed to export metrics to CSV",
                                    metric_type=metric_type,
                                    filepath=filepath,
                                    exception=e)
            raise
    
    def clear_metrics(self, metric_type: Optional[str] = None):
        """
        Clear metrics history
        
        Args:
            metric_type: Type to clear ('processing', 'memory', 'gpu', or None for all)
        """
        if metric_type is None or metric_type == 'processing':
            with self.processing_lock:
                count = len(self.processing_times)
                self.processing_times.clear()
                logging_system.log("INFO", "Processing time metrics cleared", count=count)
        
        if metric_type is None or metric_type == 'memory':
            with self.memory_lock:
                count = len(self.memory_usage)
                self.memory_usage.clear()
                logging_system.log("INFO", "Memory usage metrics cleared", count=count)
        
        if metric_type is None or metric_type == 'gpu':
            with self.gpu_lock:
                count = len(self.gpu_usage)
                self.gpu_usage.clear()
                logging_system.log("INFO", "GPU usage metrics cleared", count=count)
    
    def get_metrics_count(self) -> Dict:
        """Get count of stored metrics"""
        return {
            'processing_times': len(self.processing_times),
            'memory_usage': len(self.memory_usage),
            'gpu_usage': len(self.gpu_usage),
            'total': len(self.processing_times) + len(self.memory_usage) + len(self.gpu_usage)
        }
    
    def update_config(self, config_updates: Dict) -> bool:
        """
        Update collector configuration
        
        Args:
            config_updates: Dictionary of config updates
            
        Returns:
            True if successful
        """
        try:
            for key, value in config_updates.items():
                if key in self.config:
                    self.config[key] = value
            
            logging_system.log("INFO", "Performance metrics config updated",
                              updates=config_updates)
            
            return True
            
        except Exception as e:
            logging_system.log_error("Failed to update metrics config", exception=e)
            return False


# Global instance
_metrics_collector = None


def get_performance_metrics_collector() -> PerformanceMetricsCollector:
    """Get global performance metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = PerformanceMetricsCollector()
    return _metrics_collector


# Convenience functions
def measure_performance(operation: str, **kwargs) -> PerformanceTimer:
    """
    Create a performance timer context manager
    
    Usage:
        with measure_performance("my_operation", photo_id=123):
            # do work
            pass
    """
    return PerformanceTimer(operation, **kwargs)


def record_processing_time(operation: str, duration_ms: float, **kwargs):
    """Record processing time metric"""
    collector = get_performance_metrics_collector()
    collector.record_processing_time(operation, duration_ms, **kwargs)


def record_memory_usage(operation: Optional[str] = None):
    """Record memory usage metric"""
    collector = get_performance_metrics_collector()
    collector.record_memory_usage(operation)


def record_gpu_usage(operation: Optional[str] = None):
    """Record GPU usage metric"""
    collector = get_performance_metrics_collector()
    collector.record_gpu_usage(operation)
