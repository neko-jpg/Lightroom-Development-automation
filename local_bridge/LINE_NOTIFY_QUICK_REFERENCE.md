# LINE Notify Quick Reference

## Setup

```python
# 1. Get token from https://notify-bot.line.me/
# 2. Edit config/line_config.json:
{
  "enabled": true,
  "token": "YOUR_TOKEN_HERE"
}
```

## Basic Usage

```python
from line_notifier import get_line_notifier

notifier = get_line_notifier()
notifier.send("メッセージ")
```

## Notification Types

### Processing Complete
```python
notifier.send_processing_complete(
    session_name="Session_Name",
    photo_count=100,
    success_rate=95.5,
    processing_time="1h 30m"
)
```

### Approval Required
```python
notifier.send_approval_required(
    pending_count=50,
    sessions=[{'name': 'Session1', 'count': 30}]
)
```

### Error
```python
notifier.send_error(
    error_type="Error Type",
    error_message="Error message",
    error_details="Details"
)
```

### Export Complete
```python
notifier.send_export_complete(
    export_preset="SNS_2048px",
    photo_count=45,
    destination="D:/Export"
)
```

### Batch Complete
```python
notifier.send_batch_complete(
    batch_name="Batch_001",
    total_photos=120,
    processing_time="2h 15m",
    avg_time_per_photo="1.1s"
)
```

## Advanced Features

### With Image
```python
from pathlib import Path

notifier.send(
    message="メッセージ",
    image_path=Path("image.jpg")
)
```

### With Sticker
```python
notifier.send(
    message="メッセージ",
    sticker_package_id=1,
    sticker_id=2
)
```

## API Endpoints

### Test Connection
```bash
curl -X POST http://localhost:5100/api/line/test
```

### Send Notification
```bash
curl -X POST http://localhost:5100/api/line/send \
  -H "Content-Type: application/json" \
  -d '{"type": "processing_complete", "data": {...}}'
```

### Get Configuration
```bash
curl http://localhost:5100/api/line/config
```

### Update Configuration
```bash
curl -X POST http://localhost:5100/api/line/config \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "token": "YOUR_TOKEN"}'
```

### Check Rate Limit
```bash
curl http://localhost:5100/api/line/rate-limit
```

## Configuration

```json
{
  "enabled": true,
  "token": "YOUR_TOKEN",
  "notification_types": {
    "processing_complete": true,
    "approval_required": true,
    "error": true,
    "export_complete": false,
    "batch_complete": true,
    "system_status": false
  },
  "rate_limit": {
    "max_per_hour": 50
  }
}
```

## Troubleshooting

### Check Status
```python
notifier = get_line_notifier()
print(f"Enabled: {notifier.token_manager.is_enabled()}")
print(f"Token: {bool(notifier.token_manager.get_token())}")
```

### Test Connection
```python
success = notifier.test_connection()
print(f"Connection: {'✓' if success else '✗'}")
```

### Check Rate Limit
```python
can_send = notifier.token_manager.check_rate_limit()
print(f"Can send: {can_send}")
```

## Common Patterns

### Multi-Channel Notification
```python
from desktop_notifier import get_notifier as get_desktop
from line_notifier import get_line_notifier

def notify_all(message):
    get_desktop().send("Title", message)
    get_line_notifier().send(message)
```

### Critical Alert
```python
def critical_alert(error_type, error_message):
    line = get_line_notifier()
    line.send_error(error_type, error_message)
```

### Batch Notification
```python
def batch_notify(notifications):
    line = get_line_notifier()
    for notif in notifications:
        line.send_with_data(notif['type'], notif['data'])
```

## Rate Limits

- Default: 50 notifications/hour
- LINE API: 1000 notifications/hour
- Message length: 1000 characters max
- Image size: 1MB max

## Files

- Implementation: `line_notifier.py`
- API: `api_line_notifications.py`
- Examples: `example_line_notification_usage.py`
- Tests: `test_notification_integration.py`
- Docs: `LINE_NOTIFY_IMPLEMENTATION.md`
- Quick Start: `LINE_NOTIFY_QUICK_START.md`

## Links

- Get Token: https://notify-bot.line.me/
- API Docs: https://notify-bot.line.me/doc/en/
- My Tokens: https://notify-bot.line.me/my/
