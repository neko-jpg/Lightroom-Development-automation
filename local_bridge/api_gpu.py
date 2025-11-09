"""
GPU Management API Endpoints

Provides REST API endpoints for GPU monitoring, memory allocation,
and throttling management.

Requirements: 17.1, 17.2, 17.3, 17.5
"""

from flask import Blueprint, jsonify, request
from gpu_manager import get_gpu_manager
from logging_system import get_logging_system

logging_system = get_logging_system()
gpu_bp = Blueprint('gpu', __name__, url_prefix='/api/gpu')


@gpu_bp.route('/status', methods=['GET'])
def get_gpu_status():
    """
    Get current GPU status
    
    Query Parameters:
        gpu_id (optional): Specific GPU ID (default: 0)
    
    Returns:
        JSON with GPU status
        
    Requirements: 17.1, 17.2, 17.3
    """
    try:
        gpu_manager = get_gpu_manager()
        gpu_id = request.args.get('gpu_id', 0, type=int)
        
        status = gpu_manager.get_gpu_status(gpu_id)
        
        return jsonify({
            'success': True,
            'data': status
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get GPU status", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gpu_bp.route('/status/all', methods=['GET'])
def get_all_gpus_status():
    """
    Get status for all GPUs
    
    Returns:
        JSON with all GPUs status
    """
    try:
        gpu_manager = get_gpu_manager()
        
        statuses = gpu_manager.get_all_gpus_status()
        
        return jsonify({
            'success': True,
            'data': {
                'gpu_count': len(statuses),
                'gpus': statuses
            }
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get all GPUs status", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gpu_bp.route('/metrics', methods=['GET'])
def get_gpu_metrics():
    """
    Get GPU metrics
    
    Query Parameters:
        gpu_id (optional): Specific GPU ID
    
    Returns:
        JSON with current GPU metrics
        
    Requirements: 17.2
    """
    try:
        gpu_manager = get_gpu_manager()
        gpu_id = request.args.get('gpu_id', 0, type=int)
        
        metrics = gpu_manager.get_gpu_metrics(gpu_id)
        
        if not metrics:
            return jsonify({
                'success': False,
                'error': 'GPU not available or invalid GPU ID'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'timestamp': metrics.timestamp.isoformat(),
                'gpu_id': metrics.gpu_id,
                'gpu_name': metrics.gpu_name,
                'load_percent': metrics.load_percent,
                'memory_used_mb': metrics.memory_used_mb,
                'memory_total_mb': metrics.memory_total_mb,
                'memory_percent': metrics.memory_percent,
                'temperature_celsius': metrics.temperature_celsius,
                'state': metrics.state.value
            }
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get GPU metrics", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gpu_bp.route('/metrics/history', methods=['GET'])
def get_metrics_history():
    """
    Get historical GPU metrics
    
    Query Parameters:
        gpu_id (optional): Filter by GPU ID
        limit (optional): Maximum number of records (default: 100)
    
    Returns:
        JSON with metrics history
    """
    try:
        gpu_manager = get_gpu_manager()
        
        gpu_id = request.args.get('gpu_id', type=int)
        limit = request.args.get('limit', 100, type=int)
        
        history = gpu_manager.get_metrics_history(gpu_id=gpu_id, limit=limit)
        
        return jsonify({
            'success': True,
            'data': {
                'count': len(history),
                'metrics': history
            }
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get metrics history", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gpu_bp.route('/temperature/trend', methods=['GET'])
def get_temperature_trend():
    """
    Get temperature trend analysis
    
    Query Parameters:
        gpu_id (optional): GPU ID (default: 0)
        duration (optional): Duration in minutes (default: 5)
    
    Returns:
        JSON with temperature trend
        
    Requirements: 17.2
    """
    try:
        gpu_manager = get_gpu_manager()
        
        gpu_id = request.args.get('gpu_id', 0, type=int)
        duration = request.args.get('duration', 5, type=int)
        
        trend = gpu_manager.get_temperature_trend(duration, gpu_id)
        
        return jsonify({
            'success': True,
            'data': trend
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get temperature trend", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gpu_bp.route('/memory/allocate', methods=['POST'])
def allocate_memory():
    """
    Allocate GPU memory
    
    Request Body:
        {
            "allocation_id": "unique_id",
            "required_mb": 1024,
            "gpu_id": 0  // optional
        }
    
    Returns:
        JSON with allocation result
        
    Requirements: 17.1
    """
    try:
        data = request.get_json()
        
        if not data or 'allocation_id' not in data or 'required_mb' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: allocation_id, required_mb'
            }), 400
        
        gpu_manager = get_gpu_manager()
        
        allocation_id = data['allocation_id']
        required_mb = data['required_mb']
        gpu_id = data.get('gpu_id', 0)
        
        success = gpu_manager.allocate_memory(allocation_id, required_mb, gpu_id)
        
        if success:
            available = gpu_manager.get_available_memory(gpu_id)
            
            return jsonify({
                'success': True,
                'data': {
                    'allocation_id': allocation_id,
                    'allocated_mb': required_mb,
                    'available_mb': available
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Memory allocation failed - insufficient memory or invalid request'
            }), 400
        
    except Exception as e:
        logging_system.log_error("Failed to allocate GPU memory", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gpu_bp.route('/memory/deallocate', methods=['POST'])
def deallocate_memory():
    """
    Deallocate GPU memory
    
    Request Body:
        {
            "allocation_id": "unique_id",
            "gpu_id": 0  // optional
        }
    
    Returns:
        JSON with deallocation result
    """
    try:
        data = request.get_json()
        
        if not data or 'allocation_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: allocation_id'
            }), 400
        
        gpu_manager = get_gpu_manager()
        
        allocation_id = data['allocation_id']
        gpu_id = data.get('gpu_id', 0)
        
        success = gpu_manager.deallocate_memory(allocation_id, gpu_id)
        
        if success:
            available = gpu_manager.get_available_memory(gpu_id)
            
            return jsonify({
                'success': True,
                'data': {
                    'allocation_id': allocation_id,
                    'available_mb': available
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Deallocation failed - allocation not found'
            }), 404
        
    except Exception as e:
        logging_system.log_error("Failed to deallocate GPU memory", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gpu_bp.route('/memory/available', methods=['GET'])
def get_available_memory():
    """
    Get available GPU memory
    
    Query Parameters:
        gpu_id (optional): GPU ID (default: 0)
    
    Returns:
        JSON with available memory
        
    Requirements: 17.1
    """
    try:
        gpu_manager = get_gpu_manager()
        gpu_id = request.args.get('gpu_id', 0, type=int)
        
        available = gpu_manager.get_available_memory(gpu_id)
        
        return jsonify({
            'success': True,
            'data': {
                'gpu_id': gpu_id,
                'available_mb': available
            }
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get available memory", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gpu_bp.route('/throttle/status', methods=['GET'])
def get_throttle_status():
    """
    Get throttling status
    
    Returns:
        JSON with throttling information
        
    Requirements: 17.3, 17.5
    """
    try:
        gpu_manager = get_gpu_manager()
        
        should_throttle = gpu_manager.should_throttle_processing()
        speed_multiplier = gpu_manager.get_processing_speed_multiplier()
        
        return jsonify({
            'success': True,
            'data': {
                'should_throttle': should_throttle,
                'speed_multiplier': speed_multiplier,
                'is_throttled': gpu_manager.is_throttled,
                'current_state': gpu_manager.current_state.value
            }
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get throttle status", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gpu_bp.route('/monitoring/start', methods=['POST'])
def start_monitoring():
    """
    Start GPU monitoring
    
    Returns:
        JSON with operation result
        
    Requirements: 17.2
    """
    try:
        gpu_manager = get_gpu_manager()
        gpu_manager.start_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'GPU monitoring started'
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to start GPU monitoring", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gpu_bp.route('/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """
    Stop GPU monitoring
    
    Returns:
        JSON with operation result
    """
    try:
        gpu_manager = get_gpu_manager()
        gpu_manager.stop_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'GPU monitoring stopped'
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to stop GPU monitoring", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gpu_bp.route('/config', methods=['GET'])
def get_config():
    """
    Get GPU manager configuration
    
    Returns:
        JSON with current configuration
    """
    try:
        gpu_manager = get_gpu_manager()
        
        return jsonify({
            'success': True,
            'data': gpu_manager.config
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get GPU config", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gpu_bp.route('/config', methods=['PUT'])
def update_config():
    """
    Update GPU manager configuration
    
    Request Body:
        {
            "temp_optimal": 65,
            "temp_throttle": 85,
            ...
        }
    
    Returns:
        JSON with operation result
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No configuration data provided'
            }), 400
        
        gpu_manager = get_gpu_manager()
        success = gpu_manager.update_config(data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Configuration updated',
                'data': gpu_manager.config
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update configuration'
            }), 500
        
    except Exception as e:
        logging_system.log_error("Failed to update GPU config", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def register_gpu_api(app):
    """
    Register GPU API blueprint with Flask app
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(gpu_bp)
    logging_system.log("INFO", "GPU API endpoints registered")
