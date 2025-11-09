# Desktop Notification System - Quick Reference

## Installation

```bash
# Windows
pip install win10toast

# macOS
pip install pync
```

## Basic Usage

```python
from desktop_notifier import get_notifier, NotificationType, NotificationPriority

notifier = get_notifier()
```

## Send Notifications

### Basic
```python
notifier.send("Title", "Message")
```

### With Priority
```python
notifier.send(
    title="Title",
    message="Message",
    notification_type=NotificationType.ERROR,
    priority=NotificationPriority.HIGH
)
```

### Convenience Methods
```python
# Processing complete
notifier.send_processing_complete("Session", 120, 95.5)

# Approval required
notifier.send_approval_required(15)

# Error
notifier.send_error("Error message", "Details")

# Export complete
notifier.send_export_complete("SNS", 50, "/path")

# Batch complete
notifier.send_batch_complete("Batch", 200, 125.5)
```

## History

```python
# Get recent
history = notifier.get_history(limit=50)

# Filter by type
errors = notifier.get_history_by_type(NotificationType.ERROR)

# Filter by priority
urgent = notifier.get_history_by_priority(NotificationPriority.HIGH)

# Clear old
removed = notifier.clear_old_history(days=30)

# Clear all
notifier.clear_all_history()
```

## API Endpoints

### Send
```bash
POST /desktop-notifications/send
{
  "title": "Title",
  "message": "Message",
  "type": "processing_complete",
  "priority": 2
}
```

### History
```bash
GET /desktop-notifications/history?limit=50&type=error&priority=3
```

### Stats
```bash
GET /desktop-notifications/stats
```

### Test
```bash
POST /desktop-notifications/test
```

## Notification Types

| Type | Value |
|------|-------|
| Processing Complete | `processing_complete` |
| Approval Required | `approval_required` |
| Error | `error` |
| Export Complete | `export_complete` |
| Batch Complete | `batch_complete` |
| System Status | `system_status` |

## Priority Levels

| Priority | Value | Sound | Duration |
|----------|-------|-------|----------|
| LOW | 1 | No | 3s |
| MEDIUM | 2 | Yes | 5s |
| HIGH | 3 | Yes | 10s |

## Integration

### Flask App
```python
from api_desktop_notifications import desktop_notifications_bp
app.register_blueprint(desktop_notifications_bp)
```

### Job Queue
```python
def on_job_complete(job):
    get_notifier().send_processing_complete(
        job.session_name, job.photo_count, job.success_rate
    )
```

### Error Handler
```python
def handle_error(error):
    get_notifier().send_error(str(error), error.details)
```

## Troubleshooting

### Windows
```bash
# Install dependency
pip install win10toast

# Check notifications enabled
# Settings > System > Notifications & actions
```

### macOS
```bash
# Install dependency
pip install pync

# Check permissions
# System Preferences > Notifications
```

## Files

- `desktop_notifier.py` - Main implementation
- `api_desktop_notifications.py` - API endpoints
- `test_desktop_notifications.py` - Tests
- `example_desktop_notification_usage.py` - Examples
- `DESKTOP_NOTIFICATION_IMPLEMENTATION.md` - Full docs
- `DESKTOP_NOTIFICATION_QUICK_START.md` - Quick start

---

**Quick Start**: `py local_bridge/example_desktop_notification_usage.py`
