"""
Test Celery + Redis Job Queue Configuration

This test verifies that the Celery job queue is properly configured
and can handle basic task operations.

Requirements: 4.1, 4.2, 4.4
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from celery_config import (
    app,
    get_priority_for_photo,
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    PRIORITY_LOW,
    REDIS_URL
)
from job_queue_manager import JobQueueManager, get_job_queue_manager
import json


class TestCeleryConfiguration(unittest.TestCase):
    """Test Celery configuration"""
    
    def test_celery_app_initialized(self):
        """Test that Celery app is properly initialized"""
        self.assertIsNotNone(app)
        self.assertEqual(app.main, 'junmai_autodev')
    
    def test_redis_broker_configured(self):
        """Test that Redis broker is configured"""
        self.assertIn('redis://', app.conf.broker_url)
        self.assertIn('redis://', app.conf.result_backend)
    
    def test_task_serialization_configured(self):
        """Test that task serialization is configured"""
        self.assertEqual(app.conf.task_serializer, 'json')
        self.assertEqual(app.conf.result_serializer, 'json')
        self.assertIn('json', app.conf.accept_content)
    
    def test_priority_queues_configured(self):
        """Test that priority queues are configured (Requirement 4.4)"""
        queue_names = [q.name for q in app.conf.task_queues]
        self.assertIn('high_priority', queue_names)
        self.assertIn('medium_priority', queue_names)
        self.assertIn('low_priority', queue_names)
        self.assertIn('default', queue_names)
    
    def test_retry_settings_configured(self):
        """Test that retry settings are configured (Requirement 4.2)"""
        self.assertTrue(app.conf.task_acks_late)
        self.assertTrue(app.conf.task_reject_on_worker_lost)
    
    def test_worker_settings_configured(self):
        """Test that worker settings are configured"""
        self.assertEqual(app.conf.worker_prefetch_multiplier, 1)
        self.assertEqual(app.conf.worker_max_tasks_per_child, 100)
        self.assertEqual(app.conf.worker_concurrency, 3)


class TestPriorityCalculation(unittest.TestCase):
    """Test priority calculation logic"""
    
    def test_user_requested_gets_high_priority(self):
        """Test that user-requested tasks get high priority"""
        priority = get_priority_for_photo(ai_score=3.0, user_requested=True)
        self.assertEqual(priority, PRIORITY_HIGH)
    
    def test_high_ai_score_gets_high_priority(self):
        """Test that high AI scores get high priority"""
        priority = get_priority_for_photo(ai_score=4.8, user_requested=False)
        self.assertEqual(priority, PRIORITY_HIGH)
    
    def test_medium_ai_score_gets_medium_priority(self):
        """Test that medium AI scores get medium priority"""
        priority = get_priority_for_photo(ai_score=4.0, user_requested=False)
        self.assertEqual(priority, PRIORITY_MEDIUM)
    
    def test_low_ai_score_gets_low_priority(self):
        """Test that low AI scores get low priority"""
        priority = get_priority_for_photo(ai_score=2.5, user_requested=False)
        self.assertEqual(priority, PRIORITY_LOW)
    
    def test_no_ai_score_gets_medium_priority(self):
        """Test that tasks without AI score get medium priority"""
        priority = get_priority_for_photo(ai_score=None, user_requested=False)
        self.assertEqual(priority, PRIORITY_MEDIUM)


class TestJobQueueManager(unittest.TestCase):
    """Test JobQueueManager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = JobQueueManager()
    
    def test_manager_initialization(self):
        """Test that manager initializes correctly"""
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.manager.celery_app)
    
    def test_get_job_queue_manager_singleton(self):
        """Test that get_job_queue_manager returns singleton"""
        manager1 = get_job_queue_manager()
        manager2 = get_job_queue_manager()
        self.assertIs(manager1, manager2)
    
    @patch('job_queue_manager.get_session')
    @patch('job_queue_manager.process_photo_task')
    def test_submit_photo_processing(self, mock_task, mock_get_session):
        """Test submitting photo for processing (Requirement 4.1)"""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # Mock photo
        mock_photo = Mock()
        mock_photo.id = 1
        mock_photo.ai_score = 4.5
        mock_session.query.return_value.filter.return_value.first.return_value = mock_photo
        
        # Mock task result
        mock_result = Mock()
        mock_result.id = 'test-task-id'
        mock_task.apply_async.return_value = mock_result
        
        # Submit job
        task_id = self.manager.submit_photo_processing(
            photo_id=1,
            user_requested=True
        )
        
        # Verify task was submitted
        self.assertEqual(task_id, 'test-task-id')
        mock_task.apply_async.assert_called_once()
        
        # Verify priority was set correctly
        call_kwargs = mock_task.apply_async.call_args[1]
        self.assertEqual(call_kwargs['priority'], PRIORITY_HIGH)
    
    @patch('job_queue_manager.get_session')
    def test_get_job_status(self, mock_get_session):
        """Test getting job status"""
        # Mock AsyncResult
        with patch.object(self.manager.celery_app, 'AsyncResult') as mock_result_class:
            mock_result = Mock()
            mock_result.state = 'SUCCESS'
            mock_result.ready.return_value = True
            mock_result.successful.return_value = True
            mock_result.failed.return_value = False
            mock_result.result = {'status': 'completed'}
            mock_result_class.return_value = mock_result
            
            # Get status
            status = self.manager.get_job_status('test-task-id')
            
            # Verify status
            self.assertEqual(status['state'], 'SUCCESS')
            self.assertTrue(status['ready'])
            self.assertTrue(status['successful'])
            self.assertFalse(status['failed'])
            self.assertEqual(status['result'], {'status': 'completed'})
    
    @patch('job_queue_manager.get_session')
    def test_cancel_job(self, mock_get_session):
        """Test cancelling a job"""
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # Mock job
        mock_job = Mock()
        mock_job.id = 'test-task-id'
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job
        
        # Mock celery control
        with patch.object(self.manager.celery_app.control, 'revoke') as mock_revoke:
            # Cancel job
            result = self.manager.cancel_job('test-task-id')
            
            # Verify job was cancelled
            self.assertTrue(result)
            mock_revoke.assert_called_once_with('test-task-id', terminate=True)
            self.assertEqual(mock_job.status, 'cancelled')


class TestRetryLogic(unittest.TestCase):
    """Test retry logic implementation"""
    
    @patch('celery_tasks.get_session')
    def test_task_retry_on_failure(self, mock_get_session):
        """Test that tasks retry on failure (Requirement 4.2)"""
        from celery_tasks import BaseTask
        
        # Verify retry configuration
        self.assertEqual(BaseTask.retry_kwargs['max_retries'], 3)
        self.assertTrue(BaseTask.retry_backoff)
        self.assertTrue(BaseTask.retry_jitter)
        self.assertEqual(BaseTask.retry_backoff_max, 600)
    
    @patch('celery_tasks.get_session')
    @patch('celery_tasks.logging_system')
    def test_on_failure_updates_job_status(self, mock_logging, mock_get_session):
        """Test that on_failure updates job status"""
        from celery_tasks import BaseTask
        
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # Mock job
        mock_job = Mock()
        mock_job.id = 'test-task-id'
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job
        
        # Create task instance
        task = BaseTask()
        task.name = 'test_task'
        
        # Call on_failure
        exc = Exception("Test error")
        task.on_failure(exc, 'test-task-id', [], {}, None)
        
        # Verify job status was updated
        self.assertEqual(mock_job.status, 'failed')
        self.assertEqual(mock_job.error_message, 'Test error')


class TestTaskRouting(unittest.TestCase):
    """Test task routing to priority queues"""
    
    def test_task_routes_configured(self):
        """Test that task routes are configured"""
        routes = app.conf.task_routes
        
        # Verify critical tasks go to high priority queue
        self.assertEqual(
            routes['celery_tasks.analyze_exif_task']['queue'],
            'high_priority'
        )
        self.assertEqual(
            routes['celery_tasks.apply_preset_task']['queue'],
            'high_priority'
        )
        
        # Verify normal tasks go to medium priority queue
        self.assertEqual(
            routes['celery_tasks.process_photo_task']['queue'],
            'medium_priority'
        )
        self.assertEqual(
            routes['celery_tasks.evaluate_quality_task']['queue'],
            'medium_priority'
        )
        
        # Verify low priority tasks
        self.assertEqual(
            routes['celery_tasks.group_similar_photos_task']['queue'],
            'low_priority'
        )
        self.assertEqual(
            routes['celery_tasks.export_photo_task']['queue'],
            'low_priority'
        )


if __name__ == '__main__':
    unittest.main()
