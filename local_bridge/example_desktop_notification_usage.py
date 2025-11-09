"""
Example Usage: Desktop Notification System

This example demonstrates how to use the desktop notification system
for Windows Toast notifications and macOS Notification Center integration.
"""

import logging
from desktop_notifier import (
    DesktopNotifier,
    NotificationType,
    NotificationPriority,
    get_notifier,
    send_notification
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_basic_notification():
    """Example: Send basic notification"""
    print("\n=== Example 1: Basic Notification ===")
    
    notifier = DesktopNotifier()
    
    success = notifier.send(
        title="Junmai AutoDev",
        message="システムが正常に起動しました",
        notification_type=NotificationType.SYSTEM_STATUS,
        priority=NotificationPriority.MEDIUM
    )
    
    print(f"Notification sent: {success}")


def example_processing_complete():
    """Example: Processing complete notification"""
    print("\n=== Example 2: Processing Complete ===")
    
    notifier = get_notifier()
    
    success = notifier.send_processing_complete(
        session_name="2025-11-08_Wedding",
        photo_count=120,
        success_rate=95.5
    )
    
    print(f"Processing complete notification sent: {success}")


def example_approval_required():
    """Example: Approval required notification"""
    print("\n=== Example 3: Approval Required ===")
    
    notifier = get_notifier()
    
    success = notifier.send_approval_required(
        pending_count=15
    )
    
    print(f"Approval required notification sent: {success}")


def example_error_notification():
    """Example: Error notification"""
    print("\n=== Example 4: Error Notification ===")
    
    notifier = get_notifier()
    
    success = notifier.send_error(
        error_message="GPU メモリ不足",
        error_details="処理を一時停止しました。GPU メモリを確保してください。"
    )
    
    print(f"Error notification sent: {success}")


def example_export_complete():
    """Example: Export complete notification"""
    print("\n=== Example 5: Export Complete ===")
    
    notifier = get_notifier()
    
    success = notifier.send_export_complete(
        export_preset="SNS",
        photo_count=50,
        destination="D:/Export/SNS"
    )
    
    print(f"Export complete notification sent: {success}")


def example_batch_complete():
    """Example: Batch complete notification"""
    print("\n=== Example 6: Batch Complete ===")
    
    notifier = get_notifier()
    
    success = notifier.send_batch_complete(
        batch_name="Wedding_Batch_1",
        total_photos=200,
        processing_time=125.5
    )
    
    print(f"Batch complete notification sent: {success}")


def example_priority_management():
    """Example: Different priority levels"""
    print("\n=== Example 7: Priority Management ===")
    
    notifier = get_notifier()
    
    # Low priority - batch completion
    notifier.send(
        title="バッチ処理完了",
        message="夜間バッチが完了しました",
        notification_type=NotificationType.BATCH_COMPLETE,
        priority=NotificationPriority.LOW,
        sound=False
    )
    
    # Medium priority - processing complete
    notifier.send(
        title="処理完了",
        message="50枚の写真を処理しました",
        notification_type=NotificationType.PROCESSING_COMPLETE,
        priority=NotificationPriority.MEDIUM
    )
    
    # High priority - error
    notifier.send(
        title="緊急エラー",
        message="システムエラーが発生しました",
        notification_type=NotificationType.ERROR,
        priority=NotificationPriority.HIGH,
        duration=10
    )
    
    print("Sent notifications with different priorities")


def example_notification_history():
    """Example: Working with notification history"""
    print("\n=== Example 8: Notification History ===")
    
    notifier = get_notifier()
    
    # Send some notifications
    notifier.send("Test 1", "Message 1")
    notifier.send("Test 2", "Message 2")
    notifier.send_error("Test Error")
    
    # Get all recent notifications
    all_history = notifier.get_history(limit=10)
    print(f"Total notifications in history: {len(all_history)}")
    
    # Get error notifications only
    error_history = notifier.get_history_by_type(NotificationType.ERROR)
    print(f"Error notifications: {len(error_history)}")
    
    # Get high priority notifications
    high_priority = notifier.get_history_by_priority(NotificationPriority.HIGH)
    print(f"High priority notifications: {len(high_priority)}")
    
    # Display recent notifications
    print("\nRecent notifications:")
    for notification in all_history[-5:]:
        print(f"  - {notification['title']}: {notification['message']}")


def example_history_management():
    """Example: Managing notification history"""
    print("\n=== Example 9: History Management ===")
    
    notifier = get_notifier()
    
    # Get current history count
    history = notifier.get_history()
    print(f"Current history count: {len(history)}")
    
    # Clear old notifications (older than 30 days)
    removed = notifier.clear_old_history(days=30)
    print(f"Removed {removed} old notifications")
    
    # Note: Uncomment to clear all history
    # notifier.clear_all_history()
    # print("Cleared all notification history")


def example_convenience_function():
    """Example: Using convenience function"""
    print("\n=== Example 10: Convenience Function ===")
    
    success = send_notification(
        title="クイック通知",
        message="便利関数を使用した通知",
        notification_type=NotificationType.SYSTEM_STATUS,
        priority=NotificationPriority.MEDIUM
    )
    
    print(f"Notification sent via convenience function: {success}")


def example_custom_notification():
    """Example: Custom notification with data"""
    print("\n=== Example 11: Custom Notification with Data ===")
    
    notifier = get_notifier()
    
    success = notifier.send(
        title="カスタム通知",
        message="追加データ付きの通知",
        notification_type=NotificationType.SYSTEM_STATUS,
        priority=NotificationPriority.MEDIUM,
        duration=7,
        sound=True,
        data={
            'session_id': 123,
            'user_action': 'manual_trigger',
            'timestamp': '2025-11-08T14:30:00'
        }
    )
    
    print(f"Custom notification sent: {success}")
    
    # Retrieve and display the notification data
    history = notifier.get_history(limit=1)
    if history:
        latest = history[-1]
        print(f"Notification data: {latest.get('data', {})}")


def example_workflow_notifications():
    """Example: Complete workflow with notifications"""
    print("\n=== Example 12: Complete Workflow ===")
    
    notifier = get_notifier()
    
    # 1. Start processing
    notifier.send(
        title="処理開始",
        message="セッション '2025-11-08_Portrait' の処理を開始します",
        notification_type=NotificationType.SYSTEM_STATUS,
        priority=NotificationPriority.LOW
    )
    
    # 2. Processing complete
    notifier.send_processing_complete(
        session_name="2025-11-08_Portrait",
        photo_count=85,
        success_rate=98.8
    )
    
    # 3. Approval required
    notifier.send_approval_required(pending_count=12)
    
    # 4. Export complete
    notifier.send_export_complete(
        export_preset="SNS",
        photo_count=12,
        destination="D:/Export/SNS"
    )
    
    print("Workflow notifications sent")


if __name__ == '__main__':
    print("=== Desktop Notification System Examples ===\n")
    
    # Run examples
    example_basic_notification()
    example_processing_complete()
    example_approval_required()
    example_error_notification()
    example_export_complete()
    example_batch_complete()
    example_priority_management()
    example_notification_history()
    example_history_management()
    example_convenience_function()
    example_custom_notification()
    example_workflow_notifications()
    
    print("\n=== All examples completed! ===")
