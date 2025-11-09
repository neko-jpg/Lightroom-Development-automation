"""
Resource Management System for Junmai AutoDev

This module provides comprehensive resource monitoring and dynamic adjustment
for CPU, GPU, memory, and system idle time detection.

Requirements: 4.3, 12.4, 17.3
"""

import psutil
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, List
from logging_system import get_logging_system
from dataclasses import dataclass
from enum import Enum

logging_system = get_logging_system()


class ResourceState(Enum):
    """System resource state"""
    IDLE = "idle"
    NORMAL = "normal"
    BUSY = "busy"
    CRITICAL = "critical"


@dataclass
class ResourceMetrics:
    """Resource usage metrics snapshot"""
    timestamp: datetime
    cpu_percent: float
    cpu_per_core: List[float]
    memory_percent: float
    memory_available_mb: float
    gpu_load: Optional[float] = None
    gpu_memory_used_mb: Optional[float] = None
    gpu_memory_total_mb: Optional[float] = None
    gpu_temperature: Optional[float] = None
    disk_usage_percent: Optional[float] = None
    state: ResourceState = ResourceState.NORMAL


class ResourceManager:
    """
    Comprehensive resource monitoring and management system
    
    Features:
    - CPU usage monitoring with per-core tracking
    - GPU temperature and memory monitoring
    - System idle time detection
    - Dynamic processing speed adjustment
    - Resource threshold management
    - Automatic throttling and recovery
    
    Requirements: 4.3, 12.4, 17.3
    """
    
    def __init__(self):
        """Initialize resource manager"""
        self.config = {
            # CPU thresholds
            'cpu_limit_percent': 80,
            'cpu_critical_percent': 95,
            'cpu_idle_percent': 20,
            
            # GPU thresholds
            'gpu_temp_limit_celsius': 75,
            'gpu_temp_critical_celsius': 85,
            'gpu_memory_limit_percent': 90,
            
            # Memory thresholds
            'memory_limit_percent': 85,
            'memory_critical_percent': 95,
            
            # Idle detection
            'idle_threshold_seconds': 300,  # 5 minutes
            'idle_cpu_threshold': 15,
            'idle_check_interval': 60,  # Check every minute
            
            # Monitoring
            'monitor_interval': 5,  # Monitor every 5 seconds
            'history_size': 100,  # Keep last 100 measurements
        }
        
        self.metrics_history: List[ResourceMetrics] = []
        self.current_state = ResourceState.NORMAL
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.callbacks: Dict[str, List[Callable]] = {
            'state_change': [],
            'throttle': [],
            'resume': [],
            'critical': []
        }
        
        # Idle detection
        self.last_activity_time = datetime.now()
        self.idle_start_time: Optional[datetime] = None
        
        # GPU availability check
        self.gpu_available = self._check_gpu_availability()
        
        logging_system.log("INFO", "Resource manager initialized",
                          gpu_available=self.gpu_available)
    
    def _check_gpu_availability(self) -> bool:
        """Check if GPU monitoring is available"""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            return len(gpus) > 0
        except ImportError:
            logging_system.log("WARNING", "GPUtil not available, GPU monitoring disabled")
            return False
        except Exception as e:
            logging_system.log("WARNING", "GPU detection failed", exception=str(e))
            return False
    
    def get_current_metrics(self) -> ResourceMetrics:
        """
        Get current resource usage metrics
        
        Returns:
            ResourceMetrics snapshot
            
        Requirements: 4.3, 12.4
        """
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_per_core = psutil.cpu_percent(interval=0.5, percpu=True)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_mb = memory.available / (1024 * 1024)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_usage_percent = disk.percent
        
        # GPU metrics (if available)
        gpu_load = None
        gpu_memory_used_mb = None
        gpu_memory_total_mb = None
        gpu_temperature = None
        
        if self.gpu_available:
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # Use first GPU
                    gpu_load = gpu.load * 100
                    gpu_memory_used_mb = gpu.memoryUsed
                    gpu_memory_total_mb = gpu.memoryTotal
                    gpu_temperature = gpu.temperature
            except Exception as e:
                logging_system.log("DEBUG", "Failed to get GPU metrics", exception=str(e))
        
        # Determine resource state
        state = self._determine_state(
            cpu_percent, memory_percent, gpu_temperature, gpu_load
        )
        
        metrics = ResourceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            cpu_per_core=cpu_per_core,
            memory_percent=memory_percent,
            memory_available_mb=memory_available_mb,
            gpu_load=gpu_load,
            gpu_memory_used_mb=gpu_memory_used_mb,
            gpu_memory_total_mb=gpu_memory_total_mb,
            gpu_temperature=gpu_temperature,
            disk_usage_percent=disk_usage_percent,
            state=state
        )
        
        return metrics
    
    def _determine_state(
        self,
        cpu_percent: float,
        memory_percent: float,
        gpu_temp: Optional[float],
        gpu_load: Optional[float]
    ) -> ResourceState:
        """
        Determine overall resource state
        
        Args:
            cpu_percent: CPU usage percentage
            memory_percent: Memory usage percentage
            gpu_temp: GPU temperature (optional)
            gpu_load: GPU load percentage (optional)
            
        Returns:
            ResourceState
        """
        # Check critical conditions
        if cpu_percent >= self.config['cpu_critical_percent']:
            return ResourceState.CRITICAL
        
        if memory_percent >= self.config['memory_critical_percent']:
            return ResourceState.CRITICAL
        
        if gpu_temp and gpu_temp >= self.config['gpu_temp_critical_celsius']:
            return ResourceState.CRITICAL
        
        # Check busy conditions
        if cpu_percent >= self.config['cpu_limit_percent']:
            return ResourceState.BUSY
        
        if memory_percent >= self.config['memory_limit_percent']:
            return ResourceState.BUSY
        
        if gpu_temp and gpu_temp >= self.config['gpu_temp_limit_celsius']:
            return ResourceState.BUSY
        
        # Check idle conditions
        if cpu_percent <= self.config['cpu_idle_percent']:
            return ResourceState.IDLE
        
        return ResourceState.NORMAL
    
    def start_monitoring(self):
        """
        Start continuous resource monitoring
        
        Requirements: 4.3
        """
        if self.is_monitoring:
            logging_system.log("WARNING", "Resource monitoring already running")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logging_system.log("INFO", "Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous resource monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        logging_system.log("INFO", "Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop (runs in separate thread)"""
        while self.is_monitoring:
            try:
                # Get current metrics
                metrics = self.get_current_metrics()
                
                # Add to history
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > self.config['history_size']:
                    self.metrics_history.pop(0)
                
                # Check for state changes
                if metrics.state != self.current_state:
                    self._handle_state_change(self.current_state, metrics.state)
                    self.current_state = metrics.state
                
                # Check idle time
                self._check_idle_state(metrics)
                
                # Log metrics periodically (every 10 measurements)
                if len(self.metrics_history) % 10 == 0:
                    self._log_metrics(metrics)
                
            except Exception as e:
                logging_system.log_error("Error in monitoring loop", exception=e)
            
            # Sleep until next check
            time.sleep(self.config['monitor_interval'])
    
    def _handle_state_change(self, old_state: ResourceState, new_state: ResourceState):
        """
        Handle resource state changes
        
        Args:
            old_state: Previous state
            new_state: New state
        """
        logging_system.log("INFO", "Resource state changed",
                          old_state=old_state.value,
                          new_state=new_state.value)
        
        # Trigger callbacks
        self._trigger_callbacks('state_change', old_state, new_state)
        
        # Handle specific transitions
        if new_state == ResourceState.CRITICAL:
            self._trigger_callbacks('critical', new_state)
            logging_system.log("CRITICAL", "System resources in critical state")
        
        elif new_state == ResourceState.BUSY and old_state in [ResourceState.NORMAL, ResourceState.IDLE]:
            self._trigger_callbacks('throttle', new_state)
            logging_system.log("WARNING", "System resources busy, throttling recommended")
        
        elif new_state in [ResourceState.NORMAL, ResourceState.IDLE] and old_state in [ResourceState.BUSY, ResourceState.CRITICAL]:
            self._trigger_callbacks('resume', new_state)
            logging_system.log("INFO", "System resources recovered, resuming normal operation")
    
    def _check_idle_state(self, metrics: ResourceMetrics):
        """
        Check and update system idle state
        
        Args:
            metrics: Current resource metrics
            
        Requirements: 4.3
        """
        is_idle = metrics.cpu_percent <= self.config['idle_cpu_threshold']
        
        if is_idle:
            if self.idle_start_time is None:
                self.idle_start_time = datetime.now()
        else:
            self.idle_start_time = None
            self.last_activity_time = datetime.now()
    
    def is_system_idle(self) -> bool:
        """
        Check if system is currently idle
        
        Returns:
            True if system has been idle for threshold duration
            
        Requirements: 4.3
        """
        if self.idle_start_time is None:
            return False
        
        idle_duration = (datetime.now() - self.idle_start_time).total_seconds()
        return idle_duration >= self.config['idle_threshold_seconds']
    
    def get_idle_duration(self) -> float:
        """
        Get current idle duration in seconds
        
        Returns:
            Idle duration in seconds, or 0 if not idle
        """
        if self.idle_start_time is None:
            return 0.0
        
        return (datetime.now() - self.idle_start_time).total_seconds()
    
    def should_throttle_processing(self) -> bool:
        """
        Determine if processing should be throttled
        
        Returns:
            True if processing should be throttled
            
        Requirements: 4.3, 12.4
        """
        # Get current metrics if history is empty
        if not self.metrics_history:
            metrics = self.get_current_metrics()
            self.metrics_history.append(metrics)
        
        latest = self.metrics_history[-1]
        
        # Throttle if in busy or critical state
        if latest.state in [ResourceState.BUSY, ResourceState.CRITICAL]:
            return True
        
        # Throttle if GPU temperature is high
        if latest.gpu_temperature and latest.gpu_temperature >= self.config['gpu_temp_limit_celsius']:
            return True
        
        return False
    
    def get_recommended_speed_multiplier(self) -> float:
        """
        Get recommended processing speed multiplier
        
        Returns:
            Speed multiplier (0.0 to 1.0)
            - 1.0 = full speed
            - 0.5 = half speed
            - 0.0 = pause
            
        Requirements: 4.3, 12.4
        """
        # Get current metrics if history is empty
        if not self.metrics_history:
            metrics = self.get_current_metrics()
            self.metrics_history.append(metrics)
        
        latest = self.metrics_history[-1]
        
        # Critical state - pause processing
        if latest.state == ResourceState.CRITICAL:
            return 0.0
        
        # Busy state - reduce to 50%
        if latest.state == ResourceState.BUSY:
            return 0.5
        
        # Idle state - full speed
        if latest.state == ResourceState.IDLE or self.is_system_idle():
            return 1.0
        
        # Normal state - 80% speed
        return 0.8
    
    def get_gpu_status(self) -> Dict:
        """
        Get detailed GPU status
        
        Returns:
            GPU status dictionary
            
        Requirements: 17.3
        """
        if not self.gpu_available:
            return {
                'available': False,
                'message': 'GPU monitoring not available'
            }
        
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            
            if not gpus:
                return {
                    'available': False,
                    'message': 'No GPU detected'
                }
            
            gpu = gpus[0]
            
            return {
                'available': True,
                'id': gpu.id,
                'name': gpu.name,
                'load': gpu.load * 100,
                'memory_used_mb': gpu.memoryUsed,
                'memory_total_mb': gpu.memoryTotal,
                'memory_percent': (gpu.memoryUsed / gpu.memoryTotal * 100) if gpu.memoryTotal > 0 else 0,
                'temperature': gpu.temperature,
                'is_overheating': gpu.temperature >= self.config['gpu_temp_limit_celsius'],
                'is_critical': gpu.temperature >= self.config['gpu_temp_critical_celsius']
            }
            
        except Exception as e:
            logging_system.log_error("Failed to get GPU status", exception=e)
            return {
                'available': False,
                'error': str(e)
            }
    
    def get_cpu_status(self) -> Dict:
        """
        Get detailed CPU status
        
        Returns:
            CPU status dictionary
            
        Requirements: 4.3
        """
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_per_core = psutil.cpu_percent(interval=0.5, percpu=True)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        return {
            'usage_percent': cpu_percent,
            'per_core_percent': cpu_per_core,
            'core_count': cpu_count,
            'frequency_mhz': cpu_freq.current if cpu_freq else None,
            'is_busy': cpu_percent >= self.config['cpu_limit_percent'],
            'is_critical': cpu_percent >= self.config['cpu_critical_percent']
        }
    
    def get_memory_status(self) -> Dict:
        """
        Get detailed memory status
        
        Returns:
            Memory status dictionary
        """
        memory = psutil.virtual_memory()
        
        return {
            'total_mb': memory.total / (1024 * 1024),
            'available_mb': memory.available / (1024 * 1024),
            'used_mb': memory.used / (1024 * 1024),
            'percent': memory.percent,
            'is_busy': memory.percent >= self.config['memory_limit_percent'],
            'is_critical': memory.percent >= self.config['memory_critical_percent']
        }
    
    def get_system_status(self) -> Dict:
        """
        Get comprehensive system status
        
        Returns:
            Complete system status dictionary
            
        Requirements: 4.3, 12.4, 17.3
        """
        metrics = self.get_current_metrics()
        
        return {
            'timestamp': metrics.timestamp.isoformat(),
            'state': metrics.state.value,
            'cpu': self.get_cpu_status(),
            'memory': self.get_memory_status(),
            'gpu': self.get_gpu_status(),
            'disk_usage_percent': metrics.disk_usage_percent,
            'is_idle': self.is_system_idle(),
            'idle_duration_seconds': self.get_idle_duration(),
            'should_throttle': self.should_throttle_processing(),
            'recommended_speed': self.get_recommended_speed_multiplier()
        }
    
    def get_metrics_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get historical metrics
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of metrics dictionaries
        """
        history = self.metrics_history[-limit:] if limit else self.metrics_history
        
        return [
            {
                'timestamp': m.timestamp.isoformat(),
                'cpu_percent': m.cpu_percent,
                'memory_percent': m.memory_percent,
                'gpu_temperature': m.gpu_temperature,
                'gpu_load': m.gpu_load,
                'state': m.state.value
            }
            for m in history
        ]
    
    def get_average_metrics(self, duration_minutes: int = 5) -> Dict:
        """
        Get average metrics over specified duration
        
        Args:
            duration_minutes: Duration to average over
            
        Returns:
            Average metrics dictionary
        """
        if not self.metrics_history:
            return {}
        
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {}
        
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        
        gpu_temps = [m.gpu_temperature for m in recent_metrics if m.gpu_temperature is not None]
        avg_gpu_temp = sum(gpu_temps) / len(gpu_temps) if gpu_temps else None
        
        gpu_loads = [m.gpu_load for m in recent_metrics if m.gpu_load is not None]
        avg_gpu_load = sum(gpu_loads) / len(gpu_loads) if gpu_loads else None
        
        return {
            'duration_minutes': duration_minutes,
            'sample_count': len(recent_metrics),
            'avg_cpu_percent': avg_cpu,
            'avg_memory_percent': avg_memory,
            'avg_gpu_temperature': avg_gpu_temp,
            'avg_gpu_load': avg_gpu_load
        }
    
    def register_callback(self, event: str, callback: Callable):
        """
        Register callback for resource events
        
        Args:
            event: Event type ('state_change', 'throttle', 'resume', 'critical')
            callback: Callback function
        """
        if event not in self.callbacks:
            raise ValueError(f"Invalid event type: {event}")
        
        self.callbacks[event].append(callback)
        logging_system.log("DEBUG", "Callback registered", event=event)
    
    def _trigger_callbacks(self, event: str, *args):
        """Trigger all callbacks for an event"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                logging_system.log_error("Callback execution failed",
                                        event=event,
                                        exception=e)
    
    def _log_metrics(self, metrics: ResourceMetrics):
        """Log current metrics"""
        log_data = {
            'cpu_percent': metrics.cpu_percent,
            'memory_percent': metrics.memory_percent,
            'state': metrics.state.value
        }
        
        if metrics.gpu_temperature:
            log_data['gpu_temperature'] = metrics.gpu_temperature
        if metrics.gpu_load:
            log_data['gpu_load'] = metrics.gpu_load
        
        logging_system.log("DEBUG", "Resource metrics", **log_data)
    
    def update_config(self, config_updates: Dict) -> bool:
        """
        Update resource manager configuration
        
        Args:
            config_updates: Dictionary of config updates
            
        Returns:
            True if successful
        """
        try:
            for key, value in config_updates.items():
                if key in self.config:
                    self.config[key] = value
            
            logging_system.log("INFO", "Resource manager config updated",
                              updates=config_updates)
            
            return True
            
        except Exception as e:
            logging_system.log_error("Failed to update resource config",
                                    exception=e)
            return False


# Global instance
_resource_manager = None

def get_resource_manager() -> ResourceManager:
    """Get global resource manager instance"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager
