import React from 'react';
import NotificationSettings from '../components/NotificationSettings';

const Settings = () => {
  return (
    <div className="page-transition p-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Settings</h1>
        <p className="text-gray-600">Configure your preferences</p>
      </div>

      {/* Push Notifications */}
      <NotificationSettings />

      {/* System Settings */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-3">System</h2>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-700">Auto-refresh</span>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Connection Settings */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-3">Connection</h2>
        <div className="space-y-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              API Server
            </label>
            <input
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              defaultValue="http://localhost:5100"
            />
          </div>
        </div>
      </div>

      {/* About */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-3">About</h2>
        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex justify-between">
            <span>Version</span>
            <span className="font-medium">1.0.0</span>
          </div>
          <div className="flex justify-between">
            <span>Build</span>
            <span className="font-medium">2025.11.09</span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="space-y-2">
        <button className="btn btn-secondary w-full">
          Clear Cache
        </button>
        <button className="btn btn-danger w-full">
          Sign Out
        </button>
      </div>
    </div>
  );
};

export default Settings;
