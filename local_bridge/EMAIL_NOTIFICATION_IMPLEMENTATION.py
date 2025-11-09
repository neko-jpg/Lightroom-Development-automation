# Email Notification System Implementation

## Overview

The Email Notification System provides comprehensive email notification capabilities for the Junmai AutoDev system. It supports SMTP configuration management, HTML/text email templates, batch notification buffering, and various notification types.

## Features

### Core Features
- **SMTP Configuration Management**: Flexible SMTP server configuration with support for TLS/SSL
- **Email Templates**: Pre-built HTML and plain text templates for all notification types
- **Batch Notifications**: Buffer and send multiple notifications together to reduce email volume
- **Notification Type Control**: Enable/disable specific notification types
- **Test Functionality**: Test SMTP connection and send test emails

### Notification Types
1. **Processing Complete**: Notify when photo processing is complete
2. **Approval Required**: Alert when photos need approval
3. **Error**: Send immediate notifications for errors
4. **Export Complete**: Notify when photo export is finished
5. **Batch Complete**: Alert when batch processing completes
6. **Daily Summary**: Send daily statistics report
7. **Weekly Summary**: Send weekly statistics report

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Email Notifier                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ SMTP Config  │  │   Templates  │  │ Batch Manager   │  │
│  │  Manager     │  │              │  │                 │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Email Sending Engine                    │  │
│  │  - HTML/Text formatting                              │  │
│  │  - SMTP connection management                        │  │
│  │  - Attachment support                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  SMTP Server  │
                    │  (Gmail, etc) │
                    └───────────────┘
```

## Components

### 1. EmailNotifier
Main class that handles email sending and configuration.

**Key Methods:**
- `send()`: Send email with custom content
- `send_with_template()`: Send email using predefined template
- `send_processing_complete()`: Send processing complete notification
- `send_approval_required()`: Send approval required notification
- `send_error()`: Send error notification
- `send_export_complete()`: Send export complete notification
- `send_batch_complete()`: Send batch complete notification
- `send_daily_summary()`: Send daily summary
- `send_weekly_summary()`: Send weekly summary
- `test_connection()`: Test SMTP connection

### 2. SMTPConfig
Manages SMTP configuration with persistence.

**Configuration Options:**
- `enabled`: Enable/disable email notifications
- `smtp_server`: SMTP server address
- `smtp_port`: SMTP server port
- `use_tls`: Use TLS encryption
- `use_ssl`: Use SSL encryption
- `username`: SMTP username
- `password`: SMTP password
- `from_address`: Sender email address
- `from_name`: Sender display name
- `to_addresses`: List of recipient addresses
- `batch_notifications`: Batch notification settings
- `notification_types`: Enable/disable specific types

### 3. EmailTemplate
Provides HTML and plain text templates for all notification types.

**Template Variables:**
- Processing Complete: `session_name`, `photo_count`, `success_rate`, `processing_time`
- Approval Required: `pending_count`, `session_list`, `approval_url`
- Error: `error_type`, `error_message`, `error_details`, `timestamp`
- Export Complete: `export_preset`, `photo_count`, `destination`
- Batch Complete: `batch_name`, `total_photos`, `processing_time`, `avg_time_per_photo`
- Daily Summary: `date`, `total_imported`, `total_selected`, `total_processed`, `total_exported`, `avg_processing_time`, `success_rate`
- Weekly Summary: `week_range`, `total_imported`, `total_processed`, `total_exported`, `avg_success_rate`, `top_preset`, `daily_breakdown`

### 4. BatchNotificationManager
Buffers notifications and sends them in batches to reduce email volume.

**Configuration:**
- `enabled`: Enable batch notifications
- `interval_minutes`: Time interval between batch sends
- `min_notifications`: Minimum notifications before sending

## API Endpoints

### Configuration
- `GET /email-notifications/config` - Get email configuration
- `POST /email-notifications/config` - Update email configuration
- `POST /email-notifications/test` - Test SMTP connection
- `POST /email-notifications/send-test` - Send test email

### Notification Sending
- `POST /email-notifications/send/processing-complete` - Send processing complete notification
- `POST /email-notifications/send/approval-required` - Send approval required notification
- `POST /email-notifications/send/error` - Send error notification
- `POST /email-notifications/send/export-complete` - Send export complete notification
- `POST /email-notifications/send/batch-complete` - Send batch complete notification
- `POST /email-notifications/send/daily-summary` - Send daily summary
- `POST /email-notifications/send/weekly-summary` - Send weekly summary

## Usage Examples

### Basic Configuration

```python
from email_notifier import get_email_notifier

notifier = get_email_notifier()

# Configure SMTP
notifier.update_config({
    'enabled': True,
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'use_tls': True,
    'username': 'your-email@gmail.com',
    'password': 'your-app-password',
    'from_address': 'your-email@gmail.com',
    'to_addresses': ['recipient@example.com']
})

# Test connection
if notifier.test_connection():
    print("SMTP connection successful")
```

### Send Processing Complete Notification

```python
notifier.send_processing_complete(
    session_name='2025-11-08_Wedding',
    photo_count=120,
    success_rate=95.5,
    processing_time='2h 15m'
)
```

### Send Error Notification

```python
notifier.send_error(
    error_type='Processing Error',
    error_message='Failed to process photo',
    error_details='GPU memory exceeded'
)
```

### Send Daily Summary

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

### Using Batch Notifications

```python
# Add notifications to batch
for i in range(5):
    should_flush = notifier.add_to_batch({
        'type': 'processing_complete',
        'message': f'Processed photo {i+1}'
    })
    
    if should_flush:
        notifier.send_batch()
```

## Configuration File

Email configuration is stored in `config/email_config.json`:

```json
{
  "enabled": true,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "use_tls": true,
  "use_ssl": false,
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

## Gmail Configuration

For Gmail, you need to use an App Password:

1. Enable 2-Step Verification in your Google Account
2. Go to Security > 2-Step Verification > App passwords
3. Generate a new app password for "Mail"
4. Use this password in the configuration

## Security Considerations

1. **Password Storage**: Passwords are stored in the configuration file. Consider using environment variables or a secrets manager for production.
2. **TLS/SSL**: Always use TLS or SSL for SMTP connections to encrypt credentials.
3. **API Access**: The configuration API endpoint should be protected with authentication.
4. **Sensitive Data**: The API masks passwords when returning configuration.

## Integration with Other Systems

### Desktop Notifier Integration

```python
from desktop_notifier import get_notifier as get_desktop_notifier
from email_notifier import get_email_notifier

# Send both desktop and email notifications
desktop_notifier = get_desktop_notifier()
email_notifier = get_email_notifier()

# Processing complete
desktop_notifier.send_processing_complete(session_name, photo_count, success_rate)
email_notifier.send_processing_complete(session_name, photo_count, success_rate, processing_time)
```

### WebSocket Integration

```python
from websocket_events import broadcast_job_completed
from email_notifier import get_email_notifier

# When job completes
broadcast_job_completed(job_id, photo_id, result)

# Also send email notification
email_notifier = get_email_notifier()
email_notifier.send_processing_complete(
    session_name=session.name,
    photo_count=1,
    success_rate=100.0,
    processing_time='2.3s'
)
```

## Testing

Run the example script to test email notifications:

```bash
python example_email_notification_usage.py
```

Or run the module directly:

```bash
python email_notifier.py
```

## Troubleshooting

### Connection Refused
- Check SMTP server address and port
- Verify firewall settings
- Ensure TLS/SSL settings are correct

### Authentication Failed
- Verify username and password
- For Gmail, use App Password instead of account password
- Check if 2-Step Verification is enabled

### Emails Not Received
- Check spam/junk folder
- Verify recipient email addresses
- Check SMTP server logs
- Test with a different email provider

### Batch Notifications Not Sending
- Check batch configuration settings
- Verify interval_minutes and min_notifications
- Manually trigger batch send with `send_batch()`

## Requirements

- Python 3.7+
- Flask
- smtplib (built-in)
- email (built-in)

## Files

- `email_notifier.py` - Main email notification implementation
- `api_email_notifications.py` - Flask API endpoints
- `example_email_notification_usage.py` - Usage examples
- `config/email_config.json` - Configuration file (auto-generated)

## Requirements Fulfilled

- **8.1**: Email notification system with SMTP configuration
- **8.2**: Email templates and batch notification support
