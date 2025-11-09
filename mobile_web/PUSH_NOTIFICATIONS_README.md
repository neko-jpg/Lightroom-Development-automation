# Push Notifications System

## Overview

The Junmai AutoDev mobile web PWA now supports push notifications, allowing users to receive real-time updates about processing status, approvals, errors, and exports even when the app is not actively open.

## Quick Links

- 📖 [Full Implementation Guide](PUSH_NOTIFICATION_IMPLEMENTATION.md)
- 🚀 [Quick Start Guide](PUSH_NOTIFICATION_QUICK_START.md)
- ✅ [Completion Summary](TASK_35_COMPLETION_SUMMARY.md)
- 🧪 [Test Page](test_push_notifications.html)

## Features

### ✅ Implemented

- **Service Worker Push Handling**: Receives and displays push notifications
- **Permission Management**: Request and manage notification permissions
- **Subscription Management**: Subscribe/unsubscribe to push notifications
- **Smart Navigation**: Click notifications to navigate to relevant pages
- **Multiple Notification Types**: Processing, approval, error, export, session
- **Test Functionality**: Send test notifications to verify setup
- **Status Indicators**: Visual feedback on permission and subscription status
- **Backend API**: Store and manage push subscriptions
- **Troubleshooting UI**: Help users enable notifications

### 🎯 Notification Types

1. **Processing Complete** (✅)
   - Sent when batch processing finishes
   - Shows photo count and session info
   - Links to session details

2. **Approval Required** (⏳)
   - Sent when photos need review
   - Shows pending photo count
   - Links to approval queue

3. **System Error** (❌)
   - Sent on critical errors
   - Shows error message
   - Links to settings/logs

4. **Export Complete** (📤)
   - Sent when export finishes
   - Shows exported photo count
   - Links to export location

5. **Session Started** (🚀)
   - Sent when new session begins
   - Shows session name
   - Links to session details

## File Structure

```
mobile_web/
├── src/
│   ├── services/
│   │   ├── notificationService.js      # Core notification service
│   │   └── api.js                      # API client (updated)
│   ├── components/
│   │   └── NotificationSettings.js     # Settings UI component
│   ├── utils/
│   │   └── notificationHelper.js       # Helper utilities
│   ├── pages/
│   │   └── Settings.js                 # Settings page (updated)
│   └── service-worker.js               # Service worker (enhanced)
├── PUSH_NOTIFICATION_IMPLEMENTATION.md # Full documentation
├── PUSH_NOTIFICATION_QUICK_START.md    # Quick start guide
├── PUSH_NOTIFICATIONS_README.md        # This file
├── TASK_35_COMPLETION_SUMMARY.md       # Completion summary
└── test_push_notifications.html        # Test page

local_bridge/
├── api_notifications.py                # Backend API
└── app.py                              # Main app (updated)
```

## Usage

### For End Users

1. **Enable Notifications**
   ```
   Settings → Push Notifications → Enable Push Notifications
   ```

2. **Test Notifications**
   ```
   Settings → Send Test Notification
   ```

3. **Disable Notifications**
   ```
   Settings → Disable Push Notifications
   ```

### For Developers

1. **Send Notification from Backend**
   ```python
   from api_notifications import send_push_notification
   
   send_push_notification(
       title='Processing Complete',
       body='45 photos processed',
       url='/sessions/123',
       notification_type='processing',
       data={'sessionId': '123', 'count': 45}
   )
   ```

2. **Check Notification Status**
   ```javascript
   import notificationService from './services/notificationService';
   
   if (notificationService.isSupported()) {
       const permission = notificationService.getPermissionStatus();
       console.log('Permission:', permission);
   }
   ```

3. **Subscribe to Notifications**
   ```javascript
   import notificationService from './services/notificationService';
   import apiService from './services/api';
   
   await notificationService.requestPermission();
   await notificationService.subscribe(apiService);
   ```

## Setup

### Prerequisites

1. **HTTPS**: Push notifications require HTTPS (or localhost for development)
2. **VAPID Keys**: Generate VAPID keys for push authentication
3. **Service Worker**: Must be registered and active

### Generate VAPID Keys

```bash
npm install -g web-push
web-push generate-vapid-keys
```

### Configure Environment

Add to `.env`:
```env
REACT_APP_VAPID_PUBLIC_KEY=your_public_key_here
```

Add private key to backend configuration.

### Install Backend Dependencies

```bash
pip install pywebpush
```

## Testing

### Manual Testing

1. Open `test_push_notifications.html` in browser
2. Click "Check Support" to verify browser support
3. Click "Request Permission" to request notification permission
4. Click "Subscribe" to subscribe to push notifications
5. Click "Test Notification" to send a test notification
6. Verify notification appears and click works

### Integration Testing

1. Enable notifications in Settings
2. Trigger processing job
3. Verify notification appears when processing completes
4. Click notification and verify navigation
5. Test all notification types

## Browser Support

| Browser | Version | Support |
|---------|---------|---------|
| Chrome | 50+ | ✅ Full |
| Firefox | 44+ | ✅ Full |
| Edge | 17+ | ✅ Full |
| Opera | 37+ | ✅ Full |
| Safari (iOS) | All | ❌ None |
| Safari (macOS) | 16+ | ⚠️ Limited |

## Troubleshooting

### Notifications Not Appearing

1. Check permission status in Settings
2. Verify service worker is registered
3. Check browser console for errors
4. Ensure HTTPS is enabled (or using localhost)

### Permission Denied

1. Click lock icon in address bar
2. Find "Notifications" in permissions
3. Change to "Allow"
4. Refresh page

### Service Worker Issues

1. Open DevTools → Application → Service Workers
2. Check if service worker is active
3. Click "Update" to force update
4. Unregister and refresh if needed

## API Reference

### Frontend

#### NotificationService

```javascript
// Check support
notificationService.isSupported()

// Get permission status
notificationService.getPermissionStatus()

// Request permission
await notificationService.requestPermission()

// Subscribe
await notificationService.subscribe(apiService)

// Unsubscribe
await notificationService.unsubscribe(apiService)

// Test notification
await notificationService.testNotification()
```

### Backend

#### Endpoints

```
POST /notifications/subscribe
POST /notifications/unsubscribe
GET  /notifications/settings
POST /notifications/settings
GET  /notifications/subscriptions
POST /notifications/track
```

#### Send Notification

```python
send_push_notification(
    title: str,
    body: str,
    url: str = '/',
    notification_type: str = 'general',
    data: dict = None
)
```

## Security

1. **VAPID Keys**: Keep private key secure, never expose in client
2. **HTTPS Only**: Push notifications require secure context
3. **User Privacy**: Only send relevant notifications
4. **Rate Limiting**: Prevent notification spam
5. **Subscription Security**: Store subscriptions securely

## Performance

- **Lightweight**: Minimal impact on app performance
- **Efficient**: Uses native browser APIs
- **Background**: Works even when app is closed
- **Battery Friendly**: Optimized for mobile devices

## Future Enhancements

- [ ] Notification grouping
- [ ] Action buttons (approve/reject)
- [ ] Rich media (images)
- [ ] Quiet hours support
- [ ] Priority levels
- [ ] Notification history

## Support

For issues or questions:
1. Check [Implementation Guide](PUSH_NOTIFICATION_IMPLEMENTATION.md)
2. Review [Quick Start Guide](PUSH_NOTIFICATION_QUICK_START.md)
3. Test with [Test Page](test_push_notifications.html)
4. Check browser console for errors

## License

Part of Junmai AutoDev project.

---

**Status**: ✅ Complete  
**Version**: 1.0.0  
**Last Updated**: 2025-11-09
