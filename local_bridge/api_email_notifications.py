"""
Email Notification API Endpoints
Handles email notification configuration and sending
"""

import logging
from flask import Blueprint, request, jsonify
from email_notifier import get_email_notifier, EmailNotificationType

logger = logging.getLogger(__name__)

# Create blueprint
email_notifications_bp = Blueprint('email_notifications', __name__, url_prefix='/email-notifications')


@email_notifications_bp.route('/config', methods=['GET'])
def get_config():
    """
    Get email notification configuration
    
    Returns:
        JSON response with configuration
    """
    try:
        notifier = get_email_notifier()
        config = notifier.get_config()
        
        # Remove sensitive information
        safe_config = config.copy()
        if 'password' in safe_config:
            safe_config['password'] = '***' if safe_config['password'] else ''
        
        return jsonify({
            'success': True,
            'config': safe_config
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get email configuration: {e}")
        return jsonify({'error': str(e)}), 500


@email_notifications_bp.route('/config', methods=['POST'])
def update_config():
    """
    Update email notification configuration
    
    Request body:
    {
        "enabled": true,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "use_tls": true,
        "username": "user@example.com",
        "password": "password",
        "from_address": "user@example.com",
        "from_name": "Junmai AutoDev",
        "to_addresses": ["recipient@example.com"],
        "batch_notifications": {
            "enabled": true,
            "interval_minutes": 60,
            "min_notifications": 3
        },
        "notification_types": {
            "processing_complete": true,
            "approval_required": true,
            "error": true,
            "export_complete": false,
            "batch_complete": true,
            "daily_summary": true,
            "weekly_summary": true
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        notifier = get_email_notifier()
        notifier.update_config(data)
        
        logger.info("Email notification configuration updated")
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to update email configuration: {e}")
        return jsonify({'error': str(e)}), 500


@email_notifications_bp.route('/test', methods=['POST'])
def test_connection():
    """
    Test SMTP connection
    
    Returns:
        JSON response with test result
    """
    try:
        notifier = get_email_notifier()
        
        if not notifier.config.is_enabled():
            return jsonify({
                'success': False,
                'message': 'Email notifications are disabled'
            }), 400
        
        success = notifier.test_connection()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'SMTP connection successful'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'SMTP connection failed'
            }), 500
        
    except Exception as e:
        logger.error(f"Failed to test SMTP connection: {e}")
        return jsonify({'error': str(e)}), 500


@email_notifications_bp.route('/send-test', methods=['POST'])
def send_test_email():
    """
    Send test email
    
    Request body:
    {
        "to_address": "recipient@example.com"  // Optional, uses config if not provided
    }
    """
    try:
        data = request.get_json() or {}
        to_address = data.get('to_address')
        
        notifier = get_email_notifier()
        
        if not notifier.config.is_enabled():
            return jsonify({
                'success': False,
                'message': 'Email notifications are disabled'
            }), 400
        
        # Send test email
        to_addresses = [to_address] if to_address else None
        success = notifier.send(
            to_addresses=to_addresses,
            subject='Junmai AutoDev - テストメール',
            html_body='<html><body><h2>テストメール</h2><p>メール通知が正常に設定されています。</p></body></html>',
            text_body='テストメール\n\nメール通知が正常に設定されています。',
            notification_type=EmailNotificationType.PROCESSING_COMPLETE
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Test email sent successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send test email'
            }), 500
        
    except Exception as e:
        logger.error(f"Failed to send test email: {e}")
        return jsonify({'error': str(e)}), 500


@email_notifications_bp.route('/send/processing-complete', methods=['POST'])
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
        
        notifier = get_email_notifier()
        success = notifier.send_processing_complete(
            session_name=data.get('session_name', 'Unknown'),
            photo_count=data.get('photo_count', 0),
            success_rate=data.get('success_rate', 0.0),
            processing_time=data.get('processing_time', '0s')
        )
        
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
        logger.error(f"Failed to send processing complete notification: {e}")
        return jsonify({'error': str(e)}), 500


@email_notifications_bp.route('/send/approval-required', methods=['POST'])
def send_approval_required():
    """
    Send approval required notification
    
    Request body:
    {
        "pending_count": 15,
        "sessions": [
            {"name": "Session 1", "count": 10},
            {"name": "Session 2", "count": 5}
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        notifier = get_email_notifier()
        success = notifier.send_approval_required(
            pending_count=data.get('pending_count', 0),
            sessions=data.get('sessions', [])
        )
        
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
        logger.error(f"Failed to send approval required notification: {e}")
        return jsonify({'error': str(e)}), 500


@email_notifications_bp.route('/send/error', methods=['POST'])
def send_error():
    """
    Send error notification
    
    Request body:
    {
        "error_type": "Processing Error",
        "error_message": "Failed to process photo",
        "error_details": "GPU memory exceeded"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        notifier = get_email_notifier()
        success = notifier.send_error(
            error_type=data.get('error_type', 'Unknown Error'),
            error_message=data.get('error_message', 'An error occurred'),
            error_details=data.get('error_details')
        )
        
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
        logger.error(f"Failed to send error notification: {e}")
        return jsonify({'error': str(e)}), 500


@email_notifications_bp.route('/send/export-complete', methods=['POST'])
def send_export_complete():
    """
    Send export complete notification
    
    Request body:
    {
        "export_preset": "SNS",
        "photo_count": 50,
        "destination": "/path/to/export"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        notifier = get_email_notifier()
        success = notifier.send_export_complete(
            export_preset=data.get('export_preset', 'Unknown'),
            photo_count=data.get('photo_count', 0),
            destination=data.get('destination', 'Unknown')
        )
        
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
        logger.error(f"Failed to send export complete notification: {e}")
        return jsonify({'error': str(e)}), 500


@email_notifications_bp.route('/send/batch-complete', methods=['POST'])
def send_batch_complete():
    """
    Send batch complete notification
    
    Request body:
    {
        "batch_name": "Evening Batch",
        "total_photos": 200,
        "processing_time": "3h 45m",
        "avg_time_per_photo": "1.1s"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        notifier = get_email_notifier()
        success = notifier.send_batch_complete(
            batch_name=data.get('batch_name', 'Unknown'),
            total_photos=data.get('total_photos', 0),
            processing_time=data.get('processing_time', '0s'),
            avg_time_per_photo=data.get('avg_time_per_photo', '0s')
        )
        
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
        logger.error(f"Failed to send batch complete notification: {e}")
        return jsonify({'error': str(e)}), 500


@email_notifications_bp.route('/send/daily-summary', methods=['POST'])
def send_daily_summary():
    """
    Send daily summary notification
    
    Request body:
    {
        "date": "2025-11-08",
        "total_imported": 150,
        "total_selected": 120,
        "total_processed": 100,
        "total_exported": 80,
        "avg_processing_time": "2.3s",
        "success_rate": 95.5
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        notifier = get_email_notifier()
        success = notifier.send_daily_summary(
            date=data.get('date', 'Unknown'),
            total_imported=data.get('total_imported', 0),
            total_selected=data.get('total_selected', 0),
            total_processed=data.get('total_processed', 0),
            total_exported=data.get('total_exported', 0),
            avg_processing_time=data.get('avg_processing_time', '0s'),
            success_rate=data.get('success_rate', 0.0)
        )
        
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
        logger.error(f"Failed to send daily summary notification: {e}")
        return jsonify({'error': str(e)}), 500


@email_notifications_bp.route('/send/weekly-summary', methods=['POST'])
def send_weekly_summary():
    """
    Send weekly summary notification
    
    Request body:
    {
        "week_range": "2025-11-01 ~ 2025-11-07",
        "total_imported": 1000,
        "total_processed": 800,
        "total_exported": 600,
        "avg_success_rate": 95.0,
        "top_preset": "WhiteLayer_v4",
        "daily_breakdown": [
            {"date": "2025-11-01", "processed": 120},
            {"date": "2025-11-02", "processed": 150}
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        notifier = get_email_notifier()
        success = notifier.send_weekly_summary(
            week_range=data.get('week_range', 'Unknown'),
            total_imported=data.get('total_imported', 0),
            total_processed=data.get('total_processed', 0),
            total_exported=data.get('total_exported', 0),
            avg_success_rate=data.get('avg_success_rate', 0.0),
            top_preset=data.get('top_preset', 'Unknown'),
            daily_breakdown=data.get('daily_breakdown', [])
        )
        
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
        logger.error(f"Failed to send weekly summary notification: {e}")
        return jsonify({'error': str(e)}), 500
