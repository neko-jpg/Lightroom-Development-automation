"""
API endpoints for performance metrics

Provides REST API for accessing and exporting performance metrics.

Requirements: 12.1, 12.2, 15.4
"""

from flask import Blueprint, jsonify, request, send_file
from performance_metrics import get_performance_metrics_collector
from logging_system import get_logging_system
import os

logging_system = get_logging_system()

# Create blueprint
performance_metrics_bp = Blueprint('performance_metrics', __name__, url_prefix='/api/metrics')


@performance_metrics_bp.route('/processing/stats', methods=['GET'])
def get_processing_stats():
    """
    Get processing time statistics
    
    Query Parameters:
        - operation: Filter by operation name (optional)
        - duration_minutes: Time window in minutes (optional)
    
    Returns:
        JSON with processing time statistics
        
    Requirements: 12.1, 15.4
    """
    try:
        collector = get_performance_metrics_collector()
        
        operation = request.args.get('operation')
        duration_minutes = request.args.get('duration_minutes', type=int)
        
        stats = collector.get_processing_time_stats(
            operation=operation,
            duration_minutes=duration_minutes
        )
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logging_system.log_error("Failed to get processing stats", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_metrics_bp.route('/memory/stats', methods=['GET'])
def get_memory_stats():
    """
    Get memory usage statistics
    
    Query Parameters:
        - duration_minutes: Time window in minutes (optional)
    
    Returns:
        JSON with memory usage statistics
        
    Requirements: 12.2, 15.4
    """
    try:
        collector = get_performance_metrics_collector()
        
        duration_minutes = request.args.get('duration_minutes', type=int)
        
        stats = collector.get_memory_usage_stats(duration_minutes=duration_minutes)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logging_system.log_error("Failed to get memory stats", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_metrics_bp.route('/gpu/stats', methods=['GET'])
def get_gpu_stats():
    """
    Get GPU usage statistics
    
    Query Parameters:
        - gpu_id: GPU identifier (optional)
        - duration_minutes: Time window in minutes (optional)
    
    Returns:
        JSON with GPU usage statistics
        
    Requirements: 12.2, 15.4
    """
    try:
        collector = get_performance_metrics_collector()
        
        gpu_id = request.args.get('gpu_id', type=int)
        duration_minutes = request.args.get('duration_minutes', type=int)
        
        stats = collector.get_gpu_usage_stats(
            gpu_id=gpu_id,
            duration_minutes=duration_minutes
        )
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logging_system.log_error("Failed to get GPU stats", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_metrics_bp.route('/operations/summary', methods=['GET'])
def get_operations_summary():
    """
    Get summary of all operations
    
    Query Parameters:
        - duration_minutes: Time window in minutes (optional)
    
    Returns:
        JSON with operation summaries
        
    Requirements: 15.4
    """
    try:
        collector = get_performance_metrics_collector()
        
        duration_minutes = request.args.get('duration_minutes', type=int)
        
        summary = collector.get_operation_summary(duration_minutes=duration_minutes)
        
        return jsonify({
            'success': True,
            'operations': summary
        })
        
    except Exception as e:
        logging_system.log_error("Failed to get operations summary", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_metrics_bp.route('/export/json', methods=['POST'])
def export_json():
    """
    Export all metrics to JSON file
    
    Returns:
        JSON with export file path
        
    Requirements: 15.4
    """
    try:
        collector = get_performance_metrics_collector()
        
        filepath = collector.export_to_json()
        
        return jsonify({
            'success': True,
            'filepath': filepath,
            'message': 'Metrics exported successfully'
        })
        
    except Exception as e:
        logging_system.log_error("Failed to export metrics to JSON", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_metrics_bp.route('/export/csv', methods=['POST'])
def export_csv():
    """
    Export specific metric type to CSV file
    
    Request Body:
        - metric_type: Type of metric ('processing', 'memory', 'gpu')
    
    Returns:
        JSON with export file path
        
    Requirements: 15.4
    """
    try:
        data = request.get_json() or {}
        metric_type = data.get('metric_type', 'processing')
        
        if metric_type not in ['processing', 'memory', 'gpu']:
            return jsonify({
                'success': False,
                'error': 'Invalid metric_type. Must be processing, memory, or gpu'
            }), 400
        
        collector = get_performance_metrics_collector()
        filepath = collector.export_to_csv(metric_type)
        
        return jsonify({
            'success': True,
            'filepath': filepath,
            'metric_type': metric_type,
            'message': 'Metrics exported successfully'
        })
        
    except Exception as e:
        logging_system.log_error("Failed to export metrics to CSV", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_metrics_bp.route('/export/download/<filename>', methods=['GET'])
def download_export(filename):
    """
    Download exported metrics file
    
    Args:
        filename: Name of the exported file
    
    Returns:
        File download
        
    Requirements: 15.4
    """
    try:
        collector = get_performance_metrics_collector()
        filepath = os.path.join(collector.config['export_directory'], filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        return send_file(filepath, as_attachment=True)
        
    except Exception as e:
        logging_system.log_error("Failed to download export file", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_metrics_bp.route('/count', methods=['GET'])
def get_metrics_count():
    """
    Get count of stored metrics
    
    Returns:
        JSON with metrics counts
    """
    try:
        collector = get_performance_metrics_collector()
        counts = collector.get_metrics_count()
        
        return jsonify({
            'success': True,
            'counts': counts
        })
        
    except Exception as e:
        logging_system.log_error("Failed to get metrics count", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_metrics_bp.route('/clear', methods=['POST'])
def clear_metrics():
    """
    Clear metrics history
    
    Request Body:
        - metric_type: Type to clear ('processing', 'memory', 'gpu', or null for all)
    
    Returns:
        JSON with success status
    """
    try:
        data = request.get_json() or {}
        metric_type = data.get('metric_type')
        
        if metric_type and metric_type not in ['processing', 'memory', 'gpu']:
            return jsonify({
                'success': False,
                'error': 'Invalid metric_type. Must be processing, memory, gpu, or null'
            }), 400
        
        collector = get_performance_metrics_collector()
        collector.clear_metrics(metric_type)
        
        return jsonify({
            'success': True,
            'message': f'Metrics cleared: {metric_type or "all"}'
        })
        
    except Exception as e:
        logging_system.log_error("Failed to clear metrics", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_metrics_bp.route('/monitoring/start', methods=['POST'])
def start_monitoring():
    """
    Start background metrics monitoring
    
    Returns:
        JSON with success status
        
    Requirements: 12.2
    """
    try:
        collector = get_performance_metrics_collector()
        collector.start_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'Metrics monitoring started'
        })
        
    except Exception as e:
        logging_system.log_error("Failed to start monitoring", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_metrics_bp.route('/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """
    Stop background metrics monitoring
    
    Returns:
        JSON with success status
    """
    try:
        collector = get_performance_metrics_collector()
        collector.stop_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'Metrics monitoring stopped'
        })
        
    except Exception as e:
        logging_system.log_error("Failed to stop monitoring", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@performance_metrics_bp.route('/config', methods=['GET', 'PUT'])
def manage_config():
    """
    Get or update metrics collector configuration
    
    GET: Returns current configuration
    PUT: Updates configuration
    
    Returns:
        JSON with configuration
    """
    try:
        collector = get_performance_metrics_collector()
        
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'config': collector.config
            })
        
        elif request.method == 'PUT':
            data = request.get_json() or {}
            success = collector.update_config(data)
            
            return jsonify({
                'success': success,
                'config': collector.config,
                'message': 'Configuration updated' if success else 'Failed to update configuration'
            })
        
    except Exception as e:
        logging_system.log_error("Failed to manage config", exception=e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
