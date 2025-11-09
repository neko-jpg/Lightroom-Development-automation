# Desktop Notification System Implementation

## Overview

The Desktop Notification System provides cross-platform desktop notifications with Windows Toast notifications and macOS Notification Center integration. It includes notification priority management and comprehensive notification history tracking.

**Requirements Implemented**: 8.1, 8.2, 8.3

## Features

### Core Features
- ✅ Windows Toast notifications
- ✅ macOS Notification Center integration
- ✅ Notification priority management (Low, Medium, High)
- ✅ Notification history management
- ✅ Persistent notification storage
- ✅ Type-based notification filtering
- ✅ Priority-based notification filtering
- ✅ Automatic history cleanup

### Notification Types
1. **Processing Complete** - Batch processing completion
2. **Approval Required** - Photos pending approval
3. **Error** - System errors and critical issues
4. **Export Complete** - Export operation completion
5. **Batch Complete** - Batch operation completion
6. **System Status** - General system notifications

### Priority Levels
1. **Low (1)** - Batch completion, statistics (no sound)
2. **Medium (2)** - Processing complete, approval required
3. **High (3)** - Errors, critical issues (longer duration)

## Architecture

### Components

```
desktop_notifier.py
├── NotificationHistory      # History management
├── DesktopNotifier          # Main notifier class
├── NotificationType         # Notification type enum
└── NotificationPriority     # Priority level enum

api_desktop_notifications.py
├── /send                    # Send notification
├── /history                 # Get notification history
├── /history/<id>            # Get specific notification
├── /history/<id>/read       # Mark as read
├── /history/<id>/dismiss    # Dismiss notification
├── /history/mark-all-read   # Mark all as read
├── /history/clear           # Clear history
├── /stats                   # Get statistics
└── /test                    # Send test notification
```

### Database Schema

```sql
CREATE TABLE desktop_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    priority INTEGER NOT NULL DEFAULT 2,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read BOOLEAN DEFAULT FALSE,
    dismissed BOOLEAN DEFAULT FALSE,
    data TEXT,
    CHECK (notification_type IN ('processing_complete', 'approval_required', 
                                  'error', 'export_complete', 'batch_complete', 
                                  'system_status')),
    CHECK (priority IN (1, 2, 3))
);

CREATE INDEX idx_desktop_notifications_type ON desktop_notifications(notification_type);
CREATE INDEX idx_desktop_notifications_priority ON desktop_notifications(priority);
CREATE INDEX idx_desktop_notifications_sent_at ON desktop_notifications(sent_at);
```

## Installation

### Dependencies

```bash
# Windows
pip install win10toast

# macOS
pip install pync

# Both platforms
pip install sqlalchemy
```

### Platform-Specific Setup

#### Windows
- No additional setup required
- Uses Windows 10/11 Toast notifications
- Requires Windows 10 or later

#### macOS
- Requires macOS 10.8 or later
- Uses Notification Center
- May require notification permissions

## Usage

### Basic Usage

```python
from desktop_notifier import DesktopNotifier, NotificationType, NotificationPriority

# Initialize notifier
notifier = DesktopNotifier()

# Send basic notification
notifier.send(
    title="Processing Complete",
    message="120 photos processed successfully",
    notification_type=NotificationType.PROCESSING_COMPLETE,
    priority=NotificationPriority.MEDIUM
)
```

### Convenience Methods

```python
# Processing complete
notifier.send_processing_complete(
    session_name="2025-11-08_Wedding",
    photo_count=120,
    success_rate=95.5
)

# Approval required
notifier.send_approval_required(pending_count=15)

# Error notification
notifier.send_error(
    error_message="GPU memory exceeded",
    error_details="Processing paused"
)

# Export complete
notifier.send_export_complete(
    export_preset="SNS",
    photo_count=50,
    destination="/export/sns"
)

# Batch complete
notifier.send_batch_complete(
    batch_name="Wedding_Batch_1",
    total_photos=200,
    processing_time=125.5
)
```

### Singleton Pattern

```python
from desktop_notifier import get_notifier, send_notification

# Get singleton instance
notifier = get_notifier()

# Or use convenience function
send_notification(
    title="Quick Notification",
    message="Using convenience function",
    notification_type=NotificationType.SYSTEM_STATUS,
    priority=NotificationPriority.MEDIUM
)
```

### History Management

```python
# Get recent notifications
history = notifier.get_history(limit=50)

# Get by type
errors = notifier.get_history_by_type(NotificationType.ERROR)

# Get by priority
high_priority = notifier.get_history_by_priority(NotificationPriority.HIGH)

# Clear old notifications (older than 30 days)
removed = notifier.clear_old_history(days=30)

# Clear all history
notifier.clear_all_history()
```

## API Endpoints

### Send Notification

```http
POST /desktop-notifications/send
Content-Type: application/json

{
  "title": "Processing Complete",
  "message": "120 photos processed",
  "type": "processing_complete",
  "priority": 2,
  "duration": 5,
  "sound": true,
  "data": {
    "session_id": 123
  }
}
```

### Get History

```http
GET /desktop-notifications/history?limit=50&type=error&priority=3&unread=true&days=7
```

### Mark as Read

```http
POST /desktop-notifications/history/123/read
```

### Dismiss Notification

```http
POST /desktop-notifications/history/123/dismiss
```

### Mark All as Read

```http
POST /desktop-notifications/history/mark-all-read
```

### Clear History

```http
POST /desktop-notifications/history/clear?days=30
POST /desktop-notifications/history/clear?all=true
```

### Get Statistics

```http
GET /desktop-notifications/stats
```

Response:
```json
{
  "success": true,
  "stats": {
    "total": 1250,
    "unread": 15,
    "recent_24h": 45,
    "by_type": {
      "processing_complete": 500,
      "approval_required": 200,
      "error": 50,
      "export_complete": 300,
      "batch_complete": 150,
      "system_status": 50
    },
    "by_priority": {
      "1": 450,
      "2": 700,
      "3": 100
    }
  }
}
```

### Send Test Notification

```http
POST /desktop-notifications/test
```

## Integration Examples

### With Job Queue

```python
from desktop_notifier import get_notifier

def on_job_complete(job):
    notifier = get_notifier()
    
    if job.status == 'completed':
        notifier.send_processing_complete(
            session_name=job.session_name,
            photo_count=job.photo_count,
            success_rate=job.success_rate
        )
    elif job.status == 'failed':
        notifier.send_error(
            error_message=f"Job {job.id} failed",
            error_details=job.error_message
        )
```

### With Approval Queue

```python
def check_approval_queue():
    pending_count = get_pending_approval_count()
    
    if pending_count > 0:
        notifier = get_notifier()
        notifier.send_approval_required(pending_count)
```

### With Export Pipeline

```python
def on_export_complete(export_result):
    notifier = get_notifier()
    notifier.send_export_complete(
        export_preset=export_result.preset_name,
        photo_count=export_result.photo_count,
        destination=export_result.destination
    )
```

## Configuration

### Notification Settings (config.json)

```json
{
  "notifications": {
    "desktop": true,
    "quiet_hours": {
      "enabled": false,
      "start": "22:00",
      "end": "08:00"
    },
    "types": {
      "processing_complete": true,
      "approval_required": true,
      "error": true,
      "export_complete": true,
      "batch_complete": true,
      "system_status": true
    },
    "priority_settings": {
      "low": {
        "sound": false,
        "duration": 3
      },
      "medium": {
        "sound": true,
        "duration": 5
      },
      "high": {
        "sound": true,
        "duration": 10
      }
    }
  }
}
```

## Testing

### Run Tests

```bash
# Run all tests
pytest test_desktop_notifications.py -v

# Run specific test class
pytest test_desktop_notifications.py::TestDesktopNotifier -v

# Run with coverage
pytest test_desktop_notifications.py --cov=desktop_notifier --cov-report=html
```

### Test Coverage

- ✅ Notification history management
- ✅ Desktop notifier initialization
- ✅ Sending notifications
- ✅ Priority management
- ✅ Type filtering
- ✅ History persistence
- ✅ Singleton pattern
- ✅ Convenience functions

## Performance Considerations

### History Management
- Maximum history size: 1000 notifications
- Automatic cleanup of old notifications
- Indexed database queries for fast retrieval

### Notification Delivery
- Asynchronous notification sending (threaded on Windows)
- Non-blocking operation
- Graceful degradation if notification system unavailable

### Database Optimization
- Indexed columns: type, priority, sent_at
- Efficient filtering queries
- Batch operations for bulk updates

## Troubleshooting

### Windows Issues

**Problem**: Notifications not appearing
- **Solution**: Check Windows notification settings
- Ensure app notifications are enabled
- Check Focus Assist settings

**Problem**: win10toast import error
- **Solution**: `pip install win10toast`

### macOS Issues

**Problem**: Notifications not appearing
- **Solution**: Check System Preferences > Notifications
- Grant notification permissions to Terminal/Python

**Problem**: pync import error
- **Solution**: `pip install pync`

### General Issues

**Problem**: History not persisting
- **Solution**: Check file permissions for data directory
- Verify database file is writable

**Problem**: Notifications sent but not in history
- **Solution**: Ensure history is enabled: `DesktopNotifier(enable_history=True)`

## Best Practices

### Priority Guidelines
- **Low**: Batch completions, statistics, non-urgent updates
- **Medium**: Processing complete, approval requests, routine notifications
- **High**: Errors, critical issues, urgent actions required

### Notification Frequency
- Batch similar notifications together
- Avoid notification spam
- Use quiet hours for non-urgent notifications
- Implement rate limiting for high-frequency events

### Message Content
- Keep titles concise (< 50 characters)
- Provide actionable information
- Include relevant context in data field
- Use clear, user-friendly language

### History Management
- Clear old notifications regularly (30-90 days)
- Monitor history size
- Archive important notifications separately
- Implement retention policies

## Future Enhancements

### Planned Features
- [ ] Quiet hours implementation
- [ ] Notification grouping
- [ ] Custom notification sounds
- [ ] Rich notifications with images
- [ ] Action buttons in notifications
- [ ] Notification templates
- [ ] Multi-language support
- [ ] Notification scheduling

### Integration Opportunities
- Email notification fallback
- LINE Notify integration
- Slack/Discord webhooks
- Mobile push notifications
- SMS notifications

## References

- [Windows Toast Notifications](https://docs.microsoft.com/en-us/windows/apps/design/shell/tiles-and-notifications/toast-notifications-overview)
- [macOS Notification Center](https://developer.apple.com/documentation/usernotifications)
- [win10toast Documentation](https://github.com/jithurjacob/Windows-10-Toast-Notifications)
- [pync Documentation](https://github.com/SeTeM/pync)

## Support

For issues or questions:
1. Check troubleshooting section
2. Review example usage
3. Check test cases for reference implementations
4. Consult API documentation

---

**Version**: 1.0  
**Last Updated**: 2025-11-08  
**Status**: Production Ready
