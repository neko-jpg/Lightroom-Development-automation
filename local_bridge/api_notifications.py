"""
Push Notification API Endpoints
Handles push notification subscriptions and management
"""

import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from models.database import get_session
from models.database import PushSubscription

logger = logging.getLogger(__name__)

# Create blueprint
notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

# In-memory storage for subscriptions (for development)
# In production, this should be stored in database
subscriptions_store = []


@notifications_bp.route('/subscribe', methods=['POST'])
def subscribe():
    """
    Subscribe to push notifications
    
    Request body:
    {
        "endpoint": "https://...",
        "keys": {
            "p256dh": "...",
            "auth": "..."
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        endpoint = data.get('endpoint')
        keys = data.get('keys', {})
        
        if not endpoint:
            return jsonify({'error': 'Endpoint is required'}), 400
        
        # Check if subscription already exists
        existing = next((s for s in subscriptions_store if s['endpoint'] == endpoint), None)
        
        if existing:
            logger.info(f"Subscription already exists: {endpoint[:50]}...")
            return jsonify({
                'success': True,
                'message': 'Subscription already exists',
                'subscription': existing
            }), 200
        
        # Create new subscription
        subscription = {
            'endpoint': endpoint,
            'keys': keys,
            'created_at': datetime.utcnow().isoformat(),
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
        }
        
        subscriptions_store.append(subscription)
        
        logger.info(f"New push subscription added: {endpoint[:50]}...")
        
        return jsonify({
            'success': True,
            'message': 'Subscription created successfully',
            'subscription': subscription
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    """
    Unsubscribe from push notifications
    
    Request body:
    {
        "endpoint": "https://..."
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        endpoint = data.get('endpoint')
        
        if not endpoint:
            return jsonify({'error': 'Endpoint is required'}), 400
        
        # Find and remove subscription
        global subscriptions_store
        original_count = len(subscriptions_store)
        subscriptions_store = [s for s in subscriptions_store if s['endpoint'] != endpoint]
        
        if len(subscriptions_store) < original_count:
            logger.info(f"Subscription removed: {endpoint[:50]}...")
            return jsonify({
                'success': True,
                'message': 'Subscription removed successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Subscription not found'
            }), 404
        
    except Exception as e:
        logger.error(f"Failed to remove subscription: {e}")
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/settings', methods=['GET'])
def get_settings():
    """
    Get notification settings
    """
    try:
        # Return default settings
        settings = {
            'enabled': True,
            'types': {
                'processing_complete': True,
                'approval_required': True,
                'error': True,
                'export_complete': True,
            },
            'quiet_hours': {
                'enabled': False,
                'start': '22:00',
                'end': '08:00',
            },
        }
        
        return jsonify({
            'success': True,
            'settings': settings
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get notification settings: {e}")
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/settings', methods=['POST'])
def update_settings():
    """
    Update notification settings
    
    Request body:
    {
        "enabled": true,
        "types": {
            "processing_complete": true,
            "approval_required": true,
            "error": true,
            "export_complete": true
        },
        "quiet_hours": {
            "enabled": false,
            "start": "22:00",
            "end": "08:00"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # In production, save to database
        logger.info(f"Notification settings updated: {data}")
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'settings': data
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to update notification settings: {e}")
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/subscriptions', methods=['GET'])
def list_subscriptions():
    """
    List all active subscriptions (admin endpoint)
    """
    try:
        return jsonify({
            'success': True,
            'count': len(subscriptions_store),
            'subscriptions': [
                {
                    'endpoint': s['endpoint'][:50] + '...',
                    'created_at': s['created_at'],
                    'user_agent': s['user_agent'],
                }
                for s in subscriptions_store
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to list subscriptions: {e}")
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/track', methods=['POST'])
def track_notification():
    """
    Track notification interaction (click, dismiss, etc.)
    
    Request body:
    {
        "action": "clicked|dismissed",
        "notificationId": "...",
        "timestamp": "..."
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        action = data.get('action')
        notification_id = data.get('notificationId')
        
        logger.info(f"Notification {action}: {notification_id}")
        
        return jsonify({
            'success': True,
            'message': 'Tracking recorded'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to track notification: {e}")
        return jsonify({'error': str(e)}), 500


def send_push_notification(title, body, url='/', notification_type='general', data=None):
    """
    Send push notification to all subscribed clients
    
    Args:
        title: Notification title
        body: Notification body text
        url: URL to open when notification is clicked
        notification_type: Type of notification (general, processing, approval, error, export)
        data: Additional data to include
    """
    try:
        from pywebpush import webpush, WebPushException
        
        payload = {
            'title': title,
            'body': body,
            'url': url,
            'type': notification_type,
            'icon': '/logo192.png',
            'badge': '/logo192.png',
            'timestamp': datetime.utcnow().isoformat(),
            'data': data or {},
        }
        
        # Send to all subscriptions
        failed_subscriptions = []
        
        for subscription in subscriptions_store:
            try:
                webpush(
                    subscription_info={
                        'endpoint': subscription['endpoint'],
                        'keys': subscription['keys'],
                    },
                    data=json.dumps(payload),
                    vapid_private_key='YOUR_VAPID_PRIVATE_KEY',  # TODO: Load from config
                    vapid_claims={
                        'sub': 'mailto:your-email@example.com',  # TODO: Load from config
                    }
                )
                logger.info(f"Push notification sent: {title}")
                
            except WebPushException as e:
                logger.error(f"Failed to send push notification: {e}")
                if e.response and e.response.status_code in [404, 410]:
                    # Subscription is no longer valid
                    failed_subscriptions.append(subscription)
        
        # Remove failed subscriptions
        for failed in failed_subscriptions:
            subscriptions_store.remove(failed)
            logger.info(f"Removed invalid subscription: {failed['endpoint'][:50]}...")
        
        return True
        
    except ImportError:
        logger.warning("pywebpush not installed, push notifications disabled")
        return False
    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")
        return False
