"""
API endpoints for model performance statistics.

Provides REST API for:
- Recording model performance
- Retrieving model statistics
- Comparing models
- Getting model recommendations

Requirements: 18.5
"""

from flask import Blueprint, request, jsonify
import logging
from typing import Optional

from model_performance_stats import get_model_performance_stats

logger = logging.getLogger(__name__)

# Create blueprint
model_performance_bp = Blueprint('model_performance', __name__, url_prefix='/api/model-performance')


@model_performance_bp.route('/record', methods=['POST'])
def record_performance():
    """
    Record model performance metrics.
    
    POST /api/model-performance/record
    Body: {
        "model_name": "llama3.1:8b-instruct",
        "operation": "photo_evaluation",
        "processing_time_ms": 1234.56,
        "quality_score": 4.2,
        "success": true,
        "memory_used_mb": 512.0,
        "tokens_generated": 150,
        "photo_id": 123,
        "job_id": "job_abc123"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'model_name' not in data or 'operation' not in data or 'processing_time_ms' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: model_name, operation, processing_time_ms'
            }), 400
        
        collector = get_model_performance_stats()
        
        collector.record_model_performance(
            model_name=data['model_name'],
            operation=data['operation'],
            processing_time_ms=data['processing_time_ms'],
            quality_score=data.get('quality_score'),
            success=data.get('success', True),
            error_message=data.get('error_message'),
            memory_used_mb=data.get('memory_used_mb'),
            tokens_generated=data.get('tokens_generated'),
            photo_id=data.get('photo_id'),
            job_id=data.get('job_id')
        )
        
        return jsonify({
            'success': True,
            'message': 'Performance recorded'
        })
    
    except Exception as e:
        logger.error(f"Error recording performance: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_performance_bp.route('/statistics/<model_name>', methods=['GET'])
def get_statistics(model_name: str):
    """
    Get statistics for a specific model.
    
    GET /api/model-performance/statistics/<model_name>?duration_hours=24&operation=photo_evaluation
    """
    try:
        duration_hours = request.args.get('duration_hours', type=int)
        operation = request.args.get('operation')
        
        collector = get_model_performance_stats()
        stats = collector.get_model_statistics(model_name, duration_hours, operation)
        
        if not stats:
            return jsonify({
                'success': False,
                'error': f'No statistics found for model: {model_name}'
            }), 404
        
        return jsonify({
            'success': True,
            'statistics': stats.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_performance_bp.route('/statistics', methods=['GET'])
def get_all_statistics():
    """
    Get statistics for all models.
    
    GET /api/model-performance/statistics?duration_hours=24&operation=photo_evaluation
    """
    try:
        duration_hours = request.args.get('duration_hours', type=int)
        operation = request.args.get('operation')
        
        collector = get_model_performance_stats()
        all_stats = collector.get_all_model_statistics(duration_hours, operation)
        
        return jsonify({
            'success': True,
            'statistics': {
                name: stats.to_dict()
                for name, stats in all_stats.items()
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting all statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_performance_bp.route('/compare', methods=['POST'])
def compare_models():
    """
    Compare performance between multiple models.
    
    POST /api/model-performance/compare
    Body: {
        "models": ["llama3.1:8b-instruct", "llama3.1:13b-instruct"],
        "duration_hours": 24,
        "operation": "photo_evaluation"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'models' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: models'
            }), 400
        
        models = data['models']
        duration_hours = data.get('duration_hours')
        operation = data.get('operation')
        
        collector = get_model_performance_stats()
        comparison = collector.compare_models(models, duration_hours, operation)
        
        return jsonify({
            'success': True,
            'comparison': comparison
        })
    
    except Exception as e:
        logger.error(f"Error comparing models: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_performance_bp.route('/recommend', methods=['GET'])
def recommend_model():
    """
    Get model recommendation based on performance.
    
    GET /api/model-performance/recommend?priority=balanced&duration_hours=24&min_operations=10
    """
    try:
        priority = request.args.get('priority', 'balanced')
        duration_hours = request.args.get('duration_hours', type=int, default=24)
        min_operations = request.args.get('min_operations', type=int, default=10)
        
        # Get available models from query param (comma-separated)
        available_models_str = request.args.get('available_models')
        available_models = None
        if available_models_str:
            available_models = [m.strip() for m in available_models_str.split(',')]
        
        collector = get_model_performance_stats()
        recommended = collector.recommend_model(
            priority=priority,
            available_models=available_models,
            duration_hours=duration_hours,
            min_operations=min_operations
        )
        
        if not recommended:
            return jsonify({
                'success': False,
                'error': 'No suitable model found with sufficient performance history'
            }), 404
        
        # Get stats for recommended model
        stats = collector.get_model_statistics(recommended, duration_hours)
        
        return jsonify({
            'success': True,
            'recommended_model': recommended,
            'priority': priority,
            'statistics': stats.to_dict() if stats else None
        })
    
    except Exception as e:
        logger.error(f"Error recommending model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_performance_bp.route('/trend/<model_name>', methods=['GET'])
def get_performance_trend(model_name: str):
    """
    Get performance trend over time for a model.
    
    GET /api/model-performance/trend/<model_name>?metric=processing_time&hours=24&bucket_size_minutes=60
    """
    try:
        metric = request.args.get('metric', 'processing_time')
        hours = request.args.get('hours', type=int, default=24)
        bucket_size_minutes = request.args.get('bucket_size_minutes', type=int, default=60)
        
        collector = get_model_performance_stats()
        trend = collector.get_model_performance_trend(
            model_name=model_name,
            metric=metric,
            hours=hours,
            bucket_size_minutes=bucket_size_minutes
        )
        
        if 'error' in trend:
            return jsonify({
                'success': False,
                'error': trend['error']
            }), 404
        
        return jsonify({
            'success': True,
            'trend': trend
        })
    
    except Exception as e:
        logger.error(f"Error getting performance trend: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_performance_bp.route('/export', methods=['GET'])
def export_statistics():
    """
    Export all model statistics.
    
    GET /api/model-performance/export
    """
    try:
        collector = get_model_performance_stats()
        all_stats = collector.get_all_model_statistics()
        
        data = {
            'models': {
                name: stats.to_dict()
                for name, stats in all_stats.items()
            },
            'comparison': collector.compare_models(list(all_stats.keys()))
        }
        
        return jsonify({
            'success': True,
            'data': data
        })
    
    except Exception as e:
        logger.error(f"Error exporting statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_performance_bp.route('/clear/<model_name>', methods=['DELETE'])
def clear_model_data(model_name: str):
    """
    Clear performance data for a specific model.
    
    DELETE /api/model-performance/clear/<model_name>
    """
    try:
        collector = get_model_performance_stats()
        collector.clear_model_data(model_name)
        
        return jsonify({
            'success': True,
            'message': f'Performance data cleared for model: {model_name}'
        })
    
    except Exception as e:
        logger.error(f"Error clearing model data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_performance_bp.route('/clear-old', methods=['POST'])
def clear_old_data():
    """
    Clear old performance data.
    
    POST /api/model-performance/clear-old
    Body: {
        "days": 30
    }
    """
    try:
        data = request.get_json()
        days = data.get('days', 30) if data else 30
        
        collector = get_model_performance_stats()
        collector.clear_old_data(days)
        
        return jsonify({
            'success': True,
            'message': f'Cleared data older than {days} days'
        })
    
    except Exception as e:
        logger.error(f"Error clearing old data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def register_model_performance_api(app):
    """
    Register model performance API blueprint with Flask app.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(model_performance_bp)
    logger.info("Model performance API registered")
