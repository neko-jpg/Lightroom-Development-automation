# Push Notification Implementation

## Overview

This document describes the push notification implementation for the Junmai AutoDev mobile web PWA. The system allows users to receive real-time notifications about processing status, approvals, errors, and exports even when the app is not actively open.

## Architecture

### Components

1. **Service Worker** (`src/service-worker.js`)
   - Handles push events from the Push API
   - Displays notifications to the user
   - Manages notification click events and navigation
   - Tracks notification interactions

2. **Notification Service** (`src/services/notificationService.js`)
   - Manages push notification subscriptions
   - Handles permission requests
   - Communicates with backend API
   - Provides utility methods for subscription management

3. **Notification Settings Component** (`src/components/NotificationSettings.js`)
   - UI for enabling/disabling push notifications
   - Permission request interface
   - Test notification functionality
   - Status display and troubleshooting

4. **Backend API** (`local_bridge/api_notifications.py`)
   - Stores push subscriptions
   - Sends push notifications to subscribed clients
   - Manages notification settings
   - Tracks notification interactions

5. **Notification Helper** (`src/utils/notificationHelper.js`)
   - Utility functions for notification formatting
   - Type definitions and configurations
   - URL routing for notification clicks

## Features

### 1. Permission Management

- **Request Permission**: Users can enable notifications from the Settings page
- **Permission States**: Handles default, granted, denied, and unsupported states
- **User-Friendly UI**: Clear status indicators and instructions

### 2. Subscription Management

- **Subscribe**: Registers device for push notifications
- **Unsubscribe**: Removes device from notification list
- **Automatic Cleanup**: Removes invalid subscriptions automatically

### 3. Notification Types

The system supports multiple notification types:

- **Processing Complete**: Batch processing finished
- **Approval Required**: Photos ready for review
- **System Error**: Critical errors that need attention
- **Export Complete**: Photos exported successfully
- **Session Started**: New processing session initiated

### 4. Smart Navigation

- **Click Handling**: Opens relevant page when notification is clicked
- **Window Management**: Focuses existing window or opens new one
- **Deep Linking**: Routes to specific sessions, photos, or pages

### 5. Notification Tracking

- **Click Tracking**: Records when notifications are clicked
- **Dismissal Tracking**: Tracks when notifications are dismissed
- **Analytics**: Helps understand notification effectiveness

## Usage

### For Users

#### Enabling Notifications

1. Open the mobile web app
2. Navigate to Settings
3. Find the "Push Notifications" section
4. Click "Enable Push Notifications"
5. Allow notifications when prompted by the browser

#### Testing Notifications

1. After enabling notifications
2. Click "Send Test Notification"
3. You should see a test notification appear

#### Disabling Notifications

1. Navigate to Settings
2. Click "Disable Push Notifications"

### For Developers

#### Sending Notifications from Backend

```python
from api_notifications import send_push_notification

# Send a processing complete notification
send_push_notification(
    title='Processing Complete',
    body='45 photos processed successfully',
    url='/sessions/123',
    notification_type='processing',
    data={'sessionId': '123', 'count': 45}
)
```

#### Showing Local Notifications

```javascript
import { showLocalNotification } from '../utils/notificationHelper';

// Show immediate feedback
await showLocalNotification(
  'Action Complete',
  'Your changes have been saved',
  { tag: 'save-complete' }
);
```

#### Checking Notification Status

```javascript
import notificationService from '../services/notificationService';

// Check if supported
if (notificationService.isSupported()) {
  // Check permission
  const permission = notificationService.getPermissionStatus();
  
  if (permission === 'granted') {
    // Notifications are enabled
  }
}
```

## Configuration

### Environment Variables

Add to `.env` file:

```env
# VAPID public key for push notifications
REACT_APP_VAPID_PUBLIC_KEY=your_vapid_public_key_here
```

### Generating VAPID Keys

VAPID keys are required for push notifications. Generate them using:

```bash
# Install web-push globally
npm install -g web-push

# Generate VAPID keys
web-push generate-vapid-keys

# Output:
# Public Key: BN...
# Private Key: ...
```

Add the public key to your `.env` file and the private key to your backend configuration.

## Service Worker Events

### Push Event

Triggered when a push notification is received:

```javascript
self.addEventListener('push', (event) => {
  const data = event.data.json();
  // Display notification
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});
```

### Notification Click Event

Triggered when user clicks a notification:

```javascript
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  // Navigate to relevant page
  event.waitUntil(
    clients.openWindow(event.notification.data.url)
  );
});
```

### Notification Close Event

Triggered when user dismisses a notification:

```javascript
self.addEventListener('notificationclose', (event) => {
  // Track dismissal
  fetch('/api/notifications/track', {
    method: 'POST',
    body: JSON.stringify({ action: 'dismissed' })
  });
});
```

## API Endpoints

### Subscribe to Notifications

```
POST /notifications/subscribe
Content-Type: application/json

{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "keys": {
    "p256dh": "...",
    "auth": "..."
  }
}
```

### Unsubscribe from Notifications

```
POST /notifications/unsubscribe
Content-Type: application/json

{
  "endpoint": "https://fcm.googleapis.com/fcm/send/..."
}
```

### Get Notification Settings

```
GET /notifications/settings
```

### Update Notification Settings

```
POST /notifications/settings
Content-Type: application/json

{
  "enabled": true,
  "types": {
    "processing_complete": true,
    "approval_required": true,
    "error": true,
    "export_complete": true
  }
}
```

## Browser Support

Push notifications are supported in:

- ✅ Chrome 50+
- ✅ Firefox 44+
- ✅ Edge 17+
- ✅ Opera 37+
- ✅ Samsung Internet 4+
- ❌ Safari (iOS) - Not supported
- ⚠️ Safari (macOS) - Limited support

## Troubleshooting

### Notifications Not Appearing

1. **Check Permission**: Ensure notifications are allowed in browser settings
2. **Check Service Worker**: Verify service worker is registered and active
3. **Check Subscription**: Ensure device is subscribed to push notifications
4. **Check Backend**: Verify backend is sending notifications correctly

### Permission Denied

If permission is denied:

1. Click the lock icon in the address bar
2. Find "Notifications" in permissions
3. Change to "Allow"
4. Refresh the page

### Service Worker Not Updating

If service worker changes aren't reflected:

1. Close all tabs with the app
2. Open DevTools → Application → Service Workers
3. Click "Unregister"
4. Refresh the page

## Security Considerations

1. **VAPID Keys**: Keep private key secure, never expose in client code
2. **Subscription Data**: Store securely, encrypt if necessary
3. **User Privacy**: Only send relevant notifications, respect user preferences
4. **Rate Limiting**: Prevent notification spam
5. **HTTPS Required**: Push notifications only work over HTTPS

## Testing

### Manual Testing

1. Enable notifications in Settings
2. Trigger events that should send notifications
3. Verify notifications appear correctly
4. Test notification click navigation
5. Test on different devices and browsers

### Automated Testing

```javascript
// Test notification permission request
test('should request notification permission', async () => {
  const result = await notificationService.requestPermission();
  expect(['granted', 'denied', 'default']).toContain(result);
});

// Test subscription
test('should subscribe to push notifications', async () => {
  const subscription = await notificationService.subscribe(apiService);
  expect(subscription).toBeDefined();
  expect(subscription.endpoint).toBeDefined();
});
```

## Future Enhancements

1. **Notification Grouping**: Group related notifications
2. **Action Buttons**: Add approve/reject buttons to notifications
3. **Rich Media**: Include images in notifications
4. **Quiet Hours**: Respect user's quiet hours settings
5. **Priority Levels**: Different urgency levels for notifications
6. **Notification History**: View past notifications in app

## References

- [Web Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
- [Notifications API](https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [VAPID Protocol](https://tools.ietf.org/html/rfc8292)
- [Web Push Protocol](https://tools.ietf.org/html/rfc8030)

## Support

For issues or questions:
1. Check browser console for errors
2. Review service worker logs in DevTools
3. Verify backend logs for push notification errors
4. Consult the troubleshooting section above
