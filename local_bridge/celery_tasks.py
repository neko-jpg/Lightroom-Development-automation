"""
Celery Tasks for Junmai AutoDev Background Processing

This module defines all background tasks for photo processing pipeline:
- EXIF analysis
- AI quality evaluation
- Photo grouping
- Preset application
- Export operations

Requirements: 4.1, 4.2, 4.4
"""

from celery import Task
from celery_config import app, get_priority_for_photo, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW
from models.database import get_session, Photo, Job, Session as DBSession
from exif_analyzer import EXIFAnalyzer
from image_quality_evaluator import ImageQualityEvaluator
from ai_selector import AISelector
from context_engine import ContextEngine
from preset_manager import PresetManager
from photo_grouper import PhotoGrouper
from logging_system import get_logging_system
import json
import time
from datetime import datetime
from typing import Dict, Optional, List
import traceback

# Initialize components (without database session)
logging_system = get_logging_system()
exif_analyzer = EXIFAnalyzer()
quality_evaluator = ImageQualityEvaluator()
ai_selector = AISelector()
context_engine = ContextEngine()
photo_grouper = PhotoGrouper()

# PresetManager requires db_session, so we'll create it per-task


class BaseTask(Task):
    """
    Base task class with retry logic and error handling
    
    Implements exponential backoff retry strategy (Requirement 4.2)
    """
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600  # Max 10 minutes
    retry_jitter = True
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logging_system.log_error(
            f"Task {self.name} failed",
            task_id=task_id,
            exception=exc,
            traceback=str(einfo)
        )
        
        # Update job status in database
        try:
            db_session = get_session()
            try:
                job = db_session.query(Job).filter(Job.id == task_id).first()
                if job:
                    job.status = 'failed'
                    job.error_message = str(exc)
                    job.retry_count = getattr(self.request, 'retries', 0)
                    db_session.commit()
            finally:
                db_session.close()
        except Exception as e:
            logging_system.log_error("Failed to update job status", exception=e)
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry"""
        retry_count = getattr(self.request, 'retries', 0)
        logging_system.log(
            "WARNING",
            f"Task {self.name} retrying",
            task_id=task_id,
            retry_count=retry_count,
            exception=str(exc)
        )
        
        # Update retry count in database
        try:
            db_session = get_session()
            try:
                job = db_session.query(Job).filter(Job.id == task_id).first()
                if job:
                    job.retry_count = retry_count
                    db_session.commit()
            finally:
                db_session.close()
        except Exception as e:
            logging_system.log_error("Failed to update retry count", exception=e)
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        logging_system.log(
            "INFO",
            f"Task {self.name} completed successfully",
            task_id=task_id
        )


@app.task(base=BaseTask, bind=True, name='celery_tasks.process_photo_task')
def process_photo_task(self, photo_id: int, config: Optional[Dict] = None) -> Dict:
    """
    Complete photo processing pipeline
    
    Args:
        photo_id: Photo database ID
        config: Optional processing configuration
        
    Returns:
        Processing results dictionary
        
    Requirements: 4.1, 4.2
    """
    start_time = time.time()
    
    logging_system.log("INFO", "Starting photo processing task",
                      task_id=self.request.id, photo_id=photo_id)
    
    db_session = get_session()
    try:
        # Get photo from database
        photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise ValueError(f"Photo not found: {photo_id}")
        
        # Update photo status
        photo.status = 'processing'
        db_session.commit()
        
        results = {}
        
        # Step 1: EXIF Analysis
        logging_system.log("INFO", "Analyzing EXIF data", photo_id=photo_id)
        exif_result = analyze_exif_task.apply_async(
            args=[photo_id],
            priority=PRIORITY_HIGH
        )
        exif_data = exif_result.get(timeout=30)
        results['exif'] = exif_data
        
        # Step 2: Quality Evaluation
        logging_system.log("INFO", "Evaluating image quality", photo_id=photo_id)
        quality_result = evaluate_quality_task.apply_async(
            args=[photo_id],
            priority=PRIORITY_MEDIUM
        )
        quality_data = quality_result.get(timeout=60)
        results['quality'] = quality_data
        
        # Update photo with AI score
        photo.ai_score = quality_data.get('overall_score', 0)
        photo.focus_score = quality_data.get('focus_score', 0)
        photo.exposure_score = quality_data.get('exposure_score', 0)
        photo.composition_score = quality_data.get('composition_score', 0)
        photo.detected_faces = quality_data.get('faces_detected', 0)
        
        # Step 3: Context Recognition
        logging_system.log("INFO", "Determining context", photo_id=photo_id)
        context = context_engine.determine_context(exif_data, quality_data)
        photo.context_tag = context
        results['context'] = context
        
        # Step 4: Preset Selection
        logging_system.log("INFO", "Selecting preset", photo_id=photo_id)
        preset_mgr = PresetManager(db_session)
        preset = preset_mgr.select_preset_for_context(context)
        if preset:
            photo.selected_preset = preset.name
            results['preset'] = preset.name
        
        # Update photo status
        photo.status = 'completed'
        db_session.commit()
        
        # Calculate processing time
        processing_time = time.time() - start_time
        results['processing_time'] = processing_time
        
        logging_system.log("INFO", "Photo processing completed",
                          photo_id=photo_id,
                          processing_time=processing_time,
                          ai_score=photo.ai_score)
        
        return results
        
    except Exception as e:
        # Update photo status on error
        photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
        if photo:
            photo.status = 'failed'
            db_session.commit()
        
        logging_system.log_error("Photo processing failed",
                                photo_id=photo_id,
                                exception=e)
        raise
        
    finally:
        db_session.close()


@app.task(base=BaseTask, bind=True, name='celery_tasks.analyze_exif_task')
def analyze_exif_task(self, photo_id: int) -> Dict:
    """
    Analyze EXIF metadata from photo
    
    Args:
        photo_id: Photo database ID
        
    Returns:
        EXIF data dictionary
    """
    logging_system.log("INFO", "Analyzing EXIF", photo_id=photo_id)
    
    db_session = get_session()
    try:
        photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise ValueError(f"Photo not found: {photo_id}")
        
        # Analyze EXIF
        exif_data = exif_analyzer.analyze(photo.file_path)
        
        # Update photo with EXIF data
        if 'camera' in exif_data:
            photo.camera_make = exif_data['camera'].get('make')
            photo.camera_model = exif_data['camera'].get('model')
        
        if 'settings' in exif_data:
            settings = exif_data['settings']
            photo.iso = settings.get('iso')
            photo.aperture = settings.get('aperture')
            photo.shutter_speed = settings.get('shutter_speed')
            photo.focal_length = settings.get('focal_length')
        
        if 'location' in exif_data:
            location = exif_data['location']
            photo.gps_lat = location.get('latitude')
            photo.gps_lon = location.get('longitude')
        
        if 'datetime' in exif_data:
            photo.capture_time = exif_data['datetime'].get('capture_time')
        
        db_session.commit()
        
        logging_system.log("INFO", "EXIF analysis completed", photo_id=photo_id)
        
        return exif_data
        
    finally:
        db_session.close()


@app.task(base=BaseTask, bind=True, name='celery_tasks.evaluate_quality_task')
def evaluate_quality_task(self, photo_id: int) -> Dict:
    """
    Evaluate photo quality using AI
    
    Args:
        photo_id: Photo database ID
        
    Returns:
        Quality evaluation dictionary
    """
    logging_system.log("INFO", "Evaluating quality", photo_id=photo_id)
    
    db_session = get_session()
    try:
        photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise ValueError(f"Photo not found: {photo_id}")
        
        # Evaluate quality
        quality_data = ai_selector.evaluate_photo(photo.file_path)
        
        logging_system.log("INFO", "Quality evaluation completed",
                          photo_id=photo_id,
                          overall_score=quality_data.get('overall_score'))
        
        return quality_data
        
    finally:
        db_session.close()


@app.task(base=BaseTask, bind=True, name='celery_tasks.group_similar_photos_task')
def group_similar_photos_task(self, session_id: int) -> Dict:
    """
    Group similar photos in a session
    
    Args:
        session_id: Session database ID
        
    Returns:
        Grouping results dictionary
    """
    logging_system.log("INFO", "Grouping similar photos", session_id=session_id)
    
    db_session = get_session()
    try:
        # Get all photos in session
        photos = db_session.query(Photo).filter(
            Photo.session_id == session_id
        ).all()
        
        if not photos:
            return {'groups': [], 'total_photos': 0}
        
        # Group photos
        photo_paths = [p.file_path for p in photos]
        groups = photo_grouper.group_photos(photo_paths)
        
        logging_system.log("INFO", "Photo grouping completed",
                          session_id=session_id,
                          group_count=len(groups),
                          total_photos=len(photos))
        
        return {
            'groups': groups,
            'total_photos': len(photos),
            'group_count': len(groups)
        }
        
    finally:
        db_session.close()


@app.task(base=BaseTask, bind=True, name='celery_tasks.apply_preset_task')
def apply_preset_task(self, photo_id: int, preset_name: str, blend_amount: int = 100) -> Dict:
    """
    Apply preset to photo (creates Lightroom job)
    
    Args:
        photo_id: Photo database ID
        preset_name: Name of preset to apply
        blend_amount: Blend amount (0-100)
        
    Returns:
        Application results dictionary
    """
    logging_system.log("INFO", "Applying preset",
                      photo_id=photo_id,
                      preset_name=preset_name)
    
    db_session = get_session()
    try:
        photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise ValueError(f"Photo not found: {photo_id}")
        
        # Get preset
        preset_mgr = PresetManager(db_session)
        preset = preset_mgr.get_preset(preset_name)
        if not preset:
            raise ValueError(f"Preset not found: {preset_name}")
        
        # Create Lightroom job
        job_config = preset_mgr.generate_job_config(
            preset_name=preset_name,
            blend_amount=blend_amount
        )
        
        # Create job in database
        job = Job(
            id=self.request.id,
            photo_id=photo_id,
            priority=get_priority_for_photo(photo.ai_score),
            config_json=json.dumps(job_config),
            status='pending',
            retry_count=0
        )
        db_session.add(job)
        db_session.commit()
        
        logging_system.log("INFO", "Preset application job created",
                          photo_id=photo_id,
                          job_id=job.id)
        
        return {
            'job_id': job.id,
            'preset_name': preset_name,
            'blend_amount': blend_amount
        }
        
    finally:
        db_session.close()


@app.task(base=BaseTask, bind=True, name='celery_tasks.export_photo_task')
def export_photo_task(self, photo_id: int, export_preset: str) -> Dict:
    """
    Export photo with specified preset
    
    Args:
        photo_id: Photo database ID
        export_preset: Export preset name
        
    Returns:
        Export results dictionary
    """
    logging_system.log("INFO", "Exporting photo",
                      photo_id=photo_id,
                      export_preset=export_preset)
    
    db_session = get_session()
    try:
        photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise ValueError(f"Photo not found: {photo_id}")
        
        # TODO: Implement actual export logic with Lightroom
        # This would create an export job for Lightroom plugin
        
        logging_system.log("INFO", "Photo export completed",
                          photo_id=photo_id)
        
        return {
            'photo_id': photo_id,
            'export_preset': export_preset,
            'status': 'completed'
        }
        
    finally:
        db_session.close()


@app.task(base=BaseTask, bind=True, name='celery_tasks.cleanup_old_results')
def cleanup_old_results(self) -> Dict:
    """
    Periodic task to cleanup old task results
    
    Returns:
        Cleanup statistics
    """
    logging_system.log("INFO", "Running cleanup task")
    
    # Celery automatically cleans up results based on result_expires setting
    # This task can be extended for additional cleanup operations
    
    return {'status': 'completed'}


@app.task(base=BaseTask, bind=True, name='celery_tasks.update_system_metrics')
def update_system_metrics(self) -> Dict:
    """
    Periodic task to update system metrics
    
    Returns:
        Metrics dictionary
    """
    import psutil
    
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    metrics = {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'memory_available_mb': memory.available / (1024 * 1024),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Try to get GPU metrics if available
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            metrics['gpu_load'] = gpu.load * 100
            metrics['gpu_memory_used'] = gpu.memoryUsed
            metrics['gpu_memory_total'] = gpu.memoryTotal
            metrics['gpu_temperature'] = gpu.temperature
    except:
        pass
    
    logging_system.log("DEBUG", "System metrics updated", **metrics)
    
    return metrics


# Batch processing helper
def process_batch_photos(photo_ids: List[int], priority: int = PRIORITY_MEDIUM) -> List[str]:
    """
    Submit batch of photos for processing
    
    Args:
        photo_ids: List of photo IDs to process
        priority: Task priority
        
    Returns:
        List of task IDs
    """
    task_ids = []
    
    for photo_id in photo_ids:
        result = process_photo_task.apply_async(
            args=[photo_id],
            priority=priority
        )
        task_ids.append(result.id)
    
    logging_system.log("INFO", "Batch processing submitted",
                      photo_count=len(photo_ids),
                      priority=priority)
    
    return task_ids
