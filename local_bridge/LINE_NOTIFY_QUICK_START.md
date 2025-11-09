# LINE Notify Quick Start Guide

## Setup (5 minutes)

### 1. Get LINE Notify Token

1. Visit https://notify-bot.line.me/
2. Log in with your LINE account
3. Click "Generate token" (トークンを発行する)
4. Enter a token name (e.g., "Junmai AutoDev")
5. Select notification target (1-on-1 chat or group)
6. Click "Generate token"
7. **Copy the token immediately** (it won't be shown again!)

### 2. Configure Token

Edit `local_bridge/config/line_config.json`:

```json
{
  "enabled": true,
  "token": "YOUR_TOKEN_HERE",
  "notification_types": {
    "processing_complete": true,
    "approval_required": true,
    "error": true,
    "export_complete": false,
    "batch_complete": true,
    "system_status": false
  }
}
```

### 3. Test Connection

```bash
cd local_bridge
py example_line_notification_usage.py
```

## Basic Usage

### Send Simple Notification

```python
from line_notifier import get_line_notifier

notifier = get_line_notifier()
notifier.send("テスト通知: システムが起動しました")
```

### Send Processing Complete

```python
notifier.send_processing_complete(
    session_name="2025-11-08_Wedding",
    photo_count=120,
    success_rate=95.5,
    processing_time="2h 15m"
)
```

### Send Error Alert

```python
notifier.send_error(
    error_type="GPU Memory Error",
    error_message="GPU memory exceeded",
    error_details="Failed to allocate 2GB"
)
```

## API Usage

### Test Connection

```bash
curl -X POST http://localhost:5100/api/line/test
```

### Send Notification

```bash
curl -X POST http://localhost:5100/api/line/send \
  -H "Content-Type: application/json" \
  -d '{
    "type": "processing_complete",
    "data": {
      "session_name": "Test",
      "photo_count": 10,
      "success_rate": 100.0,
      "processing_time": "30s"
    }
  }'
```

## Common Notification Types

### 1. Processing Complete ✓

```python
notifier.send_processing_complete(
    session_name="Session Name",
    photo_count=100,
    success_rate=95.0,
    processing_time="1h 30m"
)
```

### 2. Approval Required 📋

```python
notifier.send_approval_required(
    pending_count=50,
    sessions=[
        {'name': 'Session 1', 'count': 30},
        {'name': 'Session 2', 'count': 20}
    ]
)
```

### 3. Error Alert ⚠

```python
notifier.send_error(
    error_type="Processing Error",
    error_message="Failed to process photo",
    error_details="GPU timeout"
)
```

### 4. Export Complete 📤

```python
notifier.send_export_complete(
    export_preset="SNS_2048px",
    photo_count=45,
    destination="D:/Export/SNS"
)
```

### 5. Batch Complete 🎯

```python
notifier.send_batch_complete(
    batch_name="Wedding_Batch_001",
    total_photos=120,
    processing_time="2h 15m",
    avg_time_per_photo="1.1s"
)
```

## Advanced Features

### With Image Attachment

```python
from pathlib import Path

notifier.send(
    message="処理完了: プレビュー画像",
    image_path=Path("preview.jpg")
)
```

### With LINE Sticker

```python
notifier.send(
    message="処理完了！",
    sticker_package_id=1,
    sticker_id=2  # Happy face
)
```

## Configuration Options

### Enable/Disable Notification Types

```json
{
  "notification_types": {
    "processing_complete": true,   // ✓ Enabled
    "approval_required": true,     // ✓ Enabled
    "error": true,                 // ✓ Enabled
    "export_complete": false,      // ✗ Disabled
    "batch_complete": true,        // ✓ Enabled
    "system_status": false         // ✗ Disabled
  }
}
```

### Rate Limiting

Default: 50 notifications per hour

```json
{
  "rate_limit": {
    "max_per_hour": 50
  }
}
```

## Troubleshooting

### ❌ Notifications Not Sending

**Check 1: Is LINE Notify enabled?**
```python
notifier = get_line_notifier()
print(notifier.token_manager.is_enabled())  # Should be True
```

**Check 2: Is token configured?**
```python
token = notifier.token_manager.get_token()
print(bool(token))  # Should be True
```

**Check 3: Test connection**
```python
success = notifier.test_connection()
print(success)  # Should be True
```

### ❌ Rate Limit Exceeded

```python
can_send = notifier.token_manager.check_rate_limit()
if not can_send:
    print("Rate limit exceeded. Wait for reset.")
```

### ❌ Invalid Token

1. Go to https://notify-bot.line.me/my/
2. Check if token is still valid
3. Generate new token if needed
4. Update configuration

## Integration Examples

### With Desktop Notifications

```python
from desktop_notifier import get_notifier as get_desktop
from line_notifier import get_line_notifier

def notify_all(title, message):
    # Desktop
    desktop = get_desktop()
    desktop.send(title, message)
    
    # LINE
    line = get_line_notifier()
    line.send(message)
```

### With Email Notifications

```python
from email_notifier import get_email_notifier
from line_notifier import get_line_notifier

def critical_alert(error_type, error_message):
    # Email (detailed)
    email = get_email_notifier()
    email.send_error(error_type, error_message, "Full details...")
    
    # LINE (quick alert)
    line = get_line_notifier()
    line.send_error(error_type, error_message)
```

## Best Practices

1. **Use Appropriate Types**: Choose the right notification type for each event
2. **Respect Rate Limits**: Don't send too many notifications
3. **Keep Messages Concise**: LINE has character limits
4. **Test First**: Always test with a test token before production
5. **Monitor Usage**: Check rate limit status regularly

## Next Steps

- Read full documentation: `LINE_NOTIFY_IMPLEMENTATION.md`
- Explore examples: `example_line_notification_usage.py`
- Check API endpoints: `api_line_notifications.py`
- Integrate with your workflow

## Support

- LINE Notify Documentation: https://notify-bot.line.me/doc/en/
- LINE Notify FAQ: https://notify-bot.line.me/doc/en/faq.html
