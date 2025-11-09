"""
Resource-Aware Job Queue Integration

This module integrates the resource manager with the job queue system
to provide dynamic processing speed adjustment based on system resources.

Requirements: 4.3, 12.4, 17.3
"""

from resource_manager import get_resource_manager, ResourceState
from job_queue_manager import get_job_queue_manager
from logging_system import get_logging_system
from typing import Optional
import threading
import time

logging_system = get_logging_system()


class ResourceAwareQueue:
    """
    Resource-aware job queue controller
    
    Automatically adjusts job processing based on system resources:
    - Pauses queue when resources are critical
    - Throttles processing when resources are busy
    - Maximizes speed when system is idle
    - Monitors GPU temperature and adjusts accordingly
    
    Requirements: 4.3, 12.4, 17.3
    """
    
    def __init__(self):
        """Initialize resource-aware queue controller"""
        self.resource_manager = get_resource_manager()
        self.job_queue_manager = get_job_queue_manager()
        
        self.is_running = False
        self.control_thread: Optional[threading.Thread] = None
        
        self.current_speed = 1.0
        self.is_paused = False
        
        self.config = {
            'check_interval': 10,  # Check resources every 10 seconds
            'auto_adjust': True,   # Enable automatic adjustment
            'pause_on_critical': True,  # Pause queue on critical state
            'resume_on_recovery': True,  # Resume queue when recovered
        }
        
        # Register callbacks with resource manager
        self._register_callbacks()
        
        logging_system.log("INFO", "Resource-aware queue controller initialized")
    
    def _register_callbacks(self):
        """Register callbacks with resource manager"""
        self.resource_manager.register_callback('critical', self._handle_critical_state)
        self.resource_manager.register_callback('throttle', self._handle_throttle_state)
        self.resource_manager.register_callback('resume', self._handle_resume_state)
    
    def start(self):
        """
        Start resource-aware queue control
        
        Requirements: 4.3
        """
        if self.is_running:
            logging_system.log("WARNING", "Resource-aware queue already running")
            return
        
        # Start resource monitoring
        self.resource_manager.start_monitoring()
        
        # Start control loop
        self.is_running = True
        self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self.control_thread.start()
        
        logging_system.log("INFO", "Resource-aware queue control started")
    
    def stop(self):
        """Stop resource-aware queue control"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.control_thread:
            self.control_thread.join(timeout=10)
        
        self.resource_manager.stop_monitoring()
        
        logging_system.log("INFO", "Resource-aware queue control stopped")
    
    def _control_loop(self):
        """Main control loop (runs in separate thread)"""
        while self.is_running:
            try:
                if self.config['auto_adjust']:
                    self._adjust_processing_speed()
            except Exception as e:
                logging_system.log_error("Error in resource control loop", exception=e)
            
            time.sleep(self.config['check_interval'])
    
    def _adjust_processing_speed(self):
        """
        Adjust processing speed based on current resources
        
        Requirements: 4.3, 12.4
        """
        # Get recommended speed
        recommended_speed = self.resource_manager.get_recommended_speed_multiplier()
        
        # Check if speed changed significantly
        if abs(recommended_speed - self.current_speed) > 0.1:
            old_speed = self.current_speed
            self.current_speed = recommended_speed
            
            logging_system.log("INFO", "Processing speed adjusted",
                              old_speed=old_speed,
                              new_speed=recommended_speed)
            
            # Handle pause/resume
            if recommended_speed == 0.0 and not self.is_paused:
                self._pause_queue()
            elif recommended_speed > 0.0 and self.is_paused:
                self._resume_queue()
    
    def _pause_queue(self):
        """Pause job queue processing"""
        if not self.config['pause_on_critical']:
            return
        
        success = self.job_queue_manager.pause_queue()
        if success:
            self.is_paused = True
            logging_system.log("WARNING", "Job queue paused due to critical resources")
    
    def _resume_queue(self):
        """Resume job queue processing"""
        if not self.config['resume_on_recovery']:
            return
        
        success = self.job_queue_manager.resume_queue()
        if success:
            self.is_paused = False
            logging_system.log("INFO", "Job queue resumed after resource recovery")
    
    def _handle_critical_state(self, state: ResourceState):
        """
        Handle critical resource state
        
        Args:
            state: Current resource state
        """
        logging_system.log("CRITICAL", "System resources in critical state",
                          state=state.value)
        
        if self.config['pause_on_critical']:
            self._pause_queue()
    
    def _handle_throttle_state(self, state: ResourceState):
        """
        Handle throttle resource state
        
        Args:
            state: Current resource state
        """
        logging_system.log("WARNING", "System resources busy, throttling processing",
                          state=state.value)
        
        # Reduce processing speed
        self.current_speed = 0.5
    
    def _handle_resume_state(self, state: ResourceState):
        """
        Handle resume resource state
        
        Args:
            state: Current resource state
        """
        logging_system.log("INFO", "System resources recovered",
                          state=state.value)
        
        if self.is_paused:
            self._resume_queue()
        
        # Restore normal speed
        if state == ResourceState.IDLE:
            self.current_speed = 1.0
        else:
            self.current_speed = 0.8
    
    def get_status(self) -> dict:
        """
        Get current status of resource-aware queue
        
        Returns:
            Status dictionary
        """
        system_status = self.resource_manager.get_system_status()
        queue_stats = self.job_queue_manager.get_queue_stats()
        
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'current_speed': self.current_speed,
            'auto_adjust': self.config['auto_adjust'],
            'system': system_status,
            'queue': queue_stats
        }
    
    def set_auto_adjust(self, enabled: bool):
        """
        Enable or disable automatic adjustment
        
        Args:
            enabled: Whether to enable auto-adjustment
        """
        self.config['auto_adjust'] = enabled
        logging_system.log("INFO", "Auto-adjustment setting changed",
                          enabled=enabled)
    
    def force_pause(self):
        """Force pause queue regardless of resources"""
        self._pause_queue()
        logging_system.log("INFO", "Queue manually paused")
    
    def force_resume(self):
        """Force resume queue regardless of resources"""
        self._resume_queue()
        logging_system.log("INFO", "Queue manually resumed")
    
    def get_recommended_concurrency(self) -> int:
        """
        Get recommended number of concurrent jobs based on resources
        
        Returns:
            Recommended concurrent job count
            
        Requirements: 4.3, 12.4
        """
        system_status = self.resource_manager.get_system_status()
        
        # Base concurrency on CPU cores
        cpu_status = system_status['cpu']
        core_count = cpu_status.get('core_count', 4)
        
        # Adjust based on resource state
        state = system_status['state']
        
        if state == 'critical':
            return 0
        elif state == 'busy':
            return max(1, core_count // 4)
        elif state == 'idle':
            return core_count
        else:  # normal
            return max(2, core_count // 2)
    
    def should_accept_new_jobs(self) -> bool:
        """
        Determine if new jobs should be accepted
        
        Returns:
            True if new jobs can be accepted
        """
        if self.is_paused:
            return False
        
        system_status = self.resource_manager.get_system_status()
        
        # Don't accept new jobs in critical state
        if system_status['state'] == 'critical':
            return False
        
        # Check GPU temperature if available
        gpu_status = system_status.get('gpu', {})
        if gpu_status.get('is_critical', False):
            return False
        
        return True
    
    def get_processing_delay(self) -> float:
        """
        Get recommended delay between job submissions
        
        Returns:
            Delay in seconds
            
        Requirements: 4.3
        """
        if self.current_speed >= 1.0:
            return 0.0
        elif self.current_speed >= 0.5:
            return 2.0
        elif self.current_speed > 0.0:
            return 5.0
        else:
            return float('inf')  # Paused


# Global instance
_resource_aware_queue = None

def get_resource_aware_queue() -> ResourceAwareQueue:
    """Get global resource-aware queue instance"""
    global _resource_aware_queue
    if _resource_aware_queue is None:
        _resource_aware_queue = ResourceAwareQueue()
    return _resource_aware_queue
