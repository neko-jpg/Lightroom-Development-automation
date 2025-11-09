"""
Tests for Desktop Notification System

Tests cover:
- Windows Toast notifications
- macOS Notification Center integration
- Notification priority management
- Notification history management
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from desktop_notifier import (
    DesktopNotifier,
    NotificationHistory,
    NotificationType,
    NotificationPriority,
    get_notifier,
    send_notification
)


class TestNotificationHistory:
    """Test notification history management"""
    
    def test_history_initialization(self):
        """Test history initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "test_history.json"
            history = NotificationHistory(history_file)
            
            assert history.history_file == history_file
            assert isinstance(history.history, list)
            assert len(history.history) == 0
    
    def test_add_notification(self):
        """Test adding notification to history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "test_history.json"
            history = NotificationHistory(history_file)
            
            notification = {
                'title': 'Test Notification',
                'message': 'Test message',
                'type': NotificationType.SYSTEM_STATUS.value,
                'priority': NotificationPriority.MEDIUM.value
            }
            
            history.add(notification)
            
            assert len(history.history) == 1
            assert history.history[0]['title'] == 'Test Notification'
            assert 'timestamp' in history.history[0]
            assert 'id' in history.history[0]
    
    def test_get_recent(self):
        """Test getting recent notifications"""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "test_history.json"
            history = NotificationHistory(history_file)
            
            # Add multiple notifications
            for i in range(10):
                notification = {
                    'title': f'Notification {i}',
                    'message': f'Message {i}',
                    'type': NotificationType.SYSTEM_STATUS.value,
                    'priority': NotificationPriority.MEDIUM.value
                }
                history.add(notification)
            
            # Get recent 5
            recent = history.get_recent(limit=5)
            assert len(recent) == 5
            assert recent[-1]['title'] == 'Notification 9'
    
    def test_get_by_type(self):
        """Test filtering notifications by type"""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "test_history.json"
            history = NotificationHistory(history_file)
            
            # Add notifications of different types
            for notification_type in [NotificationType.PROCESSING_COMPLETE, 
                                     NotificationType.ERROR,
                                     NotificationType.APPROVAL_REQUIRED]:
                notification = {
                    'title': f'{notification_type.value} notification',
                    'message': 'Test message',
                    'type': notification_type.value,
                    'priority': NotificationPriority.MEDIUM.value
                }
                history.add(notification)
            
            # Get error notifications
            errors = history.get_by_type(NotificationType.ERROR)
            assert len(errors) == 1
            assert errors[0]['type'] == NotificationType.ERROR.value
    
    def test_get_by_priority(self):
        """Test filtering notifications by priority"""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "test_history.json"
            history = NotificationHistory(history_file)
            
            # Add notifications with different priorities
            for priority in [NotificationPriority.LOW, 
                           NotificationPriority.MEDIUM,
                           NotificationPriority.HIGH]:
                notification = {
                    'title': f'Priority {priority.value} notification',
                    'message': 'Test message',
                    'type': NotificationType.SYSTEM_STATUS.value,
                    'priority': priority.value
                }
                history.add(notification)
            
            # Get high priority notifications
            high_priority = history.get_by_priority(NotificationPriority.HIGH)
            assert len(high_priority) == 1
            assert high_priority[0]['priority'] == NotificationPriority.HIGH.value
    
    def test_clear_old(self):
        """Test clearing old notifications"""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "test_history.json"
            history = NotificationHistory(history_file)
            
            # Add old notification (manually set timestamp)
            old_notification = {
                'title': 'Old Notification',
                'message': 'Old message',
                'type': NotificationType.SYSTEM_STATUS.value,
                'priority': NotificationPriority.MEDIUM.value,
                'timestamp': (datetime.now() - timedelta(days=40)).isoformat()
            }
            history.history.append(old_notification)
            
            # Add recent notification
            recent_notification = {
                'title': 'Recent Notification',
                'message': 'Recent message',
                'type': NotificationType.SYSTEM_STATUS.value,
                'priority': NotificationPriority.MEDIUM.value
            }
            history.add(recent_notification)
            
            # Clear notifications older than 30 days
            removed_count = history.clear_old(days=30)
            
            assert removed_count == 1
            assert len(history.history) == 1
            assert history.history[0]['title'] == 'Recent Notification'
    
    def test_clear_all(self):
        """Test clearing all notifications"""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "test_history.json"
            history = NotificationHistory(history_file)
            
            # Add multiple notifications
            for i in range(5):
                notification = {
                    'title': f'Notification {i}',
                    'message': f'Message {i}',
                    'type': NotificationType.SYSTEM_STATUS.value,
                    'priority': NotificationPriority.MEDIUM.value
                }
                history.add(notification)
            
            assert len(history.history) == 5
            
            # Clear all
            history.clear_all()
            
            assert len(history.history) == 0
    
    def test_persistence(self):
        """Test history persistence across instances"""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "test_history.json"
            
            # Create first instance and add notification
            history1 = NotificationHistory(history_file)
            notification = {
                'title': 'Persistent Notification',
                'message': 'Test message',
                'type': NotificationType.SYSTEM_STATUS.value,
                'priority': NotificationPriority.MEDIUM.value
            }
            history1.add(notification)
            
            # Create second instance and verify data persisted
            history2 = NotificationHistory(history_file)
            assert len(history2.history) == 1
            assert history2.history[0]['title'] == 'Persistent Notification'


class TestDesktopNotifier:
    """Test desktop notifier functionality"""
    
    def test_notifier_initialization(self):
        """Test notifier initialization"""
        notifier = DesktopNotifier(enable_history=False)
        
        assert notifier.app_name == "Junmai AutoDev"
        assert notifier.platform in ["Windows", "Darwin", "Linux"]
        assert notifier.history is None
    
    def test_notifier_with_history(self):
        """Test notifier with history enabled"""
        notifier = DesktopNotifier(enable_history=True)
        
        assert notifier.history is not None
        assert isinstance(notifier.history, NotificationHistory)
    
    def test_send_basic_notification(self):
        """Test sending basic notification"""
        notifier = DesktopNotifier(enable_history=True)
        
        # Note: Actual notification may not be sent in test environment
        # but we can verify the method executes without error
        result = notifier.send(
            title="Test Notification",
            message="Test message",
            notification_type=NotificationType.SYSTEM_STATUS,
            priority=NotificationPriority.MEDIUM
        )
        
        # Result depends on platform and availability of notification system
        assert isinstance(result, bool)
        
        # Verify history was updated
        if notifier.history:
            history = notifier.get_history(limit=1)
            assert len(history) >= 1
            assert history[-1]['title'] == "Test Notification"
    
    def test_send_processing_complete(self):
        """Test sending processing complete notification"""
        notifier = DesktopNotifier(enable_history=True)
        
        result = notifier.send_processing_complete(
            session_name="Test Session",
            photo_count=100,
            success_rate=95.5
        )
        
        assert isinstance(result, bool)
        
        # Verify history
        if notifier.history:
            history = notifier.get_history_by_type(NotificationType.PROCESSING_COMPLETE)
            assert len(history) >= 1
    
    def test_send_approval_required(self):
        """Test sending approval required notification"""
        notifier = DesktopNotifier(enable_history=True)
        
        result = notifier.send_approval_required(pending_count=15)
        
        assert isinstance(result, bool)
        
        # Verify history
        if notifier.history:
            history = notifier.get_history_by_type(NotificationType.APPROVAL_REQUIRED)
            assert len(history) >= 1
    
    def test_send_error(self):
        """Test sending error notification"""
        notifier = DesktopNotifier(enable_history=True)
        
        result = notifier.send_error(
            error_message="Test error",
            error_details="Error details"
        )
        
        assert isinstance(result, bool)
        
        # Verify history
        if notifier.history:
            history = notifier.get_history_by_type(NotificationType.ERROR)
            assert len(history) >= 1
            assert history[-1]['priority'] == NotificationPriority.HIGH.value
    
    def test_send_export_complete(self):
        """Test sending export complete notification"""
        notifier = DesktopNotifier(enable_history=True)
        
        result = notifier.send_export_complete(
            export_preset="SNS",
            photo_count=50,
            destination="/export/sns"
        )
        
        assert isinstance(result, bool)
        
        # Verify history
        if notifier.history:
            history = notifier.get_history_by_type(NotificationType.EXPORT_COMPLETE)
            assert len(history) >= 1
    
    def test_send_batch_complete(self):
        """Test sending batch complete notification"""
        notifier = DesktopNotifier(enable_history=True)
        
        result = notifier.send_batch_complete(
            batch_name="Test Batch",
            total_photos=200,
            processing_time=120.5
        )
        
        assert isinstance(result, bool)
        
        # Verify history
        if notifier.history:
            history = notifier.get_history_by_type(NotificationType.BATCH_COMPLETE)
            assert len(history) >= 1
    
    def test_get_history(self):
        """Test getting notification history"""
        notifier = DesktopNotifier(enable_history=True)
        
        # Send multiple notifications
        notifier.send("Test 1", "Message 1")
        notifier.send("Test 2", "Message 2")
        notifier.send("Test 3", "Message 3")
        
        history = notifier.get_history(limit=10)
        assert len(history) >= 3
    
    def test_get_history_by_type(self):
        """Test getting history by type"""
        notifier = DesktopNotifier(enable_history=True)
        
        # Send notifications of different types
        notifier.send_error("Error 1")
        notifier.send_processing_complete("Session 1", 10, 100.0)
        notifier.send_error("Error 2")
        
        error_history = notifier.get_history_by_type(NotificationType.ERROR)
        assert len(error_history) >= 2
    
    def test_get_history_by_priority(self):
        """Test getting history by priority"""
        notifier = DesktopNotifier(enable_history=True)
        
        # Send notifications with different priorities
        notifier.send("Low", "Message", priority=NotificationPriority.LOW)
        notifier.send("High", "Message", priority=NotificationPriority.HIGH)
        notifier.send("Medium", "Message", priority=NotificationPriority.MEDIUM)
        
        high_priority = notifier.get_history_by_priority(NotificationPriority.HIGH)
        assert len(high_priority) >= 1
    
    def test_clear_old_history(self):
        """Test clearing old history"""
        notifier = DesktopNotifier(enable_history=True)
        
        # Add some notifications
        notifier.send("Test", "Message")
        
        # Clear old (should not remove recent notifications)
        removed = notifier.clear_old_history(days=30)
        assert removed >= 0
    
    def test_clear_all_history(self):
        """Test clearing all history"""
        notifier = DesktopNotifier(enable_history=True)
        
        # Add some notifications
        notifier.send("Test 1", "Message 1")
        notifier.send("Test 2", "Message 2")
        
        # Clear all
        notifier.clear_all_history()
        
        history = notifier.get_history()
        assert len(history) == 0


class TestSingletonNotifier:
    """Test singleton notifier functionality"""
    
    def test_get_notifier_singleton(self):
        """Test that get_notifier returns singleton instance"""
        notifier1 = get_notifier()
        notifier2 = get_notifier()
        
        assert notifier1 is notifier2
    
    def test_send_notification_convenience(self):
        """Test convenience send_notification function"""
        result = send_notification(
            title="Test",
            message="Test message",
            notification_type=NotificationType.SYSTEM_STATUS,
            priority=NotificationPriority.MEDIUM
        )
        
        assert isinstance(result, bool)


class TestNotificationEnums:
    """Test notification enums"""
    
    def test_notification_type_enum(self):
        """Test NotificationType enum"""
        assert NotificationType.PROCESSING_COMPLETE.value == "processing_complete"
        assert NotificationType.APPROVAL_REQUIRED.value == "approval_required"
        assert NotificationType.ERROR.value == "error"
        assert NotificationType.EXPORT_COMPLETE.value == "export_complete"
        assert NotificationType.BATCH_COMPLETE.value == "batch_complete"
        assert NotificationType.SYSTEM_STATUS.value == "system_status"
    
    def test_notification_priority_enum(self):
        """Test NotificationPriority enum"""
        assert NotificationPriority.LOW.value == 1
        assert NotificationPriority.MEDIUM.value == 2
        assert NotificationPriority.HIGH.value == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
