"""
GPU Management System for Junmai AutoDev

This module provides comprehensive GPU monitoring, memory allocation management,
temperature monitoring, and processing throttling for optimal GPU utilization.

Requirements: 17.1, 17.2, 17.3, 17.5
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
from logging_system import get_logging_system

logging_system = get_logging_system()


class GPUState(Enum):
    """GPU operational state"""
    OPTIMAL = "optimal"          # Temperature < 65°C, memory < 70%
    NORMAL = "normal"            # Temperature 65-75°C, memory 70-85%
    THROTTLED = "throttled"      # Temperature 75-85°C, memory 85-95%
    CRITICAL = "critical"        # Temperature > 85°C, memory > 95%
    UNAVAILABLE = "unavailable"  # GPU not detected or error


@dataclass
class GPUMetrics:
    """GPU metrics snapshot"""
    timestamp: datetime
    gpu_id: int
    gpu_name: str
    load_percent: float
    memory_used_mb: float
    memory_total_mb: float
    memory_percent: float
    temperature_celsius: float
    fan_speed_percent: Optional[float] = None
    power_draw_watts: Optional[float] = None
    state: GPUState = GPUState.NORMAL


class GPUMemoryAllocation:
    """GPU memory allocation tracker"""
    
    def __init__(self, gpu_id: int, total_memory_mb: float, limit_mb: float):
        """
        Initialize memory allocation tracker
        
        Args:
            gpu_id: GPU identifier
            total_memory_mb: Total GPU memory in MB
            limit_mb: Maximum allocatable memory in MB
        """
        self.gpu_id = gpu_id
        self.total_memory_mb = total_memory_mb
        self.limit_mb = limit_mb
        self.allocations: Dict[str, float] = {}  # allocation_id -> memory_mb
        self.lock = threading.Lock()
        
        logging_system.log("INFO", "GPU memory allocation tracker initialized",
                          gpu_id=gpu_id,
                          total_mb=total_memory_mb,
                          limit_mb=limit_mb)
    
    def allocate(self, allocation_id: str, required_mb: float) -> bool:
        """
        Attempt to allocate GPU memory
        
        Args:
            allocation_id: Unique identifier for this allocation
            required_mb: Required memory in MB
            
        Returns:
            True if allocation successful, False otherwise
            
        Requirements: 17.1
        """
        with self.lock:
            # Check if allocation already exists
            if allocation_id in self.allocations:
                logging_system.log("WARNING", "Allocation ID already exists",
                                  allocation_id=allocation_id)
                return False
            
            # Calculate current usage
            current_usage = sum(self.allocations.values())
            
            # Check if allocation would exceed limit
            if current_usage + required_mb > self.limit_mb:
                logging_system.log("WARNING", "GPU memory allocation failed - limit exceeded",
                                  allocation_id=allocation_id,
                                  required_mb=required_mb,
                                  current_usage_mb=current_usage,
                                  limit_mb=self.limit_mb)
                return False
            
            # Allocate memory
            self.allocations[allocation_id] = required_mb
            
            logging_system.log("INFO", "GPU memory allocated",
                              allocation_id=allocation_id,
                              allocated_mb=required_mb,
                              total_allocated_mb=current_usage + required_mb)
            
            return True
    
    def deallocate(self, allocation_id: str) -> bool:
        """
        Deallocate GPU memory
        
        Args:
            allocation_id: Allocation identifier to release
            
        Returns:
            True if deallocation successful
        """
        with self.lock:
            if allocation_id not in self.allocations:
                logging_system.log("WARNING", "Allocation ID not found",
                                  allocation_id=allocation_id)
                return False
            
            freed_mb = self.allocations.pop(allocation_id)
            
            logging_system.log("INFO", "GPU memory deallocated",
                              allocation_id=allocation_id,
                              freed_mb=freed_mb,
                              remaining_allocated_mb=sum(self.allocations.values()))
            
            return True
    
    def get_available_memory(self) -> float:
        """
        Get available GPU memory
        
        Returns:
            Available memory in MB
        """
        with self.lock:
            current_usage = sum(self.allocations.values())
            return self.limit_mb - current_usage
    
    def get_usage_stats(self) -> Dict:
        """Get memory usage statistics"""
        with self.lock:
            allocated = sum(self.allocations.values())
            return {
                'total_mb': self.total_memory_mb,
                'limit_mb': self.limit_mb,
                'allocated_mb': allocated,
                'available_mb': self.limit_mb - allocated,
                'allocation_count': len(self.allocations),
                'allocations': dict(self.allocations)
            }


class GPUManager:
    """
    Comprehensive GPU management system
    
    Features:
    - GPU memory usage monitoring
    - GPU temperature monitoring
    - Memory allocation management
    - Processing throttling based on temperature and load
    - Multi-GPU support
    - Automatic recovery from critical states
    
    Requirements: 17.1, 17.2, 17.3, 17.5
    """
    
    def __init__(self):
        """Initialize GPU manager"""
        self.config = {
            # Temperature thresholds (Celsius)
            'temp_optimal': 65,
            'temp_normal': 75,
            'temp_throttle': 85,
            'temp_critical': 90,
            
            # Memory thresholds (percent)
            'memory_optimal': 70,
            'memory_normal': 85,
            'memory_critical': 95,
            
            # Memory limits
            'memory_limit_mb': 6144,  # 6GB for RTX 4060
            'memory_reserve_mb': 512,  # Reserve 512MB for system
            
            # Monitoring
            'monitor_interval': 3,  # Monitor every 3 seconds
            'history_size': 200,    # Keep last 200 measurements (10 minutes at 3s interval)
            
            # Throttling
            'throttle_cooldown_seconds': 30,  # Wait 30s before resuming after throttle
            'critical_pause_seconds': 60,     # Pause 60s in critical state
        }
        
        self.gpus_available = False
        self.gpu_count = 0
        self.gpus: List[Dict] = []
        self.memory_allocators: Dict[int, GPUMemoryAllocation] = {}
        
        self.metrics_history: List[GPUMetrics] = []
        self.current_state = GPUState.UNAVAILABLE
        
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        self.callbacks: Dict[str, List[Callable]] = {
            'state_change': [],
            'throttle': [],
            'resume': [],
            'critical': [],
            'overheat': []
        }
        
        # Throttling state
        self.is_throttled = False
        self.throttle_start_time: Optional[datetime] = None
        self.last_critical_time: Optional[datetime] = None
        
        # Initialize GPU detection
        self._initialize_gpus()
        
        logging_system.log("INFO", "GPU manager initialized",
                          gpus_available=self.gpus_available,
                          gpu_count=self.gpu_count)
    
    def _initialize_gpus(self):
        """
        Initialize GPU detection and memory allocators
        
        Requirements: 17.1
        """
        try:
            import GPUtil
            
            gpus = GPUtil.getGPUs()
            
            if not gpus:
                logging_system.log("WARNING", "No GPUs detected")
                self.current_state = GPUState.UNAVAILABLE
                return
            
            self.gpus_available = True
            self.gpu_count = len(gpus)
            
            for gpu in gpus:
                gpu_info = {
                    'id': gpu.id,
                    'name': gpu.name,
                    'memory_total_mb': gpu.memoryTotal,
                    'driver': getattr(gpu, 'driver', 'Unknown')
                }
                self.gpus.append(gpu_info)
                
                # Create memory allocator for this GPU
                allocatable_memory = min(
                    self.config['memory_limit_mb'],
                    gpu.memoryTotal - self.config['memory_reserve_mb']
                )
                
                self.memory_allocators[gpu.id] = GPUMemoryAllocation(
                    gpu.id,
                    gpu.memoryTotal,
                    allocatable_memory
                )
                
                logging_system.log("INFO", "GPU detected",
                                  gpu_id=gpu.id,
                                  name=gpu.name,
                                  memory_total_mb=gpu.memoryTotal,
                                  allocatable_mb=allocatable_memory)
            
            self.current_state = GPUState.OPTIMAL
            
        except ImportError:
            logging_system.log("ERROR", "GPUtil not installed - GPU monitoring unavailable")
            self.current_state = GPUState.UNAVAILABLE
        except Exception as e:
            logging_system.log_error("GPU initialization failed", exception=e)
            self.current_state = GPUState.UNAVAILABLE
    
    def is_available(self) -> bool:
        """
        Check if GPU is available
        
        Returns:
            True if GPU is available and functional
        """
        return self.gpus_available and self.current_state != GPUState.UNAVAILABLE
    
    def get_gpu_metrics(self, gpu_id: int = 0) -> Optional[GPUMetrics]:
        """
        Get current GPU metrics
        
        Args:
            gpu_id: GPU identifier (default: 0)
            
        Returns:
            GPUMetrics or None if unavailable
            
        Requirements: 17.2
        """
        if not self.gpus_available:
            return None
        
        try:
            import GPUtil
            
            gpus = GPUtil.getGPUs()
            
            if gpu_id >= len(gpus):
                logging_system.log("ERROR", "Invalid GPU ID", gpu_id=gpu_id)
                return None
            
            gpu = gpus[gpu_id]
            
            # Calculate memory percentage
            memory_percent = (gpu.memoryUsed / gpu.memoryTotal * 100) if gpu.memoryTotal > 0 else 0
            
            # Determine state
            state = self._determine_gpu_state(gpu.temperature, memory_percent, gpu.load * 100)
            
            metrics = GPUMetrics(
                timestamp=datetime.now(),
                gpu_id=gpu.id,
                gpu_name=gpu.name,
                load_percent=gpu.load * 100,
                memory_used_mb=gpu.memoryUsed,
                memory_total_mb=gpu.memoryTotal,
                memory_percent=memory_percent,
                temperature_celsius=gpu.temperature,
                state=state
            )
            
            return metrics
            
        except Exception as e:
            logging_system.log_error("Failed to get GPU metrics", gpu_id=gpu_id, exception=e)
            return None
    
    def _determine_gpu_state(
        self,
        temperature: float,
        memory_percent: float,
        load_percent: float
    ) -> GPUState:
        """
        Determine GPU state based on metrics
        
        Args:
            temperature: GPU temperature in Celsius
            memory_percent: Memory usage percentage
            load_percent: GPU load percentage
            
        Returns:
            GPUState
            
        Requirements: 17.2, 17.3
        """
        # Check critical conditions (highest priority)
        if temperature >= self.config['temp_critical']:
            return GPUState.CRITICAL
        
        if memory_percent >= self.config['memory_critical']:
            return GPUState.CRITICAL
        
        # Check throttle conditions
        if temperature >= self.config['temp_throttle']:
            return GPUState.THROTTLED
        
        if memory_percent >= self.config['memory_normal']:
            return GPUState.THROTTLED
        
        # Check normal conditions
        if temperature >= self.config['temp_normal']:
            return GPUState.NORMAL
        
        if memory_percent >= self.config['memory_optimal']:
            return GPUState.NORMAL
        
        # Check optimal conditions (temperature AND memory both in optimal range)
        if temperature < self.config['temp_optimal'] and memory_percent < self.config['memory_optimal']:
            return GPUState.OPTIMAL
        
        # Default to normal if not clearly in other states
        return GPUState.NORMAL
    
    def allocate_memory(self, allocation_id: str, required_mb: float, gpu_id: int = 0) -> bool:
        """
        Allocate GPU memory
        
        Args:
            allocation_id: Unique identifier for allocation
            required_mb: Required memory in MB
            gpu_id: GPU identifier (default: 0)
            
        Returns:
            True if allocation successful
            
        Requirements: 17.1
        """
        if not self.gpus_available:
            logging_system.log("ERROR", "GPU not available for memory allocation")
            return False
        
        if gpu_id not in self.memory_allocators:
            logging_system.log("ERROR", "Invalid GPU ID", gpu_id=gpu_id)
            return False
        
        return self.memory_allocators[gpu_id].allocate(allocation_id, required_mb)
    
    def deallocate_memory(self, allocation_id: str, gpu_id: int = 0) -> bool:
        """
        Deallocate GPU memory
        
        Args:
            allocation_id: Allocation identifier
            gpu_id: GPU identifier (default: 0)
            
        Returns:
            True if deallocation successful
        """
        if gpu_id not in self.memory_allocators:
            return False
        
        return self.memory_allocators[gpu_id].deallocate(allocation_id)
    
    def get_available_memory(self, gpu_id: int = 0) -> float:
        """
        Get available GPU memory
        
        Args:
            gpu_id: GPU identifier (default: 0)
            
        Returns:
            Available memory in MB
        """
        if gpu_id not in self.memory_allocators:
            return 0.0
        
        return self.memory_allocators[gpu_id].get_available_memory()
    
    def start_monitoring(self):
        """
        Start continuous GPU monitoring
        
        Requirements: 17.2
        """
        if not self.gpus_available:
            logging_system.log("WARNING", "Cannot start monitoring - GPU not available")
            return
        
        if self.is_monitoring:
            logging_system.log("WARNING", "GPU monitoring already running")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logging_system.log("INFO", "GPU monitoring started")
    
    def stop_monitoring(self):
        """Stop GPU monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        logging_system.log("INFO", "GPU monitoring stopped")
    
    def _monitor_loop(self):
        """Main GPU monitoring loop"""
        while self.is_monitoring:
            try:
                # Monitor all GPUs
                for gpu_id in range(self.gpu_count):
                    metrics = self.get_gpu_metrics(gpu_id)
                    
                    if metrics:
                        # Add to history
                        self.metrics_history.append(metrics)
                        if len(self.metrics_history) > self.config['history_size']:
                            self.metrics_history.pop(0)
                        
                        # Check for state changes
                        if metrics.state != self.current_state:
                            self._handle_state_change(self.current_state, metrics.state, metrics)
                            self.current_state = metrics.state
                        
                        # Check throttling conditions
                        self._check_throttling(metrics)
                        
                        # Log metrics periodically
                        if len(self.metrics_history) % 20 == 0:
                            self._log_metrics(metrics)
                
            except Exception as e:
                logging_system.log_error("Error in GPU monitoring loop", exception=e)
            
            time.sleep(self.config['monitor_interval'])
    
    def _handle_state_change(
        self,
        old_state: GPUState,
        new_state: GPUState,
        metrics: GPUMetrics
    ):
        """
        Handle GPU state changes
        
        Args:
            old_state: Previous state
            new_state: New state
            metrics: Current metrics
            
        Requirements: 17.3, 17.5
        """
        logging_system.log("INFO", "GPU state changed",
                          gpu_id=metrics.gpu_id,
                          old_state=old_state.value,
                          new_state=new_state.value,
                          temperature=metrics.temperature_celsius,
                          memory_percent=metrics.memory_percent)
        
        # Trigger callbacks
        self._trigger_callbacks('state_change', old_state, new_state, metrics)
        
        # Handle specific transitions
        if new_state == GPUState.CRITICAL:
            self.last_critical_time = datetime.now()
            self._trigger_callbacks('critical', metrics)
            logging_system.log("CRITICAL", "GPU in critical state",
                              gpu_id=metrics.gpu_id,
                              temperature=metrics.temperature_celsius,
                              memory_percent=metrics.memory_percent)
        
        elif new_state == GPUState.THROTTLED and old_state in [GPUState.OPTIMAL, GPUState.NORMAL]:
            self._trigger_callbacks('throttle', metrics)
            logging_system.log("WARNING", "GPU throttling activated",
                              gpu_id=metrics.gpu_id,
                              temperature=metrics.temperature_celsius)
        
        elif new_state in [GPUState.OPTIMAL, GPUState.NORMAL] and old_state in [GPUState.THROTTLED, GPUState.CRITICAL]:
            self._trigger_callbacks('resume', metrics)
            logging_system.log("INFO", "GPU recovered to normal operation",
                              gpu_id=metrics.gpu_id,
                              temperature=metrics.temperature_celsius)
        
        # Check for overheating
        if metrics.temperature_celsius >= self.config['temp_throttle']:
            self._trigger_callbacks('overheat', metrics)
    
    def _check_throttling(self, metrics: GPUMetrics):
        """
        Check and manage throttling state
        
        Args:
            metrics: Current GPU metrics
            
        Requirements: 17.3, 17.5
        """
        should_throttle = metrics.state in [GPUState.THROTTLED, GPUState.CRITICAL]
        
        if should_throttle and not self.is_throttled:
            # Start throttling
            self.is_throttled = True
            self.throttle_start_time = datetime.now()
            logging_system.log("WARNING", "Processing throttled due to GPU state",
                              state=metrics.state.value,
                              temperature=metrics.temperature_celsius)
        
        elif not should_throttle and self.is_throttled:
            # Check if cooldown period has passed
            if self.throttle_start_time:
                elapsed = (datetime.now() - self.throttle_start_time).total_seconds()
                if elapsed >= self.config['throttle_cooldown_seconds']:
                    self.is_throttled = False
                    self.throttle_start_time = None
                    logging_system.log("INFO", "Processing throttle released",
                                      cooldown_seconds=elapsed)
    
    def should_throttle_processing(self) -> bool:
        """
        Check if processing should be throttled
        
        Returns:
            True if processing should be throttled
            
        Requirements: 17.3, 17.5
        """
        if not self.gpus_available:
            return False
        
        # Check current state
        if self.current_state in [GPUState.THROTTLED, GPUState.CRITICAL]:
            return True
        
        # Check if in cooldown period after critical state
        if self.last_critical_time:
            elapsed = (datetime.now() - self.last_critical_time).total_seconds()
            if elapsed < self.config['critical_pause_seconds']:
                return True
        
        return self.is_throttled
    
    def get_processing_speed_multiplier(self) -> float:
        """
        Get recommended processing speed multiplier
        
        Returns:
            Speed multiplier (0.0 to 1.0)
            - 1.0 = full speed
            - 0.5 = half speed
            - 0.0 = pause
            
        Requirements: 17.3, 17.5
        """
        if not self.gpus_available:
            return 1.0  # No GPU, no throttling
        
        if self.current_state == GPUState.CRITICAL:
            return 0.0  # Pause processing
        
        if self.current_state == GPUState.THROTTLED:
            return 0.5  # Half speed
        
        if self.current_state == GPUState.NORMAL:
            return 0.8  # 80% speed
        
        # OPTIMAL state
        return 1.0  # Full speed
    
    def get_gpu_status(self, gpu_id: int = 0) -> Dict:
        """
        Get comprehensive GPU status
        
        Args:
            gpu_id: GPU identifier (default: 0)
            
        Returns:
            GPU status dictionary
            
        Requirements: 17.1, 17.2, 17.3
        """
        if not self.gpus_available:
            return {
                'available': False,
                'state': GPUState.UNAVAILABLE.value,
                'message': 'GPU not available'
            }
        
        metrics = self.get_gpu_metrics(gpu_id)
        
        if not metrics:
            return {
                'available': False,
                'state': GPUState.UNAVAILABLE.value,
                'error': 'Failed to get GPU metrics'
            }
        
        # Get memory allocation stats
        memory_stats = {}
        if gpu_id in self.memory_allocators:
            memory_stats = self.memory_allocators[gpu_id].get_usage_stats()
        
        return {
            'available': True,
            'gpu_id': metrics.gpu_id,
            'name': metrics.gpu_name,
            'state': metrics.state.value,
            'load_percent': metrics.load_percent,
            'temperature_celsius': metrics.temperature_celsius,
            'memory': {
                'used_mb': metrics.memory_used_mb,
                'total_mb': metrics.memory_total_mb,
                'percent': metrics.memory_percent,
                'allocation_stats': memory_stats
            },
            'thresholds': {
                'temp_optimal': self.config['temp_optimal'],
                'temp_normal': self.config['temp_normal'],
                'temp_throttle': self.config['temp_throttle'],
                'temp_critical': self.config['temp_critical']
            },
            'throttling': {
                'is_throttled': self.is_throttled,
                'should_throttle': self.should_throttle_processing(),
                'speed_multiplier': self.get_processing_speed_multiplier()
            },
            'timestamp': metrics.timestamp.isoformat()
        }
    
    def get_all_gpus_status(self) -> List[Dict]:
        """
        Get status for all GPUs
        
        Returns:
            List of GPU status dictionaries
        """
        if not self.gpus_available:
            return []
        
        return [self.get_gpu_status(gpu_id) for gpu_id in range(self.gpu_count)]
    
    def get_metrics_history(self, gpu_id: Optional[int] = None, limit: Optional[int] = None) -> List[Dict]:
        """
        Get historical GPU metrics
        
        Args:
            gpu_id: Filter by GPU ID (None for all)
            limit: Maximum number of records
            
        Returns:
            List of metrics dictionaries
        """
        history = self.metrics_history
        
        # Filter by GPU ID if specified
        if gpu_id is not None:
            history = [m for m in history if m.gpu_id == gpu_id]
        
        # Apply limit
        if limit:
            history = history[-limit:]
        
        return [
            {
                'timestamp': m.timestamp.isoformat(),
                'gpu_id': m.gpu_id,
                'load_percent': m.load_percent,
                'memory_percent': m.memory_percent,
                'temperature_celsius': m.temperature_celsius,
                'state': m.state.value
            }
            for m in history
        ]
    
    def get_temperature_trend(self, duration_minutes: int = 5, gpu_id: int = 0) -> Dict:
        """
        Get temperature trend analysis
        
        Args:
            duration_minutes: Duration to analyze
            gpu_id: GPU identifier
            
        Returns:
            Temperature trend dictionary
            
        Requirements: 17.2
        """
        if not self.metrics_history:
            return {}
        
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_time and m.gpu_id == gpu_id
        ]
        
        if not recent_metrics:
            return {}
        
        temps = [m.temperature_celsius for m in recent_metrics]
        
        return {
            'duration_minutes': duration_minutes,
            'sample_count': len(temps),
            'current_temp': temps[-1],
            'min_temp': min(temps),
            'max_temp': max(temps),
            'avg_temp': sum(temps) / len(temps),
            'trend': 'rising' if temps[-1] > temps[0] else 'falling',
            'is_stable': max(temps) - min(temps) < 5  # Stable if variation < 5°C
        }
    
    def register_callback(self, event: str, callback: Callable):
        """
        Register callback for GPU events
        
        Args:
            event: Event type ('state_change', 'throttle', 'resume', 'critical', 'overheat')
            callback: Callback function
        """
        if event not in self.callbacks:
            raise ValueError(f"Invalid event type: {event}")
        
        self.callbacks[event].append(callback)
        logging_system.log("DEBUG", "GPU callback registered", event=event)
    
    def _trigger_callbacks(self, event: str, *args):
        """Trigger all callbacks for an event"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                logging_system.log_error("GPU callback execution failed",
                                        event=event,
                                        exception=e)
    
    def _log_metrics(self, metrics: GPUMetrics):
        """Log GPU metrics"""
        logging_system.log("DEBUG", "GPU metrics",
                          gpu_id=metrics.gpu_id,
                          load_percent=metrics.load_percent,
                          memory_percent=metrics.memory_percent,
                          temperature=metrics.temperature_celsius,
                          state=metrics.state.value)
    
    def update_config(self, config_updates: Dict) -> bool:
        """
        Update GPU manager configuration
        
        Args:
            config_updates: Dictionary of config updates
            
        Returns:
            True if successful
        """
        try:
            for key, value in config_updates.items():
                if key in self.config:
                    self.config[key] = value
            
            logging_system.log("INFO", "GPU manager config updated",
                              updates=config_updates)
            
            return True
            
        except Exception as e:
            logging_system.log_error("Failed to update GPU config", exception=e)
            return False


# Global instance
_gpu_manager = None


def get_gpu_manager() -> GPUManager:
    """Get global GPU manager instance"""
    global _gpu_manager
    if _gpu_manager is None:
        _gpu_manager = GPUManager()
    return _gpu_manager
