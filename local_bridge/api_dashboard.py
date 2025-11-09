"""
Dashboard API Endpoints for Junmai AutoDev
ダッシュボード用APIエンドポイント

Requirements: 7.1, 7.2, 15.1, 15.2
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from models.database import get_session, Session, Photo, Statistic, Job
from sqlalchemy import func, desc
from logging_system import get_logging_system

dashboard_bp = Blueprint('dashboard', __name__)
logging_system = get_logging_system()


@dashboard_bp.route("/system/health", methods=["GET"])
def system_health():
    """
    System health check endpoint
    
    Returns:
        System health status
    """
    try:
        # Simple health check - if we can respond, system is healthy
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500


@dashboard_bp.route("/system/status", methods=["GET"])
def system_status():
    """
    Get detailed system status
    
    Returns:
        Detailed system status including components
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
            
            status = {
                "system": "running",
                "active_sessions": active_sessions,
                "pending_jobs": pending_jobs,
                "processing_jobs": processing_jobs,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return jsonify(status), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get system status", exception=e)
        return jsonify({"error": f"Failed to get system status: {e}"}), 500


@dashboard_bp.route("/sessions", methods=["GET"])
def get_sessions():
    """
    Get list of sessions
    
    Query parameters:
    - status: Filter by status (optional)
    - limit: Maximum number of sessions to return (default: 50)
    - active_only: Return only active sessions (default: false)
    
    Returns:
        List of sessions with details
    """
    try:
        status_filter = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        db_session = get_session()
        try:
            query = db_session.query(Session)
            
            if status_filter:
                query = query.filter(Session.status == status_filter)
            
            if active_only:
                query = query.filter(Session.status != 'completed')
            
            sessions = query.order_by(desc(Session.created_at)).limit(limit).all()
            
            sessions_data = []
            for session in sessions:
                sessions_data.append({
                    'id': session.id,
                    'name': session.name,
                    'created_at': session.created_at.isoformat() if session.created_at else None,
                    'import_folder': session.import_folder,
                    'total_photos': session.total_photos,
                    'processed_photos': session.processed_photos,
                    'status': session.status
                })
            
            logging_system.log("INFO", "Retrieved sessions", count=len(sessions_data))
            
            return jsonify(sessions_data), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get sessions", exception=e)
        return jsonify({"error": f"Failed to get sessions: {e}"}), 500


@dashboard_bp.route("/sessions/<int:session_id>", methods=["GET"])
def get_session_detail(session_id: int):
    """
    Get detailed information about a specific session
    
    Path parameters:
    - session_id: Session ID
    
    Returns:
        Detailed session information
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
            
            session_data = {
                'id': session.id,
                'name': session.name,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'import_folder': session.import_folder,
                'total_photos': session.total_photos,
                'processed_photos': session.processed_photos,
                'status': session.status,
                'photo_stats': {status: count for status, count in photo_stats}
            }
            
            return jsonify(session_data), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get session detail", exception=e)
        return jsonify({"error": f"Failed to get session detail: {e}"}), 500


@dashboard_bp.route("/sessions/<int:session_id>", methods=["DELETE"])
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


@dashboard_bp.route("/websocket/status", methods=["GET"])
def websocket_status():
    """
    Get WebSocket server status
    
    Returns:
        WebSocket connection status
    """
    try:
        from websocket_fallback import get_websocket_fallback
        
        ws_server = get_websocket_fallback()
        
        if ws_server:
            status = {
                "running": True,
                "connected_clients": len(ws_server.clients),
                "clients": [
                    {
                        "id": id(client),
                        "connected_at": "unknown"  # Would need to track this
                    }
                    for client in ws_server.clients
                ]
            }
        else:
            status = {
                "running": False,
                "connected_clients": 0,
                "clients": []
            }
        
        return jsonify(status), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get websocket status", exception=e)
        return jsonify({"error": f"Failed to get websocket status: {e}"}), 500


@dashboard_bp.route("/resource/status", methods=["GET"])
def resource_status():
    """
    Get resource usage status (CPU, GPU, Memory)
    
    Returns:
        Resource usage information
    """
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_used_mb = memory.used / (1024 * 1024)
        memory_total_mb = memory.total / (1024 * 1024)
        memory_percent = memory.percent
        
        # GPU information (if available)
        gpu_info = {
            "available": False,
            "temperature": 0,
            "memory_used_mb": 0,
            "memory_total_mb": 8192,
            "utilization": 0
        }
        
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            
            # GPU temperature
            gpu_temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            
            # GPU memory
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_memory_used = mem_info.used / (1024 * 1024)
            gpu_memory_total = mem_info.total / (1024 * 1024)
            
            # GPU utilization
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_util = utilization.gpu
            
            gpu_info = {
                "available": True,
                "temperature": gpu_temp,
                "memory_used_mb": gpu_memory_used,
                "memory_total_mb": gpu_memory_total,
                "utilization": gpu_util
            }
            
            pynvml.nvmlShutdown()
            
        except:
            # GPU monitoring not available
            pass
        
        status = {
            "cpu_percent": cpu_percent,
            "memory_used_mb": memory_used_mb,
            "memory_total_mb": memory_total_mb,
            "memory_percent": memory_percent,
            "gpu_available": gpu_info["available"],
            "gpu_temperature": gpu_info["temperature"],
            "gpu_memory_used_mb": gpu_info["memory_used_mb"],
            "gpu_memory_total_mb": gpu_info["memory_total_mb"],
            "gpu_utilization": gpu_info["utilization"]
        }
        
        return jsonify(status), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get resource status", exception=e)
        return jsonify({"error": f"Failed to get resource status: {e}"}), 500


@dashboard_bp.route("/statistics/daily", methods=["GET"])
def daily_statistics():
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
            # Get statistics for the target date
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())
            
            # Count photos imported today
            total_imported = db_session.query(func.count(Photo.id)).filter(
                Photo.import_time >= start_of_day,
                Photo.import_time <= end_of_day
            ).scalar()
            
            # Count photos processed today
            total_processed = db_session.query(func.count(Photo.id)).filter(
                Photo.status == 'completed',
                Photo.import_time >= start_of_day,
                Photo.import_time <= end_of_day
            ).scalar()
            
            # Count approved photos
            total_approved = db_session.query(func.count(Photo.id)).filter(
                Photo.approved == True,
                Photo.approved_at >= start_of_day,
                Photo.approved_at <= end_of_day
            ).scalar()
            
            # Calculate success rate
            success_rate = (total_approved / total_processed) if total_processed > 0 else 0
            
            # Calculate average processing time (simplified)
            avg_processing_time = 2.3  # Placeholder - would need to track actual times
            
            stats = {
                "date": target_date.isoformat(),
                "today": {
                    "total_imported": total_imported,
                    "total_processed": total_processed,
                    "total_approved": total_approved,
                    "success_rate": success_rate,
                    "avg_processing_time": avg_processing_time
                }
            }
            
            return jsonify(stats), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get daily statistics", exception=e)
        return jsonify({"error": f"Failed to get daily statistics: {e}"}), 500


@dashboard_bp.route("/approval/queue", methods=["GET"])
def approval_queue():
    """
    Get approval queue (photos awaiting approval)
    
    Query parameters:
    - limit: Maximum number of photos to return (default: 100)
    
    Returns:
        List of photos awaiting approval
    """
    try:
        limit = int(request.args.get('limit', 100))
        
        db_session = get_session()
        try:
            # Get photos that are completed but not yet approved
            photos = db_session.query(Photo).filter(
                Photo.status == 'completed',
                Photo.approved == False
            ).order_by(desc(Photo.import_time)).limit(limit).all()
            
            photos_data = [photo.to_dict() for photo in photos]
            
            logging_system.log("INFO", "Retrieved approval queue", count=len(photos_data))
            
            return jsonify({
                "photos": photos_data,
                "count": len(photos_data)
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get approval queue", exception=e)
        return jsonify({"error": f"Failed to get approval queue: {e}"}), 500


@dashboard_bp.route("/approval/<int:photo_id>/approve", methods=["POST"])
def approve_photo(photo_id: int):
    """
    Approve a photo
    
    Path parameters:
    - photo_id: Photo ID
    
    Returns:
        Success message
    """
    try:
        db_session = get_session()
        try:
            photo = db_session.query(Photo).filter(Photo.id == photo_id).first()
            
            if not photo:
                return jsonify({"error": "Photo not found"}), 404
            
            photo.approved = True
            photo.approved_at = datetime.utcnow()
            db_session.commit()
            
            logging_system.log("INFO", "Photo approved", photo_id=photo_id)
            
            return jsonify({
                "message": "Photo approved successfully",
                "photo_id": photo_id
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to approve photo", exception=e)
        return jsonify({"error": f"Failed to approve photo: {e}"}), 500


@dashboard_bp.route("/approval/<int:photo_id>/reject", methods=["POST"])
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
            
            logging_system.log("INFO", "Photo rejected", photo_id=photo_id, reason=reason)
            
            return jsonify({
                "message": "Photo rejected successfully",
                "photo_id": photo_id
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to reject photo", exception=e)
        return jsonify({"error": f"Failed to reject photo: {e}"}), 500


@dashboard_bp.route("/config", methods=["GET"])
def get_config():
    """
    Get current configuration
    
    Returns:
        Current configuration dictionary
    """
    try:
        from config_manager import get_config_manager
        
        config_mgr = get_config_manager()
        config = config_mgr.load()
        
        return jsonify(config), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get configuration", exception=e)
        return jsonify({"error": f"Failed to get configuration: {e}"}), 500


@dashboard_bp.route("/config", methods=["POST"])
def save_config():
    """
    Save configuration
    
    Request body:
    - Configuration dictionary (full or partial)
    
    Returns:
        Success message
    """
    try:
        from config_manager import get_config_manager
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No configuration data provided"}), 400
        
        config_mgr = get_config_manager()
        
        # Validate configuration
        is_valid, error_msg = config_mgr.validate(data)
        if not is_valid:
            return jsonify({"error": f"Invalid configuration: {error_msg}"}), 400
        
        # Save configuration
        config_mgr.save(data)
        
        logging_system.log("INFO", "Configuration saved successfully")
        
        return jsonify({
            "message": "Configuration saved successfully"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to save configuration", exception=e)
        return jsonify({"error": f"Failed to save configuration: {e}"}), 500


@dashboard_bp.route("/config/reset", methods=["POST"])
def reset_config():
    """
    Reset configuration to default values
    
    Returns:
        Default configuration
    """
    try:
        from config_manager import get_config_manager
        
        config_mgr = get_config_manager()
        default_config = config_mgr.reset_to_default()
        config_mgr.save()
        
        logging_system.log("INFO", "Configuration reset to default values")
        
        return jsonify({
            "message": "Configuration reset to default values",
            "config": default_config
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to reset configuration", exception=e)
        return jsonify({"error": f"Failed to reset configuration: {e}"}), 500


@dashboard_bp.route("/config/validate", methods=["POST"])
def validate_config():
    """
    Validate configuration without saving
    
    Request body:
    - Configuration dictionary to validate
    
    Returns:
        Validation result
    """
    try:
        from config_manager import get_config_manager
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No configuration data provided"}), 400
        
        config_mgr = get_config_manager()
        is_valid, error_msg = config_mgr.validate(data)
        
        if is_valid:
            return jsonify({
                "valid": True,
                "message": "Configuration is valid"
            }), 200
        else:
            return jsonify({
                "valid": False,
                "error": error_msg
            }), 400
        
    except Exception as e:
        logging_system.log_error("Failed to validate configuration", exception=e)
        return jsonify({"error": f"Failed to validate configuration: {e}"}), 500



@dashboard_bp.route("/statistics/weekly", methods=["GET"])
def weekly_statistics():
    """
    Get weekly statistics
    
    Returns:
        Weekly statistics
    """
    try:
        db_session = get_session()
        try:
            # Get statistics for the past 7 days
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=7)
            
            start_of_week = datetime.combine(start_date, datetime.min.time())
            end_of_week = datetime.combine(end_date, datetime.max.time())
            
            # Count photos imported this week
            total_imported = db_session.query(func.count(Photo.id)).filter(
                Photo.import_time >= start_of_week,
                Photo.import_time <= end_of_week
            ).scalar()
            
            # Count photos processed this week
            total_processed = db_session.query(func.count(Photo.id)).filter(
                Photo.status == 'completed',
                Photo.import_time >= start_of_week,
                Photo.import_time <= end_of_week
            ).scalar()
            
            # Count approved photos
            total_approved = db_session.query(func.count(Photo.id)).filter(
                Photo.approved == True,
                Photo.approved_at >= start_of_week,
                Photo.approved_at <= end_of_week
            ).scalar()
            
            # Calculate success rate
            success_rate = (total_approved / total_processed) if total_processed > 0 else 0
            
            # Calculate average processing time
            avg_processing_time = 2.3  # Placeholder
            
            stats = {
                "week": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_imported": total_imported,
                    "total_processed": total_processed,
                    "total_approved": total_approved,
                    "success_rate": success_rate,
                    "avg_processing_time": avg_processing_time
                }
            }
            
            return jsonify(stats), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get weekly statistics", exception=e)
        return jsonify({"error": f"Failed to get weekly statistics: {e}"}), 500


@dashboard_bp.route("/statistics/monthly", methods=["GET"])
def monthly_statistics():
    """
    Get monthly statistics
    
    Returns:
        Monthly statistics
    """
    try:
        db_session = get_session()
        try:
            # Get statistics for the current month
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
                Photo.status == 'completed',
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
            success_rate = (total_approved / total_processed) if total_processed > 0 else 0
            
            # Calculate average processing time
            avg_processing_time = 2.3  # Placeholder
            
            stats = {
                "month": {
                    "year": now.year,
                    "month": now.month,
                    "total_imported": total_imported,
                    "total_processed": total_processed,
                    "total_approved": total_approved,
                    "success_rate": success_rate,
                    "avg_processing_time": avg_processing_time
                }
            }
            
            return jsonify(stats), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get monthly statistics", exception=e)
        return jsonify({"error": f"Failed to get monthly statistics: {e}"}), 500


@dashboard_bp.route("/statistics/presets", methods=["GET"])
def preset_statistics():
    """
    Get preset usage statistics
    
    Returns:
        Preset usage frequency data
    """
    try:
        db_session = get_session()
        try:
            # Get preset usage from photos
            preset_usage = db_session.query(
                Photo.selected_preset,
                func.count(Photo.id)
            ).filter(
                Photo.selected_preset.isnot(None)
            ).group_by(Photo.selected_preset).all()
            
            # Convert to dictionary
            preset_dict = {preset: count for preset, count in preset_usage if preset}
            
            # Get preset approval rates
            preset_approval = {}
            for preset_name in preset_dict.keys():
                total = db_session.query(func.count(Photo.id)).filter(
                    Photo.selected_preset == preset_name
                ).scalar()
                
                approved = db_session.query(func.count(Photo.id)).filter(
                    Photo.selected_preset == preset_name,
                    Photo.approved == True
                ).scalar()
                
                approval_rate = (approved / total) if total > 0 else 0
                preset_approval[preset_name] = approval_rate
            
            stats = {
                "preset_usage": preset_dict,
                "preset_approval_rates": preset_approval,
                "total_presets": len(preset_dict)
            }
            
            logging_system.log("INFO", "Retrieved preset statistics", preset_count=len(preset_dict))
            
            return jsonify(stats), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        logging_system.log_error("Failed to get preset statistics", exception=e)
        return jsonify({"error": f"Failed to get preset statistics: {e}"}), 500
