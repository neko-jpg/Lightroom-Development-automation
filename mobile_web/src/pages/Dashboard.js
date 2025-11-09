/**
 * Dashboard Page
 * Main dashboard view showing system status, sessions, and statistics
 * 
 * Requirements: 9.2, 9.5
 */

import React from 'react';
import SystemStatus from '../components/SystemStatus';
import DailyStats from '../components/DailyStats';
import SessionList from '../components/SessionList';
import QuickActions from '../components/QuickActions';

const Dashboard = () => {
  return (
    <div className="page-transition p-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-gray-600">System overview and status</p>
      </div>

      {/* System Status */}
      <SystemStatus />

      {/* Today's Statistics */}
      <DailyStats />

      {/* Active Sessions */}
      <SessionList activeOnly={true} limit={10} />

      {/* Quick Actions */}
      <QuickActions />
    </div>
  );
};

export default Dashboard;
