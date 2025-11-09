# Push Notification Quick Start Guide

## For End Users

### Enable Notifications (3 Steps)

1. **Open Settings**
   - Tap the menu icon (☰)
   - Select "Settings"

2. **Enable Push Notifications**
   - Find "Push Notifications" section
   - Tap "Enable Push Notifications"
   - Allow when browser asks for permission

3. **Test It**
   - Tap "Send Test Notification"
   - You should see a notification appear!

### What You'll Get Notified About

- ✅ **Processing Complete**: When your photos are done processing
- ⏳ **Approval Required**: When photos need your review
- ❌ **Errors**: If something goes wrong
- 📤 **Export Complete**: When photos are exported

### Troubleshooting

**Notifications not working?**

1. Check if notifications are blocked:
   - Look for 🔒 icon in address bar
   - Click it → Find "Notifications"
   - Change to "Allow"
   - Refresh page

2. Still not working?
   - Close all app tabs
   - Reopen the app
   - Try enabling again

## For Developers

### Quick Setup (5 Minutes)

#### 1. Generate VAPID Keys

```bash
npm install -g web-push
web-push generate-vapid-keys
```

#### 2. Configure Environment

Create `.env` file:

```env
REACT_APP_VAPID_PUBLIC_KEY=your_public_key_here
```

Add private key to backend config.

#### 3. Install Dependencies

```bash
# Backend
pip install pywebpush

# Frontend (already included)
# Service worker handles push notifications
```

#### 4. Test Locally

```javascript
// In browser console
import notificationService from './services/notificationService';

// Request permission
await notificationService.requestPermission();

// Subscribe
await notificationService.subscribe(apiService);

// Test notification
await notificationService.testNotification();
```

#### 5. Send from Backend

```python
from api_notifications import send_push_notification

send_push_notification(
    title='Test Notification',
    body='Push notifications are working!',
    url='/',
    notification_type='general'
)
```

### Common Integration Points

#### After Processing Complete

```python
# In your processing code
from api_notifications import send_push_notification

def on_processing_complete(session_id, photo_count):
    send_push_notification(
        title='Processing Complete',
        body=f'{photo_count} photos processed',
        url=f'/sessions/{session_id}',
        notification_type='processing',
        data={'sessionId': session_id, 'count': photo_count}
    )
```

#### When Approval Needed

```python
def on_approval_required(photo_count):
    send_push_notification(
        title='Photos Ready for Approval',
        body=f'{photo_count} photos waiting for review',
        url='/approval',
        notification_type='approval',
        data={'count': photo_count}
    )
```

#### On Error

```python
def on_error(error_message):
    send_push_notification(
        title='System Error',
        body=error_message,
        url='/settings',
        notification_type='error',
        data={'message': error_message}
    )
```

### Testing Checklist

- [ ] VAPID keys generated and configured
- [ ] Service worker registered successfully
- [ ] Permission request works
- [ ] Subscription created successfully
- [ ] Test notification appears
- [ ] Notification click navigates correctly
- [ ] Backend can send notifications
- [ ] Notifications work when app is closed
- [ ] Unsubscribe works correctly

### Debug Commands

```javascript
// Check service worker status
navigator.serviceWorker.getRegistrations().then(console.log);

// Check current subscription
navigator.serviceWorker.ready.then(reg => 
  reg.pushManager.getSubscription().then(console.log)
);

// Check permission
console.log(Notification.permission);

// Force service worker update
navigator.serviceWorker.getRegistrations().then(regs => 
  regs.forEach(reg => reg.update())
);
```

## Production Deployment

### Checklist

1. **VAPID Keys**
   - [ ] Generated securely
   - [ ] Public key in frontend env
   - [ ] Private key in backend config (secure)
   - [ ] Keys never committed to git

2. **HTTPS**
   - [ ] App served over HTTPS
   - [ ] Valid SSL certificate
   - [ ] No mixed content warnings

3. **Service Worker**
   - [ ] Registered correctly
   - [ ] Caching strategy configured
   - [ ] Update mechanism working

4. **Backend**
   - [ ] pywebpush installed
   - [ ] Subscription storage configured
   - [ ] Error handling implemented
   - [ ] Rate limiting configured

5. **Testing**
   - [ ] Tested on Chrome
   - [ ] Tested on Firefox
   - [ ] Tested on Edge
   - [ ] Tested on mobile devices
   - [ ] Tested notification click navigation

### Performance Tips

1. **Batch Notifications**: Don't send too many at once
2. **Relevant Content**: Only send important notifications
3. **Clear Actions**: Make it obvious what to do
4. **Respect Preferences**: Honor user notification settings
5. **Clean Up**: Remove invalid subscriptions regularly

## Need Help?

1. Check browser console for errors
2. Review `PUSH_NOTIFICATION_IMPLEMENTATION.md` for details
3. Test with `Send Test Notification` button
4. Verify service worker is active in DevTools

## Quick Reference

### User Actions
- Enable: Settings → Push Notifications → Enable
- Test: Settings → Send Test Notification
- Disable: Settings → Disable Push Notifications

### Developer Actions
- Subscribe: `notificationService.subscribe(apiService)`
- Unsubscribe: `notificationService.unsubscribe(apiService)`
- Send: `send_push_notification(title, body, url, type)`
- Test: `notificationService.testNotification()`

### API Endpoints
- Subscribe: `POST /notifications/subscribe`
- Unsubscribe: `POST /notifications/unsubscribe`
- Settings: `GET/POST /notifications/settings`
- Track: `POST /notifications/track`
