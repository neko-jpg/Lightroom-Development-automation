/**
 * QuickActions Component
 * Displays quick action buttons for common tasks
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';

const QuickActions = () => {
  const [approvalCount, setApprovalCount] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    fetchApprovalCount();
    // Refresh every 15 seconds
    const interval = setInterval(fetchApprovalCount, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchApprovalCount = async () => {
    try {
      const data = await apiService.getApprovalQueue(100);
      setApprovalCount(data.count || 0);
    } catch (err) {
      console.error('Failed to fetch approval count:', err);
    }
  };

  const handleApprovalQueue = () => {
    navigate('/approval');
  };

  const handleViewSessions = () => {
    navigate('/sessions');
  };

  const handleSettings = () => {
    navigate('/settings');
  };

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-3">Quick Actions</h2>
      <div className="space-y-2">
        <button 
          className="btn btn-primary w-full flex items-center justify-between"
          onClick={handleApprovalQueue}
        >
          <span>Approval Queue</span>
          {approvalCount > 0 && (
            <span className="bg-white text-primary-600 px-2 py-1 rounded-full text-sm font-bold">
              {approvalCount}
            </span>
          )}
        </button>
        <button 
          className="btn btn-secondary w-full"
          onClick={handleViewSessions}
        >
          View All Sessions
        </button>
        <button 
          className="btn btn-secondary w-full"
          onClick={handleSettings}
        >
          Settings
        </button>
      </div>
    </div>
  );
};

export default QuickActions;
