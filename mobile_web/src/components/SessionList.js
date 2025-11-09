/**
 * SessionList Component
 * Displays a list of active sessions with progress
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import ProgressBar from './ProgressBar';

const SessionList = ({ activeOnly = true, limit = 10 }) => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchSessions();
    // Refresh every 10 seconds
    const interval = setInterval(fetchSessions, 10000);
    return () => clearInterval(interval);
  }, [activeOnly, limit]);

  const fetchSessions = async () => {
    try {
      const params = {
        limit,
        active_only: activeOnly,
      };
      const data = await apiService.getSessions(params);
      setSessions(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      importing: { class: 'badge badge-info', text: 'Importing' },
      selecting: { class: 'badge badge-info', text: 'Selecting' },
      developing: { class: 'badge badge-warning', text: 'Developing' },
      exporting: { class: 'badge badge-warning', text: 'Exporting' },
      completed: { class: 'badge badge-success', text: 'Completed' },
    };
    return statusMap[status] || { class: 'badge badge-info', text: status };
  };

  const calculateETA = (session) => {
    if (session.status === 'completed') return null;
    
    const remaining = session.total_photos - session.processed_photos;
    if (remaining <= 0) return null;
    
    // Assume 2.3 seconds per photo (from design doc)
    const avgTimePerPhoto = 2.3;
    const etaSeconds = remaining * avgTimePerPhoto;
    
    if (etaSeconds < 60) {
      return `${Math.round(etaSeconds)}s`;
    } else if (etaSeconds < 3600) {
      return `${Math.round(etaSeconds / 60)}m`;
    } else {
      const hours = Math.floor(etaSeconds / 3600);
      const minutes = Math.round((etaSeconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  };

  const handleSessionClick = (sessionId) => {
    navigate(`/sessions/${sessionId}`);
  };

  if (loading) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-3">Active Sessions</h2>
        <div className="text-center py-4 text-gray-500">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-3">Active Sessions</h2>
        <div className="text-center py-4 text-red-600">
          <p>Failed to load sessions</p>
          <p className="text-sm mt-2">{error}</p>
          <button 
            onClick={fetchSessions}
            className="btn btn-primary mt-3"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-3">Active Sessions</h2>
        <p className="text-gray-500 text-center py-4">No active sessions</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-3">Active Sessions</h2>
      <div className="space-y-4">
        {sessions.map((session) => {
          const statusInfo = getStatusBadge(session.status);
          const eta = calculateETA(session);
          
          return (
            <div 
              key={session.id}
              className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 cursor-pointer transition-colors"
              onClick={() => handleSessionClick(session.id)}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-gray-900 truncate">
                    📁 {session.name}
                  </h3>
                  <p className="text-xs text-gray-500 mt-1">
                    {session.import_folder}
                  </p>
                </div>
                <span className={statusInfo.class}>
                  {statusInfo.text}
                </span>
              </div>
              
              <ProgressBar 
                current={session.processed_photos}
                total={session.total_photos}
                showLabel={true}
              />
              
              {eta && (
                <div className="mt-2 text-sm text-gray-600">
                  ETA: {eta}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SessionList;
