"""
Tests for Resource Manager

Requirements: 4.3, 12.4, 17.3
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from resource_manager import (
    ResourceManager,
    ResourceState,
    ResourceMetrics,
    get_resource_manager
)
from datetime import datetime, timedelta


class TestResourceManager:
    """Test suite for ResourceManager"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.manager = ResourceManager()
    
    def teardown_method(self):
        """Cleanup after tests"""
        if self.manager.is_monitoring:
            self.manager.stop_monitoring()
    
    def test_initialization(self):
        """Test resource manager initialization"""
        assert self.manager is not None
        assert self.manager.current_state == ResourceState.NORMAL
        assert not self.manager.is_monitoring
        assert len(self.manager.metrics_history) == 0
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_get_current_metrics(self, mock_disk, mock_memory, mock_cpu):
        """Test getting current resource metrics"""
        # Mock system metrics
        mock_cpu.return_value = 45.5
        mock_memory.return_value = Mock(
            percent=60.0,
            available=4096 * 1024 * 1024
        )
        mock_disk.return_value = Mock(percent=70.0)
        
        metrics = self.manager.get_current_metrics()
        
        assert isinstance(metrics, ResourceMetrics)
        assert metrics.cpu_percent == 45.5
        assert metrics.memory_percent == 60.0
        assert metrics.disk_usage_percent == 70.0
        assert isinstance(metrics.timestamp, datetime)
    
    def test_determine_state_idle(self):
        """Test state determination for idle system"""
        state = self.manager._determine_state(
            cpu_percent=15.0,
            memory_percent=40.0,
            gpu_temp=None,
            gpu_load=None
        )
        assert state == ResourceState.IDLE
    
    def test_determine_state_normal(self):
        """Test state determination for normal system"""
        state = self.manager._determine_state(
            cpu_percent=50.0,
            memory_percent=60.0,
            gpu_temp=60.0,
            gpu_load=40.0
        )
        assert state == ResourceState.NORMAL
    
    def test_determine_state_busy_cpu(self):
        """Test state determination for busy CPU"""
        state = self.manager._determine_state(
            cpu_percent=85.0,
            memory_percent=60.0,
            gpu_temp=None,
            gpu_load=None
        )
        assert state == ResourceState.BUSY
    
    def test_determine_state_busy_gpu(self):
        """Test state determination for hot GPU"""
        state = self.manager._determine_state(
            cpu_percent=50.0,
            memory_percent=60.0,
            gpu_temp=78.0,
            gpu_load=80.0
        )
        assert state == ResourceState.BUSY
    
    def test_determine_state_critical_cpu(self):
        """Test state determination for critical CPU"""
        state = self.manager._determine_state(
            cpu_percent=96.0,
            memory_percent=60.0,
            gpu_temp=None,
            gpu_load=None
        )
        assert state == ResourceState.CRITICAL
    
    def test_determine_state_critical_gpu(self):
        """Test state determination for critical GPU temperature"""
        state = self.manager._determine_state(
            cpu_percent=50.0,
            memory_percent=60.0,
            gpu_temp=87.0,
            gpu_load=90.0
        )
        assert state == ResourceState.CRITICAL
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_should_throttle_processing_normal(self, mock_disk, mock_memory, mock_cpu):
        """Test throttling decision for normal state"""
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0, available=4096 * 1024 * 1024)
        mock_disk.return_value = Mock(percent=70.0)
        
        # Get metrics to populate history
        self.manager.get_current_metrics()
        
        assert not self.manager.should_throttle_processing()
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_should_throttle_processing_busy(self, mock_disk, mock_memory, mock_cpu):
        """Test throttling decision for busy state"""
        mock_cpu.return_value = 85.0
        mock_memory.return_value = Mock(percent=60.0, available=4096 * 1024 * 1024)
        mock_disk.return_value = Mock(percent=70.0)
        
        # Get metrics to populate history
        self.manager.get_current_metrics()
        
        assert self.manager.should_throttle_processing()
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_get_recommended_speed_multiplier_idle(self, mock_disk, mock_memory, mock_cpu):
        """Test speed multiplier for idle state"""
        mock_cpu.return_value = 15.0
        mock_memory.return_value = Mock(percent=40.0, available=8192 * 1024 * 1024)
        mock_disk.return_value = Mock(percent=50.0)
        
        self.manager.get_current_metrics()
        
        speed = self.manager.get_recommended_speed_multiplier()
        assert speed == 1.0  # Full speed when idle
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_get_recommended_speed_multiplier_busy(self, mock_disk, mock_memory, mock_cpu):
        """Test speed multiplier for busy state"""
        mock_cpu.return_value = 85.0
        mock_memory.return_value = Mock(percent=60.0, available=4096 * 1024 * 1024)
        mock_disk.return_value = Mock(percent=70.0)
        
        self.manager.get_current_metrics()
        
        speed = self.manager.get_recommended_speed_multiplier()
        assert speed == 0.5  # Half speed when busy
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_get_recommended_speed_multiplier_critical(self, mock_disk, mock_memory, mock_cpu):
        """Test speed multiplier for critical state"""
        mock_cpu.return_value = 96.0
        mock_memory.return_value = Mock(percent=60.0, available=4096 * 1024 * 1024)
        mock_disk.return_value = Mock(percent=70.0)
        
        self.manager.get_current_metrics()
        
        speed = self.manager.get_recommended_speed_multiplier()
        assert speed == 0.0  # Pause when critical
    
    def test_idle_detection_not_idle(self):
        """Test idle detection when system is active"""
        assert not self.manager.is_system_idle()
        assert self.manager.get_idle_duration() == 0.0
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_idle_detection_becomes_idle(self, mock_disk, mock_memory, mock_cpu):
        """Test idle detection when system becomes idle"""
        mock_cpu.return_value = 10.0
        mock_memory.return_value = Mock(percent=40.0, available=8192 * 1024 * 1024)
        mock_disk.return_value = Mock(percent=50.0)
        
        # Set idle threshold to 1 second for testing
        self.manager.config['idle_threshold_seconds'] = 1
        
        # Get metrics to trigger idle detection
        metrics = self.manager.get_current_metrics()
        self.manager._check_idle_state(metrics)
        
        # Should not be idle yet
        assert not self.manager.is_system_idle()
        
        # Wait for idle threshold
        time.sleep(1.1)
        
        # Should now be idle
        assert self.manager.is_system_idle()
        assert self.manager.get_idle_duration() >= 1.0
    
    @patch('psutil.cpu_percent')
    @patch('psutil.cpu_count')
    @patch('psutil.cpu_freq')
    def test_get_cpu_status(self, mock_freq, mock_count, mock_cpu):
        """Test getting CPU status"""
        mock_cpu.side_effect = [50.0, [45.0, 55.0, 48.0, 52.0]]
        mock_count.return_value = 4
        mock_freq.return_value = Mock(current=3600.0)
        
        status = self.manager.get_cpu_status()
        
        assert status['usage_percent'] == 50.0
        assert len(status['per_core_percent']) == 4
        assert status['core_count'] == 4
        assert status['frequency_mhz'] == 3600.0
        assert not status['is_busy']
        assert not status['is_critical']
    
    @patch('psutil.virtual_memory')
    def test_get_memory_status(self, mock_memory):
        """Test getting memory status"""
        mock_memory.return_value = Mock(
            total=16 * 1024 * 1024 * 1024,
            available=8 * 1024 * 1024 * 1024,
            used=8 * 1024 * 1024 * 1024,
            percent=50.0
        )
        
        status = self.manager.get_memory_status()
        
        assert status['total_mb'] == 16 * 1024
        assert status['available_mb'] == 8 * 1024
        assert status['percent'] == 50.0
        assert not status['is_busy']
        assert not status['is_critical']
    
    @patch('resource_manager.ResourceManager._check_gpu_availability')
    def test_get_gpu_status_not_available(self, mock_check):
        """Test getting GPU status when GPU not available"""
        mock_check.return_value = False
        manager = ResourceManager()
        
        status = manager.get_gpu_status()
        
        assert not status['available']
        assert 'message' in status
    
    def test_get_gpu_status_available(self):
        """Test getting GPU status when GPU is available"""
        # Skip if GPUtil not available
        try:
            import GPUtil
        except ImportError:
            pytest.skip("GPUtil not available")
        
        # This test will use real GPU if available, or skip
        status = self.manager.get_gpu_status()
        
        # Just verify the structure is correct
        assert 'available' in status
        if status['available']:
            assert 'name' in status
            assert 'load' in status
            assert 'temperature' in status
    
    def test_callback_registration(self):
        """Test callback registration"""
        callback = Mock()
        
        self.manager.register_callback('state_change', callback)
        
        assert callback in self.manager.callbacks['state_change']
    
    def test_callback_invalid_event(self):
        """Test callback registration with invalid event"""
        callback = Mock()
        
        with pytest.raises(ValueError):
            self.manager.register_callback('invalid_event', callback)
    
    def test_callback_execution(self):
        """Test callback execution on state change"""
        callback = Mock()
        self.manager.register_callback('state_change', callback)
        
        # Trigger state change
        self.manager._handle_state_change(ResourceState.NORMAL, ResourceState.BUSY)
        
        callback.assert_called_once_with(ResourceState.NORMAL, ResourceState.BUSY)
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.cpu_count')
    @patch('psutil.cpu_freq')
    def test_get_system_status(self, mock_freq, mock_count, mock_disk, mock_memory, mock_cpu):
        """Test getting comprehensive system status"""
        # Mock cpu_percent to return consistent values
        mock_cpu.return_value = 50.0
        mock_count.return_value = 4
        mock_freq.return_value = Mock(current=3600.0)
        mock_memory.return_value = Mock(
            total=16 * 1024 * 1024 * 1024,
            available=8 * 1024 * 1024 * 1024,
            used=8 * 1024 * 1024 * 1024,
            percent=50.0
        )
        mock_disk.return_value = Mock(percent=70.0)
        
        status = self.manager.get_system_status()
        
        assert 'timestamp' in status
        assert 'state' in status
        assert 'cpu' in status
        assert 'memory' in status
        assert 'gpu' in status
        assert 'is_idle' in status
        assert 'should_throttle' in status
        assert 'recommended_speed' in status
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_metrics_history(self, mock_disk, mock_memory, mock_cpu):
        """Test metrics history tracking"""
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0, available=4096 * 1024 * 1024)
        mock_disk.return_value = Mock(percent=70.0)
        
        # Generate some metrics and add to history
        for _ in range(5):
            metrics = self.manager.get_current_metrics()
            self.manager.metrics_history.append(metrics)
        
        assert len(self.manager.metrics_history) >= 5
        
        history = self.manager.get_metrics_history(limit=3)
        assert len(history) == 3
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_average_metrics(self, mock_disk, mock_memory, mock_cpu):
        """Test average metrics calculation"""
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0, available=4096 * 1024 * 1024)
        mock_disk.return_value = Mock(percent=70.0)
        
        # Generate metrics
        for _ in range(5):
            metrics = self.manager.get_current_metrics()
            self.manager.metrics_history.append(metrics)
        
        avg = self.manager.get_average_metrics(duration_minutes=10)
        
        assert 'avg_cpu_percent' in avg
        assert 'avg_memory_percent' in avg
        assert avg['sample_count'] == 5
    
    def test_config_update(self):
        """Test configuration update"""
        updates = {
            'cpu_limit_percent': 85,
            'gpu_temp_limit_celsius': 80
        }
        
        result = self.manager.update_config(updates)
        
        assert result is True
        assert self.manager.config['cpu_limit_percent'] == 85
        assert self.manager.config['gpu_temp_limit_celsius'] == 80
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_monitoring_start_stop(self, mock_disk, mock_memory, mock_cpu):
        """Test starting and stopping monitoring"""
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0, available=4096 * 1024 * 1024)
        mock_disk.return_value = Mock(percent=70.0)
        
        # Start monitoring
        self.manager.start_monitoring()
        assert self.manager.is_monitoring
        assert self.manager.monitor_thread is not None
        
        # Wait a bit for monitoring to run
        time.sleep(0.5)
        
        # Stop monitoring
        self.manager.stop_monitoring()
        assert not self.manager.is_monitoring


class TestResourceManagerIntegration:
    """Integration tests for ResourceManager"""
    
    def test_global_instance(self):
        """Test global resource manager instance"""
        manager1 = get_resource_manager()
        manager2 = get_resource_manager()
        
        assert manager1 is manager2
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_real_metrics_collection(self, mock_disk, mock_memory, mock_cpu):
        """Test real metrics collection flow"""
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0, available=4096 * 1024 * 1024)
        mock_disk.return_value = Mock(percent=70.0)
        
        manager = ResourceManager()
        
        # Collect metrics
        metrics = manager.get_current_metrics()
        
        assert metrics is not None
        assert metrics.cpu_percent >= 0
        assert metrics.memory_percent >= 0
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_throttling_workflow(self, mock_disk, mock_memory, mock_cpu):
        """Test complete throttling workflow"""
        manager = ResourceManager()
        
        # Start with normal state
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0, available=4096 * 1024 * 1024)
        mock_disk.return_value = Mock(percent=70.0)
        
        metrics = manager.get_current_metrics()
        manager.metrics_history.append(metrics)
        assert not manager.should_throttle_processing()
        assert manager.get_recommended_speed_multiplier() == 0.8
        
        # Simulate high CPU usage
        mock_cpu.return_value = 85.0
        
        metrics = manager.get_current_metrics()
        manager.metrics_history.append(metrics)
        assert manager.should_throttle_processing()
        assert manager.get_recommended_speed_multiplier() == 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
