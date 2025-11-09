"""
LINE Notify Integration for Junmai AutoDev

Provides LINE notifications with:
- LINE Notify API integration
- Token management
- Message formatting for different notification types
- Image attachment support

Requirements: 8.1
"""

import logging
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class LineNotificationType(Enum):
    """LINE notification types"""
    PROCESSING_COMPLETE = "processing_complete"
    APPROVAL_REQUIRED = "approval_required"
    ERROR = "error"
    EXPORT_COMPLETE = "export_complete"
    BATCH_COMPLETE = "batch_complete"
    SYSTEM_STATUS = "system_status"


class LineMessageFormatter:
    """LINE message formatter for different notification types"""
    
    @staticmethod
    def format_message(notification_type: LineNotificationType, data: Dict[str, Any]) -> str:
        """
        Format message for LINE notification
        
        Args:
            notification_type: Type of notification
            data: Data dictionary for formatting
            
        Returns:
            Formatted message string
        """
        formatters = {
            LineNotificationType.PROCESSING_COMPLETE: LineMessageFormatter._format_processing_complete,
            LineNotificationType.APPROVAL_REQUIRED: LineMessageFormatter._format_approval_required,
            LineNotificationType.ERROR: LineMessageFormatter._format_error,
            LineNotificationType.EXPORT_COMPLETE: LineMessageFormatter._format_export_complete,
            LineNotificationType.BATCH_COMPLETE: LineMessageFormatter._format_batch_complete,
            LineNotificationType.SYSTEM_STATUS: LineMessageFormatter._format_system_status,
        }
        
        formatter = formatters.get(notification_type, LineMessageFormatter._format_default)
        return formatter(data)
    
    @staticmethod
    def _format_processing_complete(data: Dict[str, Any]) -> str:
        """Format processing complete message"""
        session_name = data.get('session_name', 'Unknown')
        photo_count = data.get('photo_count', 0)
        success_rate = data.get('success_rate', 0.0)
        processing_time = data.get('processing_time', 'Unknown')
        
        message = f"""
✓ 処理完了

セッション: {session_name}
処理枚数: {photo_count}枚
成功率: {success_rate:.1f}%
処理時間: {processing_time}
"""
        return message.strip()
    
    @staticmethod
    def _format_approval_required(data: Dict[str, Any]) -> str:
        """Format approval required message"""
        pending_count = data.get('pending_count', 0)
        sessions = data.get('sessions', [])
        
        message = f"""
📋 承認待ち

{pending_count}枚の写真が承認待ちです
"""
        
        if sessions:
            message += "\nセッション:\n"
            for session in sessions[:5]:  # Limit to 5 sessions
                session_name = session.get('name', 'Unknown')
                count = session.get('count', 0)
                message += f"• {session_name}: {count}枚\n"
            
            if len(sessions) > 5:
                message += f"...他{len(sessions) - 5}件\n"
        
        return message.strip()
    
    @staticmethod
    def _format_error(data: Dict[str, Any]) -> str:
        """Format error message"""
        error_type = data.get('error_type', 'Unknown Error')
        error_message = data.get('error_message', 'An error occurred')
        error_details = data.get('error_details', '')
        timestamp = data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        message = f"""
⚠ エラー発生

種類: {error_type}
メッセージ: {error_message}
"""
        
        if error_details:
            # Truncate details if too long
            if len(error_details) > 200:
                error_details = error_details[:200] + '...'
            message += f"詳細: {error_details}\n"
        
        message += f"発生時刻: {timestamp}"
        
        return message.strip()
    
    @staticmethod
    def _format_export_complete(data: Dict[str, Any]) -> str:
        """Format export complete message"""
        export_preset = data.get('export_preset', 'Unknown')
        photo_count = data.get('photo_count', 0)
        destination = data.get('destination', 'Unknown')
        
        message = f"""
📤 書き出し完了

プリセット: {export_preset}
書き出し枚数: {photo_count}枚
保存先: {destination}
"""
        return message.strip()
    
    @staticmethod
    def _format_batch_complete(data: Dict[str, Any]) -> str:
        """Format batch complete message"""
        batch_name = data.get('batch_name', 'Unknown')
        total_photos = data.get('total_photos', 0)
        processing_time = data.get('processing_time', 'Unknown')
        avg_time_per_photo = data.get('avg_time_per_photo', 'Unknown')
        
        message = f"""
🎯 バッチ処理完了

バッチ: {batch_name}
処理枚数: {total_photos}枚
処理時間: {processing_time}
平均時間: {avg_time_per_photo}
"""
        return message.strip()
    
    @staticmethod
    def _format_system_status(data: Dict[str, Any]) -> str:
        """Format system status message"""
        status = data.get('status', 'Unknown')
        message_text = data.get('message', '')
        
        message = f"""
ℹ システム状態

状態: {status}
"""
        
        if message_text:
            message += f"メッセージ: {message_text}\n"
        
        return message.strip()
    
    @staticmethod
    def _format_default(data: Dict[str, Any]) -> str:
        """Format default message"""
        message = data.get('message', 'Junmai AutoDev 通知')
        return message


class LineTokenManager:
    """LINE Notify token manager"""
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize LINE token manager
        
        Args:
            config_file: Path to configuration file. If None, uses default location.
        """
        if config_file is None:
            base_dir = Path(__file__).parent
            config_file = base_dir / "config" / "line_config.json"
        
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load LINE configuration from file"""
        if not self.config_file.exists():
            self.config = self._get_default_config()
            self._save_config()
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info("LINE Notify configuration loaded")
        except Exception as e:
            logger.error(f"Failed to load LINE Notify configuration: {e}")
            self.config = self._get_default_config()
    
    def _save_config(self) -> None:
        """Save LINE configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info("LINE Notify configuration saved")
        except Exception as e:
            logger.error(f"Failed to save LINE Notify configuration: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default LINE configuration"""
        return {
            'enabled': False,
            'token': '',
            'notification_types': {
                'processing_complete': True,
                'approval_required': True,
                'error': True,
                'export_complete': False,
                'batch_complete': True,
                'system_status': False
            },
            'rate_limit': {
                'max_per_hour': 50,
                'current_count': 0,
                'reset_time': None
            }
        }
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        Update LINE configuration
        
        Args:
            config_dict: Configuration dictionary
        """
        self.config.update(config_dict)
        self._save_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def is_enabled(self) -> bool:
        """Check if LINE notifications are enabled"""
        return self.config.get('enabled', False) and bool(self.config.get('token'))
    
    def is_type_enabled(self, notification_type: LineNotificationType) -> bool:
        """
        Check if specific notification type is enabled
        
        Args:
            notification_type: Type of notification
            
        Returns:
            True if notification type is enabled
        """
        types = self.config.get('notification_types', {})
        return types.get(notification_type.value, True)
    
    def get_token(self) -> Optional[str]:
        """
        Get LINE Notify token
        
        Returns:
            LINE Notify token or None if not configured
        """
        return self.config.get('token')
    
    def set_token(self, token: str) -> None:
        """
        Set LINE Notify token
        
        Args:
            token: LINE Notify token
        """
        self.config['token'] = token
        self._save_config()
    
    def check_rate_limit(self) -> bool:
        """
        Check if rate limit allows sending
        
        Returns:
            True if sending is allowed
        """
        rate_limit = self.config.get('rate_limit', {})
        max_per_hour = rate_limit.get('max_per_hour', 50)
        current_count = rate_limit.get('current_count', 0)
        reset_time = rate_limit.get('reset_time')
        
        # Reset counter if hour has passed
        if reset_time:
            reset_dt = datetime.fromisoformat(reset_time)
            if datetime.now() > reset_dt:
                self.config['rate_limit']['current_count'] = 0
                self.config['rate_limit']['reset_time'] = (
                    datetime.now().replace(minute=0, second=0, microsecond=0)
                    .isoformat()
                )
                self._save_config()
                return True
        
        return current_count < max_per_hour
    
    def increment_rate_limit(self) -> None:
        """Increment rate limit counter"""
        if 'rate_limit' not in self.config:
            self.config['rate_limit'] = self._get_default_config()['rate_limit']
        
        self.config['rate_limit']['current_count'] = (
            self.config['rate_limit'].get('current_count', 0) + 1
        )
        
        if not self.config['rate_limit'].get('reset_time'):
            from datetime import timedelta
            self.config['rate_limit']['reset_time'] = (
                (datetime.now() + timedelta(hours=1))
                .replace(minute=0, second=0, microsecond=0)
                .isoformat()
            )
        
        self._save_config()


class LineNotifier:
    """
    LINE Notify integration manager
    
    Provides LINE notifications with token management and message formatting
    """
    
    LINE_NOTIFY_API = "https://notify-api.line.me/api/notify"
    LINE_NOTIFY_STATUS_API = "https://notify-api.line.me/api/status"
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize LINE notifier
        
        Args:
            config_file: Path to configuration file
        """
        self.token_manager = LineTokenManager(config_file)
        self.formatter = LineMessageFormatter()
    
    def send(
        self,
        message: str,
        notification_type: LineNotificationType = LineNotificationType.SYSTEM_STATUS,
        image_path: Optional[Path] = None,
        sticker_package_id: Optional[int] = None,
        sticker_id: Optional[int] = None
    ) -> bool:
        """
        Send LINE notification
        
        Args:
            message: Notification message
            notification_type: Type of notification
            image_path: Path to image file to attach
            sticker_package_id: LINE sticker package ID
            sticker_id: LINE sticker ID
            
        Returns:
            True if notification was sent successfully
        """
        if not self.token_manager.is_enabled():
            logger.warning("LINE Notify is disabled or token not configured")
            return False
        
        if not self.token_manager.is_type_enabled(notification_type):
            logger.info(f"LINE notification type {notification_type.value} is disabled")
            return False
        
        if not self.token_manager.check_rate_limit():
            logger.warning("LINE Notify rate limit exceeded")
            return False
        
        try:
            token = self.token_manager.get_token()
            if not token:
                logger.error("LINE Notify token not configured")
                return False
            
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            data = {
                'message': message
            }
            
            # Add sticker if provided
            if sticker_package_id and sticker_id:
                data['stickerPackageId'] = sticker_package_id
                data['stickerId'] = sticker_id
            
            files = None
            if image_path and image_path.exists():
                files = {
                    'imageFile': open(image_path, 'rb')
                }
            
            response = requests.post(
                self.LINE_NOTIFY_API,
                headers=headers,
                data=data,
                files=files,
                timeout=10
            )
            
            if files:
                files['imageFile'].close()
            
            if response.status_code == 200:
                logger.info(f"LINE notification sent successfully: {message[:50]}...")
                self.token_manager.increment_rate_limit()
                return True
            else:
                logger.error(f"Failed to send LINE notification: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to send LINE notification: {e}")
            return False
    
    def send_with_data(
        self,
        notification_type: LineNotificationType,
        data: Dict[str, Any],
        image_path: Optional[Path] = None
    ) -> bool:
        """
        Send LINE notification with formatted data
        
        Args:
            notification_type: Type of notification
            data: Data dictionary for formatting
            image_path: Path to image file to attach
            
        Returns:
            True if notification was sent successfully
        """
        message = self.formatter.format_message(notification_type, data)
        return self.send(message, notification_type, image_path)
    
    def send_processing_complete(
        self,
        session_name: str,
        photo_count: int,
        success_rate: float,
        processing_time: str
    ) -> bool:
        """
        Send processing complete notification
        
        Args:
            session_name: Name of the session
            photo_count: Number of photos processed
            success_rate: Success rate percentage
            processing_time: Processing time string
            
        Returns:
            True if notification was sent successfully
        """
        return self.send_with_data(
            LineNotificationType.PROCESSING_COMPLETE,
            {
                'session_name': session_name,
                'photo_count': photo_count,
                'success_rate': success_rate,
                'processing_time': processing_time
            }
        )
    
    def send_approval_required(
        self,
        pending_count: int,
        sessions: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send approval required notification
        
        Args:
            pending_count: Number of photos pending approval
            sessions: List of session dictionaries
            
        Returns:
            True if notification was sent successfully
        """
        return self.send_with_data(
            LineNotificationType.APPROVAL_REQUIRED,
            {
                'pending_count': pending_count,
                'sessions': sessions or []
            }
        )
    
    def send_error(
        self,
        error_type: str,
        error_message: str,
        error_details: Optional[str] = None
    ) -> bool:
        """
        Send error notification
        
        Args:
            error_type: Type of error
            error_message: Error message
            error_details: Additional error details
            
        Returns:
            True if notification was sent successfully
        """
        return self.send_with_data(
            LineNotificationType.ERROR,
            {
                'error_type': error_type,
                'error_message': error_message,
                'error_details': error_details or '',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        )
    
    def send_export_complete(
        self,
        export_preset: str,
        photo_count: int,
        destination: str
    ) -> bool:
        """
        Send export complete notification
        
        Args:
            export_preset: Export preset name
            photo_count: Number of photos exported
            destination: Export destination path
            
        Returns:
            True if notification was sent successfully
        """
        return self.send_with_data(
            LineNotificationType.EXPORT_COMPLETE,
            {
                'export_preset': export_preset,
                'photo_count': photo_count,
                'destination': destination
            }
        )
    
    def send_batch_complete(
        self,
        batch_name: str,
        total_photos: int,
        processing_time: str,
        avg_time_per_photo: str
    ) -> bool:
        """
        Send batch complete notification
        
        Args:
            batch_name: Batch name
            total_photos: Total number of photos in batch
            processing_time: Total processing time string
            avg_time_per_photo: Average time per photo string
            
        Returns:
            True if notification was sent successfully
        """
        return self.send_with_data(
            LineNotificationType.BATCH_COMPLETE,
            {
                'batch_name': batch_name,
                'total_photos': total_photos,
                'processing_time': processing_time,
                'avg_time_per_photo': avg_time_per_photo
            }
        )
    
    def check_token_status(self) -> Optional[Dict[str, Any]]:
        """
        Check LINE Notify token status
        
        Returns:
            Status dictionary or None if check failed
        """
        try:
            token = self.token_manager.get_token()
            if not token:
                return None
            
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            response = requests.get(
                self.LINE_NOTIFY_STATUS_API,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"LINE Notify token status: {data}")
                return data
            else:
                logger.error(f"Failed to check token status: {response.status_code}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to check LINE Notify token status: {e}")
            return None
    
    def update_config(self, config_dict: Dict[str, Any]) -> None:
        """
        Update LINE configuration
        
        Args:
            config_dict: Configuration dictionary
        """
        self.token_manager.update(config_dict)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current LINE configuration
        
        Returns:
            Configuration dictionary
        """
        return self.token_manager.config.copy()
    
    def test_connection(self) -> bool:
        """
        Test LINE Notify connection
        
        Returns:
            True if connection is successful
        """
        try:
            status = self.check_token_status()
            if status and status.get('status') == 200:
                logger.info("LINE Notify connection test successful")
                return True
            else:
                logger.error("LINE Notify connection test failed")
                return False
        except Exception as e:
            logger.error(f"LINE Notify connection test failed: {e}")
            return False


# Singleton instance
_line_notifier_instance: Optional[LineNotifier] = None


def get_line_notifier() -> LineNotifier:
    """
    Get singleton LINE notifier instance
    
    Returns:
        LineNotifier instance
    """
    global _line_notifier_instance
    if _line_notifier_instance is None:
        _line_notifier_instance = LineNotifier()
    return _line_notifier_instance


def send_line_notification(
    notification_type: LineNotificationType,
    data: Dict[str, Any],
    image_path: Optional[Path] = None
) -> bool:
    """
    Convenience function to send LINE notification
    
    Args:
        notification_type: Type of notification
        data: Data dictionary for formatting
        image_path: Path to image file to attach
        
    Returns:
        True if notification was sent successfully
    """
    notifier = get_line_notifier()
    return notifier.send_with_data(notification_type, data, image_path)


if __name__ == '__main__':
    # Setup logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=== Testing LINE Notifier ===\n")
    
    # Test 1: Initialize notifier
    print("Test 1: Initialize notifier")
    notifier = LineNotifier()
    print(f"✓ LINE notifier initialized")
    print(f"  Enabled: {notifier.token_manager.is_enabled()}")
    
    # Test 2: Get configuration
    print("\nTest 2: Get configuration")
    config = notifier.get_config()
    print(f"✓ Configuration loaded")
    print(f"  Token configured: {bool(config.get('token'))}")
    
    # Test 3: Test message formatting
    print("\nTest 3: Test message formatting")
    message = notifier.formatter.format_message(
        LineNotificationType.PROCESSING_COMPLETE,
        {
            'session_name': '2025-11-08_Wedding',
            'photo_count': 120,
            'success_rate': 95.5,
            'processing_time': '2h 15m'
        }
    )
    print(f"✓ Message formatted:")
    print(message)
    
    # Test 4: Update configuration (for testing)
    print("\nTest 4: Update configuration")
    print("⚠ To enable LINE Notify, set a valid token in the configuration")
    print(f"  Config file: {notifier.token_manager.config_file}")
    
    # Test 5: Test rate limiting
    print("\nTest 5: Test rate limiting")
    can_send = notifier.token_manager.check_rate_limit()
    print(f"✓ Rate limit check: {can_send}")
    
    print("\n=== All tests completed! ===")
    print("\nNote: To actually send LINE notifications:")
    print("1. Get a LINE Notify token from https://notify-bot.line.me/")
    print("2. Update the configuration with your token")
    print(f"3. Edit: {notifier.token_manager.config_file}")
