"""
Desktop Notification API Endpoints
Handles desktop notification management and history
"""

import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from models.database import get_session, DesktopNotification
from desktop_notifier import (
    get_notifier,
    NotificationType,
    NotificationPriority
)

logger = logging.getLogger(__name__)

# Create blueprint
desktop_notifications_bp = Blueprint('desktop_notifications', __name__, url_prefix='/desktop-notifications')


@desktop_notifications_bp.route('/send', methods=['POST'])
def send_notification():
    """
    Send desktop notification
    
    Request body:
    {
        "title": "Notification Title",
        "message": "Notification message",
        "type": "processing_complete|approval_required|error|export_complete|batch_complete|system_status",
        "priority": 1|2|3,
        "duration": 5,
        "sound": true,
        "data": {}
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        title = data.get('title')
        message = data.get('message')
        
        if not title or not message:
            return jsonify({'error': 'Title and message are required'}), 400
        
        # Parse notification type
        notification_type_str = data.get('type', 'system_status')
        try:
            notification_type = NotificationType(notification_type_str)
        except ValueError:
            return jsonify({'error': f'Invalid notification type: {notification_type_str}'}), 400
        
        # Parse priority
        priority_value = data.get('priority', 2)
        try:
            priority = NotificationPriority(priority_value)
        except ValueError:
            return jsonify({'error': f'Invalid priority: {priority_value}'}), 400
        
        # Get optional parameters
        duration = data.get('duration', 5)
        sound = data.get('sound', True)
        notification_data = data.get('data', {})
        
        # Send notification
        notifier = get_notifier()
        success = notifier.send(
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            duration=duration,
            sound=sound,
            data=notification_data
        )
        
        # Save to database
        db = get_session()
        try:
            db_notification = DesktopNotification(
                title=title,
                message=message,
                notification_type=notification_type.value,
                priority=priority.value,
                sent_at=datetime.utcnow()
            )
            db_notification.set_data(notification_data)
            db.add(db_notification)
            db.commit()
            
            notification_id = db_notification.id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save notification to database: {e}")
            notification_id = None
        finally:
            db.close()
        
        return jsonify({
            'success': success,
            'message': 'Notification sent' if success else 'Failed to send notification',
            'notification_id': notification_id
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        return jsonify({'error': str(e)}), 500


@desktop_notifications_bp.route('/history', methods=['GET'])
def get_history():
    """
    Get notification history
    
    Query parameters:
    - limit: Maximum number of notifications (default: 50)
    - type: Filter by notification type
    - priority: Filter by priority (1, 2, or 3)
    - unread: Filter unread notifications (true/false)
    - days: Get notifications from last N days
    """
    try:
        limit = int(request.args.get('limit', 50))
        notification_type = request.args.get('type')
        priority = request.args.get('priority')
        unread_only = request.args.get('unread', '').lower() == 'true'
        days = request.args.get('days')
        
        db = get_session()
        try:
            query = db.query(DesktopNotification)
            
            # Apply filters
            if notification_type:
                query = query.filter(DesktopNotification.notification_type == notification_type)
            
            if priority:
                query = query.filter(DesktopNotification.priority == int(priority))
            
            if unread_only:
                query = query.filter(DesktopNotification.read == False)
            
            if days:
                cutoff_date = datetime.utcnow() - timedelta(days=int(days))
                query = query.filter(DesktopNotification.sent_at >= cutoff_date)
            
            # Order by most recent first
            query = query.order_by(DesktopNotification.sent_at.desc())
            
            # Apply limit
            notifications = query.limit(limit).all()
            
            return jsonify({
                'success': True,
                'count': len(notifications),
                'notifications': [n.to_dict() for n in notifications]
            }), 200
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Failed to get notification history: {e}")
        return jsonify({'error': str(e)}), 500


@desktop_notifications_bp.route('/history/<int:notification_id>', methods=['GET'])
def get_notification(notification_id):
    """Get specific notification by ID"""
    try:
        db = get_session()
        try:
            notification = db.query(DesktopNotification).filter(
                DesktopNotification.id == notification_id
            ).first()
            
            if not notification:
                return jsonify({'error': 'Notification not found'}), 404
            
            return jsonify({
                'success': True,
                'notification': notification.to_dict()
            }), 200
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Failed to get notification: {e}")
        return jsonify({'error': str(e)}), 500


@desktop_notifications_bp.route('/history/<int:notification_id>/read', methods=['POST'])
def mark_as_read(notification_id):
    """Mark notification as read"""
    try:
        db = get_session()
        try:
            notification = db.query(DesktopNotification).filter(
                DesktopNotification.id == notification_id
            ).first()
            
            if not notification:
                return jsonify({'error': 'Notification not found'}), 404
            
            notification.read = True
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'Notification marked as read'
            }), 200
            
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}")
        return jsonify({'error': str(e)}), 500


@desktop_notifications_bp.route('/history/<int:notification_id>/dismiss', methods=['POST'])
def dismiss_notification(notification_id):
    """Dismiss notification"""
    try:
        db = get_session()
        try:
            notification = db.query(DesktopNotification).filter(
                DesktopNotification.id == notification_id
            ).first()
            
            if not notification:
                return jsonify({'error': 'Notification not found'}), 404
            
            notification.dismissed = True
            notification.read = True
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'Notification dismissed'
            }), 200
            
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Failed to dismiss notification: {e}")
        return jsonify({'error': str(e)}), 500


@desktop_notifications_bp.route('/history/mark-all-read', methods=['POST'])
def mark_all_as_read():
    """Mark all notifications as read"""
    try:
        db = get_session()
        try:
            updated_count = db.query(DesktopNotification).filter(
                DesktopNotification.read == False
            ).update({'read': True})
            
            db.commit()
            
            return jsonify({
                'success': True,
                'message': f'Marked {updated_count} notifications as read',
                'count': updated_count
            }), 200
            
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Failed to mark all as read: {e}")
        return jsonify({'error': str(e)}), 500


@desktop_notifications_bp.route('/history/clear', methods=['POST'])
def clear_history():
    """
    Clear notification history
    
    Query parameters:
    - days: Clear notifications older than N days (default: 30)
    - all: Clear all notifications (true/false)
    """
    try:
        clear_all = request.args.get('all', '').lower() == 'true'
        days = int(request.args.get('days', 30))
        
        db = get_session()
        try:
            if clear_all:
                deleted_count = db.query(DesktopNotification).delete()
            else:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                deleted_count = db.query(DesktopNotification).filter(
                    DesktopNotification.sent_at < cutoff_date
                ).delete()
            
            db.commit()
            
            return jsonify({
                'success': True,
                'message': f'Cleared {deleted_count} notifications',
                'count': deleted_count
            }), 200
            
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Failed to clear history: {e}")
        return jsonify({'error': str(e)}), 500


@desktop_notifications_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get notification statistics"""
    try:
        db = get_session()
        try:
            # Total notifications
            total = db.query(DesktopNotification).count()
            
            # Unread count
            unread = db.query(DesktopNotification).filter(
                DesktopNotification.read == False
            ).count()
            
            # Count by type
            type_counts = {}
            for notification_type in ['processing_complete', 'approval_required', 'error', 
                                     'export_complete', 'batch_complete', 'system_status']:
                count = db.query(DesktopNotification).filter(
                    DesktopNotification.notification_type == notification_type
                ).count()
                type_counts[notification_type] = count
            
            # Count by priority
            priority_counts = {}
            for priority in [1, 2, 3]:
                count = db.query(DesktopNotification).filter(
                    DesktopNotification.priority == priority
                ).count()
                priority_counts[str(priority)] = count
            
            # Recent notifications (last 24 hours)
            cutoff_date = datetime.utcnow() - timedelta(hours=24)
            recent_count = db.query(DesktopNotification).filter(
                DesktopNotification.sent_at >= cutoff_date
            ).count()
            
            return jsonify({
                'success': True,
                'stats': {
                    'total': total,
                    'unread': unread,
                    'recent_24h': recent_count,
                    'by_type': type_counts,
                    'by_priority': priority_counts
                }
            }), 200
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Failed to get notification stats: {e}")
        return jsonify({'error': str(e)}), 500


@desktop_notifications_bp.route('/test', methods=['POST'])
def send_test_notification():
    """Send a test notification"""
    try:
        notifier = get_notifier()
        success = notifier.send(
            title="テスト通知",
            message="これはJunmai AutoDevからのテスト通知です",
            notification_type=NotificationType.SYSTEM_STATUS,
            priority=NotificationPriority.MEDIUM
        )
        
        return jsonify({
            'success': success,
            'message': 'Test notification sent' if success else 'Failed to send test notification'
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Failed to send test notification: {e}")
        return jsonify({'error': str(e)}), 500


# Convenience functions for common notification types
def notify_processing_complete(session_name: str, photo_count: int, success_rate: float) -> bool:
    """Send processing complete notification"""
    notifier = get_notifier()
    return notifier.send_processing_complete(session_name, photo_count, success_rate)


def notify_approval_required(pending_count: int) -> bool:
    """Send approval required notification"""
    notifier = get_notifier()
    return notifier.send_approval_required(pending_count)


def notify_error(error_message: str, error_details: str = None) -> bool:
    """Send error notification"""
    notifier = get_notifier()
    return notifier.send_error(error_message, error_details)


def notify_export_complete(export_preset: str, photo_count: int, destination: str) -> bool:
    """Send export complete notification"""
    notifier = get_notifier()
    return notifier.send_export_complete(export_preset, photo_count, destination)


def notify_batch_complete(batch_name: str, total_photos: int, processing_time: float) -> bool:
    """Send batch complete notification"""
    notifier = get_notifier()
    return notifier.send_batch_complete(batch_name, total_photos, processing_time)
