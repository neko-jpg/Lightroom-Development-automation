"""
Batch Processing Controller for Junmai AutoDev

This module provides batch processing control functionality including:
- Pause/resume batch operations
- State persistence for recovery
- Progress tracking and recovery

Requirements: 11.4, 14.3
"""

import json
import pathlib
from datetime import datetime
from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, asdict
from threading import Lock

from models.database import get_session, Job, Photo, Session as DBSession
from logging_system import get_logging_system
from job_queue_manager import get_job_queue_manager

logging_system = get_logging_system()


class BatchStatus(Enum):
    """Batch processing status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchState:
    """Batch processing state for persistence"""
    batch_id: str
    session_id: Optional[int]
    photo_ids: List[int]
    processed_photo_ids: List[int]
    failed_photo_ids: List[int]
    status: str
    created_at: str
    started_at: Optional[str]
    paused_at: Optional[str]
    completed_at: Optional[str]
    total_photos: int
    processed_count: int
    failed_count: int
    config: Optional[Dict]
    task_ids: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BatchState':
        """Create from dictionary"""
        return cls(**data)


class BatchController:
    """
    Controller for batch processing operations
    
    Provides:
    - Pause/resume batch processing
    - State persistence and recovery
    - Progress tracking
    - Error handling and recovery
    """
    
    def __init__(self, state_dir: Optional[pathlib.Path] = None):
        """
        Initialize batch controller
        
        Args:
            state_dir: Directory for state persistence (default: data/batch_states)
        """
        self.job_queue_manager = get_job_queue_manager()
        
        # State directory
        if state_dir is None:
            state_dir = pathlib.Path(__file__).parent / "data" / "batch_states"
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # Active batches
        self.active_batches: Dict[str, BatchState] = {}
        self.batch_lock = Lock()
        
        # Load persisted states
        self._load_persisted_states()
        
        logging_system.log("INFO", "Batch controller initialized",
                          state_dir=str(self.state_dir))
    
    def _load_persisted_states(self):
        """Load persisted batch states from disk"""
        try:
            state_files = list(self.state_dir.glob("*.json"))
            
            for state_file in state_files:
                try:
                    with open(state_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    batch_state = BatchState.from_dict(data)
                    
                    # Only load non-completed batches
                    if batch_state.status not in [BatchStatus.COMPLETED.value, 
                                                   BatchStatus.CANCELLED.value]:
                        self.active_batches[batch_state.batch_id] = batch_state
                        logging_system.log("INFO", "Loaded persisted batch state",
                                          batch_id=batch_state.batch_id,
                                          status=batch_state.status)
                
                except Exception as e:
                    logging_system.log_error("Failed to load batch state file",
                                            file=str(state_file),
                                            exception=e)
            
            logging_system.log("INFO", "Loaded persisted batch states",
                              count=len(self.active_batches))
        
        except Exception as e:
            logging_system.log_error("Failed to load persisted states", exception=e)
    
    def _persist_state(self, batch_id: str):
        """
        Persist batch state to disk
        
        Args:
            batch_id: Batch identifier
        """
        try:
            with self.batch_lock:
                if batch_id not in self.active_batches:
                    return
                
                batch_state = self.active_batches[batch_id]
                state_file = self.state_dir / f"{batch_id}.json"
                
                with open(state_file, 'w', encoding='utf-8') as f:
                    json.dump(batch_state.to_dict(), f, indent=2, ensure_ascii=False)
                
                logging_system.log("DEBUG", "Persisted batch state",
                                  batch_id=batch_id)
        
        except Exception as e:
            logging_system.log_error("Failed to persist batch state",
                                    batch_id=batch_id,
                                    exception=e)
    
    def _delete_persisted_state(self, batch_id: str):
        """
        Delete persisted batch state
        
        Args:
            batch_id: Batch identifier
        """
        try:
            state_file = self.state_dir / f"{batch_id}.json"
            if state_file.exists():
                state_file.unlink()
                logging_system.log("DEBUG", "Deleted persisted batch state",
                                  batch_id=batch_id)
        
        except Exception as e:
            logging_system.log_error("Failed to delete persisted state",
                                    batch_id=batch_id,
                                    exception=e)
    
    def start_batch(
        self,
        photo_ids: List[int],
        session_id: Optional[int] = None,
        config: Optional[Dict] = None,
        batch_id: Optional[str] = None
    ) -> str:
        """
        Start a new batch processing operation
        
        Args:
            photo_ids: List of photo IDs to process
            session_id: Optional session ID
            config: Optional processing configuration
            batch_id: Optional batch ID (for resuming)
            
        Returns:
            Batch ID
            
        Requirements: 11.4
        """
        import uuid
        
        if batch_id is None:
            batch_id = f"batch_{uuid.uuid4().hex[:12]}"
        
        with self.batch_lock:
            # Create batch state
            batch_state = BatchState(
                batch_id=batch_id,
                session_id=session_id,
                photo_ids=photo_ids,
                processed_photo_ids=[],
                failed_photo_ids=[],
                status=BatchStatus.RUNNING.value,
                created_at=datetime.utcnow().isoformat(),
                started_at=datetime.utcnow().isoformat(),
                paused_at=None,
                completed_at=None,
                total_photos=len(photo_ids),
                processed_count=0,
                failed_count=0,
                config=config,
                task_ids=[]
            )
            
            self.active_batches[batch_id] = batch_state
        
        # Persist state
        self._persist_state(batch_id)
        
        # Submit jobs
        task_ids = self.job_queue_manager.submit_batch_processing(photo_ids)
        batch_state.task_ids = task_ids
        self._persist_state(batch_id)
        
        logging_system.log("INFO", "Started batch processing",
                          batch_id=batch_id,
                          photo_count=len(photo_ids),
                          session_id=session_id)
        
        return batch_id
    
    def pause_batch(self, batch_id: str) -> bool:
        """
        Pause a running batch
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            True if paused successfully
            
        Requirements: 11.4, 14.3
        """
        with self.batch_lock:
            if batch_id not in self.active_batches:
                logging_system.log("WARNING", "Batch not found for pause",
                                  batch_id=batch_id)
                return False
            
            batch_state = self.active_batches[batch_id]
            
            if batch_state.status != BatchStatus.RUNNING.value:
                logging_system.log("WARNING", "Batch not in running state",
                                  batch_id=batch_id,
                                  status=batch_state.status)
                return False
            
            # Cancel pending tasks
            for task_id in batch_state.task_ids:
                try:
                    self.job_queue_manager.cancel_job(task_id)
                except Exception as e:
                    logging_system.log_error("Failed to cancel task during pause",
                                            task_id=task_id,
                                            exception=e)
            
            # Update state
            batch_state.status = BatchStatus.PAUSED.value
            batch_state.paused_at = datetime.utcnow().isoformat()
        
        # Persist state
        self._persist_state(batch_id)
        
        logging_system.log("INFO", "Paused batch processing",
                          batch_id=batch_id)
        
        return True
    
    def resume_batch(self, batch_id: str) -> bool:
        """
        Resume a paused batch
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            True if resumed successfully
            
        Requirements: 11.4, 14.3
        """
        with self.batch_lock:
            if batch_id not in self.active_batches:
                logging_system.log("WARNING", "Batch not found for resume",
                                  batch_id=batch_id)
                return False
            
            batch_state = self.active_batches[batch_id]
            
            if batch_state.status != BatchStatus.PAUSED.value:
                logging_system.log("WARNING", "Batch not in paused state",
                                  batch_id=batch_id,
                                  status=batch_state.status)
                return False
            
            # Calculate remaining photos
            remaining_photo_ids = [
                pid for pid in batch_state.photo_ids
                if pid not in batch_state.processed_photo_ids
                and pid not in batch_state.failed_photo_ids
            ]
            
            if not remaining_photo_ids:
                # No photos left to process
                batch_state.status = BatchStatus.COMPLETED.value
                batch_state.completed_at = datetime.utcnow().isoformat()
                self._persist_state(batch_id)
                
                logging_system.log("INFO", "Batch already completed",
                                  batch_id=batch_id)
                return True
            
            # Update state
            batch_state.status = BatchStatus.RUNNING.value
            batch_state.started_at = datetime.utcnow().isoformat()
        
        # Persist state
        self._persist_state(batch_id)
        
        # Resubmit remaining jobs
        task_ids = self.job_queue_manager.submit_batch_processing(remaining_photo_ids)
        batch_state.task_ids = task_ids
        self._persist_state(batch_id)
        
        logging_system.log("INFO", "Resumed batch processing",
                          batch_id=batch_id,
                          remaining_photos=len(remaining_photo_ids))
        
        return True
    
    def cancel_batch(self, batch_id: str) -> bool:
        """
        Cancel a batch
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            True if cancelled successfully
        """
        with self.batch_lock:
            if batch_id not in self.active_batches:
                logging_system.log("WARNING", "Batch not found for cancel",
                                  batch_id=batch_id)
                return False
            
            batch_state = self.active_batches[batch_id]
            
            # Cancel all tasks
            for task_id in batch_state.task_ids:
                try:
                    self.job_queue_manager.cancel_job(task_id)
                except Exception as e:
                    logging_system.log_error("Failed to cancel task",
                                            task_id=task_id,
                                            exception=e)
            
            # Update state
            batch_state.status = BatchStatus.CANCELLED.value
            batch_state.completed_at = datetime.utcnow().isoformat()
        
        # Persist state
        self._persist_state(batch_id)
        
        logging_system.log("INFO", "Cancelled batch processing",
                          batch_id=batch_id)
        
        return True
    
    def update_batch_progress(
        self,
        batch_id: str,
        photo_id: int,
        success: bool,
        error_message: Optional[str] = None
    ):
        """
        Update batch progress when a photo completes
        
        Args:
            batch_id: Batch identifier
            photo_id: Photo ID that completed
            success: Whether processing succeeded
            error_message: Optional error message
            
        Requirements: 11.4, 14.3
        """
        with self.batch_lock:
            if batch_id not in self.active_batches:
                return
            
            batch_state = self.active_batches[batch_id]
            
            if success:
                if photo_id not in batch_state.processed_photo_ids:
                    batch_state.processed_photo_ids.append(photo_id)
                    batch_state.processed_count += 1
            else:
                if photo_id not in batch_state.failed_photo_ids:
                    batch_state.failed_photo_ids.append(photo_id)
                    batch_state.failed_count += 1
            
            # Check if batch is complete
            total_done = batch_state.processed_count + batch_state.failed_count
            if total_done >= batch_state.total_photos:
                batch_state.status = BatchStatus.COMPLETED.value
                batch_state.completed_at = datetime.utcnow().isoformat()
                
                logging_system.log("INFO", "Batch processing completed",
                                  batch_id=batch_id,
                                  processed=batch_state.processed_count,
                                  failed=batch_state.failed_count)
        
        # Persist state
        self._persist_state(batch_id)
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict]:
        """
        Get batch status
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Batch status dictionary or None if not found
        """
        with self.batch_lock:
            if batch_id not in self.active_batches:
                return None
            
            batch_state = self.active_batches[batch_id]
            
            return {
                'batch_id': batch_state.batch_id,
                'session_id': batch_state.session_id,
                'status': batch_state.status,
                'total_photos': batch_state.total_photos,
                'processed_count': batch_state.processed_count,
                'failed_count': batch_state.failed_count,
                'progress_percent': (batch_state.processed_count / batch_state.total_photos * 100) 
                                   if batch_state.total_photos > 0 else 0,
                'created_at': batch_state.created_at,
                'started_at': batch_state.started_at,
                'paused_at': batch_state.paused_at,
                'completed_at': batch_state.completed_at
            }
    
    def get_all_batches(self) -> List[Dict]:
        """
        Get all active batches
        
        Returns:
            List of batch status dictionaries
        """
        with self.batch_lock:
            return [
                self.get_batch_status(batch_id)
                for batch_id in self.active_batches.keys()
            ]
    
    def recover_interrupted_batches(self) -> Dict:
        """
        Recover batches that were interrupted
        
        Returns:
            Recovery statistics
            
        Requirements: 14.3
        """
        recovered_count = 0
        failed_count = 0
        
        with self.batch_lock:
            for batch_id, batch_state in list(self.active_batches.items()):
                if batch_state.status == BatchStatus.RUNNING.value:
                    # Batch was running when system stopped
                    try:
                        # Mark as paused for manual review
                        batch_state.status = BatchStatus.PAUSED.value
                        batch_state.paused_at = datetime.utcnow().isoformat()
                        self._persist_state(batch_id)
                        
                        recovered_count += 1
                        
                        logging_system.log("INFO", "Recovered interrupted batch",
                                          batch_id=batch_id)
                    
                    except Exception as e:
                        failed_count += 1
                        logging_system.log_error("Failed to recover batch",
                                                batch_id=batch_id,
                                                exception=e)
        
        result = {
            'recovered_count': recovered_count,
            'failed_count': failed_count,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logging_system.log("INFO", "Batch recovery completed", **result)
        
        return result
    
    def cleanup_completed_batches(self, days_old: int = 7) -> int:
        """
        Clean up old completed batch states
        
        Args:
            days_old: Remove batches completed more than this many days ago
            
        Returns:
            Number of batches cleaned up
        """
        from datetime import timedelta
        
        cleanup_count = 0
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        with self.batch_lock:
            for batch_id, batch_state in list(self.active_batches.items()):
                if batch_state.status in [BatchStatus.COMPLETED.value, 
                                         BatchStatus.CANCELLED.value]:
                    if batch_state.completed_at:
                        completed_date = datetime.fromisoformat(batch_state.completed_at)
                        if completed_date < cutoff_date:
                            # Remove from active batches
                            del self.active_batches[batch_id]
                            
                            # Delete persisted state
                            self._delete_persisted_state(batch_id)
                            
                            cleanup_count += 1
        
        logging_system.log("INFO", "Cleaned up old batch states",
                          count=cleanup_count,
                          days_old=days_old)
        
        return cleanup_count


# Global instance
_batch_controller = None

def get_batch_controller() -> BatchController:
    """Get global batch controller instance"""
    global _batch_controller
    if _batch_controller is None:
        _batch_controller = BatchController()
    return _batch_controller
