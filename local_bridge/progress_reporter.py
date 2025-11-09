# progress_reporter.py
#
# Real-time progress reporting system for job processing
# Sends progress updates via WebSocket to connected clients
#
# Requirements: 4.5

import logging
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger('junmai_autodev.progress')


class ProcessingStage(Enum):
    """Processing stages for photo workflow"""
    IMPORTING = "importing"
    EXIF_ANALYSIS = "exif_analysis"
    AI_EVALUATION = "ai_evaluation"
    CONTEXT_DETECTION = "context_detection"
    PRESET_SELECTION = "preset_selection"
    APPLYING_PRESET = "applying_preset"
    QUALITY_CHECK = "quality_check"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"


class ProgressReporter:
    """
    Real-time progress reporter for photo processing jobs
    
    Sends progress updates via WebSocket to connected clients
    including Lightroom plugin, GUI, and mobile apps.
    
    Requirements: 4.5
    """
    
    def __init__(self, websocket_server=None):
        """
        Initialize progress reporter
        
        Args:
            websocket_server: WebSocket server instance for broadcasting
        """
        self.websocket_server = websocket_server
        self.active_jobs = {}  # job_id -> job_info
        logger.info("Progress reporter initialized")
    
    def start_job(self, job_id: str, photo_id: int, photo_info: Dict):
        """
        Start tracking a new job
        
        Args:
            job_id: Unique job identifier
            photo_id: Photo database ID
            photo_info: Photo metadata (file_name, file_path, etc.)
        """
        self.active_jobs[job_id] = {
            'job_id': job_id,
            'photo_id': photo_id,
            'photo_info': photo_info,
            'started_at': datetime.now(),
            'current_stage': None,
            'progress': 0,
            'stages_completed': [],
            'errors': []
        }
        
        logger.info(f"Started tracking job {job_id} for photo {photo_id}")
        
        # Broadcast job start
        self._broadcast({
            'type': 'job_started',
            'job_id': job_id,
            'photo_id': photo_id,
            'photo_info': photo_info,
            'timestamp': datetime.now().isoformat()
        })
    
    def update_progress(
        self,
        job_id: str,
        stage: ProcessingStage,
        progress: float,
        message: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        """
        Update job progress
        
        Args:
            job_id: Job identifier
            stage: Current processing stage
            progress: Progress percentage (0-100)
            message: Optional progress message
            details: Optional additional details
        """
        if job_id not in self.active_jobs:
            logger.warning(f"Job {job_id} not found in active jobs")
            return
        
        job_info = self.active_jobs[job_id]
        job_info['current_stage'] = stage.value
        job_info['progress'] = progress
        job_info['last_update'] = datetime.now()
        
        logger.debug(f"Job {job_id} progress: {stage.value} - {progress}%")
        
        # Broadcast progress update
        self._broadcast({
            'type': 'job_progress',
            'job_id': job_id,
            'photo_id': job_info['photo_id'],
            'stage': stage.value,
            'progress': progress,
            'message': message or f"Processing: {stage.value}",
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }, channel='jobs')
    
    def complete_stage(self, job_id: str, stage: ProcessingStage, result: Optional[Dict] = None):
        """
        Mark a processing stage as completed
        
        Args:
            job_id: Job identifier
            stage: Completed stage
            result: Optional stage result data
        """
        if job_id not in self.active_jobs:
            logger.warning(f"Job {job_id} not found in active jobs")
            return
        
        job_info = self.active_jobs[job_id]
        job_info['stages_completed'].append({
            'stage': stage.value,
            'completed_at': datetime.now().isoformat(),
            'result': result
        })
        
        logger.info(f"Job {job_id} completed stage: {stage.value}")
        
        # Broadcast stage completion
        self._broadcast({
            'type': 'stage_completed',
            'job_id': job_id,
            'photo_id': job_info['photo_id'],
            'stage': stage.value,
            'result': result or {},
            'timestamp': datetime.now().isoformat()
        }, channel='jobs')
    
    def complete_job(self, job_id: str, success: bool, result: Optional[Dict] = None):
        """
        Mark job as completed
        
        Args:
            job_id: Job identifier
            success: Whether job completed successfully
            result: Optional job result data
        """
        if job_id not in self.active_jobs:
            logger.warning(f"Job {job_id} not found in active jobs")
            return
        
        job_info = self.active_jobs[job_id]
        job_info['completed_at'] = datetime.now()
        job_info['success'] = success
        job_info['result'] = result
        
        # Calculate total duration
        duration = (job_info['completed_at'] - job_info['started_at']).total_seconds()
        
        logger.info(f"Job {job_id} completed: success={success}, duration={duration:.2f}s")
        
        # Broadcast job completion
        self._broadcast({
            'type': 'job_completed' if success else 'job_failed',
            'job_id': job_id,
            'photo_id': job_info['photo_id'],
            'success': success,
            'result': result or {},
            'duration': duration,
            'stages_completed': job_info['stages_completed'],
            'timestamp': datetime.now().isoformat()
        }, channel='jobs')
        
        # Remove from active jobs after a delay (keep for history)
        # In production, you might want to move to a completed_jobs dict
    
    def report_error(
        self,
        job_id: str,
        error_type: str,
        error_message: str,
        error_details: Optional[Dict] = None,
        stage: Optional[ProcessingStage] = None
    ):
        """
        Report an error during job processing
        
        Args:
            job_id: Job identifier
            error_type: Type of error (e.g., 'validation_error', 'processing_error')
            error_message: Human-readable error message
            error_details: Optional detailed error information
            stage: Stage where error occurred
        """
        if job_id in self.active_jobs:
            job_info = self.active_jobs[job_id]
            error_record = {
                'error_type': error_type,
                'error_message': error_message,
                'error_details': error_details or {},
                'stage': stage.value if stage else job_info.get('current_stage'),
                'timestamp': datetime.now().isoformat()
            }
            job_info['errors'].append(error_record)
        
        logger.error(f"Job {job_id} error: {error_type} - {error_message}")
        
        # Broadcast error
        self._broadcast({
            'type': 'error_occurred',
            'job_id': job_id,
            'photo_id': self.active_jobs.get(job_id, {}).get('photo_id'),
            'error_type': error_type,
            'error_message': error_message,
            'error_details': error_details or {},
            'stage': stage.value if stage else None,
            'timestamp': datetime.now().isoformat()
        }, channel='jobs')
    
    def send_photo_info(self, job_id: str, photo_data: Dict):
        """
        Send detailed photo information
        
        Args:
            job_id: Job identifier
            photo_data: Detailed photo data (EXIF, AI scores, etc.)
        """
        if job_id not in self.active_jobs:
            logger.warning(f"Job {job_id} not found in active jobs")
            return
        
        job_info = self.active_jobs[job_id]
        
        logger.debug(f"Sending photo info for job {job_id}")
        
        # Broadcast photo information
        self._broadcast({
            'type': 'photo_info',
            'job_id': job_id,
            'photo_id': job_info['photo_id'],
            'photo_data': photo_data,
            'timestamp': datetime.now().isoformat()
        }, channel='photos')
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """
        Get current status of a job
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status dictionary or None if not found
        """
        if job_id not in self.active_jobs:
            return None
        
        job_info = self.active_jobs[job_id].copy()
        
        # Calculate elapsed time
        if 'started_at' in job_info:
            elapsed = (datetime.now() - job_info['started_at']).total_seconds()
            job_info['elapsed_seconds'] = elapsed
        
        return job_info
    
    def get_active_jobs(self) -> Dict[str, Dict]:
        """
        Get all active jobs
        
        Returns:
            Dictionary of job_id -> job_info
        """
        return self.active_jobs.copy()
    
    def _broadcast(self, message: Dict, channel: Optional[str] = None):
        """
        Broadcast message via WebSocket
        
        Args:
            message: Message to broadcast
            channel: Optional channel for filtered broadcast
        """
        if self.websocket_server:
            try:
                self.websocket_server.broadcast(message, channel=channel)
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")
        else:
            logger.debug(f"No WebSocket server configured, message not broadcast: {message['type']}")


# Global progress reporter instance
_progress_reporter: Optional[ProgressReporter] = None


def init_progress_reporter(websocket_server=None) -> ProgressReporter:
    """
    Initialize global progress reporter
    
    Args:
        websocket_server: WebSocket server instance
        
    Returns:
        ProgressReporter instance
    """
    global _progress_reporter
    _progress_reporter = ProgressReporter(websocket_server)
    return _progress_reporter


def get_progress_reporter() -> Optional[ProgressReporter]:
    """
    Get global progress reporter instance
    
    Returns:
        ProgressReporter instance or None if not initialized
    """
    return _progress_reporter
