# Email Notification System - Quick Start Guide

## Overview

The Email Notification System provides comprehensive email notifications for the Junmai AutoDev system. This guide will help you get started quickly.

## Quick Setup (5 minutes)

### Step 1: Configure SMTP Settings

```python
from email_notifier import get_email_notifier

notifier = get_email_notifier()

# For Gmail users
notifier.update_config({
    'enabled': True,
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'use_tls': True,
    'username': 'your-email@gmail.com',
    'password': 'your-app-password',  # See Gmail setup below
    'from_address': 'your-email@gmail.com',
    'from_name': 'Junmai AutoDev',
    'to_addresses': ['recipient@example.com']
})
```

### Step 2: Test Connection

```python
# Test SMTP connection
if notifier.test_connection():
    print("✓ SMTP connection successful!")
else:
    print("✗ Connection failed. Check your settings.")
```

### Step 3: Send Your First Email

```python
# Send a test email
notifier.send_processing_complete(
    session_name='Test Session',
    photo_count=10,
    success_rate=100.0,
    processing_time='30s'
)
```

## Gmail Setup (Recommended)

### 1. Enable 2-Step Verification
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Click "2-Step Verification"
3. Follow the setup wizard

### 2. Generate App Password
1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and "Windows Computer"
3. Click "Generate"
4. Copy the 16-character password
5. Use this password in your configuration (not your regular password)

### 3. Configure Junmai AutoDev

```python
notifier.update_config({
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'use_tls': True,
    'username': 'your-email@gmail.com',
    'password': 'xxxx xxxx xxxx xxxx',  # Your 16-char app password
    'from_address': 'your-email@gmail.com'
})
```

## Common Use Cases

### 1. Processing Complete Notification

```python
notifier.send_processing_complete(
    session_name='2025-11-08_Wedding',
    photo_count=120,
    success_rate=95.5,
    processing_time='2h 15m'
)
```

### 2. Error Notification

```python
notifier.send_error(
    error_type='Processing Error',
    error_message='Failed to process photo',
    error_details='GPU memory exceeded'
)
```

### 3. Daily Summary

```python
notifier.send_daily_summary(
    date='2025-11-08',
    total_imported=150,
    total_selected=120,
    total_processed=100,
    total_exported=80,
    avg_processing_time='2.3s',
    success_rate=95.5
)
```

### 4. Approval Required

```python
notifier.send_approval_required(
    pending_count=15,
    sessions=[
        {'name': 'Session 1', 'count': 10},
        {'name': 'Session 2', 'count': 5}
    ]
)
```

## Using the API

### Get Configuration

```bash
curl http://localhost:5100/email-notifications/config
```

### Update Configuration

```bash
curl -X POST http://localhost:5100/email-notifications/config \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "user@gmail.com",
    "password": "app-password"
  }'
```

### Test Connection

```bash
curl -X POST http://localhost:5100/email-notifications/test
```

### Send Test Email

```bash
curl -X POST http://localhost:5100/email-notifications/send-test
```

### Send Processing Complete

```bash
curl -X POST http://localhost:5100/email-notifications/send/processing-complete \
  -H "Content-Type: application/json" \
  -d '{
    "session_name": "2025-11-08_Wedding",
    "photo_count": 120,
    "success_rate": 95.5,
    "processing_time": "2h 15m"
  }'
```

## Batch Notifications

Batch notifications reduce email volume by grouping multiple notifications together.

### Configure Batch Settings

```python
notifier.update_config({
    'batch_notifications': {
        'enabled': True,
        'interval_minutes': 60,    # Send batch every 60 minutes
        'min_notifications': 3     # Or when 3+ notifications buffered
    }
})
```

### Add to Batch

```python
# Notifications are automatically batched
for i in range(5):
    should_flush = notifier.add_to_batch({
        'type': 'processing_complete',
        'message': f'Processed photo {i+1}'
    })
    
    if should_flush:
        notifier.send_batch()
```

## Notification Types

The system supports 7 notification types:

1. **processing_complete** - Photo processing completed
2. **approval_required** - Photos need approval
3. **error** - Error occurred
4. **export_complete** - Photo export finished
5. **batch_complete** - Batch processing completed
6. **daily_summary** - Daily statistics report
7. **weekly_summary** - Weekly statistics report

### Enable/Disable Specific Types

```python
notifier.update_config({
    'notification_types': {
        'processing_complete': True,
        'approval_required': True,
        'error': True,
        'export_complete': False,  # Disabled
        'batch_complete': True,
        'daily_summary': True,
        'weekly_summary': True
    }
})
```

## Configuration File

Configuration is stored in `config/email_config.json`:

```json
{
  "enabled": true,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "use_tls": true,
  "username": "your-email@gmail.com",
  "password": "your-app-password",
  "from_address": "your-email@gmail.com",
  "from_name": "Junmai AutoDev",
  "to_addresses": ["recipient@example.com"],
  "batch_notifications": {
    "enabled": true,
    "interval_minutes": 60,
    "min_notifications": 3
  },
  "notification_types": {
    "processing_complete": true,
    "approval_required": true,
    "error": true,
    "export_complete": false,
    "batch_complete": true,
    "daily_summary": true,
    "weekly_summary": true
  }
}
```

## Other Email Providers

### Outlook/Hotmail

```python
notifier.update_config({
    'smtp_server': 'smtp-mail.outlook.com',
    'smtp_port': 587,
    'use_tls': True,
    'username': 'your-email@outlook.com',
    'password': 'your-password'
})
```

### Yahoo Mail

```python
notifier.update_config({
    'smtp_server': 'smtp.mail.yahoo.com',
    'smtp_port': 587,
    'use_tls': True,
    'username': 'your-email@yahoo.com',
    'password': 'your-app-password'  # Generate at Yahoo Account Security
})
```

### Custom SMTP Server

```python
notifier.update_config({
    'smtp_server': 'mail.yourdomain.com',
    'smtp_port': 587,
    'use_tls': True,
    'username': 'user@yourdomain.com',
    'password': 'your-password'
})
```

## Troubleshooting

### Connection Refused

**Problem**: Cannot connect to SMTP server

**Solutions**:
- Check SMTP server address and port
- Verify firewall settings
- Try different port (587 for TLS, 465 for SSL, 25 for plain)

### Authentication Failed

**Problem**: Login credentials rejected

**Solutions**:
- Verify username and password
- For Gmail, use App Password (not account password)
- Check if 2-Step Verification is enabled
- Try disabling "Less secure app access" (not recommended)

### Emails Not Received

**Problem**: Emails sent but not received

**Solutions**:
- Check spam/junk folder
- Verify recipient email addresses
- Check SMTP server logs
- Try sending to a different email address
- Verify sender email is not blacklisted

### Batch Not Sending

**Problem**: Batch notifications not being sent

**Solutions**:
- Check if batch notifications are enabled
- Verify interval_minutes and min_notifications settings
- Manually trigger with `notifier.send_batch()`
- Check if enough notifications are buffered

## Testing

### Run Example Script

```bash
cd local_bridge
python example_email_notification_usage.py
```

### Run Quick Test

```bash
cd local_bridge
python test_email_quick.py
```

### Test API Endpoints

```bash
# Test connection
curl -X POST http://localhost:5100/email-notifications/test

# Send test email
curl -X POST http://localhost:5100/email-notifications/send-test
```

## Security Best Practices

1. **Use App Passwords**: Never use your main account password
2. **Enable TLS/SSL**: Always encrypt SMTP connections
3. **Restrict File Permissions**: Protect `email_config.json`
4. **Use Environment Variables**: For production deployments
5. **Regular Password Rotation**: Change passwords periodically

## Integration Examples

### With Desktop Notifier

```python
from desktop_notifier import get_notifier as get_desktop_notifier
from email_notifier import get_email_notifier

desktop = get_desktop_notifier()
email = get_email_notifier()

# Send both notifications
desktop.send_processing_complete(session_name, photo_count, success_rate)
email.send_processing_complete(session_name, photo_count, success_rate, processing_time)
```

### With Job Queue

```python
from job_queue_manager import JobQueueManager
from email_notifier import get_email_notifier

job_queue = JobQueueManager()
email = get_email_notifier()

# After job completion
if job.status == 'completed':
    email.send_processing_complete(
        session_name=job.session_name,
        photo_count=1,
        success_rate=100.0,
        processing_time=f'{job.duration}s'
    )
```

### With WebSocket Events

```python
from websocket_events import broadcast_job_completed
from email_notifier import get_email_notifier

email = get_email_notifier()

# When job completes
broadcast_job_completed(job_id, photo_id, result)
email.send_processing_complete(...)
```

## Next Steps

1. **Configure SMTP**: Set up your email provider
2. **Test Connection**: Verify SMTP settings work
3. **Send Test Email**: Confirm email delivery
4. **Customize Templates**: Modify templates if needed
5. **Configure Batch Settings**: Adjust batch notification settings
6. **Enable/Disable Types**: Choose which notifications to receive
7. **Integrate**: Connect with other system components

## Support

For more information, see:
- `EMAIL_NOTIFICATION_IMPLEMENTATION.py` - Detailed implementation guide
- `example_email_notification_usage.py` - 12 usage examples
- `TASK_37_COMPLETION_SUMMARY.md` - Complete feature list

## Quick Reference

### Singleton Access
```python
from email_notifier import get_email_notifier
notifier = get_email_notifier()
```

### Convenience Function
```python
from email_notifier import send_email_notification, EmailNotificationType

send_email_notification(
    EmailNotificationType.PROCESSING_COMPLETE,
    {'session_name': 'Test', 'photo_count': 10, ...}
)
```

### Configuration
```python
notifier.update_config({...})  # Update
config = notifier.get_config()  # Get
```

### Testing
```python
notifier.test_connection()  # Test SMTP
```

### Sending
```python
notifier.send_processing_complete(...)
notifier.send_approval_required(...)
notifier.send_error(...)
notifier.send_export_complete(...)
notifier.send_batch_complete(...)
notifier.send_daily_summary(...)
notifier.send_weekly_summary(...)
```

---

**Ready to start?** Configure your SMTP settings and send your first email notification!
