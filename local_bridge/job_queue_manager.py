"""
Job Queue Manager for Junmai AutoDev

This module provides a high-level interface for managing the Celery job queue,
including job submission, status tracking, and priority management.

Requirements: 4.1, 4.2, 4.4
"""

from celery_config import app, get_priority_for_photo, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW
from celery_tasks import (
    process_photo_task,
    analyze_exif_task,
    evaluate_quality_task,
    group_similar_photos_task,
    apply_preset_task,
    export_photo_task,
    process_batch_photos
)
from models.database import get_session, Photo, Job, Session as DBSession
from logging_system import get_logging_system
from priority_manager import get_priority_manager
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

logging_system = get_logging_system()


class JobQueueManager:
    """
    Manager for background job queue operations
    
    Provides methods for:
    - Submitting jobs with priority
    - Tracking job status
    - Managing job lifecycle
    - Resource monitoring
    """
    
    def __init__(self):
        """Initialize job queue manager"""
        self.celery_app = app
        self.priority_manager = get_priority_manager()
        logging_system.log("INFO", "Job queue manager initialized")
    
    def submit_photo_processing(
        self,
        photo_id: int,
        user_requested: bool = False,
        config: Optional[Dict] = None
    ) -> str:
        """
        Submit photo for processing
        
        Args:
            photo_id: Photo database ID
            user_requested: Whether manually requested by user
            config: Optional processing configuration
            
        Returns:
            Task ID
            
        Requirements: 4.1, 4.4
        """
        db_session = get_session()
        try:
            # Get photo to determine priority
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                raise ValueError(f"Photo not found: {photo_id}")
            
            # Calculate priority using advanced priority manager
            priority = self.priority_manager.calculate_priority(
                photo_id=photo_id,
                user_requested=user_requested
            )
            
            # Submit task
            result = process_photo_task.apply_async(
                args=[photo_id, config],
                priority=priority
            )
            
            # Create job record
            job = Job(
                id=result.id,
                photo_id=photo_id,
                priority=priority,
                config_json=json.dumps(config) if config else None,
                status='pending',
                retry_count=0
            )
            db_session.add(job)
            db_session.commit()
            
            logging_system.log("INFO", "Photo processing job submitted",
                              photo_id=photo_id,
                              task_id=result.id,
                              priority=priority,
                              user_requested=user_requested)
            
            return result.id
            
        finally:
            db_session.close()
    
    def submit_batch_processing(
        self,
        photo_ids: List[int],
        priority: int = PRIORITY_MEDIUM
    ) -> List[str]:
        """
        Submit batch of photos for processing
        
        Args:
            photo_ids: List of photo IDs
            priority: Task priority
            
        Returns:
            List of task IDs
            
        Requirements: 4.1
        """
        task_ids = process_batch_photos(photo_ids, priority)
        
        logging_system.log("INFO", "Batch processing submitted",
                          photo_count=len(photo_ids),
                          priority=priority)
        
        return task_ids
    
    def submit_session_processing(
        self,
        session_id: int,
        auto_select: bool = True
    ) -> Dict:
        """
        Submit all photos in a session for processing
        
        Args:
            session_id: Session database ID
            auto_select: Whether to only process selected photos
            
        Returns:
            Processing results with task IDs
            
        Requirements: 4.1
        """
        db_session = get_session()
        try:
            # Get session
            session = db_session.query(DBSession).filter(
                DBSession.id == session_id
            ).first()
            
            if not session:
                raise ValueError(f"Session not found: {session_id}")
            
            # Get photos
            query = db_session.query(Photo).filter(Photo.session_id == session_id)
            
            if auto_select:
                # Only process photos with AI score >= 3.5
                query = query.filter(Photo.ai_score >= 3.5)
            
            photos = query.all()
            photo_ids = [p.id for p in photos]
            
            # Submit batch
            task_ids = self.submit_batch_processing(photo_ids)
            
            # Update session status
            session.status = 'processing'
            db_session.commit()
            
            logging_system.log("INFO", "Session processing submitted",
                              session_id=session_id,
                              photo_count=len(photo_ids))
            
            return {
                'session_id': session_id,
                'photo_count': len(photo_ids),
                'task_ids': task_ids
            }
            
        finally:
            db_session.close()
    
    def get_job_status(self, task_id: str) -> Dict:
        """
        Get status of a job
        
        Args:
            task_id: Celery task ID
            
        Returns:
            Job status dictionary
            
        Requirements: 4.1
        """
        result = self.celery_app.AsyncResult(task_id)
        
        status = {
            'task_id': task_id,
            'state': result.state,
            'ready': result.ready(),
            'successful': result.successful() if result.ready() else None,
            'failed': result.failed() if result.ready() else None,
        }
        
        if result.ready():
            if result.successful():
                status['result'] = result.result
            elif result.failed():
                status['error'] = str(result.info)
        
        return status
    
    def get_queue_stats(self) -> Dict:
        """
        Get statistics about job queues
        
        Returns:
            Queue statistics dictionary
            
        Requirements: 4.1
        """
        inspect = self.celery_app.control.inspect()
        
        # Get active tasks
        active = inspect.active()
        active_count = sum(len(tasks) for tasks in (active or {}).values())
        
        # Get scheduled tasks
        scheduled = inspect.scheduled()
        scheduled_count = sum(len(tasks) for tasks in (scheduled or {}).values())
        
        # Get reserved tasks
        reserved = inspect.reserved()
        reserved_count = sum(len(tasks) for tasks in (reserved or {}).values())
        
        # Get stats from database
        db_session = get_session()
        try:
            from sqlalchemy import func
            
            # Count jobs by status
            status_counts = db_session.query(
                Job.status,
                func.count(Job.id)
            ).group_by(Job.status).all()
            
            # Count jobs by priority
            priority_counts = db_session.query(
                Job.priority,
                func.count(Job.id)
            ).group_by(Job.priority).all()
            
            stats = {
                'active_tasks': active_count,
                'scheduled_tasks': scheduled_count,
                'reserved_tasks': reserved_count,
                'total_pending': active_count + scheduled_count + reserved_count,
                'jobs_by_status': {status: count for status, count in status_counts},
                'jobs_by_priority': {priority: count for priority, count in priority_counts},
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return stats
            
        finally:
            db_session.close()
    
    def cancel_job(self, task_id: str) -> bool:
        """
        Cancel a pending or running job
        
        Args:
            task_id: Celery task ID
            
        Returns:
            True if cancelled successfully
            
        Requirements: 4.1
        """
        try:
            self.celery_app.control.revoke(task_id, terminate=True)
            
            # Update job status in database
            db_session = get_session()
            try:
                job = db_session.query(Job).filter(Job.id == task_id).first()
                if job:
                    job.status = 'cancelled'
                    db_session.commit()
            finally:
                db_session.close()
            
            logging_system.log("INFO", "Job cancelled", task_id=task_id)
            
            return True
            
        except Exception as e:
            logging_system.log_error("Failed to cancel job",
                                    task_id=task_id,
                                    exception=e)
            return False
    
    def pause_queue(self) -> bool:
        """
        Pause job processing
        
        Returns:
            True if paused successfully
            
        Requirements: 4.1
        """
        try:
            # Stop consuming from queues
            self.celery_app.control.cancel_consumer('high_priority')
            self.celery_app.control.cancel_consumer('medium_priority')
            self.celery_app.control.cancel_consumer('low_priority')
            self.celery_app.control.cancel_consumer('default')
            
            logging_system.log("INFO", "Job queue paused")
            
            return True
            
        except Exception as e:
            logging_system.log_error("Failed to pause queue", exception=e)
            return False
    
    def resume_queue(self) -> bool:
        """
        Resume job processing
        
        Returns:
            True if resumed successfully
            
        Requirements: 4.1
        """
        try:
            # Resume consuming from queues
            self.celery_app.control.add_consumer('high_priority')
            self.celery_app.control.add_consumer('medium_priority')
            self.celery_app.control.add_consumer('low_priority')
            self.celery_app.control.add_consumer('default')
            
            logging_system.log("INFO", "Job queue resumed")
            
            return True
            
        except Exception as e:
            logging_system.log_error("Failed to resume queue", exception=e)
            return False
    
    def get_worker_stats(self) -> Dict:
        """
        Get statistics about Celery workers
        
        Returns:
            Worker statistics dictionary
        """
        inspect = self.celery_app.control.inspect()
        
        stats = inspect.stats()
        active = inspect.active()
        registered = inspect.registered()
        
        return {
            'workers': stats or {},
            'active_tasks': active or {},
            'registered_tasks': registered or {},
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def purge_queue(self, queue_name: Optional[str] = None) -> int:
        """
        Purge all pending tasks from queue
        
        Args:
            queue_name: Specific queue to purge (optional)
            
        Returns:
            Number of tasks purged
            
        Requirements: 4.1
        """
        try:
            if queue_name:
                count = self.celery_app.control.purge()
            else:
                count = self.celery_app.control.purge()
            
            logging_system.log("WARNING", "Queue purged",
                              queue_name=queue_name or 'all',
                              tasks_purged=count)
            
            return count
            
        except Exception as e:
            logging_system.log_error("Failed to purge queue", exception=e)
            return 0
    
    def get_failed_jobs(self, limit: int = 50) -> List[Dict]:
        """
        Get list of failed jobs
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of failed job dictionaries
        """
        db_session = get_session()
        try:
            jobs = db_session.query(Job).filter(
                Job.status == 'failed'
            ).order_by(Job.created_at.desc()).limit(limit).all()
            
            failed_jobs = []
            for job in jobs:
                failed_jobs.append({
                    'id': job.id,
                    'photo_id': job.photo_id,
                    'priority': job.priority,
                    'created_at': job.created_at.isoformat() if job.created_at else None,
                    'error_message': job.error_message,
                    'retry_count': job.retry_count
                })
            
            return failed_jobs
            
        finally:
            db_session.close()
    
    def retry_failed_job(self, task_id: str) -> Optional[str]:
        """
        Retry a failed job
        
        Args:
            task_id: Original task ID
            
        Returns:
            New task ID if successful, None otherwise
            
        Requirements: 4.2
        """
        db_session = get_session()
        try:
            job = db_session.query(Job).filter(Job.id == task_id).first()
            if not job:
                return None
            
            # Submit new task
            config = json.loads(job.config_json) if job.config_json else None
            new_task_id = self.submit_photo_processing(
                photo_id=job.photo_id,
                config=config
            )
            
            logging_system.log("INFO", "Failed job retried",
                              original_task_id=task_id,
                              new_task_id=new_task_id)
            
            return new_task_id
            
        finally:
            db_session.close()
    
    def adjust_job_priority(self, job_id: str, new_priority: int) -> bool:
        """
        Adjust priority of an existing job
        
        Args:
            job_id: Job database ID
            new_priority: New priority value (1-10)
            
        Returns:
            True if successful
            
        Requirements: 4.4
        """
        return self.priority_manager.adjust_job_priority(job_id, new_priority)
    
    def rebalance_priorities(self) -> Dict:
        """
        Rebalance priorities for all pending jobs
        
        Returns:
            Rebalancing statistics
            
        Requirements: 4.4
        """
        return self.priority_manager.rebalance_queue_priorities()
    
    def boost_session_priority(self, session_id: int, boost_amount: int = 2) -> Dict:
        """
        Boost priority for all jobs in a session
        
        Args:
            session_id: Session database ID
            boost_amount: Amount to increase priority by
            
        Returns:
            Boost statistics
            
        Requirements: 4.4
        """
        return self.priority_manager.boost_session_priority(session_id, boost_amount)
    
    def get_priority_distribution(self) -> Dict:
        """
        Get distribution of priorities in the queue
        
        Returns:
            Priority distribution statistics
            
        Requirements: 4.4
        """
        return self.priority_manager.get_priority_distribution()
    
    def auto_boost_starving_jobs(self, age_threshold_hours: int = 12) -> Dict:
        """
        Automatically boost priority of jobs waiting too long
        
        Args:
            age_threshold_hours: Hours threshold for auto-boost
            
        Returns:
            Auto-boost statistics
            
        Requirements: 4.4
        """
        return self.priority_manager.auto_boost_starving_jobs(age_threshold_hours)
    
    def get_starvation_candidates(self, age_threshold_hours: int = 12) -> List[Dict]:
        """
        Identify jobs at risk of starvation
        
        Args:
            age_threshold_hours: Hours threshold for detection
            
        Returns:
            List of starving job details
            
        Requirements: 4.4
        """
        return self.priority_manager.get_starvation_candidates(age_threshold_hours)


# Global instance
_job_queue_manager = None

def get_job_queue_manager() -> JobQueueManager:
    """Get global job queue manager instance"""
    global _job_queue_manager
    if _job_queue_manager is None:
        _job_queue_manager = JobQueueManager()
    return _job_queue_manager
