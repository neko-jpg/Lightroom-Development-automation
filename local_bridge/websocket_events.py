"""
WebSocket Event Broadcasting Module
WebSocketイベント配信モジュール

This module provides convenience functions for broadcasting real-time events
to connected WebSocket clients. It integrates with the WebSocket server to
send standardized event messages.

Requirements: 4.5, 7.2
"""

from datetime import datetime
from typing import Dict, Optional, Any
from websocket_server import get_websocket_server, EventType
from logging_system import get_logging_system

logging_system = get_logging_system()


def broadcast_event(event_type: str, data: Dict[str, Any], channel: Optional[str] = None):
    """
    Broadcast a generic event to WebSocket clients
    
    Args:
        event_type: Type of event (from EventType class)
        data: Event data dictionary
        channel: Optional channel for filtered broadcast
    """
    ws_server = get_websocket_server()
    if not ws_server:
        logging_system.log("WARNING", "WebSocket server not available for event broadcast",
                          event_type=event_type)
        return
    
    message = {
        'type': event_type,
        'timestamp': datetime.now().isoformat(),
        **data
    }
    
    ws_server.broadcast(message, channel=channel)
    logging_system.log("DEBUG", "Broadcasted WebSocket event", 
                      event_type=event_type, channel=channel)


# ============================================================================
# JOB EVENTS
# ============================================================================

def broadcast_job_created(job_id: str, photo_id: int, priority: int):
    """
    Broadcast job created event
    
    Args:
        job_id: Job identifier
        photo_id: Photo ID
        priority: Job priority
    """
    broadcast_event(EventType.JOB_CREATED, {
        'job_id': job_id,
        'photo_id': photo_id,
        'priority': priority
    }, channel='jobs')


def broadcast_job_started(job_id: str, photo_id: int):
    """
    Broadcast job started event
    
    Args:
        job_id: Job identifier
        photo_id: Photo ID
    """
    broadcast_event(EventType.JOB_STARTED, {
        'job_id': job_id,
        'photo_id': photo_id
    }, channel='jobs')


def broadcast_job_progress(job_id: str, stage: str, progress: float, message: str = ""):
    """
    Broadcast job progress update
    
    Args:
        job_id: Job identifier
        stage: Current processing stage
        progress: Progress percentage (0-100)
        message: Optional progress message
    """
    broadcast_event(EventType.JOB_PROGRESS, {
        'job_id': job_id,
        'stage': stage,
        'progress': progress,
        'message': message
    }, channel='jobs')


def broadcast_job_completed(job_id: str, photo_id: int, result: Dict[str, Any]):
    """
    Broadcast job completed event
    
    Args:
        job_id: Job identifier
        photo_id: Photo ID
        result: Job result data
    """
    broadcast_event(EventType.JOB_COMPLETED, {
        'job_id': job_id,
        'photo_id': photo_id,
        'result': result
    }, channel='jobs')


def broadcast_job_failed(job_id: str, photo_id: int, error_message: str, error_details: Optional[Dict] = None):
    """
    Broadcast job failed event
    
    Args:
        job_id: Job identifier
        photo_id: Photo ID
        error_message: Error message
        error_details: Optional detailed error information
    """
    broadcast_event(EventType.JOB_FAILED, {
        'job_id': job_id,
        'photo_id': photo_id,
        'error_message': error_message,
        'error_details': error_details or {}
    }, channel='jobs')


# ============================================================================
# PHOTO EVENTS
# ============================================================================

def broadcast_photo_imported(photo_id: int, session_id: int, file_name: str, file_path: str):
    """
    Broadcast photo imported event
    
    Args:
        photo_id: Photo ID
        session_id: Session ID
        file_name: File name
        file_path: File path
    """
    broadcast_event(EventType.PHOTO_IMPORTED, {
        'photo_id': photo_id,
        'session_id': session_id,
        'file_name': file_name,
        'file_path': file_path
    }, channel='photos')


def broadcast_photo_analyzed(photo_id: int, ai_score: float, analysis_results: Dict[str, Any]):
    """
    Broadcast photo analyzed event
    
    Args:
        photo_id: Photo ID
        ai_score: AI evaluation score
        analysis_results: Analysis results including focus, exposure, composition scores
    """
    broadcast_event(EventType.PHOTO_ANALYZED, {
        'photo_id': photo_id,
        'ai_score': ai_score,
        'analysis_results': analysis_results
    }, channel='photos')


def broadcast_photo_selected(photo_id: int, context_tag: str, selected_preset: str):
    """
    Broadcast photo selected for processing event
    
    Args:
        photo_id: Photo ID
        context_tag: Context tag
        selected_preset: Selected preset name
    """
    broadcast_event(EventType.PHOTO_SELECTED, {
        'photo_id': photo_id,
        'context_tag': context_tag,
        'selected_preset': selected_preset
    }, channel='photos')


def broadcast_photo_approved(photo_id: int, session_id: int):
    """
    Broadcast photo approved event
    
    Args:
        photo_id: Photo ID
        session_id: Session ID
    """
    broadcast_event(EventType.PHOTO_APPROVED, {
        'photo_id': photo_id,
        'session_id': session_id
    }, channel='photos')


def broadcast_photo_rejected(photo_id: int, session_id: int, reason: str):
    """
    Broadcast photo rejected event
    
    Args:
        photo_id: Photo ID
        session_id: Session ID
        reason: Rejection reason
    """
    broadcast_event(EventType.PHOTO_REJECTED, {
        'photo_id': photo_id,
        'session_id': session_id,
        'reason': reason
    }, channel='photos')


# ============================================================================
# SESSION EVENTS
# ============================================================================

def broadcast_session_created(session_id: int, session_name: str, import_folder: str):
    """
    Broadcast session created event
    
    Args:
        session_id: Session ID
        session_name: Session name
        import_folder: Import folder path
    """
    broadcast_event(EventType.SESSION_CREATED, {
        'session_id': session_id,
        'session_name': session_name,
        'import_folder': import_folder
    }, channel='sessions')


def broadcast_session_updated(session_id: int, total_photos: int, processed_photos: int, status: str):
    """
    Broadcast session updated event
    
    Args:
        session_id: Session ID
        total_photos: Total number of photos
        processed_photos: Number of processed photos
        status: Session status
    """
    progress_percent = (processed_photos / total_photos * 100) if total_photos > 0 else 0
    
    broadcast_event(EventType.SESSION_UPDATED, {
        'session_id': session_id,
        'total_photos': total_photos,
        'processed_photos': processed_photos,
        'progress_percent': round(progress_percent, 2),
        'status': status
    }, channel='sessions')


def broadcast_session_completed(session_id: int, session_name: str, total_photos: int, approved_photos: int):
    """
    Broadcast session completed event
    
    Args:
        session_id: Session ID
        session_name: Session name
        total_photos: Total number of photos
        approved_photos: Number of approved photos
    """
    broadcast_event(EventType.SESSION_COMPLETED, {
        'session_id': session_id,
        'session_name': session_name,
        'total_photos': total_photos,
        'approved_photos': approved_photos,
        'approval_rate': round((approved_photos / total_photos * 100) if total_photos > 0 else 0, 2)
    }, channel='sessions')


# ============================================================================
# SYSTEM EVENTS
# ============================================================================

def broadcast_system_status(status: str, details: Dict[str, Any]):
    """
    Broadcast system status update
    
    Args:
        status: System status (running, paused, error, etc.)
        details: Status details
    """
    broadcast_event(EventType.SYSTEM_STATUS, {
        'status': status,
        'details': details
    }, channel='system')


def broadcast_resource_warning(resource_type: str, current_value: float, threshold: float, message: str):
    """
    Broadcast resource warning event
    
    Args:
        resource_type: Type of resource (cpu, memory, gpu, disk)
        current_value: Current resource value
        threshold: Warning threshold
        message: Warning message
    """
    broadcast_event(EventType.RESOURCE_WARNING, {
        'resource_type': resource_type,
        'current_value': current_value,
        'threshold': threshold,
        'message': message
    }, channel='system')


def broadcast_error_occurred(error_type: str, error_message: str, error_details: Optional[Dict] = None, 
                            job_id: Optional[str] = None, photo_id: Optional[int] = None):
    """
    Broadcast error occurred event
    
    Args:
        error_type: Type of error
        error_message: Error message
        error_details: Optional detailed error information
        job_id: Optional job ID if error is job-related
        photo_id: Optional photo ID if error is photo-related
    """
    data = {
        'error_type': error_type,
        'error_message': error_message,
        'error_details': error_details or {}
    }
    
    if job_id:
        data['job_id'] = job_id
    if photo_id:
        data['photo_id'] = photo_id
    
    broadcast_event(EventType.ERROR_OCCURRED, data, channel='system')


# ============================================================================
# QUEUE EVENTS
# ============================================================================

def broadcast_queue_status(pending_count: int, processing_count: int, completed_count: int, failed_count: int):
    """
    Broadcast queue status update
    
    Args:
        pending_count: Number of pending jobs
        processing_count: Number of processing jobs
        completed_count: Number of completed jobs
        failed_count: Number of failed jobs
    """
    broadcast_event(EventType.QUEUE_STATUS, {
        'pending': pending_count,
        'processing': processing_count,
        'completed': completed_count,
        'failed': failed_count,
        'total': pending_count + processing_count + completed_count + failed_count
    }, channel='queue')


def broadcast_priority_changed(job_id: str, old_priority: int, new_priority: int, reason: str):
    """
    Broadcast priority changed event
    
    Args:
        job_id: Job identifier
        old_priority: Previous priority
        new_priority: New priority
        reason: Reason for priority change
    """
    broadcast_event(EventType.PRIORITY_CHANGED, {
        'job_id': job_id,
        'old_priority': old_priority,
        'new_priority': new_priority,
        'reason': reason
    }, channel='queue')


# ============================================================================
# APPROVAL QUEUE EVENTS
# ============================================================================

def broadcast_approval_queue_updated(queue_count: int, session_id: Optional[int] = None):
    """
    Broadcast approval queue updated event
    
    Args:
        queue_count: Number of photos in approval queue
        session_id: Optional session ID if update is session-specific
    """
    data = {
        'queue_count': queue_count
    }
    
    if session_id:
        data['session_id'] = session_id
    
    broadcast_event('approval_queue_updated', data, channel='approval')


# ============================================================================
# EXPORT EVENTS
# ============================================================================

def broadcast_export_started(photo_id: int, preset_name: str, destination: str):
    """
    Broadcast export started event
    
    Args:
        photo_id: Photo ID
        preset_name: Export preset name
        destination: Export destination path
    """
    broadcast_event('export_started', {
        'photo_id': photo_id,
        'preset_name': preset_name,
        'destination': destination
    }, channel='export')


def broadcast_export_completed(photo_id: int, preset_name: str, output_path: str, file_size: int):
    """
    Broadcast export completed event
    
    Args:
        photo_id: Photo ID
        preset_name: Export preset name
        output_path: Output file path
        file_size: Output file size in bytes
    """
    broadcast_event('export_completed', {
        'photo_id': photo_id,
        'preset_name': preset_name,
        'output_path': output_path,
        'file_size': file_size
    }, channel='export')


def broadcast_export_failed(photo_id: int, preset_name: str, error_message: str):
    """
    Broadcast export failed event
    
    Args:
        photo_id: Photo ID
        preset_name: Export preset name
        error_message: Error message
    """
    broadcast_event('export_failed', {
        'photo_id': photo_id,
        'preset_name': preset_name,
        'error_message': error_message
    }, channel='export')
