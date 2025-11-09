"""
Tests for Batch Processing Controller

Requirements: 11.4, 14.3
"""

import pytest
import json
import pathlib
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from batch_controller import (
    BatchController,
    BatchStatus,
    BatchState,
    get_batch_controller
)


@pytest.fixture
def temp_state_dir():
    """Create temporary state directory"""
    temp_dir = tempfile.mkdtemp()
    yield pathlib.Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_job_queue_manager():
    """Mock job queue manager"""
    with patch('batch_controller.get_job_queue_manager') as mock:
        manager = Mock()
        manager.submit_batch_processing.return_value = ['task1', 'task2', 'task3']
        manager.cancel_job.return_value = True
        mock.return_value = manager
        yield manager


@pytest.fixture
def batch_controller(temp_state_dir, mock_job_queue_manager):
    """Create batch controller instance"""
    return BatchController(state_dir=temp_state_dir)


class TestBatchState:
    """Test BatchState dataclass"""
    
    def test_batch_state_creation(self):
        """Test creating batch state"""
        state = BatchState(
            batch_id="test_batch",
            session_id=1,
            photo_ids=[1, 2, 3],
            processed_photo_ids=[],
            failed_photo_ids=[],
            status=BatchStatus.PENDING.value,
            created_at=datetime.utcnow().isoformat(),
            started_at=None,
            paused_at=None,
            completed_at=None,
            total_photos=3,
            processed_count=0,
            failed_count=0,
            config=None,
            task_ids=[]
        )
        
        assert state.batch_id == "test_batch"
        assert state.total_photos == 3
        assert state.status == BatchStatus.PENDING.value
    
    def test_batch_state_to_dict(self):
        """Test converting batch state to dictionary"""
        state = BatchState(
            batch_id="test_batch",
            session_id=1,
            photo_ids=[1, 2, 3],
            processed_photo_ids=[],
            failed_photo_ids=[],
            status=BatchStatus.PENDING.value,
            created_at=datetime.utcnow().isoformat(),
            started_at=None,
            paused_at=None,
            completed_at=None,
            total_photos=3,
            processed_count=0,
            failed_count=0,
            config=None,
            task_ids=[]
        )
        
        data = state.to_dict()
        
        assert isinstance(data, dict)
        assert data['batch_id'] == "test_batch"
        assert data['total_photos'] == 3
    
    def test_batch_state_from_dict(self):
        """Test creating batch state from dictionary"""
        data = {
            'batch_id': "test_batch",
            'session_id': 1,
            'photo_ids': [1, 2, 3],
            'processed_photo_ids': [],
            'failed_photo_ids': [],
            'status': BatchStatus.PENDING.value,
            'created_at': datetime.utcnow().isoformat(),
            'started_at': None,
            'paused_at': None,
            'completed_at': None,
            'total_photos': 3,
            'processed_count': 0,
            'failed_count': 0,
            'config': None,
            'task_ids': []
        }
        
        state = BatchState.from_dict(data)
        
        assert state.batch_id == "test_batch"
        assert state.total_photos == 3


class TestBatchController:
    """Test BatchController"""
    
    def test_initialization(self, batch_controller, temp_state_dir):
        """Test batch controller initialization"""
        assert batch_controller.state_dir == temp_state_dir
        assert isinstance(batch_controller.active_batches, dict)
        assert len(batch_controller.active_batches) == 0
    
    def test_start_batch(self, batch_controller):
        """Test starting a batch"""
        photo_ids = [1, 2, 3, 4, 5]
        
        batch_id = batch_controller.start_batch(
            photo_ids=photo_ids,
            session_id=1
        )
        
        assert batch_id is not None
        assert batch_id in batch_controller.active_batches
        
        batch_state = batch_controller.active_batches[batch_id]
        assert batch_state.total_photos == 5
        assert batch_state.status == BatchStatus.RUNNING.value
        assert len(batch_state.task_ids) == 3  # Mocked return value
    
    def test_pause_batch(self, batch_controller):
        """Test pausing a batch"""
        photo_ids = [1, 2, 3]
        batch_id = batch_controller.start_batch(photo_ids=photo_ids)
        
        success = batch_controller.pause_batch(batch_id)
        
        assert success is True
        
        batch_state = batch_controller.active_batches[batch_id]
        assert batch_state.status == BatchStatus.PAUSED.value
        assert batch_state.paused_at is not None
    
    def test_pause_nonexistent_batch(self, batch_controller):
        """Test pausing a non-existent batch"""
        success = batch_controller.pause_batch("nonexistent_batch")
        
        assert success is False
    
    def test_resume_batch(self, batch_controller):
        """Test resuming a paused batch"""
        photo_ids = [1, 2, 3, 4, 5]
        batch_id = batch_controller.start_batch(photo_ids=photo_ids)
        
        # Pause the batch
        batch_controller.pause_batch(batch_id)
        
        # Resume the batch
        success = batch_controller.resume_batch(batch_id)
        
        assert success is True
        
        batch_state = batch_controller.active_batches[batch_id]
        assert batch_state.status == BatchStatus.RUNNING.value
    
    def test_resume_nonexistent_batch(self, batch_controller):
        """Test resuming a non-existent batch"""
        success = batch_controller.resume_batch("nonexistent_batch")
        
        assert success is False
    
    def test_cancel_batch(self, batch_controller):
        """Test cancelling a batch"""
        photo_ids = [1, 2, 3]
        batch_id = batch_controller.start_batch(photo_ids=photo_ids)
        
        success = batch_controller.cancel_batch(batch_id)
        
        assert success is True
        
        batch_state = batch_controller.active_batches[batch_id]
        assert batch_state.status == BatchStatus.CANCELLED.value
        assert batch_state.completed_at is not None
    
    def test_update_batch_progress(self, batch_controller):
        """Test updating batch progress"""
        photo_ids = [1, 2, 3]
        batch_id = batch_controller.start_batch(photo_ids=photo_ids)
        
        # Update progress for successful photo
        batch_controller.update_batch_progress(batch_id, 1, success=True)
        
        batch_state = batch_controller.active_batches[batch_id]
        assert batch_state.processed_count == 1
        assert 1 in batch_state.processed_photo_ids
        
        # Update progress for failed photo
        batch_controller.update_batch_progress(batch_id, 2, success=False)
        
        assert batch_state.failed_count == 1
        assert 2 in batch_state.failed_photo_ids
    
    def test_batch_auto_completion(self, batch_controller):
        """Test batch auto-completion when all photos are processed"""
        photo_ids = [1, 2, 3]
        batch_id = batch_controller.start_batch(photo_ids=photo_ids)
        
        # Process all photos
        batch_controller.update_batch_progress(batch_id, 1, success=True)
        batch_controller.update_batch_progress(batch_id, 2, success=True)
        batch_controller.update_batch_progress(batch_id, 3, success=True)
        
        batch_state = batch_controller.active_batches[batch_id]
        assert batch_state.status == BatchStatus.COMPLETED.value
        assert batch_state.completed_at is not None
    
    def test_get_batch_status(self, batch_controller):
        """Test getting batch status"""
        photo_ids = [1, 2, 3, 4, 5]
        batch_id = batch_controller.start_batch(photo_ids=photo_ids)
        
        status = batch_controller.get_batch_status(batch_id)
        
        assert status is not None
        assert status['batch_id'] == batch_id
        assert status['total_photos'] == 5
        assert status['processed_count'] == 0
        assert status['status'] == BatchStatus.RUNNING.value
        assert 'progress_percent' in status
    
    def test_get_nonexistent_batch_status(self, batch_controller):
        """Test getting status of non-existent batch"""
        status = batch_controller.get_batch_status("nonexistent_batch")
        
        assert status is None
    
    def test_get_all_batches(self, batch_controller):
        """Test getting all batches"""
        # Start multiple batches
        batch_id1 = batch_controller.start_batch([1, 2, 3])
        batch_id2 = batch_controller.start_batch([4, 5, 6])
        
        batches = batch_controller.get_all_batches()
        
        assert len(batches) == 2
        assert any(b['batch_id'] == batch_id1 for b in batches)
        assert any(b['batch_id'] == batch_id2 for b in batches)
    
    def test_state_persistence(self, batch_controller, temp_state_dir):
        """Test batch state persistence"""
        photo_ids = [1, 2, 3]
        batch_id = batch_controller.start_batch(photo_ids=photo_ids)
        
        # Check that state file was created
        state_file = temp_state_dir / f"{batch_id}.json"
        assert state_file.exists()
        
        # Verify state file content
        with open(state_file, 'r') as f:
            data = json.load(f)
        
        assert data['batch_id'] == batch_id
        assert data['total_photos'] == 3
    
    def test_state_loading(self, temp_state_dir, mock_job_queue_manager):
        """Test loading persisted states"""
        # Create a persisted state file
        batch_id = "test_batch_123"
        state_data = {
            'batch_id': batch_id,
            'session_id': 1,
            'photo_ids': [1, 2, 3],
            'processed_photo_ids': [1],
            'failed_photo_ids': [],
            'status': BatchStatus.PAUSED.value,
            'created_at': datetime.utcnow().isoformat(),
            'started_at': datetime.utcnow().isoformat(),
            'paused_at': datetime.utcnow().isoformat(),
            'completed_at': None,
            'total_photos': 3,
            'processed_count': 1,
            'failed_count': 0,
            'config': None,
            'task_ids': ['task1', 'task2']
        }
        
        state_file = temp_state_dir / f"{batch_id}.json"
        with open(state_file, 'w') as f:
            json.dump(state_data, f)
        
        # Create new controller (should load persisted state)
        controller = BatchController(state_dir=temp_state_dir)
        
        assert batch_id in controller.active_batches
        batch_state = controller.active_batches[batch_id]
        assert batch_state.processed_count == 1
        assert batch_state.status == BatchStatus.PAUSED.value
    
    def test_recover_interrupted_batches(self, temp_state_dir, mock_job_queue_manager):
        """Test recovering interrupted batches"""
        # Create a batch that was running when system stopped
        batch_id = "interrupted_batch"
        state_data = {
            'batch_id': batch_id,
            'session_id': 1,
            'photo_ids': [1, 2, 3],
            'processed_photo_ids': [1],
            'failed_photo_ids': [],
            'status': BatchStatus.RUNNING.value,  # Was running
            'created_at': datetime.utcnow().isoformat(),
            'started_at': datetime.utcnow().isoformat(),
            'paused_at': None,
            'completed_at': None,
            'total_photos': 3,
            'processed_count': 1,
            'failed_count': 0,
            'config': None,
            'task_ids': ['task1', 'task2']
        }
        
        state_file = temp_state_dir / f"{batch_id}.json"
        with open(state_file, 'w') as f:
            json.dump(state_data, f)
        
        # Create controller and recover
        controller = BatchController(state_dir=temp_state_dir)
        result = controller.recover_interrupted_batches()
        
        assert result['recovered_count'] == 1
        assert result['failed_count'] == 0
        
        # Batch should now be paused
        batch_state = controller.active_batches[batch_id]
        assert batch_state.status == BatchStatus.PAUSED.value
    
    def test_cleanup_completed_batches(self, batch_controller):
        """Test cleaning up old completed batches"""
        from datetime import timedelta
        
        # Create a completed batch
        photo_ids = [1, 2, 3]
        batch_id = batch_controller.start_batch(photo_ids=photo_ids)
        
        # Mark as completed with old date
        batch_state = batch_controller.active_batches[batch_id]
        batch_state.status = BatchStatus.COMPLETED.value
        old_date = datetime.utcnow() - timedelta(days=10)
        batch_state.completed_at = old_date.isoformat()
        batch_controller._persist_state(batch_id)
        
        # Cleanup batches older than 7 days
        count = batch_controller.cleanup_completed_batches(days_old=7)
        
        assert count == 1
        assert batch_id not in batch_controller.active_batches
    
    def test_resume_with_remaining_photos(self, batch_controller):
        """Test resuming batch with remaining photos"""
        photo_ids = [1, 2, 3, 4, 5]
        batch_id = batch_controller.start_batch(photo_ids=photo_ids)
        
        # Process some photos
        batch_controller.update_batch_progress(batch_id, 1, success=True)
        batch_controller.update_batch_progress(batch_id, 2, success=True)
        
        # Pause
        batch_controller.pause_batch(batch_id)
        
        # Resume (should only process remaining photos)
        success = batch_controller.resume_batch(batch_id)
        
        assert success is True
        
        # Should have submitted jobs for remaining 3 photos
        batch_state = batch_controller.active_batches[batch_id]
        assert len(batch_state.task_ids) == 3  # Mocked return value


class TestBatchControllerGlobalInstance:
    """Test global batch controller instance"""
    
    def test_get_batch_controller(self):
        """Test getting global batch controller instance"""
        controller1 = get_batch_controller()
        controller2 = get_batch_controller()
        
        assert controller1 is controller2  # Should be same instance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
