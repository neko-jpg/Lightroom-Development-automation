"""
API endpoints for multi-model management.

Provides REST API for:
- Listing available models
- Switching models
- Downloading models
- Model metadata management
- Performance statistics

Requirements: 18.1, 18.2, 18.3, 18.4
"""

import logging
from flask import Blueprint, jsonify, request
from model_manager import ModelManager, ModelPurpose

logger = logging.getLogger(__name__)

# Create blueprint
model_bp = Blueprint('model', __name__, url_prefix='/api/model')

# Global model manager instance
model_manager = None


def init_model_api(manager: ModelManager):
    """
    Initialize model API with manager instance.
    
    Args:
        manager: ModelManager instance
    """
    global model_manager
    model_manager = manager
    logger.info("Model API initialized")


@model_bp.route('/list', methods=['GET'])
def list_models():
    """
    List available models with optional filtering.
    
    Query Parameters:
        purpose: Filter by purpose (speed/balanced/quality/specialized)
        max_vram: Filter by maximum VRAM requirement (GB)
        installed_only: Only show installed models (true/false)
    
    Returns:
        JSON response with model list
    """
    try:
        # Parse query parameters
        purpose_str = request.args.get('purpose')
        max_vram_str = request.args.get('max_vram')
        installed_only = request.args.get('installed_only', 'false').lower() == 'true'
        
        # Convert purpose string to enum
        purpose = None
        if purpose_str:
            try:
                purpose = ModelPurpose(purpose_str)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'Invalid purpose: {purpose_str}'
                }), 400
        
        # Convert max_vram to float
        max_vram = None
        if max_vram_str:
            try:
                max_vram = float(max_vram_str)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'Invalid max_vram: {max_vram_str}'
                }), 400
        
        # Get models
        models = model_manager.list_available_models(
            purpose=purpose,
            max_vram_gb=max_vram,
            installed_only=installed_only
        )
        
        # Convert to dict
        models_data = [model.to_dict() for model in models]
        
        return jsonify({
            'success': True,
            'models': models_data,
            'count': len(models_data)
        })
    
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_bp.route('/installed', methods=['GET'])
def list_installed():
    """
    List models installed in Ollama.
    
    Returns:
        JSON response with installed model names
    """
    try:
        installed = model_manager.list_installed_models()
        
        return jsonify({
            'success': True,
            'models': installed,
            'count': len(installed)
        })
    
    except Exception as e:
        logger.error(f"Error listing installed models: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_bp.route('/current', methods=['GET'])
def get_current():
    """
    Get currently selected model.
    
    Returns:
        JSON response with current model info
    """
    try:
        current = model_manager.get_current_model()
        
        if not current:
            return jsonify({
                'success': False,
                'error': 'No model selected'
            }), 404
        
        info = model_manager.get_model_info(current)
        
        return jsonify({
            'success': True,
            'model': current,
            'info': info.to_dict() if info else None
        })
    
    except Exception as e:
        logger.error(f"Error getting current model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_bp.route('/info/<model_name>', methods=['GET'])
def get_info(model_name: str):
    """
    Get detailed information about a model.
    
    Args:
        model_name: Model name
    
    Returns:
        JSON response with model info
    """
    try:
        info = model_manager.get_model_info(model_name)
        
        if not info:
            return jsonify({
                'success': False,
                'error': f'Model not found: {model_name}'
            }), 404
        
        return jsonify({
            'success': True,
            'model': info.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_bp.route('/switch', methods=['POST'])
def switch_model():
    """
    Switch to a different model.
    
    Request Body:
        {
            "model": "model_name"
        }
    
    Returns:
        JSON response with success status
    """
    try:
        data = request.get_json()
        
        if not data or 'model' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing model parameter'
            }), 400
        
        model_name = data['model']
        
        success = model_manager.switch_model(model_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Switched to model: {model_name}',
                'model': model_name
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to switch to model: {model_name}'
            }), 400
    
    except Exception as e:
        logger.error(f"Error switching model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_bp.route('/download', methods=['POST'])
def download_model():
    """
    Download a model from Ollama.
    
    Request Body:
        {
            "model": "model_name"
        }
    
    Returns:
        JSON response with download status
    """
    try:
        data = request.get_json()
        
        if not data or 'model' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing model parameter'
            }), 400
        
        model_name = data['model']
        
        # Start download (this is synchronous for now)
        # In production, this should be async with progress updates via WebSocket
        success, message = model_manager.download_model(model_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'model': model_name
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
    
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_bp.route('/delete', methods=['DELETE'])
def delete_model():
    """
    Delete a model from Ollama.
    
    Request Body:
        {
            "model": "model_name"
        }
    
    Returns:
        JSON response with deletion status
    """
    try:
        data = request.get_json()
        
        if not data or 'model' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing model parameter'
            }), 400
        
        model_name = data['model']
        
        success, message = model_manager.delete_model(model_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'model': model_name
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
    
    except Exception as e:
        logger.error(f"Error deleting model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_bp.route('/recommend', methods=['POST'])
def recommend_model():
    """
    Get model recommendation based on resources and priority.
    
    Request Body:
        {
            "available_vram_gb": 8.0,
            "priority": "balanced"  // "speed", "balanced", "quality"
        }
    
    Returns:
        JSON response with recommended model
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing request body'
            }), 400
        
        available_vram = data.get('available_vram_gb', 8.0)
        priority = data.get('priority', 'balanced')
        
        if priority not in ['speed', 'balanced', 'quality']:
            return jsonify({
                'success': False,
                'error': f'Invalid priority: {priority}'
            }), 400
        
        recommended = model_manager.recommend_model(available_vram, priority)
        
        if recommended:
            info = model_manager.get_model_info(recommended)
            
            return jsonify({
                'success': True,
                'recommended_model': recommended,
                'info': info.to_dict() if info else None,
                'criteria': {
                    'available_vram_gb': available_vram,
                    'priority': priority
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No suitable model found',
                'criteria': {
                    'available_vram_gb': available_vram,
                    'priority': priority
                }
            }), 404
    
    except Exception as e:
        logger.error(f"Error recommending model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_bp.route('/check_compatibility', methods=['POST'])
def check_compatibility():
    """
    Check if a model is compatible with available resources.
    
    Request Body:
        {
            "model": "model_name",
            "available_vram_gb": 8.0
        }
    
    Returns:
        JSON response with compatibility status
    """
    try:
        data = request.get_json()
        
        if not data or 'model' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing model parameter'
            }), 400
        
        model_name = data['model']
        available_vram = data.get('available_vram_gb', 8.0)
        
        compatible, message = model_manager.check_model_compatibility(
            model_name,
            available_vram
        )
        
        return jsonify({
            'success': True,
            'compatible': compatible,
            'message': message,
            'model': model_name,
            'available_vram_gb': available_vram
        })
    
    except Exception as e:
        logger.error(f"Error checking compatibility: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """
    Get usage statistics for all models.
    
    Query Parameters:
        model: Optional model name for specific model stats
    
    Returns:
        JSON response with statistics
    """
    try:
        model_name = request.args.get('model')
        
        if model_name:
            stats = model_manager.get_model_statistics(model_name)
            
            if not stats:
                return jsonify({
                    'success': False,
                    'error': f'Model not found: {model_name}'
                }), 404
            
            return jsonify({
                'success': True,
                'model': model_name,
                'statistics': stats
            })
        else:
            stats = model_manager.get_all_statistics()
            
            return jsonify({
                'success': True,
                'statistics': stats,
                'count': len(stats)
            })
    
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_bp.route('/sync', methods=['POST'])
def sync_models():
    """
    Sync model list with Ollama server.
    
    Returns:
        JSON response with sync status
    """
    try:
        model_manager._sync_with_ollama()
        
        installed = model_manager.list_installed_models()
        
        return jsonify({
            'success': True,
            'message': 'Models synced successfully',
            'installed_count': len(installed)
        })
    
    except Exception as e:
        logger.error(f"Error syncing models: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_bp.route('/export', methods=['POST'])
def export_metadata():
    """
    Export model metadata to a file.
    
    Request Body:
        {
            "output_file": "path/to/file.json"
        }
    
    Returns:
        JSON response with export status
    """
    try:
        data = request.get_json()
        
        if not data or 'output_file' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing output_file parameter'
            }), 400
        
        output_file = data['output_file']
        
        model_manager.export_metadata(output_file)
        
        return jsonify({
            'success': True,
            'message': f'Metadata exported to: {output_file}',
            'output_file': output_file
        })
    
    except Exception as e:
        logger.error(f"Error exporting metadata: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@model_bp.route('/import', methods=['POST'])
def import_metadata():
    """
    Import model metadata from a file.
    
    Request Body:
        {
            "input_file": "path/to/file.json"
        }
    
    Returns:
        JSON response with import status
    """
    try:
        data = request.get_json()
        
        if not data or 'input_file' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing input_file parameter'
            }), 400
        
        input_file = data['input_file']
        
        model_manager.import_metadata(input_file)
        
        return jsonify({
            'success': True,
            'message': f'Metadata imported from: {input_file}',
            'input_file': input_file
        })
    
    except Exception as e:
        logger.error(f"Error importing metadata: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
