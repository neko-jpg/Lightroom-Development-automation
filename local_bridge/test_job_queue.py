"""
Tests for Celery Job Queue System

Tests cover:
- Job submission and priority handling
- Retry logic
- Queue management
- Worker status monitoring

Requirements: 4.1, 4.2, 4.4
"""

import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from celery_config import app, get_priority_for_photo, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW
from job_queue_manager import JobQueueManager, get_job_queue_manager
from celery_tasks import (
    process_photo_task,
    analyze_exif_task,
    evaluate_quality_task,
    process_batch_photos
)
from models.database import init_db, get_session, Photo, Job, Session as DBSession


@pytest.fixture
def test_db():
    """Initialize test database"""
    init_db('sqlite:///:memory:')
    yield
    # Cleanup handled by in-memory database


@pytest.fixture
def sample_photo(test_db):
    """Create sample photo for testing"""
    db_session = get_session()
    try:
        # Create session
        session = DBSession(
            name='Test Session',
            import_folder='/test/folder',
            status='importing'
        )
        db_session.add(session)
        db_session.flush()
        
        # Create photo
        photo = Photo(
            session_id=session.id,
            file_path='/test/photo.jpg',
            file_name='photo.jpg',
            file_size=1024000,
            status='imported',
            ai_score=4.2
        )
        db_session.add(photo)
        db_session.commit()
        
        return photo.id
    finally:
        db_session.close()


@pytest.fixture
def job_manager():
    """Get job queue manager instance"""
    return get_job_queue_manager()


class TestPriorityCalculation:
    """Test priority calculation logic"""
    
    def test_user_requested_high_priority(self):
        """User-requested jobs should have high priority"""
        priority = get_priority_for_photo(user_requested=True)
        assert priority == PRIORITY_HIGH
    
    def test_high_score_high_priority(self):
        """Photos with AI score >= 4.5 should have high priority"""
        priority = get_priority_for_photo(ai_score=4.8)
        assert priority == PRIORITY_HIGH
    
    def test_medium_score_medium_priority(self):
        """Photos with AI score 3.5-4.5 should have medium priority"""
        priority = get_priority_for_photo(ai_score=4.0)
        assert priority == PRIORITY_MEDIUM
    
    def test_low_score_low_priority(self):
        """Photos with AI score < 3.5 should have low priority"""
        priority = get_priority_for_photo(ai_score=2.5)
        assert priority == PRIORITY_LOW
    
    def test_no_score_medium_priority(self):
        """Photos without AI score should have medium priority"""
        priority = get_priority_for_photo()
        assert priority == PRIORITY_MEDIUM


class TestJobSubmission:
    """Test job submission functionality"""
    
    @patch('celery_tasks.process_photo_task.apply_async')
    def test_submit_photo_processing(self, mock_apply_async, job_manager, sample_photo):
        """Test submitting photo for processing"""
        # Mock task result
        mock_result = Mock()
        mock_result.id = 'test-task-id-123'
        mock_apply_async.return_value = mock_result
        
        # Submit job
        task_id = job_manager.submit_photo_processing(sample_photo)
        
        # Verify task was submitted
        assert task_id == 'test-task-id-123'
        mock_apply_async.assert_called_once()
        
        # Verify job was created in database
        db_session = get_session()
        try:
            job = db_session.query(Job).filter(Job.id == task_id).first()
            assert job is not None
            assert job.photo_id == sample_photo
            assert job.status == 'pending'
        finally:
            db_session.close()
    
    @patch('celery_tasks.process_photo_task.apply_async')
    def test_submit_user_requested_high_priority(self, mock_apply_async, job_manager, sample_photo):
        """Test user-requested jobs get high priority"""
        mock_result = Mock()
        mock_result.id = 'test-task-id-456'
        mock_apply_async.return_value = mock_result
        
        # Submit user-requested job
        task_id = job_manager.submit_photo_processing(
            sample_photo,
            user_requested=True
        )
        
        # Verify high priority was used
        call_kwargs = mock_apply_async.call_args[1]
        assert call_kwargs['priority'] == PRIORITY_HIGH
    
    @patch('celery_tasks.process_batch_photos')
    def test_submit_batch_processing(self, mock_batch, job_manager, sample_photo):
        """Test batch processing submission"""
        mock_batch.return_value = ['task-1', 'task-2', 'task-3']
        
        photo_ids = [sample_photo, sample_photo + 1, sample_photo + 2]
        task_ids = job_manager.submit_batch_processing(photo_ids)
        
        assert len(task_ids) == 3
        mock_batch.assert_called_once_with(photo_ids, PRIORITY_MEDIUM)


class TestJobStatus:
    """Test job status tracking"""
    
    @patch('celery_config.app.AsyncResult')
    def test_get_job_status_pending(self, mock_result, job_manager):
        """Test getting status of pending job"""
        mock_task = Mock()
        mock_task.state = 'PENDING'
        mock_task.ready.return_value = False
        mock_result.return_value = mock_task
        
        status = job_manager.get_job_status('test-task-id')
        
        assert status['state'] == 'PENDING'
        assert status['ready'] is False
    
    @patch('celery_config.app.AsyncResult')
    def test_get_job_status_success(self, mock_result, job_manager):
        """Test getting status of successful job"""
        mock_task = Mock()
        mock_task.state = 'SUCCESS'
        mock_task.ready.return_value = True
        mock_task.successful.return_value = True
        mock_task.result = {'processing_time': 5.2}
        mock_result.return_value = mock_task
        
        status = job_manager.get_job_status('test-task-id')
        
        assert status['state'] == 'SUCCESS'
        assert status['ready'] is True
        assert status['successful'] is True
        assert 'result' in status
    
    @patch('celery_config.app.AsyncResult')
    def test_get_job_status_failed(self, mock_result, job_manager):
        """Test getting status of failed job"""
        mock_task = Mock()
        mock_task.state = 'FAILURE'
        mock_task.ready.return_value = True
        mock_task.failed.return_value = True
        mock_task.info = Exception('Test error')
        mock_result.return_value = mock_task
        
        status = job_manager.get_job_status('test-task-id')
        
        assert status['state'] == 'FAILURE'
        assert status['ready'] is True
        assert status['failed'] is True
        assert 'error' in status


class TestQueueManagement:
    """Test queue management operations"""
    
    @patch('celery_config.app.control.inspect')
    def test_get_queue_stats(self, mock_inspect, job_manager, test_db):
        """Test getting queue statistics"""
        # Mock inspect results
        mock_inspect_obj = Mock()
        mock_inspect_obj.active.return_value = {'worker1': [{'id': 'task1'}]}
        mock_inspect_obj.scheduled.return_value = {'worker1': []}
        mock_inspect_obj.reserved.return_value = {'worker1': [{'id': 'task2'}]}
        mock_inspect.return_value = mock_inspect_obj
        
        stats = job_manager.get_queue_stats()
        
        assert 'active_tasks' in stats
        assert 'scheduled_tasks' in stats
        assert 'reserved_tasks' in stats
        assert 'total_pending' in stats
    
    @patch('celery_config.app.control.revoke')
    def test_cancel_job(self, mock_revoke, job_manager, sample_photo):
        """Test cancelling a job"""
        # Create job in database
        db_session = get_session()
        try:
            job = Job(
                id='test-cancel-task',
                photo_id=sample_photo,
                priority=PRIORITY_MEDIUM,
                status='pending'
            )
            db_session.add(job)
            db_session.commit()
        finally:
            db_session.close()
        
        # Cancel job
        success = job_manager.cancel_job('test-cancel-task')
        
        assert success is True
        mock_revoke.assert_called_once_with('test-cancel-task', terminate=True)
        
        # Verify status updated
        db_session = get_session()
        try:
            job = db_session.query(Job).filter(Job.id == 'test-cancel-task').first()
            assert job.status == 'cancelled'
        finally:
            db_session.close()
    
    @patch('celery_config.app.control.cancel_consumer')
    def test_pause_queue(self, mock_cancel, job_manager):
        """Test pausing queue"""
        success = job_manager.pause_queue()
        
        assert success is True
        assert mock_cancel.call_count == 4  # 4 queues
    
    @patch('celery_config.app.control.add_consumer')
    def test_resume_queue(self, mock_add, job_manager):
        """Test resuming queue"""
        success = job_manager.resume_queue()
        
        assert success is True
        assert mock_add.call_count == 4  # 4 queues


class TestRetryLogic:
    """Test retry logic for failed tasks"""
    
    def test_retry_failed_job(self, job_manager, sample_photo):
        """Test retrying a failed job"""
        # Create failed job
        db_session = get_session()
        try:
            job = Job(
                id='failed-task-123',
                photo_id=sample_photo,
                priority=PRIORITY_MEDIUM,
                status='failed',
                error_message='Test error',
                retry_count=1
            )
            db_session.add(job)
            db_session.commit()
        finally:
            db_session.close()
        
        # Mock task submission
        with patch.object(job_manager, 'submit_photo_processing') as mock_submit:
            mock_submit.return_value = 'new-task-456'
            
            new_task_id = job_manager.retry_failed_job('failed-task-123')
            
            assert new_task_id == 'new-task-456'
            mock_submit.assert_called_once()
    
    def test_get_failed_jobs(self, job_manager, sample_photo):
        """Test getting list of failed jobs"""
        # Create multiple failed jobs
        db_session = get_session()
        try:
            for i in range(3):
                job = Job(
                    id=f'failed-{i}',
                    photo_id=sample_photo,
                    priority=PRIORITY_MEDIUM,
                    status='failed',
                    error_message=f'Error {i}'
                )
                db_session.add(job)
            db_session.commit()
        finally:
            db_session.close()
        
        failed_jobs = job_manager.get_failed_jobs(limit=10)
        
        assert len(failed_jobs) == 3
        assert all(job['error_message'] for job in failed_jobs)


class TestWorkerStats:
    """Test worker statistics"""
    
    @patch('celery_config.app.control.inspect')
    def test_get_worker_stats(self, mock_inspect, job_manager):
        """Test getting worker statistics"""
        mock_inspect_obj = Mock()
        mock_inspect_obj.stats.return_value = {
            'worker1': {'total': 100, 'pool': 'prefork'}
        }
        mock_inspect_obj.active.return_value = {
            'worker1': [{'id': 'task1'}]
        }
        mock_inspect_obj.registered.return_value = {
            'worker1': ['celery_tasks.process_photo_task']
        }
        mock_inspect.return_value = mock_inspect_obj
        
        stats = job_manager.get_worker_stats()
        
        assert 'workers' in stats
        assert 'active_tasks' in stats
        assert 'registered_tasks' in stats


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
