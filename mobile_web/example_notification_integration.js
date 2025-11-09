/**
 * Example: Push Notification Integration
 * 
 * This file demonstrates how to integrate push notifications
 * into different parts of the Junmai AutoDev application.
 */

import notificationService from './src/services/notificationService';
import apiService from './src/services/api';
import { 
  showLocalNotification, 
  canSendNotifications,
  NotificationType 
} from './src/utils/notificationHelper';

// ============================================================================
// Example 1: Initialize Notifications on App Start
// ============================================================================

export async function initializeNotifications() {
  console.log('Initializing push notifications...');
  
  // Check if notifications are supported
  if (!notificationService.isSupported()) {
    console.warn('Push notifications not supported in this browser');
    return false;
  }
  
  // Check current permission status
  const permission = notificationService.getPermissionStatus();
  console.log('Current permission:', permission);
  
  // If already granted, ensure subscription is active
  if (permission === 'granted') {
    const subscription = await notificationService.getSubscription();
    
    if (!subscription) {
      console.log('Permission granted but not subscribed, subscribing...');
      await notificationService.subscribe(apiService);
    } else {
      console.log('Already subscribed to push notifications');
    }
  }
  
  return true;
}

// ============================================================================
// Example 2: Request Notifications with User Prompt
// ============================================================================

export async function promptUserForNotifications() {
  // Check if already enabled
  if (canSendNotifications()) {
    console.log('Notifications already enabled');
    return true;
  }
  
  // Show custom prompt (you can use a modal or dialog)
  const userWantsNotifications = confirm(
    'Enable push notifications to stay updated on processing status, ' +
    'approvals, and errors?'
  );
  
  if (!userWantsNotifications) {
    console.log('User declined notifications');
    return false;
  }
  
  try {
    // Request permission
    const permission = await notificationService.requestPermission();
    
    if (permission === 'granted') {
      // Subscribe to push notifications
      await notificationService.subscribe(apiService);
      
      // Show success notification
      await showLocalNotification(
        'Notifications Enabled!',
        'You will now receive updates about your photo processing.',
        { tag: 'notification-enabled' }
      );
      
      return true;
    } else {
      console.log('Permission denied');
      return false;
    }
  } catch (error) {
    console.error('Failed to enable notifications:', error);
    return false;
  }
}

// ============================================================================
// Example 3: Send Notification When Processing Completes
// ============================================================================

export async function notifyProcessingComplete(sessionId, photoCount) {
  // This would typically be called from the backend
  // But here's how you'd trigger it from the frontend for testing
  
  if (!canSendNotifications()) {
    console.log('Notifications not enabled, skipping');
    return;
  }
  
  // Show local notification (for immediate feedback)
  await showLocalNotification(
    'Processing Complete',
    `${photoCount} photos processed successfully`,
    {
      tag: `processing-${sessionId}`,
      data: {
        url: `/sessions/${sessionId}`,
        type: 'processing',
        sessionId,
        count: photoCount
      },
      ...NotificationType.PROCESSING_COMPLETE
    }
  );
}

// ============================================================================
// Example 4: Send Notification When Approval Needed
// ============================================================================

export async function notifyApprovalRequired(photoCount) {
  if (!canSendNotifications()) {
    return;
  }
  
  await showLocalNotification(
    'Photos Ready for Approval',
    `${photoCount} photos waiting for your review`,
    {
      tag: 'approval-required',
      data: {
        url: '/approval',
        type: 'approval',
        count: photoCount
      },
      ...NotificationType.APPROVAL_REQUIRED
    }
  );
}

// ============================================================================
// Example 5: Send Error Notification
// ============================================================================

export async function notifyError(errorMessage) {
  if (!canSendNotifications()) {
    return;
  }
  
  await showLocalNotification(
    'System Error',
    errorMessage,
    {
      tag: 'error',
      data: {
        url: '/settings',
        type: 'error',
        message: errorMessage
      },
      ...NotificationType.ERROR
    }
  );
}

// ============================================================================
// Example 6: Backend Integration (Python)
// ============================================================================

/*
# In your Python backend code:

from api_notifications import send_push_notification

# After processing completes
def on_processing_complete(session_id, photo_count):
    send_push_notification(
        title='Processing Complete',
        body=f'{photo_count} photos processed successfully',
        url=f'/sessions/{session_id}',
        notification_type='processing',
        data={
            'sessionId': session_id,
            'count': photo_count
        }
    )

# When approval is needed
def on_approval_required(photo_count):
    send_push_notification(
        title='Photos Ready for Approval',
        body=f'{photo_count} photos waiting for review',
        url='/approval',
        notification_type='approval',
        data={
            'count': photo_count
        }
    )

# On error
def on_error(error_message):
    send_push_notification(
        title='System Error',
        body=error_message,
        url='/settings',
        notification_type='error',
        data={
            'message': error_message
        }
    )

# When export completes
def on_export_complete(photo_count, destination):
    send_push_notification(
        title='Export Complete',
        body=f'{photo_count} photos exported to {destination}',
        url='/',
        notification_type='export',
        data={
            'count': photo_count,
            'destination': destination
        }
    )
*/

// ============================================================================
// Example 7: React Component Integration
// ============================================================================

/*
import React, { useEffect, useState } from 'react';
import notificationService from './services/notificationService';
import apiService from './services/api';

function NotificationButton() {
  const [isEnabled, setIsEnabled] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    checkNotificationStatus();
  }, []);

  const checkNotificationStatus = async () => {
    const permission = notificationService.getPermissionStatus();
    if (permission === 'granted') {
      const subscription = await notificationService.getSubscription();
      setIsEnabled(!!subscription);
    }
  };

  const handleToggle = async () => {
    setIsLoading(true);
    try {
      if (isEnabled) {
        await notificationService.unsubscribe(apiService);
        setIsEnabled(false);
      } else {
        const permission = await notificationService.requestPermission();
        if (permission === 'granted') {
          await notificationService.subscribe(apiService);
          setIsEnabled(true);
        }
      }
    } catch (error) {
      console.error('Failed to toggle notifications:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button onClick={handleToggle} disabled={isLoading}>
      {isLoading ? 'Loading...' : isEnabled ? 'Disable Notifications' : 'Enable Notifications'}
    </button>
  );
}
*/

// ============================================================================
// Example 8: WebSocket Integration
// ============================================================================

export function setupWebSocketNotifications(ws) {
  // Listen for WebSocket events and trigger notifications
  
  ws.on('processing_complete', (data) => {
    notifyProcessingComplete(data.sessionId, data.photoCount);
  });
  
  ws.on('approval_required', (data) => {
    notifyApprovalRequired(data.photoCount);
  });
  
  ws.on('error', (data) => {
    notifyError(data.message);
  });
  
  ws.on('export_complete', (data) => {
    showLocalNotification(
      'Export Complete',
      `${data.photoCount} photos exported`,
      {
        tag: 'export-complete',
        data: {
          url: '/',
          type: 'export',
          count: data.photoCount
        },
        ...NotificationType.EXPORT_COMPLETE
      }
    );
  });
}

// ============================================================================
// Example 9: Notification Settings Persistence
// ============================================================================

export async function saveNotificationPreferences(preferences) {
  // Save to backend
  await apiService.updateNotificationSettings(preferences);
  
  // Save to local storage as backup
  localStorage.setItem('notificationPreferences', JSON.stringify(preferences));
  
  console.log('Notification preferences saved:', preferences);
}

export async function loadNotificationPreferences() {
  try {
    // Try to load from backend first
    const response = await apiService.getNotificationSettings();
    return response.settings;
  } catch (error) {
    // Fallback to local storage
    const stored = localStorage.getItem('notificationPreferences');
    return stored ? JSON.parse(stored) : getDefaultPreferences();
  }
}

function getDefaultPreferences() {
  return {
    enabled: true,
    types: {
      processing_complete: true,
      approval_required: true,
      error: true,
      export_complete: true,
      session_started: false
    },
    quiet_hours: {
      enabled: false,
      start: '22:00',
      end: '08:00'
    }
  };
}

// ============================================================================
// Example 10: Testing Notifications
// ============================================================================

export async function testAllNotificationTypes() {
  console.log('Testing all notification types...');
  
  if (!canSendNotifications()) {
    console.error('Notifications not enabled');
    return;
  }
  
  // Test processing complete
  await notifyProcessingComplete('test-session-1', 45);
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Test approval required
  await notifyApprovalRequired(12);
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Test error
  await notifyError('This is a test error message');
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Test export complete
  await showLocalNotification(
    'Export Complete',
    '30 photos exported to /exports',
    {
      tag: 'export-test',
      data: { url: '/', type: 'export' },
      ...NotificationType.EXPORT_COMPLETE
    }
  );
  
  console.log('All notification types tested!');
}

// ============================================================================
// Export all examples
// ============================================================================

export default {
  initializeNotifications,
  promptUserForNotifications,
  notifyProcessingComplete,
  notifyApprovalRequired,
  notifyError,
  setupWebSocketNotifications,
  saveNotificationPreferences,
  loadNotificationPreferences,
  testAllNotificationTypes
};
