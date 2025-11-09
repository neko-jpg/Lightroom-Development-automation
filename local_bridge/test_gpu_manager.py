"""
Test suite for GPU Manager

Tests GPU monitoring, memory allocation, temperature monitoring,
and throttling functionality.

Requirements: 17.1, 17.2, 17.3, 17.5
"""

import pytest
import time
from gpu_manager import (
    GPUManager,
    GPUState,
    GPUMemoryAllocation,
    get_gpu_manager
)


class TestGPUMemoryAllocation:
    """Test GPU memory allocation tracker"""
    
    def test_allocation_initialization(self):
        """Test memory allocator initialization"""
        allocator = GPUMemoryAllocation(gpu_id=0, total_memory_mb=8192, limit_mb=6144)
        
        assert allocator.gpu_id == 0
        assert allocator.total_memory_mb == 8192
        assert allocator.limit_mb == 6144
        assert allocator.get_available_memory() == 6144
    
    def test_successful_allocation(self):
        """Test successful memory allocation"""
        allocator = GPUMemoryAllocation(gpu_id=0, total_memory_mb=8192, limit_mb=6144)
        
        success = allocator.allocate("test_alloc_1", 1024)
        
        assert success is True
        assert allocator.get_available_memory() == 5120  # 6144 - 1024
    
    def test_multiple_allocations(self):
        """Test multiple memory allocations"""
        allocator = GPUMemoryAllocation(gpu_id=0, total_memory_mb=8192, limit_mb=6144)
        
        assert allocator.allocate("alloc_1", 1024) is True
        assert allocator.allocate("alloc_2", 2048) is True
        assert allocator.allocate("alloc_3", 512) is True
        
        assert allocator.get_available_memory() == 2560  # 6144 - 3584
    
    def test_allocation_exceeds_limit(self):
        """Test allocation that exceeds limit"""
        allocator = GPUMemoryAllocation(gpu_id=0, total_memory_mb=8192, limit_mb=6144)
        
        # Allocate most of the memory
        allocator.allocate("alloc_1", 5000)
        
        # Try to allocate more than available
        success = allocator.allocate("alloc_2", 2000)
        
        assert success is False
        assert allocator.get_available_memory() == 1144  # 6144 - 5000
    
    def test_duplicate_allocation_id(self):
        """Test allocation with duplicate ID"""
        allocator = GPUMemoryAllocation(gpu_id=0, total_memory_mb=8192, limit_mb=6144)
        
        assert allocator.allocate("test_id", 1024) is True
        assert allocator.allocate("test_id", 512) is False  # Duplicate ID
    
    def test_deallocation(self):
        """Test memory deallocation"""
        allocator = GPUMemoryAllocation(gpu_id=0, total_memory_mb=8192, limit_mb=6144)
        
        allocator.allocate("alloc_1", 1024)
        allocator.allocate("alloc_2", 2048)
        
        assert allocator.get_available_memory() == 3072  # 6144 - 3072
        
        success = allocator.deallocate("alloc_1")
        
        assert success is True
        assert allocator.get_available_memory() == 4096  # 3072 + 1024
    
    def test_deallocation_nonexistent(self):
        """Test deallocation of nonexistent allocation"""
        allocator = GPUMemoryAllocation(gpu_id=0, total_memory_mb=8192, limit_mb=6144)
        
        success = allocator.deallocate("nonexistent")
        
        assert success is False
    
    def test_usage_stats(self):
        """Test getting usage statistics"""
        allocator = GPUMemoryAllocation(gpu_id=0, total_memory_mb=8192, limit_mb=6144)
        
        allocator.allocate("alloc_1", 1024)
        allocator.allocate("alloc_2", 2048)
        
        stats = allocator.get_usage_stats()
        
        assert stats['total_mb'] == 8192
        assert stats['limit_mb'] == 6144
        assert stats['allocated_mb'] == 3072
        assert stats['available_mb'] == 3072
        assert stats['allocation_count'] == 2
        assert 'alloc_1' in stats['allocations']
        assert 'alloc_2' in stats['allocations']


class TestGPUManager:
    """Test GPU Manager"""
    
    def test_gpu_manager_initialization(self):
        """Test GPU manager initialization"""
        manager = GPUManager()
        
        assert manager is not None
        assert manager.config is not None
        assert 'temp_optimal' in manager.config
        assert 'memory_limit_mb' in manager.config
    
    def test_gpu_availability_check(self):
        """Test GPU availability detection"""
        manager = GPUManager()
        
        # Should return boolean
        is_available = manager.is_available()
        assert isinstance(is_available, bool)
    
    def test_get_gpu_metrics(self):
        """Test getting GPU metrics"""
        manager = GPUManager()
        
        if not manager.is_available():
            pytest.skip("GPU not available")
        
        metrics = manager.get_gpu_metrics(gpu_id=0)
        
        if metrics:
            assert metrics.gpu_id >= 0
            assert metrics.gpu_name is not None
            assert 0 <= metrics.load_percent <= 100
            assert metrics.memory_total_mb > 0
            assert metrics.temperature_celsius > 0
            assert isinstance(metrics.state, GPUState)
    
    def test_gpu_state_determination(self):
        """Test GPU state determination logic"""
        manager = GPUManager()
        
        # Test optimal state (< 65°C, < 70% memory)
        state = manager._determine_gpu_state(
            temperature=60,
            memory_percent=50,
            load_percent=30
        )
        assert state == GPUState.OPTIMAL
        
        # Test normal state (65-75°C, 70-85% memory)
        state = manager._determine_gpu_state(
            temperature=70,
            memory_percent=75,
            load_percent=60
        )
        assert state == GPUState.NORMAL
        
        # Test throttled state (75-85°C or 85-95% memory)
        state = manager._determine_gpu_state(
            temperature=80,
            memory_percent=88,
            load_percent=80
        )
        assert state == GPUState.THROTTLED
        
        # Test critical state (>= 90°C or >= 95% memory)
        state = manager._determine_gpu_state(
            temperature=92,
            memory_percent=96,
            load_percent=95
        )
        assert state == GPUState.CRITICAL
    
    def test_memory_allocation_integration(self):
        """Test memory allocation through GPU manager"""
        manager = GPUManager()
        
        if not manager.is_available():
            pytest.skip("GPU not available")
        
        # Test allocation
        success = manager.allocate_memory("test_alloc", 1024, gpu_id=0)
        
        if success:
            # Check available memory decreased
            available = manager.get_available_memory(gpu_id=0)
            assert available >= 0
            
            # Test deallocation
            success = manager.deallocate_memory("test_alloc", gpu_id=0)
            assert success is True
    
    def test_throttling_logic(self):
        """Test processing throttling logic"""
        manager = GPUManager()
        
        # Should return boolean
        should_throttle = manager.should_throttle_processing()
        assert isinstance(should_throttle, bool)
        
        # Get speed multiplier
        speed = manager.get_processing_speed_multiplier()
        assert 0.0 <= speed <= 1.0
    
    def test_gpu_status(self):
        """Test getting GPU status"""
        manager = GPUManager()
        
        status = manager.get_gpu_status(gpu_id=0)
        
        assert 'available' in status
        assert 'state' in status
        
        if status['available']:
            assert 'gpu_id' in status
            assert 'name' in status
            assert 'temperature_celsius' in status
            assert 'memory' in status
            assert 'throttling' in status
    
    def test_all_gpus_status(self):
        """Test getting all GPUs status"""
        manager = GPUManager()
        
        statuses = manager.get_all_gpus_status()
        
        assert isinstance(statuses, list)
        
        if manager.is_available():
            assert len(statuses) > 0
    
    def test_temperature_trend(self):
        """Test temperature trend analysis"""
        manager = GPUManager()
        
        if not manager.is_available():
            pytest.skip("GPU not available")
        
        # Start monitoring to collect data
        manager.start_monitoring()
        time.sleep(5)  # Wait for some data
        manager.stop_monitoring()
        
        trend = manager.get_temperature_trend(duration_minutes=1, gpu_id=0)
        
        if trend:
            assert 'current_temp' in trend
            assert 'min_temp' in trend
            assert 'max_temp' in trend
            assert 'avg_temp' in trend
            assert 'trend' in trend
    
    def test_metrics_history(self):
        """Test metrics history retrieval"""
        manager = GPUManager()
        
        if not manager.is_available():
            pytest.skip("GPU not available")
        
        # Start monitoring to collect data
        manager.start_monitoring()
        time.sleep(5)
        manager.stop_monitoring()
        
        history = manager.get_metrics_history(limit=10)
        
        assert isinstance(history, list)
        
        if history:
            assert 'timestamp' in history[0]
            assert 'gpu_id' in history[0]
            assert 'temperature_celsius' in history[0]
    
    def test_config_update(self):
        """Test configuration update"""
        manager = GPUManager()
        
        original_temp = manager.config['temp_optimal']
        
        success = manager.update_config({'temp_optimal': 70})
        
        assert success is True
        assert manager.config['temp_optimal'] == 70
        
        # Restore original
        manager.update_config({'temp_optimal': original_temp})
    
    def test_callback_registration(self):
        """Test callback registration"""
        manager = GPUManager()
        
        callback_called = {'count': 0}
        
        def test_callback(*args):
            callback_called['count'] += 1
        
        manager.register_callback('state_change', test_callback)
        
        # Trigger callback manually
        manager._trigger_callbacks('state_change', GPUState.NORMAL, GPUState.THROTTLED)
        
        assert callback_called['count'] == 1
    
    def test_monitoring_start_stop(self):
        """Test monitoring start and stop"""
        manager = GPUManager()
        
        if not manager.is_available():
            pytest.skip("GPU not available")
        
        # Start monitoring
        manager.start_monitoring()
        assert manager.is_monitoring is True
        
        time.sleep(2)
        
        # Stop monitoring
        manager.stop_monitoring()
        assert manager.is_monitoring is False
    
    def test_global_instance(self):
        """Test global GPU manager instance"""
        manager1 = get_gpu_manager()
        manager2 = get_gpu_manager()
        
        # Should return same instance
        assert manager1 is manager2


class TestGPUManagerIntegration:
    """Integration tests for GPU manager"""
    
    def test_full_monitoring_cycle(self):
        """Test complete monitoring cycle"""
        manager = GPUManager()
        
        if not manager.is_available():
            pytest.skip("GPU not available")
        
        # Start monitoring
        manager.start_monitoring()
        
        # Wait for data collection
        time.sleep(10)
        
        # Check metrics were collected
        assert len(manager.metrics_history) > 0
        
        # Get current status
        status = manager.get_gpu_status()
        assert status['available'] is True
        
        # Check throttling status
        should_throttle = manager.should_throttle_processing()
        assert isinstance(should_throttle, bool)
        
        # Stop monitoring
        manager.stop_monitoring()
    
    def test_memory_allocation_lifecycle(self):
        """Test complete memory allocation lifecycle"""
        manager = GPUManager()
        
        if not manager.is_available():
            pytest.skip("GPU not available")
        
        # Allocate memory
        alloc_id = "test_lifecycle"
        success = manager.allocate_memory(alloc_id, 512)
        
        if success:
            # Check allocation
            available_before = manager.get_available_memory()
            
            # Deallocate
            success = manager.deallocate_memory(alloc_id)
            assert success is True
            
            # Check memory freed
            available_after = manager.get_available_memory()
            assert available_after > available_before
    
    def test_state_transitions(self):
        """Test GPU state transitions"""
        manager = GPUManager()
        
        state_changes = []
        
        def track_state_change(old_state, new_state, metrics):
            state_changes.append((old_state, new_state))
        
        manager.register_callback('state_change', track_state_change)
        
        # Simulate state changes by updating current state
        initial_state = manager.current_state
        
        # Create a mock metrics object for testing
        if manager.is_available():
            metrics = manager.get_gpu_metrics()
        else:
            # Skip test if GPU not available
            pytest.skip("GPU not available")
        
        # This would normally happen through monitoring
        # For testing, we just verify the callback mechanism works
        manager._handle_state_change(GPUState.NORMAL, GPUState.THROTTLED, metrics)
        
        assert len(state_changes) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
