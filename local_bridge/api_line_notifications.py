"""
LINE Notify API Endpoints
Handles LINE notification configuration and sending
"""

import logging
from flask import Blueprint, request, jsonify
from line_notifier import get_line_notifier, LineNotificationType

logger = logging.getLogger(__name__)

# Create blueprint
line_notifications_bp = Blueprint('line_notifications', __name__, url_prefix='/api/line')


@line_notifications_bp.route('/config', methods=['GET'])
def get_config():
    """
    Get LINE Notify configuration
    
    Returns:
        JSON response with configuration
    """
    try:
        notifier = get_line_notifier()
        config = notifier.get_config()
        
        # Remove sensitive token from response
        safe_config = config.copy()
        if safe_config.get('token'):
            safe_config['token'] = '***' + safe_config['token'][-4:] if len(safe_config['token']) > 4 else '***'
        
        return jsonify({
            'success': True,
            'config': safe_config
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get LINE config: {e}")
        return jsonify({'error': str(e)}), 500


@line_notifications_bp.route('/config', methods=['POST'])
def update_config():
    """
    Update LINE Notify configuration
    
    Request body:
    {
        "enabled": true,
        "token": "YOUR_LINE_NOTIFY_TOKEN",
        "notification_types": {
            "processing_complete": true,
            "approval_required": true,
            "error": true,
            "export_complete": false,
            "batch_complete": true,
            "system_status": false
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        notifier = get_line_notifier()
        notifier.update_config(data)
        
        logger.info("LINE Notify configuration updated")
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to update LINE config: {e}")
        return jsonify({'error': str(e)}), 500


@line_notifications_bp.route('/test', methods=['POST'])
def test_connection():
    """
    Test LINE Notify connection
    
    Returns:
        JSON response with test result
    """
    try:
        notifier = get_line_notifier()
        
        if not notifier.token_manager.is_enabled():
            return jsonify({
                'success': False,
                'message': 'LINE Notify is not enabled or token not configured'
            }), 400
        
        # Check token status
        status = notifier.check_token_status()
        
        if status and status.get('status') == 200:
            # Send test notification
            test_success = notifier.send(
                message="テスト通知: Junmai AutoDev からの接続テストです",
                notification_type=LineNotificationType.SYSTEM_STATUS
            )
            
            if test_success:
                return jsonify({
                    'success': True,
                    'message': 'Connection test successful',
                    'status': status
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to send test notification'
                }), 500
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid token or connection failed',
                'status': status
            }), 400
        
    except Exception as e:
        logger.error(f"Failed to test LINE connection: {e}")
        return jsonify({'error': str(e)}), 500


@line_notifications_bp.route('/status', methods=['GET'])
def get_status():
    """
    Get LINE Notify token status
    
    Returns:
        JSON response with token status
    """
    try:
        notifier = get_line_notifier()
        
        if not notifier.token_manager.is_enabled():
            return jsonify({
                'success': False,
                'message': 'LINE Notify is not enabled or token not configured'
            }), 400
        
        status = notifier.check_token_status()
        
        if status:
            return jsonify({
                'success': True,
                'status': status
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to check token status'
            }), 500
        
    except Exception as e:
        logger.error(f"Failed to get LINE status: {e}")
        return jsonify({'error': str(e)}), 500


@line_notifications_bp.route('/send', methods=['POST'])
def send_notification():
    """
    Send LINE notification
    
    Request body:
    {
        "type": "processing_complete",
        "data": {
            "session_name": "2025-11-08_Wedding",
            "photo_count": 120,
            "success_rate": 95.5,
            "processing_time": "2h 15m"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        notification_type_str = data.get('type')
        notification_data = data.get('data', {})
        
        if not notification_type_str:
            return jsonify({'error': 'Notification type is required'}), 400
        
        # Convert string to enum
        try:
            notification_type = LineNotificationType(notification_type_str)
        except ValueError:
            return jsonify({'error': f'Invalid notification type: {notification_type_str}'}), 400
        
        notifier = get_line_notifier()
        success = notifier.send_with_data(notification_type, notification_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notification sent successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send notification'
            }), 500
        
    except Exception as e:
        logger.error(f"Failed to send LINE notification: {e}")
        return jsonify({'error': str(e)}), 500


@line_notifications_bp.route('/send/processing-complete', methods=['POST'])
def send_processing_complete():
    """
    Send processing complete notification
    
    Request body:
    {
        "session_name": "2025-11-08_Wedding",
        "photo_count": 120,
        "success_rate": 95.5,
        "processing_time": "2h 15m"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        notifier = get_line_notifier()
        success = notifier.send_processing_complete(
            session_name=data.get('session_name', 'Unknown'),
            photo_count=data.get('photo_count', 0),
            success_rate=data.get('success_rate', 0.0),
            processing_time=data.get('processing_time', 'Unknown')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Processing complete notification sent'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send notification'
            }), 500
        
    except Exception as e:
        logger.error(f"Failed to send processing complete notification: {e}")
        return jsonify({'error': str(e)}), 500


@line_notifications_bp.route('/send/approval-required', methods=['POST'])
def send_approval_required():
    """
    Send approval required notification
    
    Request body:
    {
        "pending_count": 65,
        "sessions": [
            {"name": "2025-11-08_Wedding", "count": 45},
            {"name": "2025-11-07_Portrait", "count": 20}
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        notifier = get_line_notifier()
        success = notifier.send_approval_required(
            pending_count=data.get('pending_count', 0),
            sessions=data.get('sessions', [])
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Approval required notification sent'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send notification'
            }), 500
        
    except Exception as e:
        logger.error(f"Failed to send approval required notification: {e}")
        return jsonify({'error': str(e)}), 500


@line_notifications_bp.route('/send/error', methods=['POST'])
def send_error():
    """
    Send error notification
    
    Request body:
    {
        "error_type": "GPU Memory Error",
        "error_message": "GPU memory exceeded",
        "error_details": "Failed to allocate memory"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        notifier = get_line_notifier()
        success = notifier.send_error(
            error_type=data.get('error_type', 'Unknown Error'),
            error_message=data.get('error_message', 'An error occurred'),
            error_details=data.get('error_details')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Error notification sent'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send notification'
            }), 500
        
    except Exception as e:
        logger.error(f"Failed to send error notification: {e}")
        return jsonify({'error': str(e)}), 500


@line_notifications_bp.route('/send/export-complete', methods=['POST'])
def send_export_complete():
    """
    Send export complete notification
    
    Request body:
    {
        "export_preset": "SNS_2048px",
        "photo_count": 45,
        "destination": "D:/Export/SNS"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        notifier = get_line_notifier()
        success = notifier.send_export_complete(
            export_preset=data.get('export_preset', 'Unknown'),
            photo_count=data.get('photo_count', 0),
            destination=data.get('destination', 'Unknown')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Export complete notification sent'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send notification'
            }), 500
        
    except Exception as e:
        logger.error(f"Failed to send export complete notification: {e}")
        return jsonify({'error': str(e)}), 500


@line_notifications_bp.route('/send/batch-complete', methods=['POST'])
def send_batch_complete():
    """
    Send batch complete notification
    
    Request body:
    {
        "batch_name": "Wedding_Batch_001",
        "total_photos": 120,
        "processing_time": "2h 15m",
        "avg_time_per_photo": "1.1s"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        notifier = get_line_notifier()
        success = notifier.send_batch_complete(
            batch_name=data.get('batch_name', 'Unknown'),
            total_photos=data.get('total_photos', 0),
            processing_time=data.get('processing_time', 'Unknown'),
            avg_time_per_photo=data.get('avg_time_per_photo', 'Unknown')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Batch complete notification sent'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send notification'
            }), 500
        
    except Exception as e:
        logger.error(f"Failed to send batch complete notification: {e}")
        return jsonify({'error': str(e)}), 500


@line_notifications_bp.route('/rate-limit', methods=['GET'])
def get_rate_limit():
    """
    Get current rate limit status
    
    Returns:
        JSON response with rate limit information
    """
    try:
        notifier = get_line_notifier()
        rate_limit = notifier.token_manager.config.get('rate_limit', {})
        
        return jsonify({
            'success': True,
            'rate_limit': {
                'max_per_hour': rate_limit.get('max_per_hour', 50),
                'current_count': rate_limit.get('current_count', 0),
                'reset_time': rate_limit.get('reset_time'),
                'can_send': notifier.token_manager.check_rate_limit()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get rate limit: {e}")
        return jsonify({'error': str(e)}), 500
