"""
Unit Tests for Cloud Sync Manager

Tests cloud storage synchronization functionality including:
- rclone integration
- Upload job management
- Progress tracking
- Error retry logic
- Batch operations

Requirements: 6.3
"""

import pytest
import pathlib
import tempfile
import json
import subprocess
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from cloud_sync_manager import (
    CloudSyncManager,
    CloudProvider,
    UploadStatus,
    UploadJob,
    get_cloud_sync_manager
)


class TestUploadJob:
    """Test UploadJob data class"""
    
    def test_upload_job_creation(self):
        """Test creating an upload job"""
        job = UploadJob(
            id="test123",
            local_path="/path/to/file.jpg",
            remote_path="/Photos/file.jpg",
            provider="dropbox",
            status="pending",
            created_at=datetime.now().isoformat(),
            file_size=1024000
        )
        
        assert job.id == "test123"
        assert job.local_path == "/path/to/file.jpg"
        assert job.status == "pending"
        assert job.file_size == 1024000
        assert job.bytes_uploaded == 0
        assert job.progress_percent == 0.0
    
    def test_upload_job_to_dict(self):
        """Test converting upload job to dictionary"""
        job = UploadJob(
            id="test123",
            local_path="/path/to/file.jpg",
            remote_path="/Photos/file.jpg",
            provider="dropbox",
            status="pending",
            created_at=datetime.now().isoformat()
        )
        
        job_dict = job.to_dict()
        
        assert isinstance(job_dict, dict)
        assert job_dict['id'] == "test123"
        assert job_dict['status'] == "pending"
    
    def test_upload_job_from_dict(self):
        """Test creating upload job from dictionary"""
        data = {
            'id': "test123",
            'local_path': "/path/to/file.jpg",
            'remote_path': "/Photos/file.jpg",
            'provider': "dropbox",
            'status': "pending",
            'created_at': datetime.now().isoformat(),
            'started_at': None,
            'completed_at': None,
            'file_size': 1024000,
            'bytes_uploaded': 0,
            'progress_percent': 0.0,
            'retry_count': 0,
            'max_retries': 3,
            'error_message': None
        }
        
        job = UploadJob.from_dict(data)
        
        assert job.id == "test123"
        assert job.file_size == 1024000
    
    def test_update_progress(self):
        """Test updating upload progress"""
        job = UploadJob(
            id="test123",
            local_path="/path/to/file.jpg",
            remote_path="/Photos/file.jpg",
            provider="dropbox",
            status="uploading",
            created_at=datetime.now().isoformat(),
            file_size=1000000
        )
        
        job.update_progress(500000, 1000000)
        
        assert job.bytes_uploaded == 500000
        assert job.progress_percent == 50.0


class TestCloudSyncManager:
    """Test CloudSyncManager class"""
    
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return {
            'enabled': True,
            'provider': 'dropbox',
            'remote_path': '/Photos/Test'
        }
    
    @pytest.fixture
    def manager(self, config):
        """Create CloudSyncManager instance"""
        with patch.object(CloudSyncManager, '_check_rclone', return_value=True):
            return CloudSyncManager(config)
    
    def test_manager_initialization(self, config):
        """Test manager initialization"""
        with patch.object(CloudSyncManager, '_check_rclone', return_value=True):
            manager = CloudSyncManager(config)
            
            assert manager.enabled is True
            assert manager.provider == CloudProvider.DROPBOX
            assert manager.remote_path == '/Photos/Test'
            assert manager.rclone_available is True
    
    def test_manager_initialization_without_config(self):
        """Test manager initialization without config"""
        with patch.object(CloudSyncManager, '_check_rclone', return_value=False):
            manager = CloudSyncManager()
            
            assert manager.enabled is False
            assert manager.provider == CloudProvider.NONE
    
    def test_check_rclone_available(self):
        """Test checking rclone availability"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="rclone v1.60.0")
            
            manager = CloudSyncManager()
            
            assert manager.rclone_available is True
    
    def test_check_rclone_not_available(self):
        """Test checking rclone when not available"""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            manager = CloudSyncManager()
            
            assert manager.rclone_available is False
    
    def test_is_enabled(self, manager):
        """Test checking if cloud sync is enabled"""
        assert manager.is_enabled() is True
    
    def test_is_enabled_when_disabled(self):
        """Test checking when cloud sync is disabled"""
        config = {
            'enabled': False,
            'provider': 'dropbox',
            'remote_path': '/Photos/Test'
        }
        
        with patch.object(CloudSyncManager, '_check_rclone', return_value=True):
            manager = CloudSyncManager(config)
            
            assert manager.is_enabled() is False
    
    def test_configure(self, manager):
        """Test configuring cloud sync"""
        success = manager.configure(True, 'google_drive', '/Photos/New')
        
        assert success is True
        assert manager.provider == CloudProvider.GOOGLE_DRIVE
        assert manager.remote_path == '/Photos/New'
    
    def test_configure_invalid_provider(self, manager):
        """Test configuring with invalid provider"""
        success = manager.configure(True, 'invalid_provider', '/Photos/New')
        
        assert success is False
    
    def test_get_rclone_remote_name(self, manager):
        """Test getting rclone remote name"""
        manager.provider = CloudProvider.DROPBOX
        assert manager.get_rclone_remote_name() == 'dropbox'
        
        manager.provider = CloudProvider.GOOGLE_DRIVE
        assert manager.get_rclone_remote_name() == 'gdrive'
        
        manager.provider = CloudProvider.ONEDRIVE
        assert manager.get_rclone_remote_name() == 'onedrive'
    
    def test_upload_file(self, manager):
        """Test uploading a file"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(b'test data')
            tmp_path = pathlib.Path(tmp.name)
        
        try:
            job = manager.upload_file(tmp_path)
            
            assert job is not None
            assert job.local_path == str(tmp_path)
            assert job.status == UploadStatus.PENDING.value
            assert job.provider == 'dropbox'
            assert len(manager.upload_queue) == 1
        finally:
            tmp_path.unlink()
    
    def test_upload_file_with_subpath(self, manager):
        """Test uploading a file with remote subpath"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(b'test data')
            tmp_path = pathlib.Path(tmp.name)
        
        try:
            job = manager.upload_file(tmp_path, remote_subpath='2024/01')
            
            assert job is not None
            assert '2024/01' in job.remote_path
        finally:
            tmp_path.unlink()
    
    def test_upload_file_not_found(self, manager):
        """Test uploading a non-existent file"""
        job = manager.upload_file(pathlib.Path('/nonexistent/file.jpg'))
        
        assert job is None
    
    def test_upload_file_when_disabled(self):
        """Test uploading when cloud sync is disabled"""
        config = {
            'enabled': False,
            'provider': 'dropbox',
            'remote_path': '/Photos/Test'
        }
        
        with patch.object(CloudSyncManager, '_check_rclone', return_value=True):
            manager = CloudSyncManager(config)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                tmp.write(b'test data')
                tmp_path = pathlib.Path(tmp.name)
            
            try:
                job = manager.upload_file(tmp_path)
                
                assert job is None
            finally:
                tmp_path.unlink()
    
    def test_upload_batch(self, manager):
        """Test batch upload"""
        temp_files = []
        
        try:
            # Create multiple temp files
            for i in range(3):
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{i}.jpg')
                tmp.write(b'test data')
                temp_files.append(pathlib.Path(tmp.name))
                tmp.close()
            
            jobs = manager.upload_batch(temp_files)
            
            assert len(jobs) == 3
            assert len(manager.upload_queue) == 3
            
            for job in jobs:
                assert job.status == UploadStatus.PENDING.value
        finally:
            for tmp_path in temp_files:
                tmp_path.unlink()
    
    def test_get_next_upload_job(self, manager):
        """Test getting next upload job"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(b'test data')
            tmp_path = pathlib.Path(tmp.name)
        
        try:
            job1 = manager.upload_file(tmp_path)
            job2 = manager.upload_file(tmp_path)
            
            next_job = manager.get_next_upload_job()
            
            assert next_job is not None
            assert next_job.id == job1.id  # FIFO
        finally:
            tmp_path.unlink()
    
    def test_get_next_upload_job_empty_queue(self, manager):
        """Test getting next job from empty queue"""
        next_job = manager.get_next_upload_job()
        
        assert next_job is None
    
    def test_get_upload_status(self, manager):
        """Test getting upload status"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(b'test data')
            tmp_path = pathlib.Path(tmp.name)
        
        try:
            job = manager.upload_file(tmp_path)
            
            status = manager.get_upload_status(job.id)
            
            assert status is not None
            assert status.id == job.id
        finally:
            tmp_path.unlink()
    
    def test_get_upload_status_not_found(self, manager):
        """Test getting status of non-existent job"""
        status = manager.get_upload_status('nonexistent')
        
        assert status is None
    
    def test_get_queue_status(self, manager):
        """Test getting queue status"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(b'test data' * 1000)
            tmp_path = pathlib.Path(tmp.name)
        
        try:
            manager.upload_file(tmp_path)
            manager.upload_file(tmp_path)
            
            status = manager.get_queue_status()
            
            assert status['enabled'] is True
            assert status['provider'] == 'dropbox'
            assert status['pending_count'] == 2
            assert status['active_count'] == 0
            assert status['completed_count'] == 0
            assert status['failed_count'] == 0
        finally:
            tmp_path.unlink()
    
    def test_cancel_upload(self, manager):
        """Test cancelling an upload"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(b'test data')
            tmp_path = pathlib.Path(tmp.name)
        
        try:
            job = manager.upload_file(tmp_path)
            
            success = manager.cancel_upload(job.id)
            
            assert success is True
            assert len(manager.upload_queue) == 0
        finally:
            tmp_path.unlink()
    
    def test_cancel_upload_not_found(self, manager):
        """Test cancelling non-existent upload"""
        success = manager.cancel_upload('nonexistent')
        
        assert success is False
    
    def test_retry_failed_upload(self, manager):
        """Test retrying a failed upload"""
        # Create a failed job
        job = UploadJob(
            id="failed123",
            local_path="/path/to/file.jpg",
            remote_path="/Photos/file.jpg",
            provider="dropbox",
            status=UploadStatus.FAILED.value,
            created_at=datetime.now().isoformat(),
            retry_count=3,
            error_message="Upload failed"
        )
        
        manager.failed_uploads.append(job)
        
        success = manager.retry_failed_upload(job.id)
        
        assert success is True
        assert len(manager.failed_uploads) == 0
        assert len(manager.upload_queue) == 1
        assert manager.upload_queue[0].retry_count == 0
        assert manager.upload_queue[0].status == UploadStatus.PENDING.value
    
    def test_retry_all_failed_uploads(self, manager):
        """Test retrying all failed uploads"""
        # Create multiple failed jobs
        for i in range(3):
            job = UploadJob(
                id=f"failed{i}",
                local_path=f"/path/to/file{i}.jpg",
                remote_path=f"/Photos/file{i}.jpg",
                provider="dropbox",
                status=UploadStatus.FAILED.value,
                created_at=datetime.now().isoformat(),
                retry_count=3
            )
            manager.failed_uploads.append(job)
        
        count = manager.retry_all_failed_uploads()
        
        assert count == 3
        assert len(manager.failed_uploads) == 0
        assert len(manager.upload_queue) == 3
    
    def test_clear_completed_uploads(self, manager):
        """Test clearing completed uploads"""
        # Create completed jobs
        for i in range(5):
            job = UploadJob(
                id=f"completed{i}",
                local_path=f"/path/to/file{i}.jpg",
                remote_path=f"/Photos/file{i}.jpg",
                provider="dropbox",
                status=UploadStatus.COMPLETED.value,
                created_at=datetime.now().isoformat()
            )
            manager.completed_uploads.append(job)
        
        count = manager.clear_completed_uploads()
        
        assert count == 5
        assert len(manager.completed_uploads) == 0
    
    def test_test_connection_success(self, manager):
        """Test successful connection test"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            success, error = manager.test_connection()
            
            assert success is True
            assert error is None
    
    def test_test_connection_failure(self, manager):
        """Test failed connection test"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="Connection failed")
            
            success, error = manager.test_connection()
            
            assert success is False
            assert error is not None
    
    def test_test_connection_when_disabled(self):
        """Test connection test when cloud sync is disabled"""
        config = {
            'enabled': False,
            'provider': 'dropbox',
            'remote_path': '/Photos/Test'
        }
        
        with patch.object(CloudSyncManager, '_check_rclone', return_value=True):
            manager = CloudSyncManager(config)
            
            success, error = manager.test_connection()
            
            assert success is False
            assert "not enabled" in error


class TestRcloneIntegration:
    """Test rclone integration functionality"""
    
    @pytest.fixture
    def manager(self):
        """Create CloudSyncManager instance with rclone enabled"""
        config = {
            'enabled': True,
            'provider': 'dropbox',
            'remote_path': '/Photos/Test'
        }
        with patch.object(CloudSyncManager, '_check_rclone', return_value=True):
            return CloudSyncManager(config)
    
    def test_rclone_command_construction(self, manager):
        """Test rclone command is constructed correctly"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(b'test data')
            tmp_path = pathlib.Path(tmp.name)
        
        try:
            job = manager.upload_file(tmp_path)
            
            # Mock subprocess to capture command
            with patch('subprocess.Popen') as mock_popen:
                mock_process = MagicMock()
                mock_process.poll.return_value = 0
                mock_process.stderr.readline.return_value = ''
                mock_process.stderr.read.return_value = ''
                mock_popen.return_value = mock_process
                
                manager.process_upload_job(job.id)
                
                # Verify rclone command was called
                assert mock_popen.called
                call_args = mock_popen.call_args[0][0]
                
                assert call_args[0] == 'rclone'
                assert call_args[1] == 'copy'
                assert str(tmp_path) in call_args
                assert 'dropbox:' in call_args[3]
                assert '--progress' in call_args
        finally:
            tmp_path.unlink()
    
    def test_rclone_progress_parsing(self, manager):
        """Test parsing rclone progress output"""
        job = UploadJob(
            id="test123",
            local_path="/path/to/file.jpg",
            remote_path="/Photos/file.jpg",
            provider="dropbox",
            status="uploading",
            created_at=datetime.now().isoformat(),
            file_size=10000000
        )
        
        # Test various rclone progress formats
        progress_outputs = [
            "Transferred: 1.234 MiB / 10.000 MiB, 12%, 123 KiB/s, ETA 1m23s",
            "Transferred: 5.000 MiB / 10.000 MiB, 50%, 500 KiB/s, ETA 30s",
            "Transferred: 10.000 MiB / 10.000 MiB, 100%, 1 MiB/s, ETA 0s"
        ]
        
        expected_percents = [12.0, 50.0, 100.0]
        
        for output, expected in zip(progress_outputs, expected_percents):
            manager._parse_rclone_progress(job, output)
            assert abs(job.progress_percent - expected) < 0.1
    
    def test_rclone_progress_parsing_invalid_format(self, manager):
        """Test parsing invalid rclone progress output"""
        job = UploadJob(
            id="test123",
            local_path="/path/to/file.jpg",
            remote_path="/Photos/file.jpg",
            provider="dropbox",
            status="uploading",
            created_at=datetime.now().isoformat(),
            file_size=10000000
        )
        
        initial_progress = job.progress_percent
        
        # Should not crash on invalid output
        manager._parse_rclone_progress(job, "Invalid output format")
        manager._parse_rclone_progress(job, "")
        manager._parse_rclone_progress(job, "Transferred: invalid")
        
        # Progress should remain unchanged
        assert job.progress_percent == initial_progress
    
    def test_process_upload_job_success(self, manager):
        """Test successful upload job processing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(b'test data')
            tmp_path = pathlib.Path(tmp.name)
        
        try:
            job = manager.upload_file(tmp_path)
            
            # Mock successful rclone execution
            with patch('subprocess.Popen') as mock_popen:
                mock_process = MagicMock()
                mock_process.poll.return_value = 0
                mock_process.stderr.readline.return_value = ''
                mock_process.stderr.read.return_value = ''
                mock_popen.return_value = mock_process
                
                success, error = manager.process_upload_job(job.id)
                
                assert success is True
                assert error is None
                assert len(manager.completed_uploads) == 1
                assert manager.completed_uploads[0].status == UploadStatus.COMPLETED.value
                assert manager.completed_uploads[0].progress_percent == 100.0
        finally:
            tmp_path.unlink()
    
    def test_process_upload_job_with_progress_updates(self, manager):
        """Test upload job processing with progress updates"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(b'test data' * 1000)
            tmp_path = pathlib.Path(tmp.name)
        
        try:
            job = manager.upload_file(tmp_path)
            
            # Mock rclone with progress updates
            with patch('subprocess.Popen') as mock_popen:
                mock_process = MagicMock()
                
                # Simulate progress updates - need to return empty string at end to break loop
                def readline_side_effect():
                    for line in [
                        "Transferred: 1 MiB / 10 MiB, 10%, 100 KiB/s, ETA 1m",
                        "Transferred: 5 MiB / 10 MiB, 50%, 500 KiB/s, ETA 30s",
                        "Transferred: 10 MiB / 10 MiB, 100%, 1 MiB/s, ETA 0s"
                    ]:
                        yield line
                    # Keep returning empty string
                    while True:
                        yield ''
                
                def poll_side_effect():
                    # Return None for first few calls, then 0 (success)
                    for _ in range(3):
                        yield None
                    # Keep returning 0 (success)
                    while True:
                        yield 0
                
                mock_process.stderr.readline.side_effect = readline_side_effect()
                mock_process.poll.side_effect = poll_side_effect()
                mock_process.stderr.read.return_value = ''
                mock_popen.return_value = mock_process
                
                success, error = manager.process_upload_job(job.id)
                
                assert success is True
                # Progress should have been updated during upload
                assert len(manager.completed_uploads) == 1
        finally:
            tmp_path.unlink()
    
    def test_rclone_remote_name_mapping(self, manager):
        """Test rclone remote name mapping for different providers"""
        test_cases = [
            (CloudProvider.DROPBOX, 'dropbox'),
            (CloudProvider.GOOGLE_DRIVE, 'gdrive'),
            (CloudProvider.ONEDRIVE, 'onedrive')
        ]
        
        for provider, expected_remote in test_cases:
            manager.provider = provider
            remote_name = manager.get_rclone_remote_name()
            assert remote_name == expected_remote
    
    def test_rclone_timeout_handling(self, manager):
        """Test handling of rclone timeout"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(b'test data')
            tmp_path = pathlib.Path(tmp.name)
        
        try:
            job = manager.upload_file(tmp_path)
            
            # Mock rclone timeout
            with patch('subprocess.Popen') as mock_popen:
                mock_popen.side_effect = subprocess.TimeoutExpired('rclone', 30)
                
                success, error = manager.process_upload_job(job.id)
                
                assert success is False
                assert error is not None
        finally:
            tmp_path.unlink()


class TestUploadRetryLogic:
    """Test upload failure and retry logic"""
    
    @pytest.fixture
    def manager(self):
        """Create CloudSyncManager instance"""
        config = {
            'enabled': True,
            'provider': 'dropbox',
            'remote_path': '/Photos/Test'
        }
        with patch.object(CloudSyncManager, '_check_rclone', return_value=True):
            return CloudSyncManager(config)
    
    def test_upload_failure_triggers_retry(self, manager):
        """Test that upload failure triggers retry logic"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(b'test data')
            tmp_path = pathlib.Path(tmp.name)
        
        try:
            job = manager.upload_file(tmp_path)
            initial_retry_count = job.retry_count
            
            # Mock failed rclone execution
            with patch('subprocess.Popen') as mock_popen:
                mock_process = MagicMock()
                mock_process.poll.return_value = 1  # Non-zero exit code
                mock_process.stderr.readline.return_value = ''
                mock_process.stderr.read.return_value = 'Network error'
                mock_popen.return_value = mock_process
                
                with patch('time.sleep'):  # Skip actual sleep
                    success, error = manager.process_upload_job(job.id)
                
                assert success is False
                assert error is not None
                # Job should be back in queue for retry
                assert len(manager.upload_queue) == 1
                assert manager.upload_queue[0].retry_count == initial_retry_count + 1
                assert manager.upload_queue[0].status == UploadStatus.RETRYING.value
        finally:
            tmp_path.unlink()
    
    def test_exponential_backoff_retry_delay(self, manager):
        """Test exponential backoff for retry delays"""
        job = UploadJob(
            id="test123",
            local_path="/path/to/file.jpg",
            remote_path="/Photos/file.jpg",
            provider="dropbox",
            status="uploading",
            created_at=datetime.now().isoformat()
        )
        
        # Test retry delays with exponential backoff
        expected_delays = []
        for retry_count in range(1, 4):
            job.retry_count = retry_count - 1
            manager.active_uploads[job.id] = job  # Add to active uploads before each call
            
            with patch('time.sleep') as mock_sleep:
                manager._handle_upload_failure(job, "Test error")
                
                if mock_sleep.called:
                    actual_delay = mock_sleep.call_args[0][0]
                    expected_delay = min(
                        manager.retry_delay_base ** retry_count,
                        manager.retry_delay_max
                    )
                    expected_delays.append(expected_delay)
                    assert actual_delay == expected_delay
    
    def test_max_retries_exceeded(self, manager):
        """Test behavior when max retries are exceeded"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(b'test data')
            tmp_path = pathlib.Path(tmp.name)
        
        try:
            job = manager.upload_file(tmp_path)
            job.retry_count = manager.max_retries - 1  # One retry left
            
            # Mock failed rclone execution
            with patch('subprocess.Popen') as mock_popen:
                mock_process = MagicMock()
                mock_process.poll.return_value = 1
                mock_process.stderr.readline.return_value = ''
                mock_process.stderr.read.return_value = 'Permanent error'
                mock_popen.return_value = mock_process
                
                with patch('time.sleep'):
                    success, error = manager.process_upload_job(job.id)
                
                assert success is False
                # Job should be in failed queue, not retry queue
                assert len(manager.failed_uploads) == 1
                assert len(manager.upload_queue) == 0
                assert manager.failed_uploads[0].status == UploadStatus.FAILED.value
                assert manager.failed_uploads[0].retry_count == manager.max_retries
        finally:
            tmp_path.unlink()
    
    def test_retry_with_different_error_types(self, manager):
        """Test retry logic with different error types"""
        error_scenarios = [
            ('Network timeout', True),  # Should retry
            ('Connection refused', True),  # Should retry
            ('File not found', True),  # Should retry (might be temporary)
            ('Permission denied', True),  # Should retry
        ]
        
        for error_message, should_retry in error_scenarios:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                tmp.write(b'test data')
                tmp_path = pathlib.Path(tmp.name)
            
            try:
                job = manager.upload_file(tmp_path)
                
                with patch('subprocess.Popen') as mock_popen:
                    mock_process = MagicMock()
                    mock_process.poll.return_value = 1
                    mock_process.stderr.readline.return_value = ''
                    mock_process.stderr.read.return_value = error_message
                    mock_popen.return_value = mock_process
                    
                    with patch('time.sleep'):
                        success, error = manager.process_upload_job(job.id)
                    
                    assert success is False
                    if should_retry:
                        # Should be queued for retry
                        assert len(manager.upload_queue) == 1 or len(manager.failed_uploads) == 1
                
                # Clean up for next iteration
                manager.upload_queue.clear()
                manager.failed_uploads.clear()
            finally:
                tmp_path.unlink()
    
    def test_retry_failed_upload_resets_state(self, manager):
        """Test that retrying a failed upload resets its state"""
        job = UploadJob(
            id="failed123",
            local_path="/path/to/file.jpg",
            remote_path="/Photos/file.jpg",
            provider="dropbox",
            status=UploadStatus.FAILED.value,
            created_at=datetime.now().isoformat(),
            retry_count=3,
            error_message="Previous error",
            bytes_uploaded=5000,
            progress_percent=50.0
        )
        
        manager.failed_uploads.append(job)
        
        success = manager.retry_failed_upload(job.id)
        
        assert success is True
        assert len(manager.upload_queue) == 1
        
        retried_job = manager.upload_queue[0]
        assert retried_job.status == UploadStatus.PENDING.value
        assert retried_job.retry_count == 0
        assert retried_job.error_message is None
        assert retried_job.bytes_uploaded == 0
        assert retried_job.progress_percent == 0.0
    
    def test_concurrent_upload_retry_handling(self, manager):
        """Test retry handling with concurrent uploads"""
        temp_files = []
        
        try:
            # Create multiple files
            for i in range(3):
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{i}.jpg')
                tmp.write(b'test data')
                temp_files.append(pathlib.Path(tmp.name))
                tmp.close()
            
            jobs = manager.upload_batch(temp_files)
            
            # Mock failures for all jobs
            with patch('subprocess.Popen') as mock_popen:
                mock_process = MagicMock()
                mock_process.poll.return_value = 1
                mock_process.stderr.readline.return_value = ''
                mock_process.stderr.read.return_value = 'Network error'
                mock_popen.return_value = mock_process
                
                with patch('time.sleep'):
                    for job in jobs:
                        manager.process_upload_job(job.id)
                
                # All jobs should be queued for retry
                assert len(manager.upload_queue) == 3
                for job in manager.upload_queue:
                    assert job.status == UploadStatus.RETRYING.value
                    assert job.retry_count == 1
        finally:
            for tmp_path in temp_files:
                tmp_path.unlink()
    
    def test_process_upload_queue_with_retries(self, manager):
        """Test processing upload queue with retry logic"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(b'test data')
            tmp_path = pathlib.Path(tmp.name)
        
        try:
            # Add multiple jobs
            for _ in range(3):
                manager.upload_file(tmp_path)
            
            # Mock first attempt fails, second succeeds
            call_count = [0]
            
            def mock_popen_side_effect(*args, **kwargs):
                mock_process = MagicMock()
                call_count[0] += 1
                
                if call_count[0] <= 3:  # First 3 calls fail
                    mock_process.poll.return_value = 1
                    mock_process.stderr.read.return_value = 'Temporary error'
                else:  # Subsequent calls succeed
                    mock_process.poll.return_value = 0
                    mock_process.stderr.read.return_value = ''
                
                mock_process.stderr.readline.return_value = ''
                return mock_process
            
            with patch('subprocess.Popen', side_effect=mock_popen_side_effect):
                with patch('time.sleep'):
                    result = manager.process_upload_queue(max_concurrent=2)
                    
                    # Some jobs should have been processed
                    assert result['processed'] > 0
        finally:
            tmp_path.unlink()


class TestConvenienceFunction:
    """Test convenience function"""
    
    def test_get_cloud_sync_manager(self):
        """Test getting manager instance"""
        config = {
            'enabled': True,
            'provider': 'dropbox',
            'remote_path': '/Photos/Test'
        }
        
        with patch.object(CloudSyncManager, '_check_rclone', return_value=True):
            manager = get_cloud_sync_manager(config)
            
            assert isinstance(manager, CloudSyncManager)
            assert manager.provider == CloudProvider.DROPBOX


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
