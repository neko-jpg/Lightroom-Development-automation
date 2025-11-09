"""
Extended API Endpoints for Junmai AutoDev
拡張APIエンドポイント

This module provides comprehensive REST API endpoints for:
- Session management
- Photo management
- Job management
- Approval queue
- Statistics
- System management

Requirements: 9.1
"""

from flask import Blueprint, jsonify, request, send_file
from datetime import datetime, timedelta
from models.database import get_session, Session, Photo, Job, Statistic, Preset, LearningData
from sqlalchemy import func, desc, and_, or_
from logging_system import get_logging_system
import pathlib
import io
from PIL import Image
import websocket_events

api_bp = Blueprint('api', __name__, url_prefix='/api')
logging_system = get_logging_system()


# ============================================================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================================================

@api_bp.route("/sessions", methods=["GET"])
def get_sessions():
    """
    Get list of sessions with filtering and pagination
    
    Query parameters:
    - status: Filter by status (optional)
    - limit: Maximum number of sessions (default: 50)
    - offset: Pagination offset (default: 0)
    - active_only: Return only active sessions (default: false)
    - sort: Sort field (created_at, name, total_photos) (default: created_at)
    - order: Sort order (asc, desc) (default: desc)
    
    Returns:
        List of sessions with metadata
    """
    try:
        status_filter = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        sort_field = request.args.get('sort', 'created_at')
        sort_order = request.args.get('order', 'desc')
        
        db_session = get_session()
        try:
            query = db_session.query(Session)
            
            if status_filter:
                query = query.filter(Session.status == status_filter)
            
            if active_only:
                query = query.filter(Session.status != 'completed')
            
            # Apply sorting
            sort_column = getattr(Session, sort_field, Session.created_at)
            if sort_order == 'asc':
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination
            sessions = query.offset(offset).limit(limit).all()
            
            sessions_data = []
            for session in sessions:
                sessions_data.append({
                    'id': session.id,
                    'name': session.name,
                    'created_at': session.created_at.isoformat() if session.created_at else None,
                    'import_folder': session.import_folder,
                    'total_photos': session.total_photos,
                    'processed_photos': session.processed_photos,
                    'status': session.status,
                    'progress_percent': (session.processed_photos / session.total_photos * 100) if session.total_photos > 0 else 0
                })
            
            logging_system.log("INFO", "Retrieved sessions", count=len(sessions_data), total=total_count)
            
            return jsonify({
                'sessions': sessions_data,
                'count': len(sessions_data),
                'total': total_count,
                'offset': offset,
                'limit': limit
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get sessions", exception=e)
        return jsonify({"error": f"Failed to get sessions: {e}"}), 500


@api_bp.route("/sessions/<int:session_id>", methods=["GET"])
def get_session_detail(session_id: int):
    """
    Get detailed information about a specific session
    
    Path parameters:
    - session_id: Session ID
    
    Returns:
        Detailed session information with photo statistics
    """
    try:
        db_session = get_session()
        try:
            session = db_session.query(Session).filter(Session.id == session_id).first()
            
            if not session:
                return jsonify({"error": "Session not found"}), 404
            
            # Get photo statistics for this session
            photo_stats = db_session.query(
                Photo.status,
                func.count(Photo.id)
            ).filter(
                Photo.session_id == session_id
            ).group_by(Photo.status).all()
            
            # Get AI score distribution
            score_distribution = db_session.query(
                func.round(Photo.ai_score).label('score'),
                func.count(Photo.id)
            ).filter(
                Photo.session_id == session_id,
                Photo.ai_score.isnot(None)
            ).group_by('score').all()
            
            session_data = {
                'id': session.id,
                'name': session.name,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'import_folder': session.import_folder,
                'total_photos': session.total_photos,
                'processed_photos': session.processed_photos,
                'status': session.status,
                'progress_percent': (session.processed_photos / session.total_photos * 100) if session.total_photos > 0 else 0,
                'photo_stats': {status: count for status, count in photo_stats},
                'score_distribution': {int(score): count for score, count in score_distribution if score}
            }
            
            return jsonify(session_data), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get session detail", exception=e)
        return jsonify({"error": f"Failed to get session detail: {e}"}), 500


@api_bp.route("/sessions", methods=["POST"])
def create_session():
    """
    Create a new session
    
    Request body:
    - name: Session name (required)
    - import_folder: Import folder path (required)
    
    Returns:
        Created session information
    """
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'import_folder' not in data:
            return jsonify({"error": "name and import_folder are required"}), 400
        
        db_session = get_session()
        try:
            # Check if session with same name exists
            existing = db_session.query(Session).filter(Session.name == data['name']).first()
            if existing:
                return jsonify({"error": "Session with this name already exists"}), 409
            
            # Create new session
            new_session = Session(
                name=data['name'],
                import_folder=data['import_folder'],
                status='importing'
            )
            
            db_session.add(new_session)
            db_session.commit()
            
            logging_system.log("INFO", "Session created", session_id=new_session.id, name=new_session.name)
            
            # Broadcast session created event
            websocket_events.broadcast_session_created(
                session_id=new_session.id,
                session_name=new_session.name,
                import_folder=new_session.import_folder
            )
            
            return jsonify({
                'id': new_session.id,
                'name': new_session.name,
                'import_folder': new_session.import_folder,
                'status': new_session.status,
                'created_at': new_session.created_at.isoformat() if new_session.created_at else None
            }), 201
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to create session", exception=e)
        return jsonify({"error": f"Failed to create session: {e}"}), 500


@api_bp.route("/sessions/<int:session_id>", methods=["PATCH"])
def update_session(session_id: int):
    """
    Update session information
    
    Path parameters:
    - session_id: Session ID
    
    Request body:
    - name: New session name (optional)
    - status: New status (optional)
    
    Returns:
        Updated session information
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No update data provided"}), 400
        
        db_session = get_session()
        try:
            session = db_session.query(Session).filter(Session.id == session_id).first()
            
            if not session:
                return jsonify({"error": "Session not found"}), 404
            
            # Update fields
            if 'name' in data:
                session.name = data['name']
            if 'status' in data:
                session.status = data['status']
            
            db_session.commit()
            
            logging_system.log("INFO", "Session updated", session_id=session_id)
            
            # Broadcast session updated event
            websocket_events.broadcast_session_updated(
                session_id=session.id,
                total_photos=session.total_photos,
                processed_photos=session.processed_photos,
                status=session.status
            )
            
            return jsonify({
                'id': session.id,
                'name': session.name,
                'status': session.status,
                'import_folder': session.import_folder
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to update session", exception=e)
        return jsonify({"error": f"Failed to update session: {e}"}), 500


@api_bp.route("/sessions/<int:session_id>", methods=["DELETE"])
def delete_session(session_id: int):
    """
    Delete a session and all associated data
    
    Path parameters:
    - session_id: Session ID
    
    Returns:
        Success message
    """
    try:
        db_session = get_session()
        try:
            session = db_session.query(Session).filter(Session.id == session_id).first()
            
            if not session:
                return jsonify({"error": "Session not found"}), 404
            
            # Delete session (cascade will delete associated photos, jobs, etc.)
            db_session.delete(session)
            db_session.commit()
            
            logging_system.log("INFO", "Session deleted", session_id=session_id)
            
            return jsonify({
                "message": "Session deleted successfully",
                "session_id": session_id
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to delete session", exception=e)
        return jsonify({"error": f"Failed to delete session: {e}"}), 500


# ============================================================================
# PHOTO MANAGEMENT ENDPOINTS
# ============================================================================

@api_bp.route("/photos", methods=["GET"])
def get_photos():
    """
    Get list of photos with filtering and pagination
    
    Query parameters:
    - session_id: Filter by session ID (optional)
    - status: Filter by status (optional)
    - min_score: Minimum AI score (optional)
    - approved: Filter by approval status (true/false) (optional)
    - limit: Maximum number of photos (default: 100)
    - offset: Pagination offset (default: 0)
    - sort: Sort field (import_time, ai_score, file_name) (default: import_time)
    - order: Sort order (asc, desc) (default: desc)
    
    Returns:
        List of photos with metadata
    """
    try:
        session_id = request.args.get('session_id', type=int)
        status_filter = request.args.get('status')
        min_score = request.args.get('min_score', type=float)
        approved_filter = request.args.get('approved')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        sort_field = request.args.get('sort', 'import_time')
        sort_order = request.args.get('order', 'desc')
        
        db_session = get_session()
        try:
            query = db_session.query(Photo)
            
            # Apply filters
            if session_id:
                query = query.filter(Photo.session_id == session_id)
            if status_filter:
                query = query.filter(Photo.status == status_filter)
            if min_score:
                query = query.filter(Photo.ai_score >= min_score)
            if approved_filter:
                approved_bool = approved_filter.lower() == 'true'
                query = query.filter(Photo.approved == approved_bool)
            
            # Apply sorting
            sort_column = getattr(Photo, sort_field, Photo.import_time)
            if sort_order == 'asc':
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination
            photos = query.offset(offset).limit(limit).all()
            
            photos_data = [photo.to_dict() for photo in photos]
            
            logging_system.log("INFO", "Retrieved photos", count=len(photos_data), total=total_count)
            
            return jsonify({
                'photos': photos_data,
                'count': len(photos_data),
                'total': total_count,
                'offset': offset,
                'limit': limit
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get photos", exception=e)
        return jsonify({"error": f"Failed to get photos: {e}"}), 500


@api_bp.route("/photos/<int:photo_id>", methods=["GET"])
def get_photo_detail(photo_id: int):
    """
    Get detailed information about a specific photo
    
    Path parameters:
    - photo_id: Photo ID
    
    Returns:
        Detailed photo information
    """
    try:
        db_session = get_session()
        try:
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            
            if not photo:
                return jsonify({"error": "Photo not found"}), 404
            
            photo_data = photo.to_dict()
            
            # Add additional information
            if photo.session_id:
                session = db_session.query(Session).filter(Session.id == photo.session_id).first()
                if session:
                    photo_data['session_name'] = session.name
            
            return jsonify(photo_data), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get photo detail", exception=e)
        return jsonify({"error": f"Failed to get photo detail: {e}"}), 500


@api_bp.route("/photos/<int:photo_id>", methods=["PATCH"])
def update_photo(photo_id: int):
    """
    Update photo information
    
    Path parameters:
    - photo_id: Photo ID
    
    Request body:
    - status: New status (optional)
    - approved: Approval status (optional)
    - rejection_reason: Rejection reason (optional)
    - context_tag: Context tag (optional)
    - selected_preset: Selected preset (optional)
    
    Returns:
        Updated photo information
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No update data provided"}), 400
        
        db_session = get_session()
        try:
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            
            if not photo:
                return jsonify({"error": "Photo not found"}), 404
            
            # Update fields
            if 'status' in data:
                photo.status = data['status']
            if 'approved' in data:
                photo.approved = data['approved']
                if data['approved']:
                    photo.approved_at = datetime.utcnow()
            if 'rejection_reason' in data:
                photo.rejection_reason = data['rejection_reason']
            if 'context_tag' in data:
                photo.context_tag = data['context_tag']
            if 'selected_preset' in data:
                photo.selected_preset = data['selected_preset']
            
            db_session.commit()
            
            logging_system.log("INFO", "Photo updated", photo_id=photo_id)
            
            return jsonify(photo.to_dict()), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to update photo", exception=e)
        return jsonify({"error": f"Failed to update photo: {e}"}), 500


@api_bp.route("/photos/<int:photo_id>/thumbnail", methods=["GET"])
def get_photo_thumbnail(photo_id: int):
    """
    Get thumbnail for a photo
    
    Path parameters:
    - photo_id: Photo ID
    
    Query parameters:
    - size: Thumbnail size (small=200, medium=400, large=800) (default: medium)
    
    Returns:
        JPEG thumbnail image
    """
    try:
        size_param = request.args.get('size', 'medium')
        size_map = {'small': 200, 'medium': 400, 'large': 800}
        max_size = size_map.get(size_param, 400)
        
        db_session = get_session()
        try:
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            
            if not photo:
                return jsonify({"error": "Photo not found"}), 404
            
            file_path = pathlib.Path(photo.file_path)
            
            if not file_path.exists():
                return jsonify({"error": "Photo file not found"}), 404
            
            # Generate thumbnail
            try:
                img = Image.open(file_path)
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Save to bytes buffer
                img_io = io.BytesIO()
                img.save(img_io, 'JPEG', quality=85)
                img_io.seek(0)
                
                return send_file(img_io, mimetype='image/jpeg')
                
            except Exception as img_error:
                logging_system.log_error("Failed to generate thumbnail", exception=img_error)
                return jsonify({"error": "Failed to generate thumbnail"}), 500
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get photo thumbnail", exception=e)
        return jsonify({"error": f"Failed to get thumbnail: {e}"}), 500


# ============================================================================
# JOB MANAGEMENT ENDPOINTS
# ============================================================================

@api_bp.route("/jobs", methods=["GET"])
def get_jobs():
    """
    Get list of jobs with filtering and pagination
    
    Query parameters:
    - status: Filter by status (optional)
    - photo_id: Filter by photo ID (optional)
    - priority: Filter by priority (optional)
    - limit: Maximum number of jobs (default: 100)
    - offset: Pagination offset (default: 0)
    
    Returns:
        List of jobs with metadata
    """
    try:
        status_filter = request.args.get('status')
        photo_id = request.args.get('photo_id', type=int)
        priority = request.args.get('priority', type=int)
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        db_session = get_session()
        try:
            query = db_session.query(Job)
            
            # Apply filters
            if status_filter:
                query = query.filter(Job.status == status_filter)
            if photo_id:
                query = query.filter(Job.photo_id == photo_id)
            if priority:
                query = query.filter(Job.priority == priority)
            
            # Order by created_at descending
            query = query.order_by(Job.created_at.desc())
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination
            jobs = query.offset(offset).limit(limit).all()
            
            jobs_data = []
            for job in jobs:
                jobs_data.append({
                    'id': job.id,
                    'photo_id': job.photo_id,
                    'priority': job.priority,
                    'status': job.status,
                    'created_at': job.created_at.isoformat() if job.created_at else None,
                    'started_at': job.started_at.isoformat() if job.started_at else None,
                    'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                    'error_message': job.error_message,
                    'retry_count': job.retry_count
                })
            
            logging_system.log("INFO", "Retrieved jobs", count=len(jobs_data), total=total_count)
            
            return jsonify({
                'jobs': jobs_data,
                'count': len(jobs_data),
                'total': total_count,
                'offset': offset,
                'limit': limit
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get jobs", exception=e)
        return jsonify({"error": f"Failed to get jobs: {e}"}), 500


@api_bp.route("/jobs/<string:job_id>", methods=["GET"])
def get_job_detail(job_id: str):
    """
    Get detailed information about a specific job
    
    Path parameters:
    - job_id: Job ID
    
    Returns:
        Detailed job information including config
    """
    try:
        db_session = get_session()
        try:
            job = db_session.query(Job).filter(Job.id == job_id).first()
            
            if not job:
                return jsonify({"error": "Job not found"}), 404
            
            job_data = {
                'id': job.id,
                'photo_id': job.photo_id,
                'priority': job.priority,
                'status': job.status,
                'config': job.get_config(),
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'error_message': job.error_message,
                'retry_count': job.retry_count
            }
            
            # Add photo information if available
            if job.photo:
                job_data['photo'] = {
                    'id': job.photo.id,
                    'file_name': job.photo.file_name,
                    'ai_score': job.photo.ai_score
                }
            
            return jsonify(job_data), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get job detail", exception=e)
        return jsonify({"error": f"Failed to get job detail: {e}"}), 500


@api_bp.route("/jobs", methods=["POST"])
def create_job():
    """
    Create a new job
    
    Request body:
    - photo_id: Photo ID (required)
    - config: Job configuration (required)
    - priority: Job priority 1-3 (optional, default: 2)
    
    Returns:
        Created job information
    """
    try:
        data = request.get_json()
        
        if not data or 'photo_id' not in data or 'config' not in data:
            return jsonify({"error": "photo_id and config are required"}), 400
        
        import uuid
        
        db_session = get_session()
        try:
            # Verify photo exists
            photo = db_session.query(Photo).filter(Photo.id == data['photo_id']).first()
            if not photo:
                return jsonify({"error": "Photo not found"}), 404
            
            # Create new job
            new_job = Job(
                id=uuid.uuid4().hex,
                photo_id=data['photo_id'],
                priority=data.get('priority', 2),
                status='pending'
            )
            new_job.set_config(data['config'])
            
            db_session.add(new_job)
            db_session.commit()
            
            logging_system.log("INFO", "Job created", job_id=new_job.id, photo_id=new_job.photo_id)
            
            # Broadcast job created event
            websocket_events.broadcast_job_created(
                job_id=new_job.id,
                photo_id=new_job.photo_id,
                priority=new_job.priority
            )
            
            return jsonify({
                'id': new_job.id,
                'photo_id': new_job.photo_id,
                'priority': new_job.priority,
                'status': new_job.status,
                'created_at': new_job.created_at.isoformat() if new_job.created_at else None
            }), 201
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to create job", exception=e)
        return jsonify({"error": f"Failed to create job: {e}"}), 500


@api_bp.route("/jobs/<string:job_id>", methods=["DELETE"])
def delete_job(job_id: str):
    """
    Delete/cancel a job
    
    Path parameters:
    - job_id: Job ID
    
    Returns:
        Success message
    """
    try:
        db_session = get_session()
        try:
            job = db_session.query(Job).filter(Job.id == job_id).first()
            
            if not job:
                return jsonify({"error": "Job not found"}), 404
            
            # Only allow deletion of pending or failed jobs
            if job.status in ['processing', 'completed']:
                return jsonify({"error": f"Cannot delete job with status: {job.status}"}), 400
            
            db_session.delete(job)
            db_session.commit()
            
            logging_system.log("INFO", "Job deleted", job_id=job_id)
            
            return jsonify({
                "message": "Job deleted successfully",
                "job_id": job_id
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to delete job", exception=e)
        return jsonify({"error": f"Failed to delete job: {e}"}), 500


# ============================================================================
# APPROVAL QUEUE ENDPOINTS
# ============================================================================

@api_bp.route("/approval/queue", methods=["GET"])
def get_approval_queue():
    """
    Get approval queue (photos awaiting approval)
    
    Query parameters:
    - session_id: Filter by session ID (optional)
    - min_score: Minimum AI score (optional)
    - limit: Maximum number of photos (default: 100)
    - offset: Pagination offset (default: 0)
    
    Returns:
        List of photos awaiting approval
    """
    try:
        session_id = request.args.get('session_id', type=int)
        min_score = request.args.get('min_score', type=float)
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        db_session = get_session()
        try:
            # Get photos that are completed but not yet approved or rejected
            query = db_session.query(Photo).filter(
                Photo.status == 'completed',
                Photo.approved == False
            )
            
            if session_id:
                query = query.filter(Photo.session_id == session_id)
            if min_score:
                query = query.filter(Photo.ai_score >= min_score)
            
            # Order by AI score descending (best photos first)
            query = query.order_by(Photo.ai_score.desc())
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            photos = query.offset(offset).limit(limit).all()
            
            photos_data = [photo.to_dict() for photo in photos]
            
            logging_system.log("INFO", "Retrieved approval queue", count=len(photos_data), total=total_count)
            
            return jsonify({
                "photos": photos_data,
                "count": len(photos_data),
                "total": total_count,
                "offset": offset,
                "limit": limit
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get approval queue", exception=e)
        return jsonify({"error": f"Failed to get approval queue: {e}"}), 500


@api_bp.route("/approval/<int:photo_id>/approve", methods=["POST"])
def approve_photo(photo_id: int):
    """
    Approve a photo
    
    Path parameters:
    - photo_id: Photo ID
    
    Request body:
    - auto_export: Whether to trigger auto-export (optional, default: false)
    
    Returns:
        Success message
    """
    try:
        data = request.get_json() or {}
        auto_export = data.get('auto_export', False)
        
        db_session = get_session()
        try:
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            
            if not photo:
                return jsonify({"error": "Photo not found"}), 404
            
            photo.approved = True
            photo.approved_at = datetime.utcnow()
            photo.status = 'completed'
            db_session.commit()
            
            # Record learning data
            learning_entry = LearningData(
                photo_id=photo_id,
                action='approved',
                original_preset=photo.selected_preset,
                final_preset=photo.selected_preset
            )
            db_session.add(learning_entry)
            db_session.commit()
            
            logging_system.log("INFO", "Photo approved", photo_id=photo_id)
            
            # Broadcast photo approved event
            websocket_events.broadcast_photo_approved(
                photo_id=photo_id,
                session_id=photo.session_id
            )
            
            # Update approval queue count
            approval_queue_count = db_session.query(func.count(Photo.id)).filter(
                Photo.status == 'completed',
                Photo.approved == False
            ).scalar()
            websocket_events.broadcast_approval_queue_updated(queue_count=approval_queue_count)
            
            response_data = {
                "message": "Photo approved successfully",
                "photo_id": photo_id
            }
            
            # Trigger auto-export if requested
            if auto_export:
                try:
                    from auto_export_engine import get_auto_export_engine
                    export_engine = get_auto_export_engine()
                    if export_engine:
                        export_engine.trigger_export(photo_id)
                        response_data['export_triggered'] = True
                except Exception as export_error:
                    logging_system.log_error("Failed to trigger auto-export", exception=export_error)
                    response_data['export_triggered'] = False
            
            return jsonify(response_data), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to approve photo", exception=e)
        return jsonify({"error": f"Failed to approve photo: {e}"}), 500


@api_bp.route("/approval/<int:photo_id>/reject", methods=["POST"])
def reject_photo(photo_id: int):
    """
    Reject a photo
    
    Path parameters:
    - photo_id: Photo ID
    
    Request body:
    - reason: Rejection reason (optional)
    
    Returns:
        Success message
    """
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'User rejected')
        
        db_session = get_session()
        try:
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            
            if not photo:
                return jsonify({"error": "Photo not found"}), 404
            
            photo.status = 'rejected'
            photo.rejection_reason = reason
            db_session.commit()
            
            # Record learning data
            learning_entry = LearningData(
                photo_id=photo_id,
                action='rejected',
                original_preset=photo.selected_preset,
                final_preset=None
            )
            db_session.add(learning_entry)
            db_session.commit()
            
            logging_system.log("INFO", "Photo rejected", photo_id=photo_id, reason=reason)
            
            # Broadcast photo rejected event
            websocket_events.broadcast_photo_rejected(
                photo_id=photo_id,
                session_id=photo.session_id,
                reason=reason
            )
            
            # Update approval queue count
            approval_queue_count = db_session.query(func.count(Photo.id)).filter(
                Photo.status == 'completed',
                Photo.approved == False
            ).scalar()
            websocket_events.broadcast_approval_queue_updated(queue_count=approval_queue_count)
            
            return jsonify({
                "message": "Photo rejected successfully",
                "photo_id": photo_id
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to reject photo", exception=e)
        return jsonify({"error": f"Failed to reject photo: {e}"}), 500


@api_bp.route("/approval/<int:photo_id>/modify", methods=["POST"])
def modify_photo_preset(photo_id: int):
    """
    Request modification of photo preset
    
    Path parameters:
    - photo_id: Photo ID
    
    Request body:
    - new_preset: New preset name (required)
    - adjustments: Parameter adjustments (optional)
    
    Returns:
        Success message
    """
    try:
        data = request.get_json()
        
        if not data or 'new_preset' not in data:
            return jsonify({"error": "new_preset is required"}), 400
        
        new_preset = data['new_preset']
        adjustments = data.get('adjustments', {})
        
        db_session = get_session()
        try:
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            
            if not photo:
                return jsonify({"error": "Photo not found"}), 404
            
            original_preset = photo.selected_preset
            photo.selected_preset = new_preset
            photo.status = 'queued'  # Re-queue for processing
            db_session.commit()
            
            # Record learning data
            learning_entry = LearningData(
                photo_id=photo_id,
                action='modified',
                original_preset=original_preset,
                final_preset=new_preset,
                parameter_adjustments=str(adjustments) if adjustments else None
            )
            db_session.add(learning_entry)
            db_session.commit()
            
            logging_system.log("INFO", "Photo preset modified", 
                             photo_id=photo_id, 
                             original_preset=original_preset,
                             new_preset=new_preset)
            
            return jsonify({
                "message": "Photo preset modified, re-queued for processing",
                "photo_id": photo_id,
                "new_preset": new_preset
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to modify photo preset", exception=e)
        return jsonify({"error": f"Failed to modify preset: {e}"}), 500


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@api_bp.route("/statistics/daily", methods=["GET"])
def get_daily_statistics():
    """
    Get daily statistics
    
    Query parameters:
    - date: Specific date (YYYY-MM-DD format, default: today)
    
    Returns:
        Daily statistics
    """
    try:
        date_str = request.args.get('date')
        
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = datetime.utcnow().date()
        
        db_session = get_session()
        try:
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())
            
            # Count photos imported today
            total_imported = db_session.query(func.count(Photo.id)).filter(
                Photo.import_time >= start_of_day,
                Photo.import_time <= end_of_day
            ).scalar()
            
            # Count photos processed today
            total_processed = db_session.query(func.count(Photo.id)).filter(
                Photo.status.in_(['completed', 'rejected']),
                Photo.import_time >= start_of_day,
                Photo.import_time <= end_of_day
            ).scalar()
            
            # Count approved photos
            total_approved = db_session.query(func.count(Photo.id)).filter(
                Photo.approved == True,
                Photo.approved_at >= start_of_day,
                Photo.approved_at <= end_of_day
            ).scalar()
            
            # Count rejected photos
            total_rejected = db_session.query(func.count(Photo.id)).filter(
                Photo.status == 'rejected',
                Photo.import_time >= start_of_day,
                Photo.import_time <= end_of_day
            ).scalar()
            
            # Calculate success rate
            success_rate = (total_approved / total_processed * 100) if total_processed > 0 else 0
            
            # Calculate average AI score
            avg_ai_score = db_session.query(func.avg(Photo.ai_score)).filter(
                Photo.import_time >= start_of_day,
                Photo.import_time <= end_of_day,
                Photo.ai_score.isnot(None)
            ).scalar() or 0
            
            stats = {
                "date": target_date.isoformat(),
                "total_imported": total_imported,
                "total_processed": total_processed,
                "total_approved": total_approved,
                "total_rejected": total_rejected,
                "success_rate": round(success_rate, 2),
                "avg_ai_score": round(float(avg_ai_score), 2),
                "avg_processing_time": 2.3  # Placeholder - would need actual tracking
            }
            
            return jsonify(stats), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get daily statistics", exception=e)
        return jsonify({"error": f"Failed to get daily statistics: {e}"}), 500


@api_bp.route("/statistics/weekly", methods=["GET"])
def get_weekly_statistics():
    """
    Get weekly statistics (last 7 days)
    
    Returns:
        Weekly statistics
    """
    try:
        db_session = get_session()
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            
            # Count photos imported this week
            total_imported = db_session.query(func.count(Photo.id)).filter(
                Photo.import_time >= start_date,
                Photo.import_time <= end_date
            ).scalar()
            
            # Count photos processed this week
            total_processed = db_session.query(func.count(Photo.id)).filter(
                Photo.status.in_(['completed', 'rejected']),
                Photo.import_time >= start_date,
                Photo.import_time <= end_date
            ).scalar()
            
            # Count approved photos
            total_approved = db_session.query(func.count(Photo.id)).filter(
                Photo.approved == True,
                Photo.approved_at >= start_date,
                Photo.approved_at <= end_date
            ).scalar()
            
            # Calculate success rate
            success_rate = (total_approved / total_processed * 100) if total_processed > 0 else 0
            
            # Get daily breakdown
            daily_stats = []
            for i in range(7):
                day_start = (end_date - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                
                day_imported = db_session.query(func.count(Photo.id)).filter(
                    Photo.import_time >= day_start,
                    Photo.import_time < day_end
                ).scalar()
                
                daily_stats.append({
                    'date': day_start.date().isoformat(),
                    'imported': day_imported
                })
            
            stats = {
                "period": {
                    "start_date": start_date.date().isoformat(),
                    "end_date": end_date.date().isoformat()
                },
                "total_imported": total_imported,
                "total_processed": total_processed,
                "total_approved": total_approved,
                "success_rate": round(success_rate, 2),
                "daily_breakdown": list(reversed(daily_stats))
            }
            
            return jsonify(stats), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get weekly statistics", exception=e)
        return jsonify({"error": f"Failed to get weekly statistics: {e}"}), 500


@api_bp.route("/statistics/monthly", methods=["GET"])
def get_monthly_statistics():
    """
    Get monthly statistics (current month)
    
    Returns:
        Monthly statistics
    """
    try:
        db_session = get_session()
        try:
            now = datetime.utcnow()
            start_of_month = datetime(now.year, now.month, 1)
            
            # Calculate end of month
            if now.month == 12:
                end_of_month = datetime(now.year + 1, 1, 1) - timedelta(seconds=1)
            else:
                end_of_month = datetime(now.year, now.month + 1, 1) - timedelta(seconds=1)
            
            # Count photos imported this month
            total_imported = db_session.query(func.count(Photo.id)).filter(
                Photo.import_time >= start_of_month,
                Photo.import_time <= end_of_month
            ).scalar()
            
            # Count photos processed this month
            total_processed = db_session.query(func.count(Photo.id)).filter(
                Photo.status.in_(['completed', 'rejected']),
                Photo.import_time >= start_of_month,
                Photo.import_time <= end_of_month
            ).scalar()
            
            # Count approved photos
            total_approved = db_session.query(func.count(Photo.id)).filter(
                Photo.approved == True,
                Photo.approved_at >= start_of_month,
                Photo.approved_at <= end_of_month
            ).scalar()
            
            # Calculate success rate
            success_rate = (total_approved / total_processed * 100) if total_processed > 0 else 0
            
            # Get subject type distribution
            subject_distribution = db_session.query(
                Photo.subject_type,
                func.count(Photo.id)
            ).filter(
                Photo.import_time >= start_of_month,
                Photo.import_time <= end_of_month,
                Photo.subject_type.isnot(None)
            ).group_by(Photo.subject_type).all()
            
            stats = {
                "period": {
                    "year": now.year,
                    "month": now.month,
                    "start_date": start_of_month.date().isoformat(),
                    "end_date": end_of_month.date().isoformat()
                },
                "total_imported": total_imported,
                "total_processed": total_processed,
                "total_approved": total_approved,
                "success_rate": round(success_rate, 2),
                "subject_distribution": {subject: count for subject, count in subject_distribution if subject}
            }
            
            return jsonify(stats), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get monthly statistics", exception=e)
        return jsonify({"error": f"Failed to get monthly statistics: {e}"}), 500


@api_bp.route("/statistics/presets", methods=["GET"])
def get_preset_statistics():
    """
    Get preset usage statistics
    
    Query parameters:
    - days: Number of days to analyze (default: 30)
    
    Returns:
        Preset usage frequency and approval rates
    """
    try:
        days = int(request.args.get('days', 30))
        
        db_session = get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get preset usage counts
            preset_usage = db_session.query(
                Photo.selected_preset,
                func.count(Photo.id).label('usage_count')
            ).filter(
                Photo.selected_preset.isnot(None),
                Photo.import_time >= cutoff_date
            ).group_by(Photo.selected_preset).all()
            
            # Calculate approval rates for each preset
            preset_stats = []
            for preset_name, usage_count in preset_usage:
                total = db_session.query(func.count(Photo.id)).filter(
                    Photo.selected_preset == preset_name,
                    Photo.import_time >= cutoff_date
                ).scalar()
                
                approved = db_session.query(func.count(Photo.id)).filter(
                    Photo.selected_preset == preset_name,
                    Photo.approved == True,
                    Photo.import_time >= cutoff_date
                ).scalar()
                
                approval_rate = (approved / total * 100) if total > 0 else 0
                
                preset_stats.append({
                    'preset_name': preset_name,
                    'usage_count': usage_count,
                    'approval_rate': round(approval_rate, 2),
                    'approved_count': approved
                })
            
            # Sort by usage count descending
            preset_stats.sort(key=lambda x: x['usage_count'], reverse=True)
            
            logging_system.log("INFO", "Retrieved preset statistics", preset_count=len(preset_stats))
            
            return jsonify({
                "period_days": days,
                "presets": preset_stats,
                "total_presets": len(preset_stats)
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get preset statistics", exception=e)
        return jsonify({"error": f"Failed to get preset statistics: {e}"}), 500


# ============================================================================
# SYSTEM MANAGEMENT ENDPOINTS
# ============================================================================

@api_bp.route("/system/status", methods=["GET"])
def get_system_status():
    """
    Get detailed system status
    
    Returns:
        System status including components, resources, and queue info
    """
    try:
        db_session = get_session()
        try:
            # Count active sessions
            active_sessions = db_session.query(func.count(Session.id)).filter(
                Session.status != 'completed'
            ).scalar()
            
            # Count pending jobs
            pending_jobs = db_session.query(func.count(Job.id)).filter(
                Job.status == 'pending'
            ).scalar()
            
            # Count processing jobs
            processing_jobs = db_session.query(func.count(Job.id)).filter(
                Job.status == 'processing'
            ).scalar()
            
            # Count photos in approval queue
            approval_queue_count = db_session.query(func.count(Photo.id)).filter(
                Photo.status == 'completed',
                Photo.approved == False
            ).scalar()
            
            # Get resource usage
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            status = {
                "system": "running",
                "timestamp": datetime.utcnow().isoformat(),
                "sessions": {
                    "active": active_sessions
                },
                "jobs": {
                    "pending": pending_jobs,
                    "processing": processing_jobs
                },
                "approval_queue": {
                    "count": approval_queue_count
                },
                "resources": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_mb": memory.used / (1024 * 1024),
                    "memory_total_mb": memory.total / (1024 * 1024)
                }
            }
            
            # Try to get GPU info
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                gpu_temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                
                status["resources"]["gpu"] = {
                    "available": True,
                    "temperature": gpu_temp,
                    "memory_used_mb": mem_info.used / (1024 * 1024),
                    "memory_total_mb": mem_info.total / (1024 * 1024),
                    "utilization": utilization.gpu
                }
                
                pynvml.nvmlShutdown()
            except:
                status["resources"]["gpu"] = {"available": False}
            
            return jsonify(status), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get system status", exception=e)
        return jsonify({"error": f"Failed to get system status: {e}"}), 500


@api_bp.route("/system/health", methods=["GET"])
def get_system_health():
    """
    System health check endpoint
    
    Returns:
        Simple health status
    """
    try:
        # Simple health check - if we can respond, system is healthy
        db_session = get_session()
        try:
            # Test database connection
            db_session.execute("SELECT 1")
            
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "connected"
            }), 200
        finally:
            db_session.close()
            
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@api_bp.route("/system/pause", methods=["POST"])
def pause_system():
    """
    Pause system processing
    
    Returns:
        Success message
    """
    try:
        from job_queue_manager import get_job_queue_manager
        
        job_queue_manager = get_job_queue_manager()
        success = job_queue_manager.pause_queue()
        
        if success:
            logging_system.log("WARNING", "System processing paused")
            return jsonify({"message": "System processing paused successfully"}), 200
        else:
            return jsonify({"error": "Failed to pause system"}), 500
            
    except Exception as e:
        logging_system.log_error("Failed to pause system", exception=e)
        return jsonify({"error": f"Failed to pause system: {e}"}), 500


@api_bp.route("/system/resume", methods=["POST"])
def resume_system():
    """
    Resume system processing
    
    Returns:
        Success message
    """
    try:
        from job_queue_manager import get_job_queue_manager
        
        job_queue_manager = get_job_queue_manager()
        success = job_queue_manager.resume_queue()
        
        if success:
            logging_system.log("INFO", "System processing resumed")
            return jsonify({"message": "System processing resumed successfully"}), 200
        else:
            return jsonify({"error": "Failed to resume system"}), 500
            
    except Exception as e:
        logging_system.log_error("Failed to resume system", exception=e)
        return jsonify({"error": f"Failed to resume system: {e}"}), 500


@api_bp.route("/system/info", methods=["GET"])
def get_system_info():
    """
    Get system information
    
    Returns:
        System version and configuration info
    """
    try:
        from config_manager import get_config_manager
        
        config_mgr = get_config_manager()
        config = config_mgr.load()
        
        info = {
            "version": "2.0",
            "system_name": "Junmai AutoDev",
            "llm_provider": config.get('ai', {}).get('llm_provider', 'ollama'),
            "llm_model": config.get('ai', {}).get('llm_model', 'llama3.1:8b-instruct'),
            "auto_import": config.get('processing', {}).get('auto_import', True),
            "auto_select": config.get('processing', {}).get('auto_select', True),
            "auto_develop": config.get('processing', {}).get('auto_develop', True),
            "auto_export": config.get('processing', {}).get('auto_export', False)
        }
        
        return jsonify(info), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get system info", exception=e)
        return jsonify({"error": f"Failed to get system info: {e}"}), 500


# ============================================================================
# WEBSOCKET MANAGEMENT ENDPOINTS
# ============================================================================

@api_bp.route("/websocket/clients", methods=["GET"])
def get_websocket_clients():
    """
    Get list of connected WebSocket clients
    
    Returns:
        List of connected clients with their information
    """
    try:
        from websocket_server import get_websocket_server
        
        ws_server = get_websocket_server()
        if not ws_server:
            return jsonify({"error": "WebSocket server not initialized"}), 500
        
        clients = ws_server.get_connected_clients()
        
        logging_system.log("INFO", "Retrieved WebSocket clients", count=len(clients))
        
        return jsonify({
            "clients": clients,
            "count": len(clients)
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get WebSocket clients", exception=e)
        return jsonify({"error": f"Failed to get WebSocket clients: {e}"}), 500


@api_bp.route("/websocket/broadcast", methods=["POST"])
def broadcast_websocket_message():
    """
    Broadcast a message to all connected WebSocket clients
    
    Request body:
    - message: Message object to broadcast (required)
    - channel: Optional channel name for filtered broadcast
    
    Returns:
        Success message
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "message is required"}), 400
        
        from websocket_server import get_websocket_server
        
        ws_server = get_websocket_server()
        if not ws_server:
            return jsonify({"error": "WebSocket server not initialized"}), 500
        
        message = data['message']
        channel = data.get('channel')
        
        ws_server.broadcast(message, channel=channel)
        
        logging_system.log("INFO", "Broadcasted WebSocket message", 
                          message_type=message.get('type'), channel=channel)
        
        return jsonify({
            "message": "Message broadcasted successfully",
            "channel": channel
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to broadcast WebSocket message", exception=e)
        return jsonify({"error": f"Failed to broadcast message: {e}"}), 500


@api_bp.route("/websocket/disconnect/<int:client_id>", methods=["POST"])
def disconnect_websocket_client(client_id: int):
    """
    Disconnect a specific WebSocket client
    
    Path parameters:
    - client_id: Client ID to disconnect
    
    Returns:
        Success message
    """
    try:
        from websocket_server import get_websocket_server
        
        ws_server = get_websocket_server()
        if not ws_server:
            return jsonify({"error": "WebSocket server not initialized"}), 500
        
        ws_server.disconnect_client(client_id)
        
        logging_system.log("INFO", "Disconnected WebSocket client", client_id=client_id)
        
        return jsonify({
            "message": "Client disconnected successfully",
            "client_id": client_id
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to disconnect WebSocket client", exception=e)
        return jsonify({"error": f"Failed to disconnect client: {e}"}), 500
