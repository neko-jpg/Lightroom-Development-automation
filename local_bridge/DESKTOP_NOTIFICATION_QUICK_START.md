# Desktop Notification System - Quick Start Guide

## Installation

### 1. Install Dependencies

```bash
# Windows
pip install win10toast

# macOS
pip install pync

# Both platforms (already installed)
pip install sqlalchemy
```

### 2. Verify Installation

```python
from desktop_notifier import DesktopNotifier

notifier = DesktopNotifier()
print(f"Platform: {notifier.platform}")
print(f"Notifier available: {notifier._notifier is not None}")
```

## Basic Usage

### Send Your First Notification

```python
from desktop_notifier import get_notifier, NotificationType, NotificationPriority

# Get notifier instance
notifier = get_notifier()

# Send notification
notifier.send(
    title="Hello from Junmai AutoDev!",
    message="Your first desktop notification",
    notification_type=NotificationType.SYSTEM_STATUS,
    priority=NotificationPriority.MEDIUM
)
```

### Send Test Notification

```bash
# Via API
curl -X POST http://localhost:5100/desktop-notifications/test

# Via Python
python -c "from desktop_notifier import get_notifier; get_notifier().send('Test', 'Test message')"
```

## Common Use Cases

### 1. Processing Complete

```python
notifier.send_processing_complete(
    session_name="2025-11-08_Wedding",
    photo_count=120,
    success_rate=95.5
)
```

### 2. Approval Required

```python
notifier.send_approval_required(pending_count=15)
```

### 3. Error Notification

```python
notifier.send_error(
    error_message="GPU memory exceeded",
    error_details="Processing paused. Free up GPU memory."
)
```

### 4. Export Complete

```python
notifier.send_export_complete(
    export_preset="SNS",
    photo_count=50,
    destination="D:/Export/SNS"
)
```

## API Quick Reference

### Send Notification

```bash
curl -X POST http://localhost:5100/desktop-notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Processing Complete",
    "message": "120 photos processed",
    "type": "processing_complete",
    "priority": 2
  }'
```

### Get History

```bash
# Get recent 10 notifications
curl http://localhost:5100/desktop-notifications/history?limit=10

# Get unread notifications
curl http://localhost:5100/desktop-notifications/history?unread=true

# Get error notifications
curl http://localhost:5100/desktop-notifications/history?type=error
```

### Get Statistics

```bash
curl http://localhost:5100/desktop-notifications/stats
```

## Priority Levels

| Priority | Value | Use Case | Sound | Duration |
|----------|-------|----------|-------|----------|
| LOW | 1 | Batch completion, statistics | No | 3s |
| MEDIUM | 2 | Processing complete, approval | Yes | 5s |
| HIGH | 3 | Errors, critical issues | Yes | 10s |

## Notification Types

| Type | Description | Default Priority |
|------|-------------|------------------|
| `processing_complete` | Batch processing done | MEDIUM |
| `approval_required` | Photos need approval | MEDIUM |
| `error` | System errors | HIGH |
| `export_complete` | Export finished | LOW |
| `batch_complete` | Batch operation done | LOW |
| `system_status` | General updates | MEDIUM |

## Integration with Your Code

### In Job Queue

```python
from desktop_notifier import get_notifier

def process_job(job):
    notifier = get_notifier()
    
    try:
        # Process job
        result = do_processing(job)
        
        # Notify success
        notifier.send_processing_complete(
            session_name=job.session_name,
            photo_count=result.photo_count,
            success_rate=result.success_rate
        )
    except Exception as e:
        # Notify error
        notifier.send_error(
            error_message=str(e),
            error_details=f"Job ID: {job.id}"
        )
```

### In Flask App

```python
from flask import Flask
from api_desktop_notifications import desktop_notifications_bp

app = Flask(__name__)
app.register_blueprint(desktop_notifications_bp)

# Now endpoints are available at /desktop-notifications/*
```

## Viewing History

### Python

```python
from desktop_notifier import get_notifier

notifier = get_notifier()

# Get all recent notifications
history = notifier.get_history(limit=50)

# Get error notifications only
errors = notifier.get_history_by_type(NotificationType.ERROR)

# Get high priority notifications
urgent = notifier.get_history_by_priority(NotificationPriority.HIGH)

# Display
for notification in history:
    print(f"{notification['title']}: {notification['message']}")
```

### API

```bash
# Get recent notifications
curl http://localhost:5100/desktop-notifications/history?limit=20

# Get errors from last 7 days
curl "http://localhost:5100/desktop-notifications/history?type=error&days=7"

# Get high priority notifications
curl "http://localhost:5100/desktop-notifications/history?priority=3"
```

## Managing History

### Clear Old Notifications

```python
# Clear notifications older than 30 days
removed = notifier.clear_old_history(days=30)
print(f"Removed {removed} old notifications")
```

```bash
# Via API
curl -X POST "http://localhost:5100/desktop-notifications/history/clear?days=30"
```

### Mark as Read

```python
# Via API
curl -X POST http://localhost:5100/desktop-notifications/history/123/read

# Mark all as read
curl -X POST http://localhost:5100/desktop-notifications/history/mark-all-read
```

## Troubleshooting

### Notifications Not Appearing?

**Windows:**
```powershell
# Check if notifications are enabled
Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\PushNotifications" -Name "ToastEnabled"
```

**macOS:**
```bash
# Check notification permissions
# System Preferences > Notifications > Terminal (or your app)
```

### Import Errors?

```bash
# Windows
pip install --upgrade win10toast

# macOS
pip install --upgrade pync
```

### History Not Saving?

```python
# Ensure history is enabled
notifier = DesktopNotifier(enable_history=True)

# Check data directory permissions
import os
data_dir = "local_bridge/data"
print(f"Data directory exists: {os.path.exists(data_dir)}")
print(f"Data directory writable: {os.access(data_dir, os.W_OK)}")
```

## Next Steps

1. **Read Full Documentation**: See `DESKTOP_NOTIFICATION_IMPLEMENTATION.md`
2. **Run Examples**: Execute `example_desktop_notification_usage.py`
3. **Run Tests**: `pytest test_desktop_notifications.py -v`
4. **Integrate**: Add notifications to your workflow

## Quick Tips

✅ **DO:**
- Use appropriate priority levels
- Keep titles concise
- Provide actionable information
- Clear old history regularly

❌ **DON'T:**
- Spam notifications
- Use HIGH priority for routine events
- Forget to handle notification failures
- Store sensitive data in notifications

## Example Workflow

```python
from desktop_notifier import get_notifier, NotificationType, NotificationPriority

notifier = get_notifier()

# 1. Start processing
notifier.send("Processing Started", "Starting batch processing...")

# 2. Processing complete
notifier.send_processing_complete("Wedding_2025", 120, 95.5)

# 3. Approval needed
notifier.send_approval_required(15)

# 4. Export complete
notifier.send_export_complete("SNS", 15, "D:/Export/SNS")

# 5. Check history
history = notifier.get_history(limit=10)
print(f"Sent {len(history)} notifications")
```

## Support

- **Documentation**: `DESKTOP_NOTIFICATION_IMPLEMENTATION.md`
- **Examples**: `example_desktop_notification_usage.py`
- **Tests**: `test_desktop_notifications.py`
- **API Reference**: See implementation documentation

---

**Ready to use!** Start sending notifications with just a few lines of code.
