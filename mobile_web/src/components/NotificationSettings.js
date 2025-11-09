import React, { useState, useEffect } from 'react';
import notificationService from '../services/notificationService';
import apiService from '../services/api';

const NotificationSettings = () => {
  const [permission, setPermission] = useState('default');
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    checkNotificationStatus();
  }, []);

  const checkNotificationStatus = async () => {
    const currentPermission = notificationService.getPermissionStatus();
    setPermission(currentPermission);

    if (currentPermission === 'granted') {
      const subscription = await notificationService.getSubscription();
      setIsSubscribed(!!subscription);
    }
  };

  const handleEnableNotifications = async () => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Request permission
      const permission = await notificationService.requestPermission();
      setPermission(permission);

      if (permission === 'granted') {
        // Subscribe to push notifications
        await notificationService.subscribe(apiService);
        setIsSubscribed(true);
        setSuccess('Push notifications enabled successfully!');
      } else if (permission === 'denied') {
        setError('Notification permission denied. Please enable it in your browser settings.');
      }
    } catch (err) {
      console.error('Failed to enable notifications:', err);
      setError('Failed to enable notifications: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisableNotifications = async () => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await notificationService.unsubscribe(apiService);
      setIsSubscribed(false);
      setSuccess('Push notifications disabled successfully!');
    } catch (err) {
      console.error('Failed to disable notifications:', err);
      setError('Failed to disable notifications: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestNotification = async () => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await notificationService.testNotification();
      setSuccess('Test notification sent!');
    } catch (err) {
      console.error('Failed to send test notification:', err);
      setError('Failed to send test notification: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = () => {
    if (permission === 'unsupported') {
      return (
        <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
          Not Supported
        </span>
      );
    }

    if (permission === 'granted' && isSubscribed) {
      return (
        <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
          Enabled
        </span>
      );
    }

    if (permission === 'denied') {
      return (
        <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">
          Blocked
        </span>
      );
    }

    return (
      <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
        Disabled
      </span>
    );
  };

  const getStatusMessage = () => {
    if (permission === 'unsupported') {
      return 'Push notifications are not supported in your browser.';
    }

    if (permission === 'granted' && isSubscribed) {
      return 'You will receive notifications about processing status, approvals, and errors.';
    }

    if (permission === 'denied') {
      return 'Notifications are blocked. Please enable them in your browser settings.';
    }

    return 'Enable push notifications to stay updated on processing status.';
  };

  return (
    <div className="card">
      <div className="flex justify-between items-start mb-3">
        <h2 className="text-lg font-semibold">Push Notifications</h2>
        {getStatusBadge()}
      </div>

      <p className="text-sm text-gray-600 mb-4">{getStatusMessage()}</p>

      {/* Alert Messages */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-800">{success}</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="space-y-2">
        {permission !== 'unsupported' && !isSubscribed && permission !== 'denied' && (
          <button
            onClick={handleEnableNotifications}
            disabled={isLoading}
            className="btn btn-primary w-full"
          >
            {isLoading ? 'Enabling...' : 'Enable Push Notifications'}
          </button>
        )}

        {permission === 'granted' && isSubscribed && (
          <>
            <button
              onClick={handleTestNotification}
              disabled={isLoading}
              className="btn btn-secondary w-full"
            >
              {isLoading ? 'Sending...' : 'Send Test Notification'}
            </button>
            <button
              onClick={handleDisableNotifications}
              disabled={isLoading}
              className="btn btn-danger w-full"
            >
              {isLoading ? 'Disabling...' : 'Disable Push Notifications'}
            </button>
          </>
        )}

        {permission === 'denied' && (
          <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
            <p className="text-sm text-gray-700 mb-2">
              To enable notifications:
            </p>
            <ol className="text-sm text-gray-600 list-decimal list-inside space-y-1">
              <li>Click the lock icon in your browser's address bar</li>
              <li>Find "Notifications" in the permissions list</li>
              <li>Change the setting to "Allow"</li>
              <li>Refresh this page</li>
            </ol>
          </div>
        )}
      </div>

      {/* Notification Types Info */}
      {permission === 'granted' && isSubscribed && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-2">
            You'll receive notifications for:
          </h3>
          <ul className="text-sm text-gray-600 space-y-1">
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Processing completion (batch finished)</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Photos ready for approval</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>System errors and warnings</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Export completion</span>
            </li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default NotificationSettings;
