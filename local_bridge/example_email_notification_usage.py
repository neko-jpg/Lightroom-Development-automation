"""
Example usage of Email Notification System

This script demonstrates how to use the email notification system
for various notification types.
"""

import logging
from email_notifier import (
    EmailNotifier,
    EmailNotificationType,
    get_email_notifier,
    send_email_notification
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_1_basic_configuration():
    """Example 1: Configure email notifications"""
    print("\n=== Example 1: Configure Email Notifications ===")
    
    notifier = get_email_notifier()
    
    # Update configuration
    notifier.update_config({
        'enabled': True,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'use_tls': True,
        'username': 'your-email@gmail.com',
        'password': 'your-app-password',  # Use app-specific password for Gmail
        'from_address': 'your-email@gmail.com',
        'from_name': 'Junmai AutoDev',
        'to_addresses': ['recipient@example.com'],
        'batch_notifications': {
            'enabled': True,
            'interval_minutes': 60,
            'min_notifications': 3
        },
        'notification_types': {
            'processing_complete': True,
            'approval_required': True,
            'error': True,
            'export_complete': False,
            'batch_complete': True,
            'daily_summary': True,
            'weekly_summary': True
        }
    })
    
    print("✓ Email configuration updated")
    print(f"  SMTP Server: {notifier.config.get('smtp_server')}")
    print(f"  Enabled: {notifier.config.is_enabled()}")


def example_2_test_connection():
    """Example 2: Test SMTP connection"""
    print("\n=== Example 2: Test SMTP Connection ===")
    
    notifier = get_email_notifier()
    
    if not notifier.config.is_enabled():
        print("⚠ Email notifications are disabled")
        print("  Please configure SMTP settings first")
        return
    
    print("Testing SMTP connection...")
    success = notifier.test_connection()
    
    if success:
        print("✓ SMTP connection successful")
    else:
        print("✗ SMTP connection failed")
        print("  Please check your SMTP settings")


def example_3_processing_complete():
    """Example 3: Send processing complete notification"""
    print("\n=== Example 3: Processing Complete Notification ===")
    
    notifier = get_email_notifier()
    
    success = notifier.send_processing_complete(
        session_name='2025-11-08_Wedding',
        photo_count=120,
        success_rate=95.5,
        processing_time='2h 15m'
    )
    
    if success:
        print("✓ Processing complete notification sent")
    else:
        print("✗ Failed to send notification")


def example_4_approval_required():
    """Example 4: Send approval required notification"""
    print("\n=== Example 4: Approval Required Notification ===")
    
    notifier = get_email_notifier()
    
    sessions = [
        {'name': '2025-11-08_Wedding', 'count': 10},
        {'name': '2025-11-07_Portrait', 'count': 5}
    ]
    
    success = notifier.send_approval_required(
        pending_count=15,
        sessions=sessions
    )
    
    if success:
        print("✓ Approval required notification sent")
    else:
        print("✗ Failed to send notification")


def example_5_error_notification():
    """Example 5: Send error notification"""
    print("\n=== Example 5: Error Notification ===")
    
    notifier = get_email_notifier()
    
    success = notifier.send_error(
        error_type='Processing Error',
        error_message='Failed to process photo IMG_5432.CR3',
        error_details='GPU memory exceeded: 8GB limit reached'
    )
    
    if success:
        print("✓ Error notification sent")
    else:
        print("✗ Failed to send notification")


def example_6_export_complete():
    """Example 6: Send export complete notification"""
    print("\n=== Example 6: Export Complete Notification ===")
    
    notifier = get_email_notifier()
    
    success = notifier.send_export_complete(
        export_preset='SNS',
        photo_count=50,
        destination='D:/Export/SNS'
    )
    
    if success:
        print("✓ Export complete notification sent")
    else:
        print("✗ Failed to send notification")


def example_7_batch_complete():
    """Example 7: Send batch complete notification"""
    print("\n=== Example 7: Batch Complete Notification ===")
    
    notifier = get_email_notifier()
    
    success = notifier.send_batch_complete(
        batch_name='Evening Batch',
        total_photos=200,
        processing_time='3h 45m',
        avg_time_per_photo='1.1s'
    )
    
    if success:
        print("✓ Batch complete notification sent")
    else:
        print("✗ Failed to send notification")


def example_8_daily_summary():
    """Example 8: Send daily summary notification"""
    print("\n=== Example 8: Daily Summary Notification ===")
    
    notifier = get_email_notifier()
    
    success = notifier.send_daily_summary(
        date='2025-11-08',
        total_imported=150,
        total_selected=120,
        total_processed=100,
        total_exported=80,
        avg_processing_time='2.3s',
        success_rate=95.5
    )
    
    if success:
        print("✓ Daily summary notification sent")
    else:
        print("✗ Failed to send notification")


def example_9_weekly_summary():
    """Example 9: Send weekly summary notification"""
    print("\n=== Example 9: Weekly Summary Notification ===")
    
    notifier = get_email_notifier()
    
    daily_breakdown = [
        {'date': '2025-11-01', 'processed': 120},
        {'date': '2025-11-02', 'processed': 150},
        {'date': '2025-11-03', 'processed': 100},
        {'date': '2025-11-04', 'processed': 180},
        {'date': '2025-11-05', 'processed': 90},
        {'date': '2025-11-06', 'processed': 110},
        {'date': '2025-11-07', 'processed': 130}
    ]
    
    success = notifier.send_weekly_summary(
        week_range='2025-11-01 ~ 2025-11-07',
        total_imported=1000,
        total_processed=880,
        total_exported=650,
        avg_success_rate=95.0,
        top_preset='WhiteLayer_Transparency_v4',
        daily_breakdown=daily_breakdown
    )
    
    if success:
        print("✓ Weekly summary notification sent")
    else:
        print("✗ Failed to send notification")


def example_10_batch_notifications():
    """Example 10: Use batch notification buffering"""
    print("\n=== Example 10: Batch Notification Buffering ===")
    
    notifier = get_email_notifier()
    
    # Add notifications to batch
    print("Adding notifications to batch buffer...")
    
    for i in range(5):
        should_flush = notifier.add_to_batch({
            'type': 'processing_complete',
            'message': f'Processed photo {i+1}'
        })
        print(f"  Added notification {i+1} (flush: {should_flush})")
        
        if should_flush:
            print("  Sending batch...")
            success = notifier.send_batch()
            if success:
                print("  ✓ Batch sent successfully")
            else:
                print("  ✗ Failed to send batch")


def example_11_custom_email():
    """Example 11: Send custom email with template"""
    print("\n=== Example 11: Custom Email with Template ===")
    
    notifier = get_email_notifier()
    
    # Use convenience function
    success = send_email_notification(
        EmailNotificationType.PROCESSING_COMPLETE,
        {
            'session_name': 'Custom Session',
            'photo_count': 75,
            'success_rate': 98.0,
            'processing_time': '1h 30m',
            'dashboard_url': 'http://localhost:5100/dashboard'
        },
        to_addresses=['custom-recipient@example.com']
    )
    
    if success:
        print("✓ Custom email sent")
    else:
        print("✗ Failed to send custom email")


def example_12_disable_specific_types():
    """Example 12: Disable specific notification types"""
    print("\n=== Example 12: Disable Specific Notification Types ===")
    
    notifier = get_email_notifier()
    
    # Disable export complete notifications
    config = notifier.get_config()
    config['notification_types']['export_complete'] = False
    notifier.update_config(config)
    
    print("✓ Export complete notifications disabled")
    
    # Try to send (will be skipped)
    success = notifier.send_export_complete(
        export_preset='Test',
        photo_count=10,
        destination='/test'
    )
    
    print(f"  Send attempt result: {success}")
    print("  (Should be False because type is disabled)")


if __name__ == '__main__':
    print("=== Email Notification System Examples ===")
    print("\nNote: These examples require valid SMTP configuration.")
    print("Please update the configuration in example_1_basic_configuration()")
    print("with your actual SMTP credentials before running.\n")
    
    # Run examples
    try:
        example_1_basic_configuration()
        example_2_test_connection()
        
        # Uncomment to test actual email sending
        # (requires valid SMTP configuration)
        
        # example_3_processing_complete()
        # example_4_approval_required()
        # example_5_error_notification()
        # example_6_export_complete()
        # example_7_batch_complete()
        # example_8_daily_summary()
        # example_9_weekly_summary()
        # example_10_batch_notifications()
        # example_11_custom_email()
        # example_12_disable_specific_types()
        
        print("\n=== Examples completed! ===")
        
    except Exception as e:
        logger.error(f"Error running examples: {e}")
        print(f"\n✗ Error: {e}")
