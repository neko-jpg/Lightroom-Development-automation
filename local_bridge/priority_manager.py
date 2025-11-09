"""
Priority Management System for Junmai AutoDev

This module provides advanced priority calculation and dynamic adjustment
for the job queue system.

Requirements: 4.4
"""

from models.database import get_session, Photo, Job, Session as DBSession
from logging_system import get_logging_system
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import math

logging_system = get_logging_system()

# Priority constants
PRIORITY_MAX = 10
PRIORITY_MIN = 1
PRIORITY_HIGH = 9
PRIORITY_MEDIUM = 5
PRIORITY_LOW = 1


class PriorityManager:
    """
    Advanced priority management system
    
    Provides:
    - Dynamic priority calculation based on multiple factors
    - Age-based priority adjustment
    - User preference weighting
    - Queue balancing
    """
    
    def __init__(self):
        """Initialize priority manager"""
        self.config = {
            'ai_score_weight': 0.4,
            'age_weight': 0.3,
            'user_request_weight': 0.2,
            'context_weight': 0.1,
            'max_age_hours': 24,  # Max age for priority boost
            'age_boost_per_hour': 0.1,  # Priority increase per hour
        }
        logging_system.log("INFO", "Priority manager initialized")
    
    def calculate_priority(
        self,
        photo_id: int,
        user_requested: bool = False,
        override_priority: Optional[int] = None
    ) -> int:
        """
        Calculate comprehensive priority for a photo
        
        Args:
            photo_id: Photo database ID
            user_requested: Whether manually requested by user
            override_priority: Manual priority override
            
        Returns:
            Priority value (1-10)
            
        Requirements: 4.4
        """
        if override_priority is not None:
            return max(PRIORITY_MIN, min(PRIORITY_MAX, override_priority))
        
        db_session = get_session()
        try:
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                return PRIORITY_MEDIUM
            
            # Base priority from AI score
            ai_priority = self._calculate_ai_score_priority(photo.ai_score)
            
            # Age-based priority boost
            age_priority = self._calculate_age_priority(photo.import_time)
            
            # User request boost
            user_priority = PRIORITY_HIGH if user_requested else 0
            
            # Context-based priority
            context_priority = self._calculate_context_priority(photo.context_tag)
            
            # Weighted combination
            weights = self.config
            combined_priority = (
                ai_priority * weights['ai_score_weight'] +
                age_priority * weights['age_weight'] +
                user_priority * weights['user_request_weight'] +
                context_priority * weights['context_weight']
            )
            
            # Normalize to 1-10 range
            final_priority = max(PRIORITY_MIN, min(PRIORITY_MAX, int(combined_priority)))
            
            logging_system.log("DEBUG", "Priority calculated",
                              photo_id=photo_id,
                              ai_priority=ai_priority,
                              age_priority=age_priority,
                              user_priority=user_priority,
                              context_priority=context_priority,
                              final_priority=final_priority)
            
            return final_priority
            
        finally:
            db_session.close()
    
    def _calculate_ai_score_priority(self, ai_score: Optional[float]) -> float:
        """
        Calculate priority based on AI evaluation score
        
        Args:
            ai_score: AI score (1-5)
            
        Returns:
            Priority contribution (0-10)
        """
        if ai_score is None:
            return PRIORITY_MEDIUM
        
        # Map AI score (1-5) to priority (1-10)
        # 5.0 -> 10, 4.5 -> 9, 4.0 -> 8, 3.5 -> 6, 3.0 -> 5, 2.0 -> 3, 1.0 -> 1
        if ai_score >= 4.5:
            return 10
        elif ai_score >= 4.0:
            return 8
        elif ai_score >= 3.5:
            return 6
        elif ai_score >= 3.0:
            return 5
        elif ai_score >= 2.0:
            return 3
        else:
            return 1
    
    def _calculate_age_priority(self, import_time: Optional[datetime]) -> float:
        """
        Calculate priority boost based on photo age
        
        Older photos get higher priority to prevent starvation
        
        Args:
            import_time: Photo import timestamp
            
        Returns:
            Priority contribution (0-10)
        """
        if import_time is None:
            return 0
        
        age = datetime.utcnow() - import_time
        age_hours = age.total_seconds() / 3600
        
        # Calculate age boost (linear increase up to max_age_hours)
        max_hours = self.config['max_age_hours']
        boost_per_hour = self.config['age_boost_per_hour']
        
        age_boost = min(age_hours * boost_per_hour, max_hours * boost_per_hour)
        
        return age_boost
    
    def _calculate_context_priority(self, context_tag: Optional[str]) -> float:
        """
        Calculate priority based on photo context
        
        Some contexts may be prioritized (e.g., portraits over landscapes)
        
        Args:
            context_tag: Context classification
            
        Returns:
            Priority contribution (0-10)
        """
        if context_tag is None:
            return PRIORITY_MEDIUM
        
        # Priority mapping for different contexts
        context_priorities = {
            'backlit_portrait': 8,
            'low_light_indoor': 7,
            'portrait': 7,
            'event': 8,
            'wedding': 9,
            'landscape': 5,
            'landscape_sky': 6,
            'default': 5
        }
        
        return context_priorities.get(context_tag, PRIORITY_MEDIUM)
    
    def adjust_job_priority(self, job_id: str, new_priority: int) -> bool:
        """
        Dynamically adjust priority of an existing job
        
        Args:
            job_id: Job database ID
            new_priority: New priority value (1-10)
            
        Returns:
            True if successful
            
        Requirements: 4.4
        """
        new_priority = max(PRIORITY_MIN, min(PRIORITY_MAX, new_priority))
        
        db_session = get_session()
        try:
            job = db_session.query(Job).filter(Job.id == job_id).first()
            if not job:
                logging_system.log("WARNING", "Job not found for priority adjustment",
                                  job_id=job_id)
                return False
            
            old_priority = job.priority
            job.priority = new_priority
            db_session.commit()
            
            logging_system.log("INFO", "Job priority adjusted",
                              job_id=job_id,
                              old_priority=old_priority,
                              new_priority=new_priority)
            
            return True
            
        except Exception as e:
            logging_system.log_error("Failed to adjust job priority",
                                    job_id=job_id,
                                    exception=e)
            return False
            
        finally:
            db_session.close()
    
    def rebalance_queue_priorities(self) -> Dict:
        """
        Rebalance priorities for all pending jobs
        
        Adjusts priorities based on current age and queue state
        to prevent starvation and ensure fair processing
        
        Returns:
            Rebalancing statistics
            
        Requirements: 4.4
        """
        logging_system.log("INFO", "Starting queue priority rebalancing")
        
        db_session = get_session()
        try:
            # Get all pending jobs
            pending_jobs = db_session.query(Job).filter(
                Job.status == 'pending'
            ).all()
            
            if not pending_jobs:
                return {'adjusted_count': 0, 'total_pending': 0}
            
            adjusted_count = 0
            
            for job in pending_jobs:
                # Get photo for this job
                photo = db_session.query(Photo).filter(
                    Photo.id == job.photo_id
                ).first()
                
                if not photo:
                    continue
                
                # Recalculate priority
                new_priority = self.calculate_priority(photo.id)
                
                # Update if changed
                if new_priority != job.priority:
                    job.priority = new_priority
                    adjusted_count += 1
            
            db_session.commit()
            
            stats = {
                'adjusted_count': adjusted_count,
                'total_pending': len(pending_jobs),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logging_system.log("INFO", "Queue priority rebalancing completed",
                              **stats)
            
            return stats
            
        except Exception as e:
            logging_system.log_error("Failed to rebalance queue priorities",
                                    exception=e)
            return {'error': str(e)}
            
        finally:
            db_session.close()
    
    def get_priority_distribution(self) -> Dict:
        """
        Get distribution of priorities in the queue
        
        Returns:
            Priority distribution statistics
        """
        db_session = get_session()
        try:
            from sqlalchemy import func
            
            # Count jobs by priority
            priority_counts = db_session.query(
                Job.priority,
                func.count(Job.id)
            ).filter(
                Job.status == 'pending'
            ).group_by(Job.priority).all()
            
            distribution = {
                'by_priority': {priority: count for priority, count in priority_counts},
                'total_pending': sum(count for _, count in priority_counts),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Calculate average priority
            if priority_counts:
                total_weighted = sum(priority * count for priority, count in priority_counts)
                total_count = sum(count for _, count in priority_counts)
                distribution['average_priority'] = total_weighted / total_count if total_count > 0 else 0
            else:
                distribution['average_priority'] = 0
            
            return distribution
            
        finally:
            db_session.close()
    
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
        logging_system.log("INFO", "Boosting session priority",
                          session_id=session_id,
                          boost_amount=boost_amount)
        
        db_session = get_session()
        try:
            # Get all pending jobs for photos in this session
            jobs = db_session.query(Job).join(Photo).filter(
                Photo.session_id == session_id,
                Job.status == 'pending'
            ).all()
            
            boosted_count = 0
            
            for job in jobs:
                new_priority = min(PRIORITY_MAX, job.priority + boost_amount)
                if new_priority != job.priority:
                    job.priority = new_priority
                    boosted_count += 1
            
            db_session.commit()
            
            stats = {
                'session_id': session_id,
                'boosted_count': boosted_count,
                'total_jobs': len(jobs),
                'boost_amount': boost_amount
            }
            
            logging_system.log("INFO", "Session priority boost completed", **stats)
            
            return stats
            
        except Exception as e:
            logging_system.log_error("Failed to boost session priority",
                                    session_id=session_id,
                                    exception=e)
            return {'error': str(e)}
            
        finally:
            db_session.close()
    
    def get_starvation_candidates(self, age_threshold_hours: int = 12) -> List[Dict]:
        """
        Identify jobs at risk of starvation (waiting too long)
        
        Args:
            age_threshold_hours: Hours threshold for starvation detection
            
        Returns:
            List of starving job details
        """
        db_session = get_session()
        try:
            threshold_time = datetime.utcnow() - timedelta(hours=age_threshold_hours)
            
            # Find old pending jobs
            starving_jobs = db_session.query(Job).filter(
                Job.status == 'pending',
                Job.created_at < threshold_time
            ).order_by(Job.created_at).all()
            
            candidates = []
            for job in starving_jobs:
                age = datetime.utcnow() - job.created_at
                candidates.append({
                    'job_id': job.id,
                    'photo_id': job.photo_id,
                    'priority': job.priority,
                    'age_hours': age.total_seconds() / 3600,
                    'created_at': job.created_at.isoformat() if job.created_at else None
                })
            
            if candidates:
                logging_system.log("WARNING", "Starvation candidates detected",
                                  count=len(candidates),
                                  threshold_hours=age_threshold_hours)
            
            return candidates
            
        finally:
            db_session.close()
    
    def auto_boost_starving_jobs(self, age_threshold_hours: int = 12) -> Dict:
        """
        Automatically boost priority of jobs waiting too long
        
        Args:
            age_threshold_hours: Hours threshold for auto-boost
            
        Returns:
            Auto-boost statistics
            
        Requirements: 4.4
        """
        candidates = self.get_starvation_candidates(age_threshold_hours)
        
        if not candidates:
            return {'boosted_count': 0, 'candidates': 0}
        
        boosted_count = 0
        
        for candidate in candidates:
            # Boost priority by 2 levels
            success = self.adjust_job_priority(candidate['job_id'], candidate['priority'] + 2)
            if success:
                boosted_count += 1
        
        stats = {
            'boosted_count': boosted_count,
            'candidates': len(candidates),
            'threshold_hours': age_threshold_hours
        }
        
        logging_system.log("INFO", "Auto-boost completed for starving jobs", **stats)
        
        return stats
    
    def update_config(self, config_updates: Dict) -> bool:
        """
        Update priority calculation configuration
        
        Args:
            config_updates: Dictionary of config updates
            
        Returns:
            True if successful
        """
        try:
            for key, value in config_updates.items():
                if key in self.config:
                    self.config[key] = value
            
            logging_system.log("INFO", "Priority manager config updated",
                              updates=config_updates)
            
            return True
            
        except Exception as e:
            logging_system.log_error("Failed to update priority config",
                                    exception=e)
            return False


# Global instance
_priority_manager = None

def get_priority_manager() -> PriorityManager:
    """Get global priority manager instance"""
    global _priority_manager
    if _priority_manager is None:
        _priority_manager = PriorityManager()
    return _priority_manager
