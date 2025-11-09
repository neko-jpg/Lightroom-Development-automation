"""
Desktop Notification System for Junmai AutoDev

Provides cross-platform desktop notifications with:
- Windows Toast notifications
- macOS Notification Center integration
- Notification priority management
- Notification history management

Requirements: 8.1, 8.2, 8.3
"""

import logging
import platform
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = 1      # Batch completion, statistics
    MEDIUM = 2   # Processing complete, approval required
    HIGH = 3     # Errors, critical issues


class NotificationType(Enum):
    """Notification types"""
    PROCESSING_COMPLETE = "processing_complete"
    APPROVAL_REQUIRED = "approval_required"
    ERROR = "error"
    EXPORT_COMPLETE = "export_complete"
    BATCH_COMPLETE = "batch_complete"
    SYSTEM_STATUS = "system_status"


class NotificationHistory:
    """Manages notification history and persistence"""
    
    def __init__(self, history_file: Optional[Path] = None):
        """
        Initialize notification history
        
        Args:
            history_file: Path to history file. If None, uses default location.
        """
        if history_file is None:
            base_dir = Path(__file__).parent
            history_file = base_dir / "data" / "notification_history.json"
        
        self.history_file = Path(history_file)
        self.history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        self._ensure_history_directory()
        self._load_history()
    
    def _ensure_history_directory(self) -> None:
        """Ensure history directory exists"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_history(self) -> None:
        """Load notification history from file"""
        if not self.history_file.exists():
            self.history = []
            return
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
            logger.info(f"Loaded {len(self.history)} notifications from history")
        except Exception as e:
            logger.error(f"Failed to load notification history: {e}")
            self.history = []
    
    def _save_history(self) -> None:
        """Save notification history to file"""
        try:
            self._ensure_history_directory()
            
            # Keep only the most recent notifications
            if len(self.history) > self.max_history_size:
                self.history = self.history[-self.max_history_size:]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Saved {len(self.history)} notifications to history")
        except Exception as e:
            logger.error(f"Failed to save notification history: {e}")
    
    def add(self, notification: Dict[str, Any]) -> None:
        """
        Add notification to history
        
        Args:
            notification: Notification data dictionary
        """
        notification['timestamp'] = datetime.now().isoformat()
        notification['id'] = f"notif_{datetime.now().timestamp()}"
        self.history.append(notification)
        self._save_history()
    
    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent notifications
        
        Args:
            limit: Maximum number of notifications to return
            
        Returns:
            List of recent notifications
        """
        return self.history[-limit:]
    
    def get_by_type(self, notification_type: NotificationType, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get notifications by type
        
        Args:
            notification_type: Type of notifications to retrieve
            limit: Maximum number of notifications to return
            
        Returns:
            List of notifications of specified type
        """
        filtered = [n for n in self.history if n.get('type') == notification_type.value]
        return filtered[-limit:]
    
    def get_by_priority(self, priority: NotificationPriority, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get notifications by priority
        
        Args:
            priority: Priority level
            limit: Maximum number of notifications to return
            
        Returns:
            List of notifications with specified priority
        """
        filtered = [n for n in self.history if n.get('priority') == priority.value]
        return filtered[-limit:]
    
    def clear_old(self, days: int = 30) -> int:
        """
        Clear notifications older than specified days
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of notifications removed
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        original_count = len(self.history)
        
        self.history = [
            n for n in self.history
            if datetime.fromisoformat(n['timestamp']) > cutoff_date
        ]
        
        removed_count = original_count - len(self.history)
        if removed_count > 0:
            self._save_history()
            logger.info(f"Removed {removed_count} old notifications")
        
        return removed_count
    
    def clear_all(self) -> None:
        """Clear all notification history"""
        self.history = []
        self._save_history()
        logger.info("Cleared all notification history")


class DesktopNotifier:
    """
    Cross-platform desktop notification manager
    
    Supports Windows Toast notifications and macOS Notification Center
    """
    
    def __init__(self, app_name: str = "Junmai AutoDev", enable_history: bool = True):
        """
        Initialize desktop notifier
        
        Args:
            app_name: Application name for notifications
            enable_history: Whether to enable notification history
        """
        self.app_name = app_name
        self.platform = platform.system()
        self.history = NotificationHistory() if enable_history else None
        self._notifier = None
        self._initialize_notifier()
    
    def _initialize_notifier(self) -> None:
        """Initialize platform-specific notifier"""
        try:
            if self.platform == "Windows":
                self._initialize_windows_notifier()
            elif self.platform == "Darwin":  # macOS
                self._initialize_macos_notifier()
            else:
                logger.warning(f"Desktop notifications not supported on {self.platform}")
        except Exception as e:
            logger.error(f"Failed to initialize desktop notifier: {e}")
    
    def _initialize_windows_notifier(self) -> None:
        """Initialize Windows Toast notifier"""
        try:
            from win10toast import ToastNotifier
            self._notifier = ToastNotifier()
            logger.info("Windows Toast notifier initialized")
        except ImportError:
            logger.warning("win10toast not installed. Install with: pip install win10toast")
            self._notifier = None
        except Exception as e:
            logger.error(f"Failed to initialize Windows notifier: {e}")
            self._notifier = None
    
    def _initialize_macos_notifier(self) -> None:
        """Initialize macOS Notification Center notifier"""
        try:
            import pync
            self._notifier = pync
            logger.info("macOS Notification Center initialized")
        except ImportError:
            logger.warning("pync not installed. Install with: pip install pync")
            self._notifier = None
        except Exception as e:
            logger.error(f"Failed to initialize macOS notifier: {e}")
            self._notifier = None
    
    def send(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.SYSTEM_STATUS,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        duration: int = 5,
        icon_path: Optional[str] = None,
        sound: bool = True,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send desktop notification
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            duration: Duration in seconds (Windows only)
            icon_path: Path to icon file
            sound: Whether to play sound
            data: Additional data to store with notification
            
        Returns:
            True if notification was sent successfully
        """
        if self._notifier is None:
            logger.warning("Desktop notifier not available")
            return False
        
        try:
            # Add to history
            if self.history:
                notification_data = {
                    'title': title,
                    'message': message,
                    'type': notification_type.value,
                    'priority': priority.value,
                    'data': data or {}
                }
                self.history.add(notification_data)
            
            # Send platform-specific notification
            if self.platform == "Windows":
                return self._send_windows_notification(
                    title, message, duration, icon_path, sound
                )
            elif self.platform == "Darwin":
                return self._send_macos_notification(
                    title, message, sound
                )
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def _send_windows_notification(
        self,
        title: str,
        message: str,
        duration: int,
        icon_path: Optional[str],
        sound: bool
    ) -> bool:
        """Send Windows Toast notification"""
        try:
            # Determine icon path
            if icon_path is None:
                # Use default icon if available
                base_dir = Path(__file__).parent
                default_icon = base_dir / "resources" / "icon.ico"
                if default_icon.exists():
                    icon_path = str(default_icon)
            
            # Send notification
            self._notifier.show_toast(
                title=title,
                msg=message,
                duration=duration,
                icon_path=icon_path,
                threaded=True
            )
            
            logger.info(f"Windows notification sent: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Windows notification: {e}")
            return False
    
    def _send_macos_notification(
        self,
        title: str,
        message: str,
        sound: bool
    ) -> bool:
        """Send macOS Notification Center notification"""
        try:
            self._notifier.notify(
                message,
                title=title,
                appIcon=None,  # Use default app icon
                sound='default' if sound else None
            )
            
            logger.info(f"macOS notification sent: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send macOS notification: {e}")
            return False
    
    def send_processing_complete(
        self,
        session_name: str,
        photo_count: int,
        success_rate: float
    ) -> bool:
        """
        Send processing complete notification
        
        Args:
            session_name: Name of the session
            photo_count: Number of photos processed
            success_rate: Success rate percentage
            
        Returns:
            True if notification was sent successfully
        """
        title = "処理完了"
        message = f"{session_name}: {photo_count}枚処理完了 (成功率: {success_rate:.1f}%)"
        
        return self.send(
            title=title,
            message=message,
            notification_type=NotificationType.PROCESSING_COMPLETE,
            priority=NotificationPriority.MEDIUM,
            data={
                'session_name': session_name,
                'photo_count': photo_count,
                'success_rate': success_rate
            }
        )
    
    def send_approval_required(
        self,
        pending_count: int
    ) -> bool:
        """
        Send approval required notification
        
        Args:
            pending_count: Number of photos pending approval
            
        Returns:
            True if notification was sent successfully
        """
        title = "承認待ち"
        message = f"{pending_count}枚の写真が承認待ちです"
        
        return self.send(
            title=title,
            message=message,
            notification_type=NotificationType.APPROVAL_REQUIRED,
            priority=NotificationPriority.MEDIUM,
            sound=False,  # Less intrusive for approval requests
            data={'pending_count': pending_count}
        )
    
    def send_error(
        self,
        error_message: str,
        error_details: Optional[str] = None
    ) -> bool:
        """
        Send error notification
        
        Args:
            error_message: Error message
            error_details: Additional error details
            
        Returns:
            True if notification was sent successfully
        """
        title = "エラー発生"
        message = error_message
        
        return self.send(
            title=title,
            message=message,
            notification_type=NotificationType.ERROR,
            priority=NotificationPriority.HIGH,
            duration=10,  # Longer duration for errors
            data={'error_details': error_details}
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
        title = "書き出し完了"
        message = f"{export_preset}: {photo_count}枚を書き出しました"
        
        return self.send(
            title=title,
            message=message,
            notification_type=NotificationType.EXPORT_COMPLETE,
            priority=NotificationPriority.LOW,
            data={
                'export_preset': export_preset,
                'photo_count': photo_count,
                'destination': destination
            }
        )
    
    def send_batch_complete(
        self,
        batch_name: str,
        total_photos: int,
        processing_time: float
    ) -> bool:
        """
        Send batch complete notification
        
        Args:
            batch_name: Batch name
            total_photos: Total number of photos in batch
            processing_time: Total processing time in seconds
            
        Returns:
            True if notification was sent successfully
        """
        title = "バッチ処理完了"
        message = f"{batch_name}: {total_photos}枚 ({processing_time:.1f}秒)"
        
        return self.send(
            title=title,
            message=message,
            notification_type=NotificationType.BATCH_COMPLETE,
            priority=NotificationPriority.LOW,
            data={
                'batch_name': batch_name,
                'total_photos': total_photos,
                'processing_time': processing_time
            }
        )
    
    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get notification history
        
        Args:
            limit: Maximum number of notifications to return
            
        Returns:
            List of recent notifications
        """
        if self.history is None:
            return []
        return self.history.get_recent(limit)
    
    def get_history_by_type(
        self,
        notification_type: NotificationType,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get notification history by type
        
        Args:
            notification_type: Type of notifications to retrieve
            limit: Maximum number of notifications to return
            
        Returns:
            List of notifications of specified type
        """
        if self.history is None:
            return []
        return self.history.get_by_type(notification_type, limit)
    
    def get_history_by_priority(
        self,
        priority: NotificationPriority,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get notification history by priority
        
        Args:
            priority: Priority level
            limit: Maximum number of notifications to return
            
        Returns:
            List of notifications with specified priority
        """
        if self.history is None:
            return []
        return self.history.get_by_priority(priority, limit)
    
    def clear_old_history(self, days: int = 30) -> int:
        """
        Clear old notification history
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of notifications removed
        """
        if self.history is None:
            return 0
        return self.history.clear_old(days)
    
    def clear_all_history(self) -> None:
        """Clear all notification history"""
        if self.history:
            self.history.clear_all()


# Singleton instance
_notifier_instance: Optional[DesktopNotifier] = None


def get_notifier() -> DesktopNotifier:
    """
    Get singleton desktop notifier instance
    
    Returns:
        DesktopNotifier instance
    """
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = DesktopNotifier()
    return _notifier_instance


def send_notification(
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.SYSTEM_STATUS,
    priority: NotificationPriority = NotificationPriority.MEDIUM,
    **kwargs
) -> bool:
    """
    Convenience function to send notification
    
    Args:
        title: Notification title
        message: Notification message
        notification_type: Type of notification
        priority: Priority level
        **kwargs: Additional arguments passed to send()
        
    Returns:
        True if notification was sent successfully
    """
    notifier = get_notifier()
    return notifier.send(title, message, notification_type, priority, **kwargs)


if __name__ == '__main__':
    # Setup logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=== Testing Desktop Notifier ===\n")
    
    # Test 1: Initialize notifier
    print("Test 1: Initialize notifier")
    notifier = DesktopNotifier()
    print(f"✓ Notifier initialized for platform: {notifier.platform}")
    
    # Test 2: Send basic notification
    print("\nTest 2: Send basic notification")
    success = notifier.send(
        title="Test Notification",
        message="This is a test notification from Junmai AutoDev",
        notification_type=NotificationType.SYSTEM_STATUS,
        priority=NotificationPriority.MEDIUM
    )
    print(f"✓ Notification sent: {success}")
    
    # Test 3: Send processing complete notification
    print("\nTest 3: Send processing complete notification")
    success = notifier.send_processing_complete(
        session_name="2025-11-08_Wedding",
        photo_count=120,
        success_rate=95.5
    )
    print(f"✓ Processing complete notification sent: {success}")
    
    # Test 4: Send approval required notification
    print("\nTest 4: Send approval required notification")
    success = notifier.send_approval_required(pending_count=15)
    print(f"✓ Approval required notification sent: {success}")
    
    # Test 5: Send error notification
    print("\nTest 5: Send error notification")
    success = notifier.send_error(
        error_message="Failed to process photo",
        error_details="GPU memory exceeded"
    )
    print(f"✓ Error notification sent: {success}")
    
    # Test 6: Get notification history
    print("\nTest 6: Get notification history")
    history = notifier.get_history(limit=10)
    print(f"✓ Retrieved {len(history)} notifications from history")
    
    # Test 7: Get history by type
    print("\nTest 7: Get history by type")
    error_history = notifier.get_history_by_type(NotificationType.ERROR)
    print(f"✓ Retrieved {len(error_history)} error notifications")
    
    # Test 8: Get history by priority
    print("\nTest 8: Get history by priority")
    high_priority = notifier.get_history_by_priority(NotificationPriority.HIGH)
    print(f"✓ Retrieved {len(high_priority)} high priority notifications")
    
    print("\n=== All tests completed! ===")
