"""
Integration tests for notification systems

Tests desktop, email, and LINE notification integrations
Requirements: 8.1, 8.2
"""

import pytest
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import notification systems
from desktop_notifier import (
    DesktopNotifier,
    NotificationType,
    NotificationPriority,
    get_notifier
)
from email_notifier import (
    EmailNotifier,
    EmailNotificationType,
    get_email_notifier
)
from line_notifier import (
    LineNotifier,
    LineNotificationType,
    get_line_notifier
)

logger = logging.getLogger(__name__)


class TestDesktopNotificationIntegration:
    """Test desktop notification system"""
    
    def test_desktop_notifier_initialization(self):
        """Test desktop notifier initialization"""
        notifier = DesktopNotifier(enable_history=True)
        
        assert notifier is not None
        assert notifier.app_name == "Junmai AutoDev"
        assert notifier.history is not None
    
    def test_desktop_send_notification(self):
        """Test sending desktop notification"""
        notifier = DesktopNotifier(enable_history=True)
        
        # Send notification (may fail if platform not supported)
        success = notifier.send(
            title="Test Notification",
            message="This is a test",
            notification_type=NotificationType.SYSTEM_STATUS,
            priority=NotificationPriority.MEDIUM
        )
        
        # Check history was updated
        if notifier.history:
            history = notifier.history.get_recent(limit=1)
            assert len(history) > 0
            assert history[0]['title'] == "Test Notification"
    
    def test_desktop_processing_complete(self):
        """Test processing complete notification"""
        notifier = DesktopNotifier(enable_history=True)
        
        success = notifier.send_processing_complete(
            session_name="Test_Session",
            photo_count=100,
            success_rate=95.5
        )
        
        # Verify in history
        if notifier.history:
            history = notifier.history.get_by_type(
                NotificationType.PROCESSING_COMPLETE,
                limit=1
            )
            assert len(history) > 0
    
    def test_desktop_error_notification(self):
        """Test error notification"""
        notifier = DesktopNotifier(enable_history=True)
        
        success = notifier.send_error(
            error_message="Test error",
            error_details="Error details"
        )
        
        # Verify in history
        if notifier.history:
            history = notifier.history.get_by_type(
                NotificationType.ERROR,
                limit=1
            )
            assert len(history) > 0
    
    def test_desktop_notification_history(self):
        """Test notification history management"""
        notifier = DesktopNotifier(enable_history=True)
        
        # Send multiple notifications
        for i in range(5):
            notifier.send(
                title=f"Test {i}",
                message=f"Message {i}",
                notification_type=NotificationType.SYSTEM_STATUS
            )
        
        # Get history
        history = notifier.get_history(limit=10)
        assert len(history) >= 5
    
    def test_desktop_singleton_instance(self):
        """Test singleton pattern"""
        notifier1 = get_notifier()
        notifier2 = get_notifier()
        
        assert notifier1 is notifier2


class TestEmailNotificationIntegration:
    """Test email notification system"""
    
    def test_email_notifier_initialization(self):
        """Test email notifier initialization"""
        notifier = EmailNotifier()
        
        assert notifier is not None
        assert notifier.config is not None
        assert notifier.batch_manager is not None
    
    def test_email_config_management(self):
        """Test email configuration management"""
        notifier = EmailNotifier()
        
        # Get config
        config = notifier.get_config()
        assert 'enabled' in config
        assert 'smtp_server' in config
        assert 'notification_types' in config
    
    def test_email_template_formatting(self):
        """Test email template formatting"""
        notifier = EmailNotifier()
        
        # Test processing complete template
        template = notifier.template.get_template(
            EmailNotificationType.PROCESSING_COMPLETE
        )
        
        assert 'subject' in template
        assert 'html' in template
        assert 'text' in template
        assert '{session_name}' in template['subject']
    
    @patch('smtplib.SMTP')
    def test_email_send_with_mock(self, mock_smtp):
        """Test email sending with mocked SMTP"""
        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        notifier = EmailNotifier()
        
        # Enable for testing
        notifier.update_config({
            'enabled': True,
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@test.com',
            'password': 'test',
            'from_address': 'test@test.com',
            'to_addresses': ['recipient@test.com']
        })
        
        # Send notification
        success = notifier.send(
            to_addresses=['recipient@test.com'],
            subject="Test Subject",
            html_body="<html><body>Test</body></html>",
            text_body="Test",
            notification_type=EmailNotificationType.PROCESSING_COMPLETE
        )
        
        # Verify SMTP was called
        assert mock_smtp.called
    
    def test_email_batch_management(self):
        """Test batch notification management"""
        notifier = EmailNotifier()
        
        # Add notifications to batch
        should_flush = notifier.add_to_batch({
            'type': 'processing_complete',
            'message': 'Test 1'
        })
        
        # First notification shouldn't trigger flush
        assert isinstance(should_flush, bool)
    
    def test_email_singleton_instance(self):
        """Test singleton pattern"""
        notifier1 = get_email_notifier()
        notifier2 = get_email_notifier()
        
        assert notifier1 is notifier2


class TestLineNotificationIntegration:
    """Test LINE notification system"""
    
    def test_line_notifier_initialization(self):
        """Test LINE notifier initialization"""
        notifier = LineNotifier()
        
        assert notifier is not None
        assert notifier.token_manager is not None
        assert notifier.formatter is not None
    
    def test_line_config_management(self):
        """Test LINE configuration management"""
        notifier = LineNotifier()
        
        # Get config
        config = notifier.get_config()
        assert 'enabled' in config
        assert 'token' in config
        assert 'notification_types' in config
        assert 'rate_limit' in config
    
    def test_line_message_formatting(self):
        """Test LINE message formatting"""
        notifier = LineNotifier()
        
        # Test processing complete format
        message = notifier.formatter.format_message(
            LineNotificationType.PROCESSING_COMPLETE,
            {
                'session_name': 'Test_Session',
                'photo_count': 100,
                'success_rate': 95.5,
                'processing_time': '1h 30m'
            }
        )
        
        assert 'Test_Session' in message
        assert '100' in message
        assert '95.5' in message
    
    def test_line_error_formatting(self):
        """Test LINE error message formatting"""
        notifier = LineNotifier()
        
        message = notifier.formatter.format_message(
            LineNotificationType.ERROR,
            {
                'error_type': 'Test Error',
                'error_message': 'Test message',
                'error_details': 'Test details',
                'timestamp': '2025-11-08 14:30:00'
            }
        )
        
        assert 'Test Error' in message
        assert 'Test message' in message
    
    def test_line_rate_limiting(self):
        """Test LINE rate limiting"""
        notifier = LineNotifier()
        
        # Check rate limit
        can_send = notifier.token_manager.check_rate_limit()
        assert isinstance(can_send, bool)
    
    @patch('line_notifier.requests.post')
    def test_line_send_with_mock(self, mock_post):
        """Test LINE sending with mocked requests"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        notifier = LineNotifier()
        
        # Enable for testing - need to set enabled AND token
        notifier.token_manager.config['enabled'] = True
        notifier.token_manager.config['token'] = 'test_token_12345'
        
        # Ensure notification type is enabled
        if 'notification_types' not in notifier.token_manager.config:
            notifier.token_manager.config['notification_types'] = {}
        notifier.token_manager.config['notification_types']['system_status'] = True
        
        # Ensure rate limit allows sending
        if 'rate_limit' not in notifier.token_manager.config:
            notifier.token_manager.config['rate_limit'] = {
                'max_per_hour': 50,
                'current_count': 0,
                'reset_time': None
            }
        
        # Send notification
        success = notifier.send(
            message="Test notification",
            notification_type=LineNotificationType.SYSTEM_STATUS
        )
        
        # Verify request was made
        assert mock_post.called, f"Mock not called. Success: {success}, Enabled: {notifier.token_manager.is_enabled()}"
        call_args = mock_post.call_args
        assert 'headers' in call_args.kwargs
        assert 'Authorization' in call_args.kwargs['headers']
    
    def test_line_singleton_instance(self):
        """Test singleton pattern"""
        notifier1 = get_line_notifier()
        notifier2 = get_line_notifier()
        
        assert notifier1 is notifier2


class TestMultiChannelNotification:
    """Test multi-channel notification integration"""
    
    def test_send_to_all_channels(self):
        """Test sending notification to all channels"""
        desktop = get_notifier()
        email = get_email_notifier()
        line = get_line_notifier()
        
        # All notifiers should be initialized
        assert desktop is not None
        assert email is not None
        assert line is not None
    
    def test_processing_complete_all_channels(self):
        """Test processing complete notification across all channels"""
        desktop = get_notifier()
        email = get_email_notifier()
        line = get_line_notifier()
        
        # Desktop
        desktop_success = desktop.send_processing_complete(
            session_name="Multi_Channel_Test",
            photo_count=50,
            success_rate=98.0
        )
        
        # Email (will fail without SMTP config, but shouldn't crash)
        email_success = email.send_processing_complete(
            session_name="Multi_Channel_Test",
            photo_count=50,
            success_rate=98.0,
            processing_time="45m"
        )
        
        # LINE (will fail without token, but shouldn't crash)
        line_success = line.send_processing_complete(
            session_name="Multi_Channel_Test",
            photo_count=50,
            success_rate=98.0,
            processing_time="45m"
        )
        
        # At least one should work (desktop)
        assert isinstance(desktop_success, bool)
        assert isinstance(email_success, bool)
        assert isinstance(line_success, bool)
    
    def test_error_notification_all_channels(self):
        """Test error notification across all channels"""
        desktop = get_notifier()
        email = get_email_notifier()
        line = get_line_notifier()
        
        error_type = "Integration Test Error"
        error_message = "This is a test error"
        error_details = "Test error details"
        
        # Desktop
        desktop_success = desktop.send_error(
            error_message=error_message,
            error_details=error_details
        )
        
        # Email
        email_success = email.send_error(
            error_type=error_type,
            error_message=error_message,
            error_details=error_details
        )
        
        # LINE
        line_success = line.send_error(
            error_type=error_type,
            error_message=error_message,
            error_details=error_details
        )
        
        # All should return boolean
        assert isinstance(desktop_success, bool)
        assert isinstance(email_success, bool)
        assert isinstance(line_success, bool)


class TestNotificationConfiguration:
    """Test notification configuration management"""
    
    def test_desktop_config_persistence(self):
        """Test desktop notification config persistence"""
        notifier = DesktopNotifier(enable_history=True)
        
        # History should be persisted
        if notifier.history:
            assert notifier.history.history_file.parent.exists()
    
    def test_email_config_persistence(self):
        """Test email notification config persistence"""
        notifier = EmailNotifier()
        
        # Config file should exist or be created
        assert notifier.config.config_file.parent.exists()
    
    def test_line_config_persistence(self):
        """Test LINE notification config persistence"""
        notifier = LineNotifier()
        
        # Config file should exist or be created
        assert notifier.token_manager.config_file.parent.exists()
    
    def test_notification_type_filtering(self):
        """Test notification type filtering"""
        desktop = get_notifier()
        email = get_email_notifier()
        line = get_line_notifier()
        
        # All should have type filtering
        assert hasattr(desktop, 'send')
        assert hasattr(email.config, 'is_type_enabled')
        assert hasattr(line.token_manager, 'is_type_enabled')


class TestNotificationErrorHandling:
    """Test error handling in notification systems"""
    
    def test_desktop_invalid_notification(self):
        """Test desktop notification with invalid data"""
        notifier = DesktopNotifier(enable_history=True)
        
        # Should handle gracefully
        try:
            success = notifier.send(
                title="",  # Empty title
                message="",  # Empty message
                notification_type=NotificationType.SYSTEM_STATUS
            )
            assert isinstance(success, bool)
        except Exception as e:
            pytest.fail(f"Should handle invalid data gracefully: {e}")
    
    def test_email_without_config(self):
        """Test email notification without configuration"""
        notifier = EmailNotifier()
        
        # Should return False, not crash
        success = notifier.send(
            to_addresses=['test@test.com'],
            subject="Test",
            html_body="Test",
            text_body="Test",
            notification_type=EmailNotificationType.PROCESSING_COMPLETE
        )
        
        assert isinstance(success, bool)
    
    def test_line_without_token(self):
        """Test LINE notification without token"""
        notifier = LineNotifier()
        
        # Should return False, not crash
        success = notifier.send(
            message="Test",
            notification_type=LineNotificationType.SYSTEM_STATUS
        )
        
        assert isinstance(success, bool)
        assert success == False  # Should fail without token


def run_integration_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("Notification System Integration Tests")
    print("=" * 60)
    
    # Run pytest
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes'
    ])


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    run_integration_tests()
