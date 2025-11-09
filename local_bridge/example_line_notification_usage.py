"""
Example usage of LINE Notify integration

This script demonstrates how to use the LINE notifier for various notification types.
"""

import logging
from pathlib import Path
from line_notifier import (
    LineNotifier,
    LineNotificationType,
    get_line_notifier,
    send_line_notification
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_basic_notification():
    """Example: Send basic LINE notification"""
    print("\n=== Example 1: Basic Notification ===")
    
    notifier = get_line_notifier()
    
    # Send simple message
    success = notifier.send(
        message="テスト通知: Junmai AutoDev システムが起動しました",
        notification_type=LineNotificationType.SYSTEM_STATUS
    )
    
    print(f"Notification sent: {success}")


def example_processing_complete():
    """Example: Send processing complete notification"""
    print("\n=== Example 2: Processing Complete ===")
    
    notifier = get_line_notifier()
    
    success = notifier.send_processing_complete(
        session_name="2025-11-08_Wedding",
        photo_count=120,
        success_rate=95.5,
        processing_time="2h 15m"
    )
    
    print(f"Processing complete notification sent: {success}")


def example_approval_required():
    """Example: Send approval required notification"""
    print("\n=== Example 3: Approval Required ===")
    
    notifier = get_line_notifier()
    
    sessions = [
        {'name': '2025-11-08_Wedding', 'count': 45},
        {'name': '2025-11-07_Portrait', 'count': 12},
        {'name': '2025-11-06_Landscape', 'count': 8}
    ]
    
    success = notifier.send_approval_required(
        pending_count=65,
        sessions=sessions
    )
    
    print(f"Approval required notification sent: {success}")


def example_error_notification():
    """Example: Send error notification"""
    print("\n=== Example 4: Error Notification ===")
    
    notifier = get_line_notifier()
    
    success = notifier.send_error(
        error_type="GPU Memory Error",
        error_message="GPU memory exceeded during processing",
        error_details="Failed to allocate 2GB for model inference. Current usage: 7.5GB/8GB"
    )
    
    print(f"Error notification sent: {success}")


def example_export_complete():
    """Example: Send export complete notification"""
    print("\n=== Example 5: Export Complete ===")
    
    notifier = get_line_notifier()
    
    success = notifier.send_export_complete(
        export_preset="SNS_2048px",
        photo_count=45,
        destination="D:/Export/SNS/2025-11-08"
    )
    
    print(f"Export complete notification sent: {success}")


def example_batch_complete():
    """Example: Send batch complete notification"""
    print("\n=== Example 6: Batch Complete ===")
    
    notifier = get_line_notifier()
    
    success = notifier.send_batch_complete(
        batch_name="Wedding_Batch_001",
        total_photos=120,
        processing_time="2h 15m",
        avg_time_per_photo="1.1s"
    )
    
    print(f"Batch complete notification sent: {success}")


def example_with_image():
    """Example: Send notification with image attachment"""
    print("\n=== Example 7: Notification with Image ===")
    
    notifier = get_line_notifier()
    
    # Create a sample image path (replace with actual image)
    image_path = Path("sample_preview.jpg")
    
    if image_path.exists():
        success = notifier.send(
            message="処理完了: プレビュー画像を確認してください",
            notification_type=LineNotificationType.PROCESSING_COMPLETE,
            image_path=image_path
        )
        print(f"Notification with image sent: {success}")
    else:
        print(f"⚠ Image not found: {image_path}")
        print("  Sending notification without image")
        success = notifier.send(
            message="処理完了: プレビュー画像を確認してください",
            notification_type=LineNotificationType.PROCESSING_COMPLETE
        )
        print(f"Notification sent: {success}")


def example_with_sticker():
    """Example: Send notification with LINE sticker"""
    print("\n=== Example 8: Notification with Sticker ===")
    
    notifier = get_line_notifier()
    
    # LINE sticker IDs (package 1, sticker 2 = happy face)
    success = notifier.send(
        message="処理が正常に完了しました！",
        notification_type=LineNotificationType.PROCESSING_COMPLETE,
        sticker_package_id=1,
        sticker_id=2
    )
    
    print(f"Notification with sticker sent: {success}")


def example_check_token_status():
    """Example: Check LINE Notify token status"""
    print("\n=== Example 9: Check Token Status ===")
    
    notifier = get_line_notifier()
    
    status = notifier.check_token_status()
    
    if status:
        print("✓ Token status:")
        print(f"  Status: {status.get('status')}")
        print(f"  Message: {status.get('message')}")
        print(f"  Target: {status.get('target')}")
        print(f"  Target Type: {status.get('targetType')}")
    else:
        print("✗ Failed to check token status")
        print("  Make sure token is configured correctly")


def example_test_connection():
    """Example: Test LINE Notify connection"""
    print("\n=== Example 10: Test Connection ===")
    
    notifier = get_line_notifier()
    
    success = notifier.test_connection()
    
    if success:
        print("✓ Connection test successful")
    else:
        print("✗ Connection test failed")
        print("  Check your token configuration")


def example_configuration():
    """Example: Configure LINE Notify"""
    print("\n=== Example 11: Configuration ===")
    
    notifier = get_line_notifier()
    
    # Get current configuration
    config = notifier.get_config()
    print("Current configuration:")
    print(f"  Enabled: {config.get('enabled')}")
    print(f"  Token configured: {bool(config.get('token'))}")
    print(f"  Notification types:")
    for notif_type, enabled in config.get('notification_types', {}).items():
        print(f"    {notif_type}: {enabled}")
    
    # Update configuration
    print("\nUpdating configuration...")
    notifier.update_config({
        'enabled': True,
        'notification_types': {
            'processing_complete': True,
            'approval_required': True,
            'error': True,
            'export_complete': False,
            'batch_complete': True,
            'system_status': False
        }
    })
    print("✓ Configuration updated")


def example_convenience_function():
    """Example: Use convenience function"""
    print("\n=== Example 12: Convenience Function ===")
    
    # Use the convenience function for quick notifications
    success = send_line_notification(
        LineNotificationType.PROCESSING_COMPLETE,
        {
            'session_name': 'Quick_Test',
            'photo_count': 10,
            'success_rate': 100.0,
            'processing_time': '30s'
        }
    )
    
    print(f"Notification sent via convenience function: {success}")


def main():
    """Run all examples"""
    print("=" * 60)
    print("LINE Notify Integration - Example Usage")
    print("=" * 60)
    
    # Check if LINE Notify is configured
    notifier = get_line_notifier()
    if not notifier.token_manager.is_enabled():
        print("\n⚠ WARNING: LINE Notify is not configured!")
        print("\nTo use LINE Notify:")
        print("1. Visit https://notify-bot.line.me/")
        print("2. Generate a personal access token")
        print("3. Update the configuration file:")
        print(f"   {notifier.token_manager.config_file}")
        print("4. Set 'enabled': true and 'token': 'YOUR_TOKEN'")
        print("\nRunning examples in demo mode (notifications will not be sent)...\n")
    
    # Run examples
    try:
        example_configuration()
        example_basic_notification()
        example_processing_complete()
        example_approval_required()
        example_error_notification()
        example_export_complete()
        example_batch_complete()
        example_with_image()
        example_with_sticker()
        example_check_token_status()
        example_test_connection()
        example_convenience_function()
        
    except Exception as e:
        logger.error(f"Error running examples: {e}")
        raise
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
