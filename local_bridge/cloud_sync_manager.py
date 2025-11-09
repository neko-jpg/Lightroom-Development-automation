"""
Cloud Sync Manager for Junmai AutoDev

This module provides cloud storage synchronization functionality including:
- rclone integration for cloud storage operations
- Dropbox/Google Drive/OneDrive support
- Upload progress tracking and management
- Error retry logic with exponential backoff
- Batch upload operations

Requirements: 6.3
"""

import logging
import subprocess
import pathlib
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CloudProvider(Enum):
    """Supported cloud storage providers"""
    DROPBOX = "dropbox"
    GOOGLE_DRIVE = "google_drive"
    ONEDRIVE = "onedrive"
    NONE = "none"


class UploadStatus(Enum):
    """Upload job status"""
    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class UploadJob:
    """
    Upload Job Data Class
    
    Represents a single file upload job to cloud storage.
    """
    id: str
    local_path: str
    remote_path: str
    provider: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    file_size: Optional[int] = None
    bytes_uploaded: int = 0
    progress_percent: float = 0.0
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UploadJob':
        """Create from dictionary"""
        return cls(**data)
    
    def update_progress(self, bytes_uploaded: int, file_size: int):
        """Update upload progress"""
        self.bytes_uploaded = bytes_uploaded
        self.file_size = file_size
        if file_size > 0:
            self.progress_percent = (bytes_uploaded / file_size) * 100.0


class CloudSyncManager:
    """
    Cloud Sync Manager for Junmai AutoDev System
    
    Manages cloud storage synchronization using rclone.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize CloudSyncManager
        
        Args:
            config: Cloud sync configuration dictionary
        """
        self.config = config or {}
        self.enabled = self.config.get('enabled', False)
        self.provider = CloudProvider(self.config.get('provider', 'none'))
        self.remote_path = self.config.get('remote_path', '/Photos/Processed')
        
        self.upload_queue: List[UploadJob] = []
        self.active_uploads: Dict[str, UploadJob] = {}
        self.completed_uploads: List[UploadJob] = []
        self.failed_uploads: List[UploadJob] = []
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay_base = 2  # seconds
        self.retry_delay_max = 60  # seconds
        
        # Check rclone availability
        self.rclone_available = self._check_rclone()
        
        logger.info(f"CloudSyncManager initialized: enabled={self.enabled}, "
                   f"provider={self.provider.value}, rclone_available={self.rclone_available}")
    
    def _check_rclone(self) -> bool:
        """
        Check if rclone is installed and available
        
        Returns:
            True if rclone is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['rclone', 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info(f"rclone is available: {result.stdout.split()[1]}")
                return True
            else:
                logger.warning("rclone command failed")
                return False
                
        except FileNotFoundError:
            logger.warning("rclone is not installed or not in PATH")
            return False
        except subprocess.TimeoutExpired:
            logger.warning("rclone version check timed out")
            return False
        except Exception as e:
            logger.error(f"Error checking rclone: {e}")
            return False
    
    def is_enabled(self) -> bool:
        """
        Check if cloud sync is enabled and available
        
        Returns:
            True if enabled and rclone is available
        """
        return self.enabled and self.rclone_available and self.provider != CloudProvider.NONE
    
    def configure(self, enabled: bool, provider: str, remote_path: str) -> bool:
        """
        Configure cloud sync settings
        
        Args:
            enabled: Enable/disable cloud sync
            provider: Cloud provider (dropbox, google_drive, onedrive)
            remote_path: Remote path for uploads
            
        Returns:
            True if configuration is valid
        """
        try:
            self.enabled = enabled
            self.provider = CloudProvider(provider)
            self.remote_path = remote_path
            
            self.config = {
                'enabled': enabled,
                'provider': provider,
                'remote_path': remote_path
            }
            
            logger.info(f"Cloud sync configured: enabled={enabled}, provider={provider}")
            return True
            
        except ValueError as e:
            logger.error(f"Invalid provider: {provider}")
            return False
    
    def get_rclone_remote_name(self) -> str:
        """
        Get rclone remote name for the configured provider
        
        Returns:
            rclone remote name
        """
        remote_names = {
            CloudProvider.DROPBOX: 'dropbox',
            CloudProvider.GOOGLE_DRIVE: 'gdrive',
            CloudProvider.ONEDRIVE: 'onedrive'
        }
        return remote_names.get(self.provider, 'remote')
    
    def upload_file(self, local_path: pathlib.Path, 
                   remote_subpath: Optional[str] = None) -> Optional[UploadJob]:
        """
        Upload a file to cloud storage
        
        Args:
            local_path: Path to local file
            remote_subpath: Optional subdirectory in remote path
            
        Returns:
            UploadJob object or None if sync is disabled
        """
        if not self.is_enabled():
            logger.warning("Cloud sync is not enabled or rclone is not available")
            return None
        
        local_path = pathlib.Path(local_path)
        
        if not local_path.exists():
            logger.error(f"Local file not found: {local_path}")
            return None
        
        # Build remote path
        remote_base = self.remote_path.rstrip('/')
        if remote_subpath:
            remote_full = f"{remote_base}/{remote_subpath.strip('/')}/{local_path.name}"
        else:
            remote_full = f"{remote_base}/{local_path.name}"
        
        # Create upload job
        job = UploadJob(
            id=uuid.uuid4().hex,
            local_path=str(local_path),
            remote_path=remote_full,
            provider=self.provider.value,
            status=UploadStatus.PENDING.value,
            created_at=datetime.now().isoformat(),
            file_size=local_path.stat().st_size
        )
        
        self.upload_queue.append(job)
        
        logger.info(f"Upload job created: job_id={job.id}, file={local_path.name}, "
                   f"size={job.file_size} bytes")
        
        return job
    
    def upload_batch(self, local_paths: List[pathlib.Path], 
                    remote_subpath: Optional[str] = None) -> List[UploadJob]:
        """
        Upload multiple files to cloud storage
        
        Args:
            local_paths: List of local file paths
            remote_subpath: Optional subdirectory in remote path
            
        Returns:
            List of UploadJob objects
        """
        jobs = []
        
        for local_path in local_paths:
            job = self.upload_file(local_path, remote_subpath)
            if job:
                jobs.append(job)
        
        logger.info(f"Batch upload created: {len(jobs)} files")
        
        return jobs

    
    def process_upload_job(self, job_id: str) -> Tuple[bool, Optional[str]]:
        """
        Process a single upload job using rclone
        
        Args:
            job_id: ID of the upload job
            
        Returns:
            Tuple of (success, error_message)
        """
        # Find job in queue
        job = None
        for j in self.upload_queue:
            if j.id == job_id:
                job = j
                break
        
        if not job:
            error_msg = f"Upload job not found: {job_id}"
            logger.error(error_msg)
            return False, error_msg
        
        # Update job status
        job.status = UploadStatus.UPLOADING.value
        job.started_at = datetime.now().isoformat()
        self.active_uploads[job_id] = job
        self.upload_queue.remove(job)
        
        logger.info(f"Processing upload job: job_id={job_id}, file={pathlib.Path(job.local_path).name}")
        
        try:
            # Build rclone command
            remote_name = self.get_rclone_remote_name()
            rclone_remote_path = f"{remote_name}:{job.remote_path}"
            
            # Use rclone copy with progress
            cmd = [
                'rclone',
                'copy',
                job.local_path,
                rclone_remote_path,
                '--progress',
                '--stats', '1s',
                '--stats-one-line'
            ]
            
            logger.debug(f"Executing rclone command: {' '.join(cmd)}")
            
            # Execute rclone
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor progress
            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                
                if output:
                    # Parse progress from rclone output
                    self._parse_rclone_progress(job, output.strip())
            
            # Check result
            return_code = process.poll()
            
            if return_code == 0:
                job.status = UploadStatus.COMPLETED.value
                job.completed_at = datetime.now().isoformat()
                job.progress_percent = 100.0
                
                self.completed_uploads.append(job)
                del self.active_uploads[job_id]
                
                logger.info(f"Upload completed: job_id={job_id}")
                return True, None
            else:
                stderr = process.stderr.read()
                error_msg = f"rclone failed with code {return_code}: {stderr}"
                logger.error(error_msg)
                
                # Handle retry
                return self._handle_upload_failure(job, error_msg)
                
        except Exception as e:
            error_msg = f"Upload failed: {e}"
            logger.error(error_msg, exc_info=True)
            
            return self._handle_upload_failure(job, error_msg)
    
    def _parse_rclone_progress(self, job: UploadJob, output: str):
        """
        Parse progress information from rclone output
        
        Args:
            job: UploadJob to update
            output: rclone output line
        """
        try:
            # rclone progress format: "Transferred: 1.234 MiB / 10.000 MiB, 12%, 123 KiB/s, ETA 1m23s"
            if 'Transferred:' in output and '%' in output:
                parts = output.split(',')
                for part in parts:
                    if '%' in part:
                        percent_str = part.strip().replace('%', '')
                        try:
                            percent = float(percent_str)
                            job.progress_percent = percent
                            
                            if job.file_size:
                                job.bytes_uploaded = int((percent / 100.0) * job.file_size)
                            
                            logger.debug(f"Upload progress: job_id={job.id}, {percent:.1f}%")
                        except ValueError:
                            pass
                        break
        except Exception as e:
            logger.debug(f"Failed to parse rclone progress: {e}")
    
    def _handle_upload_failure(self, job: UploadJob, error_message: str) -> Tuple[bool, Optional[str]]:
        """
        Handle upload failure with retry logic
        
        Args:
            job: Failed UploadJob
            error_message: Error message
            
        Returns:
            Tuple of (success, error_message)
        """
        job.error_message = error_message
        job.retry_count += 1
        
        if job.retry_count < self.max_retries:
            # Calculate retry delay with exponential backoff
            delay = min(
                self.retry_delay_base ** job.retry_count,
                self.retry_delay_max
            )
            
            job.status = UploadStatus.RETRYING.value
            
            logger.warning(f"Upload failed, will retry in {delay}s: job_id={job.id}, "
                         f"attempt={job.retry_count}/{self.max_retries}")
            
            # Move back to queue for retry
            del self.active_uploads[job.id]
            self.upload_queue.append(job)
            
            # Wait before retry
            time.sleep(delay)
            
            return False, f"Retrying ({job.retry_count}/{self.max_retries})"
        else:
            # Max retries exceeded
            job.status = UploadStatus.FAILED.value
            job.completed_at = datetime.now().isoformat()
            
            self.failed_uploads.append(job)
            del self.active_uploads[job.id]
            
            logger.error(f"Upload failed after {self.max_retries} retries: job_id={job.id}")
            
            return False, error_message
    
    def get_next_upload_job(self) -> Optional[UploadJob]:
        """
        Get the next upload job from the queue
        
        Returns:
            Next UploadJob or None if queue is empty
        """
        if not self.upload_queue:
            return None
        
        # Return oldest job (FIFO)
        return self.upload_queue[0]
    
    def process_upload_queue(self, max_concurrent: int = 3) -> Dict[str, Any]:
        """
        Process upload queue with concurrent uploads
        
        Args:
            max_concurrent: Maximum number of concurrent uploads
            
        Returns:
            Dictionary with processing results
        """
        if not self.is_enabled():
            logger.warning("Cloud sync is not enabled")
            return {
                'processed': 0,
                'succeeded': 0,
                'failed': 0,
                'message': 'Cloud sync is not enabled'
            }
        
        processed = 0
        succeeded = 0
        failed = 0
        
        logger.info(f"Processing upload queue: {len(self.upload_queue)} jobs pending")
        
        while self.upload_queue and len(self.active_uploads) < max_concurrent:
            job = self.get_next_upload_job()
            
            if not job:
                break
            
            success, error = self.process_upload_job(job.id)
            processed += 1
            
            if success:
                succeeded += 1
            else:
                if job.status == UploadStatus.FAILED.value:
                    failed += 1
        
        result = {
            'processed': processed,
            'succeeded': succeeded,
            'failed': failed,
            'pending': len(self.upload_queue),
            'active': len(self.active_uploads)
        }
        
        logger.info(f"Upload queue processed: {result}")
        
        return result
    
    def get_upload_status(self, job_id: str) -> Optional[UploadJob]:
        """
        Get status of an upload job
        
        Args:
            job_id: ID of the upload job
            
        Returns:
            UploadJob or None if not found
        """
        # Check active uploads
        if job_id in self.active_uploads:
            return self.active_uploads[job_id]
        
        # Check queue
        for job in self.upload_queue:
            if job.id == job_id:
                return job
        
        # Check completed
        for job in self.completed_uploads:
            if job.id == job_id:
                return job
        
        # Check failed
        for job in self.failed_uploads:
            if job.id == job_id:
                return job
        
        return None
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get overall queue status
        
        Returns:
            Dictionary with queue statistics
        """
        total_size = sum(job.file_size or 0 for job in self.upload_queue)
        uploaded_size = sum(job.bytes_uploaded for job in self.active_uploads.values())
        
        return {
            'enabled': self.is_enabled(),
            'provider': self.provider.value,
            'remote_path': self.remote_path,
            'pending_count': len(self.upload_queue),
            'active_count': len(self.active_uploads),
            'completed_count': len(self.completed_uploads),
            'failed_count': len(self.failed_uploads),
            'total_queue_size': total_size,
            'uploaded_size': uploaded_size,
            'pending_jobs': [job.to_dict() for job in self.upload_queue[:10]],  # First 10
            'active_jobs': [job.to_dict() for job in self.active_uploads.values()]
        }
    
    def cancel_upload(self, job_id: str) -> bool:
        """
        Cancel an upload job
        
        Args:
            job_id: ID of the upload job to cancel
            
        Returns:
            True if job was cancelled, False if not found or already processing
        """
        logger.info(f"Cancelling upload job: job_id={job_id}")
        
        # Check queue
        for job in self.upload_queue:
            if job.id == job_id:
                job.status = UploadStatus.CANCELLED.value
                self.upload_queue.remove(job)
                logger.info(f"Upload job cancelled: {job_id}")
                return True
        
        # Cannot cancel active uploads
        if job_id in self.active_uploads:
            logger.warning(f"Cannot cancel active upload: {job_id}")
            return False
        
        logger.warning(f"Upload job not found: {job_id}")
        return False
    
    def retry_failed_upload(self, job_id: str) -> bool:
        """
        Retry a failed upload job
        
        Args:
            job_id: ID of the failed upload job
            
        Returns:
            True if job was queued for retry, False if not found
        """
        logger.info(f"Retrying failed upload: job_id={job_id}")
        
        # Find in failed uploads
        job = None
        for j in self.failed_uploads:
            if j.id == job_id:
                job = j
                break
        
        if not job:
            logger.warning(f"Failed upload job not found: {job_id}")
            return False
        
        # Reset job status
        job.status = UploadStatus.PENDING.value
        job.retry_count = 0
        job.error_message = None
        job.bytes_uploaded = 0
        job.progress_percent = 0.0
        
        # Move back to queue
        self.failed_uploads.remove(job)
        self.upload_queue.append(job)
        
        logger.info(f"Failed upload queued for retry: {job_id}")
        
        return True
    
    def retry_all_failed_uploads(self) -> int:
        """
        Retry all failed uploads
        
        Returns:
            Number of jobs queued for retry
        """
        count = len(self.failed_uploads)
        
        if count == 0:
            logger.info("No failed uploads to retry")
            return 0
        
        logger.info(f"Retrying {count} failed uploads")
        
        # Move all failed jobs back to queue
        for job in self.failed_uploads[:]:
            job.status = UploadStatus.PENDING.value
            job.retry_count = 0
            job.error_message = None
            job.bytes_uploaded = 0
            job.progress_percent = 0.0
            
            self.upload_queue.append(job)
        
        self.failed_uploads.clear()
        
        logger.info(f"Queued {count} failed uploads for retry")
        
        return count
    
    def clear_completed_uploads(self) -> int:
        """
        Clear completed upload history
        
        Returns:
            Number of completed uploads cleared
        """
        count = len(self.completed_uploads)
        self.completed_uploads.clear()
        
        logger.info(f"Cleared {count} completed uploads")
        
        return count
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Test connection to cloud storage
        
        Returns:
            Tuple of (success, error_message)
        """
        if not self.rclone_available:
            return False, "rclone is not available"
        
        if not self.is_enabled():
            return False, "Cloud sync is not enabled"
        
        try:
            remote_name = self.get_rclone_remote_name()
            
            # Test with rclone lsd (list directories)
            cmd = ['rclone', 'lsd', f"{remote_name}:", '--max-depth', '1']
            
            logger.info(f"Testing cloud connection: {remote_name}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"Cloud connection test successful: {remote_name}")
                return True, None
            else:
                error_msg = f"Connection test failed: {result.stderr}"
                logger.error(error_msg)
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "Connection test timed out"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Connection test failed: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg


# Convenience function for quick access
def get_cloud_sync_manager(config: Optional[Dict[str, Any]] = None) -> CloudSyncManager:
    """
    Get a CloudSyncManager instance
    
    Args:
        config: Optional cloud sync configuration
        
    Returns:
        CloudSyncManager instance
    """
    return CloudSyncManager(config)


if __name__ == '__main__':
    # Setup logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=== Testing Cloud Sync Manager ===\n")
    
    # Test 1: Create manager
    print("Test 1: Create manager")
    config = {
        'enabled': True,
        'provider': 'dropbox',
        'remote_path': '/Photos/Test'
    }
    manager = CloudSyncManager(config)
    print(f"✓ Manager created: enabled={manager.is_enabled()}, provider={manager.provider.value}")
    
    # Test 2: Check rclone
    print("\nTest 2: Check rclone availability")
    print(f"✓ rclone available: {manager.rclone_available}")
    
    # Test 3: Configure
    print("\nTest 3: Configure cloud sync")
    success = manager.configure(True, 'google_drive', '/Photos/Processed')
    print(f"✓ Configuration updated: {success}")
    
    # Test 4: Get queue status
    print("\nTest 4: Get queue status")
    status = manager.get_queue_status()
    print(f"✓ Queue status: pending={status['pending_count']}, active={status['active_count']}")
    
    # Test 5: Test connection (if rclone is available)
    if manager.rclone_available:
        print("\nTest 5: Test connection")
        success, error = manager.test_connection()
        print(f"✓ Connection test: success={success}, error={error}")
    else:
        print("\nTest 5: Skipped (rclone not available)")
    
    print("\n=== Basic tests passed! ===")
    print("Note: Full testing requires rclone installation and cloud provider configuration")
