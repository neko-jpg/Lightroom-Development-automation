"""
Auto Export Engine for Junmai AutoDev

This module provides automatic export functionality that triggers after photo approval.
Implements:
- Approval-triggered auto-export
- Multiple format simultaneous export
- Automatic filename generation
- Export queue management

Requirements: 6.1, 6.4
"""

import logging
import pathlib
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

from export_preset_manager import ExportPresetManager, ExportPreset
from models.database import get_session, Photo, Session as DBSession

logger = logging.getLogger(__name__)


@dataclass
class ExportJob:
    """
    Export Job Data Class
    
    Represents a single export job for a photo.
    """
    id: str
    photo_id: int
    preset_name: str
    status: str  # pending, processing, completed, failed
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExportJob':
        """Create from dictionary"""
        return cls(**data)


class AutoExportEngine:
    """
    Auto Export Engine for Junmai AutoDev System
    
    Manages automatic export of approved photos using configured presets.
    """
    
    def __init__(self, preset_manager: Optional[ExportPresetManager] = None):
        """
        Initialize AutoExportEngine
        
        Args:
            preset_manager: ExportPresetManager instance. If None, creates new one.
        """
        self.preset_manager = preset_manager or ExportPresetManager()
        self.export_queue: List[ExportJob] = []
        self.processing_jobs: Dict[str, ExportJob] = {}
        
        logger.info("AutoExportEngine initialized")
    
    def trigger_auto_export(self, photo_id: int, db_session=None) -> List[ExportJob]:
        """
        Trigger automatic export for an approved photo
        
        This is called when a photo is approved and auto-export is enabled.
        Creates export jobs for all enabled presets.
        
        Args:
            photo_id: ID of the approved photo
            db_session: Database session (optional, creates new if None)
            
        Returns:
            List of created ExportJob objects
            
        Raises:
            ValueError: If photo not found or not approved
        """
        logger.info(f"Triggering auto-export for photo_id={photo_id}")
        
        # Get database session
        close_session = False
        if db_session is None:
            db_session = get_session()
            close_session = True
        
        try:
            # Get photo from database
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            
            if not photo:
                raise ValueError(f"Photo not found: photo_id={photo_id}")
            
            if not photo.approved:
                raise ValueError(f"Photo not approved: photo_id={photo_id}")
            
            # Get enabled export presets
            enabled_presets = self.preset_manager.get_enabled_presets()
            
            if not enabled_presets:
                logger.warning("No enabled export presets found, skipping auto-export")
                return []
            
            # Create export jobs for each enabled preset
            export_jobs = []
            for preset in enabled_presets:
                job = self._create_export_job(photo, preset)
                export_jobs.append(job)
                self.export_queue.append(job)
                
                logger.info(f"Created export job: job_id={job.id}, preset={preset.name}")
            
            logger.info(f"Created {len(export_jobs)} export jobs for photo_id={photo_id}")
            return export_jobs
            
        finally:
            if close_session:
                db_session.close()
    
    def _create_export_job(self, photo: Photo, preset: ExportPreset) -> ExportJob:
        """
        Create an export job for a photo and preset
        
        Args:
            photo: Photo object
            preset: ExportPreset object
            
        Returns:
            ExportJob object
        """
        job_id = uuid.uuid4().hex
        
        job = ExportJob(
            id=job_id,
            photo_id=photo.id,
            preset_name=preset.name,
            status='pending',
            created_at=datetime.now().isoformat()
        )
        
        return job
    
    def export_multiple_formats(self, photo_id: int, preset_names: List[str], 
                                db_session=None) -> List[ExportJob]:
        """
        Export a photo in multiple formats simultaneously
        
        Args:
            photo_id: ID of the photo to export
            preset_names: List of preset names to use for export
            db_session: Database session (optional)
            
        Returns:
            List of created ExportJob objects
            
        Raises:
            ValueError: If photo not found or preset not found
        """
        logger.info(f"Exporting photo_id={photo_id} in multiple formats: {preset_names}")
        
        # Get database session
        close_session = False
        if db_session is None:
            db_session = get_session()
            close_session = True
        
        try:
            # Get photo from database
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            
            if not photo:
                raise ValueError(f"Photo not found: photo_id={photo_id}")
            
            # Create export jobs for each preset
            export_jobs = []
            for preset_name in preset_names:
                preset = self.preset_manager.get_preset(preset_name)
                
                if not preset:
                    logger.warning(f"Preset not found: {preset_name}, skipping")
                    continue
                
                job = self._create_export_job(photo, preset)
                export_jobs.append(job)
                self.export_queue.append(job)
                
                logger.info(f"Created export job: job_id={job.id}, preset={preset_name}")
            
            logger.info(f"Created {len(export_jobs)} export jobs for photo_id={photo_id}")
            return export_jobs
            
        finally:
            if close_session:
                db_session.close()
    
    def generate_filename(self, photo: Photo, preset: ExportPreset, 
                         sequence_number: Optional[int] = None) -> str:
        """
        Generate automatic filename based on template
        
        Supports template variables:
        - {date}: Capture date (YYYY-MM-DD)
        - {time}: Capture time (HHMMSS)
        - {sequence}: Sequence number
        - {original}: Original filename (without extension)
        - {year}: Year (YYYY)
        - {month}: Month (MM)
        - {day}: Day (DD)
        - {preset}: Preset name
        
        Args:
            photo: Photo object
            preset: ExportPreset object
            sequence_number: Optional sequence number (auto-generated if None)
            
        Returns:
            Generated filename (without extension)
        """
        template = preset.filename_template
        
        # Get capture time or use import time
        capture_time = photo.capture_time or photo.import_time
        
        # Extract original filename without extension
        original_name = pathlib.Path(photo.file_name).stem
        
        # Generate sequence number if not provided
        if sequence_number is None:
            sequence_number = preset.sequence_start
        
        # Build replacement dictionary
        replacements = {
            'date': capture_time.strftime('%Y-%m-%d'),
            'time': capture_time.strftime('%H%M%S'),
            'sequence': f"{sequence_number:04d}",
            'original': original_name,
            'year': capture_time.strftime('%Y'),
            'month': capture_time.strftime('%m'),
            'day': capture_time.strftime('%d'),
            'preset': preset.name
        }
        
        # Replace template variables
        filename = template
        for key, value in replacements.items():
            filename = filename.replace(f"{{{key}}}", value)
        
        logger.debug(f"Generated filename: {filename} from template: {template}")
        
        return filename
    
    def get_export_path(self, photo: Photo, preset: ExportPreset, 
                       sequence_number: Optional[int] = None) -> pathlib.Path:
        """
        Get full export path for a photo
        
        Args:
            photo: Photo object
            preset: ExportPreset object
            sequence_number: Optional sequence number
            
        Returns:
            Full path to export file
        """
        # Generate filename
        filename = self.generate_filename(photo, preset, sequence_number)
        
        # Get file extension based on format
        extension_map = {
            'JPEG': '.jpg',
            'PNG': '.png',
            'TIFF': '.tif',
            'DNG': '.dng'
        }
        extension = extension_map.get(preset.format, '.jpg')
        
        # Build full path
        destination = pathlib.Path(preset.destination)
        full_path = destination / f"{filename}{extension}"
        
        # Ensure destination directory exists
        destination.mkdir(parents=True, exist_ok=True)
        
        # Handle filename conflicts
        if full_path.exists():
            counter = 1
            while full_path.exists():
                conflict_filename = f"{filename}_{counter}{extension}"
                full_path = destination / conflict_filename
                counter += 1
            
            logger.warning(f"Filename conflict resolved: {full_path}")
        
        return full_path
    
    def process_export_job(self, job_id: str, db_session=None) -> Tuple[bool, Optional[str]]:
        """
        Process a single export job
        
        This method prepares the export configuration and returns it for
        Lightroom to execute. The actual export is done by Lightroom.
        
        Args:
            job_id: ID of the export job
            db_session: Database session (optional)
            
        Returns:
            Tuple of (success, error_message)
        """
        logger.info(f"Processing export job: job_id={job_id}")
        
        # Find job in queue
        job = None
        for j in self.export_queue:
            if j.id == job_id:
                job = j
                break
        
        if not job:
            error_msg = f"Export job not found: {job_id}"
            logger.error(error_msg)
            return False, error_msg
        
        # Get database session
        close_session = False
        if db_session is None:
            db_session = get_session()
            close_session = True
        
        try:
            # Update job status
            job.status = 'processing'
            job.started_at = datetime.now().isoformat()
            self.processing_jobs[job_id] = job
            self.export_queue.remove(job)
            
            # Get photo and preset
            photo = db_session.query(Photo).filter(Photo.id == job.photo_id).first()
            if not photo:
                raise ValueError(f"Photo not found: photo_id={job.photo_id}")
            
            preset = self.preset_manager.get_preset(job.preset_name)
            if not preset:
                raise ValueError(f"Preset not found: {job.preset_name}")
            
            # Generate export path
            export_path = self.get_export_path(photo, preset)
            job.output_path = str(export_path)
            
            logger.info(f"Export job prepared: job_id={job_id}, output={export_path}")
            
            return True, None
            
        except Exception as e:
            error_msg = f"Failed to process export job: {e}"
            logger.error(error_msg, exc_info=True)
            
            job.status = 'failed'
            job.error_message = error_msg
            job.completed_at = datetime.now().isoformat()
            
            if job_id in self.processing_jobs:
                del self.processing_jobs[job_id]
            
            return False, error_msg
            
        finally:
            if close_session:
                db_session.close()
    
    def complete_export_job(self, job_id: str, success: bool, 
                           error_message: Optional[str] = None) -> bool:
        """
        Mark an export job as completed
        
        Args:
            job_id: ID of the export job
            success: Whether the export was successful
            error_message: Optional error message if failed
            
        Returns:
            True if job was found and updated, False otherwise
        """
        logger.info(f"Completing export job: job_id={job_id}, success={success}")
        
        if job_id not in self.processing_jobs:
            logger.warning(f"Export job not found in processing: {job_id}")
            return False
        
        job = self.processing_jobs[job_id]
        job.status = 'completed' if success else 'failed'
        job.completed_at = datetime.now().isoformat()
        
        if error_message:
            job.error_message = error_message
        
        # Remove from processing
        del self.processing_jobs[job_id]
        
        logger.info(f"Export job completed: job_id={job_id}, status={job.status}")
        
        return True
    
    def get_next_export_job(self) -> Optional[ExportJob]:
        """
        Get the next export job from the queue
        
        Returns:
            Next ExportJob or None if queue is empty
        """
        if not self.export_queue:
            return None
        
        # Return oldest job (FIFO)
        return self.export_queue[0]
    
    def get_export_queue_status(self) -> Dict[str, Any]:
        """
        Get export queue status
        
        Returns:
            Dictionary with queue statistics
        """
        return {
            'pending_count': len(self.export_queue),
            'processing_count': len(self.processing_jobs),
            'pending_jobs': [job.to_dict() for job in self.export_queue],
            'processing_jobs': [job.to_dict() for job in self.processing_jobs.values()]
        }
    
    def get_export_job(self, job_id: str) -> Optional[ExportJob]:
        """
        Get an export job by ID
        
        Args:
            job_id: ID of the export job
            
        Returns:
            ExportJob or None if not found
        """
        # Check processing jobs
        if job_id in self.processing_jobs:
            return self.processing_jobs[job_id]
        
        # Check queue
        for job in self.export_queue:
            if job.id == job_id:
                return job
        
        return None
    
    def cancel_export_job(self, job_id: str) -> bool:
        """
        Cancel an export job
        
        Args:
            job_id: ID of the export job to cancel
            
        Returns:
            True if job was cancelled, False if not found
        """
        logger.info(f"Cancelling export job: job_id={job_id}")
        
        # Check queue
        for job in self.export_queue:
            if job.id == job_id:
                self.export_queue.remove(job)
                logger.info(f"Export job cancelled from queue: {job_id}")
                return True
        
        # Check processing (cannot cancel processing jobs)
        if job_id in self.processing_jobs:
            logger.warning(f"Cannot cancel processing job: {job_id}")
            return False
        
        logger.warning(f"Export job not found: {job_id}")
        return False
    
    def clear_export_queue(self) -> int:
        """
        Clear all pending export jobs
        
        Returns:
            Number of jobs cleared
        """
        count = len(self.export_queue)
        self.export_queue.clear()
        
        logger.info(f"Cleared {count} export jobs from queue")
        
        return count
    
    def get_export_config_for_lightroom(self, job_id: str, db_session=None) -> Optional[Dict[str, Any]]:
        """
        Get export configuration for Lightroom
        
        Generates a configuration that Lightroom can use to export the photo.
        
        Args:
            job_id: ID of the export job
            db_session: Database session (optional)
            
        Returns:
            Export configuration dictionary or None if job not found
        """
        job = self.get_export_job(job_id)
        
        if not job:
            logger.error(f"Export job not found: {job_id}")
            return None
        
        # Get database session
        close_session = False
        if db_session is None:
            db_session = get_session()
            close_session = True
        
        try:
            # Get photo and preset
            photo = db_session.query(Photo).filter(Photo.id == job.photo_id).first()
            if not photo:
                logger.error(f"Photo not found: photo_id={job.photo_id}")
                return None
            
            preset = self.preset_manager.get_preset(job.preset_name)
            if not preset:
                logger.error(f"Preset not found: {job.preset_name}")
                return None
            
            # Generate export path
            export_path = self.get_export_path(photo, preset)
            
            # Build Lightroom export configuration
            config = {
                'job_id': job_id,
                'photo_id': job.photo_id,
                'photo_path': photo.file_path,
                'lr_catalog_id': photo.lr_catalog_id,
                'export_path': str(export_path),
                'format': preset.format,
                'quality': preset.quality,
                'max_dimension': preset.max_dimension,
                'color_space': preset.color_space,
                'resize_mode': preset.resize_mode,
                'sharpen_for_screen': preset.sharpen_for_screen,
                'sharpen_amount': preset.sharpen_amount,
                'watermark_enabled': preset.watermark_enabled,
                'watermark_text': preset.watermark_text,
                'metadata_include': preset.metadata_include,
                'metadata_copyright': preset.metadata_copyright
            }
            
            logger.info(f"Generated export config for Lightroom: job_id={job_id}")
            
            return config
            
        finally:
            if close_session:
                db_session.close()


# Convenience function for quick access
def get_auto_export_engine(preset_manager: Optional[ExportPresetManager] = None) -> AutoExportEngine:
    """
    Get an AutoExportEngine instance
    
    Args:
        preset_manager: Optional ExportPresetManager instance
        
    Returns:
        AutoExportEngine instance
    """
    return AutoExportEngine(preset_manager)


if __name__ == '__main__':
    # Setup logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=== Testing Auto Export Engine ===\n")
    
    # Note: This is a basic test. Full testing requires database setup.
    print("✓ Auto Export Engine module loaded successfully")
    print("✓ For full testing, use test_auto_export_engine.py with database")
