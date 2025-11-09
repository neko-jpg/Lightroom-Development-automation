# LINE Notify Implementation

## Overview

LINE Notify integration provides instant notifications to users' LINE accounts for various system events. This implementation includes token management, message formatting, rate limiting, and API endpoints.

## Features

- ✅ LINE Notify API integration
- ✅ Token management with secure storage
- ✅ Message formatting for different notification types
- ✅ Rate limiting (50 notifications per hour)
- ✅ Image attachment support
- ✅ LINE sticker support
- ✅ REST API endpoints
- ✅ Configuration management

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ LINE Notify Integration                                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐    ┌──────────────────┐          │
│  │ LineNotifier     │───▶│ LINE Notify API  │          │
│  │                  │    │ (notify-api.     │          │
│  │ - send()         │    │  line.me)        │          │
│  │ - send_with_data│    └──────────────────┘          │
│  └──────────────────┘                                   │
│          │                                               │
│          ▼                                               │
│  ┌──────────────────┐    ┌──────────────────┐          │
│  │ LineTokenManager │    │ LineMessage      │          │
│  │                  │    │ Formatter        │          │
│  │ - Token storage  │    │                  │          │
│  │ - Rate limiting  │    │ - Format types   │          │
│  │ - Config mgmt    │    │ - Templates      │          │
│  └──────────────────┘    └──────────────────┘          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. LineNotifier

Main class for sending LINE notifications.

**Key Methods:**
- `send()` - Send basic notification
- `send_with_data()` - Send formatted notification
- `send_processing_complete()` - Processing complete notification
- `send_approval_required()` - Approval required notification
- `send_error()` - Error notification
- `send_export_complete()` - Export complete notification
- `send_batch_complete()` - Batch complete notification
- `check_token_status()` - Check token validity
- `test_connection()` - Test LINE Notify connection

### 2. LineTokenManager

Manages LINE Notify tokens and configuration.

**Key Methods:**
- `is_enabled()` - Check if LINE Notify is enabled
- `get_token()` - Get configured token
- `set_token()` - Set new token
- `check_rate_limit()` - Check if sending is allowed
- `increment_rate_limit()` - Increment rate limit counter

### 3. LineMessageFormatter

Formats messages for different notification types.

**Supported Types:**
- Processing Complete
- Approval Required
- Error
- Export Complete
- Batch Complete
- System Status

## Configuration

### Configuration File

Location: `local_bridge/config/line_config.json`

```json
{
  "enabled": false,
  "token": "",
  "notification_types": {
    "processing_complete": true,
    "approval_required": true,
    "error": true,
    "export_complete": false,
    "batch_complete": true,
    "system_status": false
  },
  "rate_limit": {
    "max_per_hour": 50,
    "current_count": 0,
    "reset_time": null
  }
}
```

### Getting a LINE Notify Token

1. Visit https://notify-bot.line.me/
2. Log in with your LINE account
3. Click "Generate token"
4. Select the chat room to receive notifications
5. Copy the generated token
6. Update the configuration file with your token

## Usage Examples

### Basic Usage

```python
from line_notifier import get_line_notifier, LineNotificationType

# Get notifier instance
notifier = get_line_notifier()

# Send simple notification
notifier.send(
    message="テスト通知",
    notification_type=LineNotificationType.SYSTEM_STATUS
)
```

### Processing Complete Notification

```python
notifier.send_processing_complete(
    session_name="2025-11-08_Wedding",
    photo_count=120,
    success_rate=95.5,
    processing_time="2h 15m"
)
```

### Approval Required Notification

```python
sessions = [
    {'name': '2025-11-08_Wedding', 'count': 45},
    {'name': '2025-11-07_Portrait', 'count': 12}
]

notifier.send_approval_required(
    pending_count=57,
    sessions=sessions
)
```

### Error Notification

```python
notifier.send_error(
    error_type="GPU Memory Error",
    error_message="GPU memory exceeded during processing",
    error_details="Failed to allocate 2GB for model inference"
)
```

### With Image Attachment

```python
from pathlib import Path

notifier.send(
    message="処理完了: プレビュー画像",
    notification_type=LineNotificationType.PROCESSING_COMPLETE,
    image_path=Path("preview.jpg")
)
```

### With LINE Sticker

```python
notifier.send(
    message="処理が正常に完了しました！",
    notification_type=LineNotificationType.PROCESSING_COMPLETE,
    sticker_package_id=1,
    sticker_id=2
)
```

## API Endpoints

### Get Configuration

```http
GET /api/line/config
```

Response:
```json
{
  "success": true,
  "config": {
    "enabled": true,
    "token": "***xyz",
    "notification_types": { ... }
  }
}
```

### Update Configuration

```http
POST /api/line/config
Content-Type: application/json

{
  "enabled": true,
  "token": "YOUR_TOKEN",
  "notification_types": {
    "processing_complete": true,
    "approval_required": true,
    "error": true
  }
}
```

### Test Connection

```http
POST /api/line/test
```

Response:
```json
{
  "success": true,
  "message": "Connection test successful",
  "status": {
    "status": 200,
    "message": "ok",
    "target": "User Name",
    "targetType": "USER"
  }
}
```

### Send Notification

```http
POST /api/line/send
Content-Type: application/json

{
  "type": "processing_complete",
  "data": {
    "session_name": "2025-11-08_Wedding",
    "photo_count": 120,
    "success_rate": 95.5,
    "processing_time": "2h 15m"
  }
}
```

### Send Processing Complete

```http
POST /api/line/send/processing-complete
Content-Type: application/json

{
  "session_name": "2025-11-08_Wedding",
  "photo_count": 120,
  "success_rate": 95.5,
  "processing_time": "2h 15m"
}
```

### Get Rate Limit Status

```http
GET /api/line/rate-limit
```

Response:
```json
{
  "success": true,
  "rate_limit": {
    "max_per_hour": 50,
    "current_count": 12,
    "reset_time": "2025-11-08T15:00:00",
    "can_send": true
  }
}
```

## Rate Limiting

LINE Notify has a rate limit of **1000 notifications per hour per token**. This implementation enforces a conservative limit of **50 notifications per hour** to prevent abuse.

**Rate Limit Behavior:**
- Counter resets every hour
- Notifications are blocked when limit is reached
- Rate limit status is persisted in configuration file

## Message Format Examples

### Processing Complete

```
✓ 処理完了

セッション: 2025-11-08_Wedding
処理枚数: 120枚
成功率: 95.5%
処理時間: 2h 15m
```

### Approval Required

```
📋 承認待ち

65枚の写真が承認待ちです

セッション:
• 2025-11-08_Wedding: 45枚
• 2025-11-07_Portrait: 12枚
• 2025-11-06_Landscape: 8枚
```

### Error

```
⚠ エラー発生

種類: GPU Memory Error
メッセージ: GPU memory exceeded during processing
詳細: Failed to allocate 2GB for model inference
発生時刻: 2025-11-08 14:30:15
```

## Integration with Other Systems

### Desktop Notifier Integration

```python
from desktop_notifier import get_notifier as get_desktop_notifier
from line_notifier import get_line_notifier

def send_multi_channel_notification(title, message, notification_type):
    """Send notification via multiple channels"""
    # Desktop notification
    desktop = get_desktop_notifier()
    desktop.send(title, message, notification_type)
    
    # LINE notification
    line = get_line_notifier()
    line.send(message, notification_type)
```

### Email Notifier Integration

```python
from email_notifier import get_email_notifier
from line_notifier import get_line_notifier

def send_critical_alert(error_type, error_message, error_details):
    """Send critical alert via email and LINE"""
    # Email notification
    email = get_email_notifier()
    email.send_error(error_type, error_message, error_details)
    
    # LINE notification
    line = get_line_notifier()
    line.send_error(error_type, error_message, error_details)
```

## Testing

### Run Example Script

```bash
cd local_bridge
py example_line_notification_usage.py
```

### Test Connection

```python
from line_notifier import get_line_notifier

notifier = get_line_notifier()
success = notifier.test_connection()
print(f"Connection test: {'✓ Success' if success else '✗ Failed'}")
```

### Check Token Status

```python
notifier = get_line_notifier()
status = notifier.check_token_status()
if status:
    print(f"Target: {status.get('target')}")
    print(f"Type: {status.get('targetType')}")
```

## Security Considerations

1. **Token Storage**: Tokens are stored in configuration file with restricted permissions
2. **API Responses**: Token is masked in API responses (shows only last 4 characters)
3. **Rate Limiting**: Prevents abuse and excessive API calls
4. **HTTPS**: All API calls use HTTPS for secure communication

## Troubleshooting

### Notifications Not Sending

1. Check if LINE Notify is enabled:
   ```python
   notifier = get_line_notifier()
   print(f"Enabled: {notifier.token_manager.is_enabled()}")
   ```

2. Verify token is configured:
   ```python
   token = notifier.token_manager.get_token()
   print(f"Token configured: {bool(token)}")
   ```

3. Test connection:
   ```python
   success = notifier.test_connection()
   print(f"Connection: {success}")
   ```

### Rate Limit Exceeded

Check rate limit status:
```python
can_send = notifier.token_manager.check_rate_limit()
print(f"Can send: {can_send}")
```

Wait for rate limit reset or increase the limit in configuration.

### Invalid Token

1. Verify token at https://notify-bot.line.me/my/
2. Generate a new token if needed
3. Update configuration with new token

## Requirements

- Python 3.8+
- requests library
- LINE Notify account

## Related Files

- `line_notifier.py` - Main implementation
- `api_line_notifications.py` - REST API endpoints
- `example_line_notification_usage.py` - Usage examples
- `config/line_config.json` - Configuration file

## References

- [LINE Notify API Documentation](https://notify-bot.line.me/doc/en/)
- [LINE Notify Official Site](https://notify-bot.line.me/)
