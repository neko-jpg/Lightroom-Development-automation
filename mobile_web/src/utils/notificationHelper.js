/**
 * Notification Helper Utilities
 * Helper functions for handling notifications in the app
 */

import notificationService from '../services/notificationService';

/**
 * Notification types and their default configurations
 */
export const NotificationType = {
  PROCESSING_COMPLETE: {
    type: 'processing',
    icon: '✅',
    vibrate: [200, 100, 200],
  },
  APPROVAL_REQUIRED: {
    type: 'approval',
    icon: '⏳',
    vibrate: [100, 50, 100, 50, 100],
    requireInteraction: true,
  },
  ERROR: {
    type: 'error',
    icon: '❌',
    vibrate: [300, 100, 300],
    requireInteraction: true,
  },
  EXPORT_COMPLETE: {
    type: 'export',
    icon: '📤',
    vibrate: [200, 100, 200],
  },
  SESSION_STARTED: {
    type: 'session',
    icon: '🚀',
    vibrate: [100],
  },
};

/**
 * Get notification URL based on type and data
 */
export const getNotificationUrl = (type, data = {}) => {
  switch (type) {
    case 'approval':
      return '/approval';
    case 'session':
      return data.sessionId ? `/sessions/${data.sessionId}` : '/sessions';
    case 'error':
      return '/settings';
    case 'processing':
    case 'export':
    default:
      return '/';
  }
};

/**
 * Format notification title based on type
 */
export const formatNotificationTitle = (type, data = {}) => {
  switch (type) {
    case 'processing':
      return `Processing Complete`;
    case 'approval':
      return `Photos Ready for Approval`;
    case 'error':
      return `System Error`;
    case 'export':
      return `Export Complete`;
    case 'session':
      return `New Session Started`;
    default:
      return 'Junmai AutoDev';
  }
};

/**
 * Format notification body based on type and data
 */
export const formatNotificationBody = (type, data = {}) => {
  switch (type) {
    case 'processing':
      return `${data.count || 0} photos processed successfully`;
    case 'approval':
      return `${data.count || 0} photos waiting for your review`;
    case 'error':
      return data.message || 'An error occurred during processing';
    case 'export':
      return `${data.count || 0} photos exported to ${data.destination || 'destination'}`;
    case 'session':
      return `Session "${data.sessionName || 'Untitled'}" has started`;
    default:
      return 'New notification';
  }
};

/**
 * Check if notifications are enabled and permission granted
 */
export const canSendNotifications = () => {
  return notificationService.isSupported() && 
         notificationService.getPermissionStatus() === 'granted';
};

/**
 * Show a local notification (for testing or immediate feedback)
 */
export const showLocalNotification = async (title, body, options = {}) => {
  if (!canSendNotifications()) {
    console.warn('Notifications not available');
    return false;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    await registration.showNotification(title, {
      body,
      icon: '/logo192.png',
      badge: '/logo192.png',
      vibrate: [200, 100, 200],
      ...options,
    });
    return true;
  } catch (error) {
    console.error('Failed to show notification:', error);
    return false;
  }
};

/**
 * Request notification permission with user-friendly prompt
 */
export const requestNotificationPermissionWithPrompt = async () => {
  if (!notificationService.isSupported()) {
    return {
      success: false,
      message: 'Notifications are not supported in your browser',
    };
  }

  const currentPermission = notificationService.getPermissionStatus();

  if (currentPermission === 'granted') {
    return {
      success: true,
      message: 'Notifications are already enabled',
    };
  }

  if (currentPermission === 'denied') {
    return {
      success: false,
      message: 'Notifications are blocked. Please enable them in your browser settings.',
    };
  }

  try {
    const permission = await notificationService.requestPermission();
    
    if (permission === 'granted') {
      return {
        success: true,
        message: 'Notifications enabled successfully!',
      };
    } else {
      return {
        success: false,
        message: 'Notification permission denied',
      };
    }
  } catch (error) {
    return {
      success: false,
      message: `Failed to request permission: ${error.message}`,
    };
  }
};

/**
 * Handle notification click navigation
 */
export const handleNotificationClick = (notificationData, navigate) => {
  const url = notificationData.url || getNotificationUrl(notificationData.type, notificationData);
  
  if (navigate && typeof navigate === 'function') {
    navigate(url);
  } else {
    window.location.href = url;
  }
};

export default {
  NotificationType,
  getNotificationUrl,
  formatNotificationTitle,
  formatNotificationBody,
  canSendNotifications,
  showLocalNotification,
  requestNotificationPermissionWithPrompt,
  handleNotificationClick,
};
