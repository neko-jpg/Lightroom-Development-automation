/**
 * Push Notification Service
 * Handles push notification subscription and management
 */

const VAPID_PUBLIC_KEY = process.env.REACT_APP_VAPID_PUBLIC_KEY || '';

class NotificationService {
  constructor() {
    this.registration = null;
    this.subscription = null;
  }

  /**
   * Check if push notifications are supported
   */
  isSupported() {
    return 'serviceWorker' in navigator && 'PushManager' in window;
  }

  /**
   * Get current notification permission status
   */
  getPermissionStatus() {
    if (!this.isSupported()) {
      return 'unsupported';
    }
    return Notification.permission;
  }

  /**
   * Request notification permission from user
   */
  async requestPermission() {
    if (!this.isSupported()) {
      throw new Error('Push notifications are not supported in this browser');
    }

    const permission = await Notification.requestPermission();
    return permission;
  }

  /**
   * Subscribe to push notifications
   */
  async subscribe(apiService) {
    try {
      // Get service worker registration
      this.registration = await navigator.serviceWorker.ready;

      // Check if already subscribed
      let subscription = await this.registration.pushManager.getSubscription();

      if (!subscription) {
        // Convert VAPID key to Uint8Array
        const convertedVapidKey = this.urlBase64ToUint8Array(VAPID_PUBLIC_KEY);

        // Subscribe to push notifications
        subscription = await this.registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: convertedVapidKey,
        });
      }

      this.subscription = subscription;

      // Send subscription to backend
      await this.sendSubscriptionToBackend(subscription, apiService);

      return subscription;
    } catch (error) {
      console.error('Failed to subscribe to push notifications:', error);
      throw error;
    }
  }

  /**
   * Unsubscribe from push notifications
   */
  async unsubscribe(apiService) {
    try {
      if (!this.subscription) {
        const registration = await navigator.serviceWorker.ready;
        this.subscription = await registration.pushManager.getSubscription();
      }

      if (this.subscription) {
        // Remove subscription from backend
        await this.removeSubscriptionFromBackend(this.subscription, apiService);

        // Unsubscribe from push manager
        await this.subscription.unsubscribe();
        this.subscription = null;
      }

      return true;
    } catch (error) {
      console.error('Failed to unsubscribe from push notifications:', error);
      throw error;
    }
  }

  /**
   * Get current subscription
   */
  async getSubscription() {
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      this.subscription = subscription;
      return subscription;
    } catch (error) {
      console.error('Failed to get subscription:', error);
      return null;
    }
  }

  /**
   * Send subscription to backend
   */
  async sendSubscriptionToBackend(subscription, apiService) {
    const subscriptionData = {
      endpoint: subscription.endpoint,
      keys: {
        p256dh: this.arrayBufferToBase64(subscription.getKey('p256dh')),
        auth: this.arrayBufferToBase64(subscription.getKey('auth')),
      },
    };

    return apiService.subscribeToNotifications(subscriptionData);
  }

  /**
   * Remove subscription from backend
   */
  async removeSubscriptionFromBackend(subscription, apiService) {
    const endpoint = subscription.endpoint;
    return apiService.unsubscribeFromNotifications(endpoint);
  }

  /**
   * Convert VAPID key from base64 to Uint8Array
   */
  urlBase64ToUint8Array(base64String) {
    if (!base64String) {
      // Return empty array if no key provided (for development)
      return new Uint8Array(0);
    }

    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  /**
   * Convert ArrayBuffer to base64
   */
  arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }

  /**
   * Test notification (show local notification)
   */
  async testNotification() {
    if (!this.isSupported()) {
      throw new Error('Notifications are not supported');
    }

    if (Notification.permission !== 'granted') {
      throw new Error('Notification permission not granted');
    }

    const registration = await navigator.serviceWorker.ready;
    await registration.showNotification('Junmai AutoDev', {
      body: 'Push notifications are working!',
      icon: '/logo192.png',
      badge: '/logo192.png',
      tag: 'test-notification',
      data: {
        url: '/',
      },
    });
  }
}

// Export singleton instance
const notificationService = new NotificationService();
export default notificationService;
