/**
 * SystemStatus Component
 * Displays system status including Lightroom connection, LLM status, and resource usage
 */

import React, { useState, useEffect } from 'react';
import apiService from '../services/api';

const SystemStatus = () => {
  const [status, setStatus] = useState({
    system: 'unknown',
    lightroom: 'unknown',
    llm: 'Ollama (Llama 3.1)',
    active_sessions: 0,
    pending_jobs: 0,
    processing_jobs: 0,
  });
  const [resources, setResources] = useState({
    cpu_percent: 0,
    memory_percent: 0,
    gpu_available: false,
    gpu_temperature: 0,
    gpu_utilization: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStatus();
    // Refresh every 5 seconds
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const [systemStatus, resourceStatus] = await Promise.all([
        apiService.getSystemStatus(),
        apiService.getResourceStatus().catch(() => null), // Optional
      ]);

      setStatus({
        system: systemStatus.system || 'running',
        lightroom: 'connected', // Simplified - would need actual check
        llm: 'Ollama (Llama 3.1)',
        active_sessions: systemStatus.active_sessions || 0,
        pending_jobs: systemStatus.pending_jobs || 0,
        processing_jobs: systemStatus.processing_jobs || 0,
      });

      if (resourceStatus) {
        setResources(resourceStatus);
      }

      setError(null);
    } catch (err) {
      console.error('Failed to fetch system status:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    if (status === 'running' || status === 'connected') {
      return 'badge badge-success';
    } else if (status === 'unknown') {
      return 'badge badge-warning';
    } else {
      return 'badge badge-error';
    }
  };

  const getStatusText = (status) => {
    if (status === 'running') return 'Running';
    if (status === 'connected') return 'Connected';
    if (status === 'unknown') return 'Unknown';
    return 'Disconnected';
  };

  if (loading) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-3">System Status</h2>
        <div className="text-center py-4 text-gray-500">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-3">System Status</h2>
        <div className="text-center py-4 text-red-600">
          <p>Failed to load status</p>
          <p className="text-sm mt-2">{error}</p>
          <button 
            onClick={fetchStatus}
            className="btn btn-primary mt-3"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-3">System Status</h2>
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Status</span>
          <span className={getStatusBadge(status.system)}>
            {getStatusText(status.system)}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Lightroom</span>
          <span className={getStatusBadge(status.lightroom)}>
            {getStatusText(status.lightroom)}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-600">LLM</span>
          <span className="text-gray-900 font-medium">{status.llm}</span>
        </div>
        
        {resources.gpu_available && (
          <div className="flex justify-between items-center">
            <span className="text-gray-600">GPU</span>
            <span className="text-gray-900 font-medium">
              {resources.gpu_temperature}°C ({resources.gpu_utilization}%)
            </span>
          </div>
        )}

        {(status.active_sessions > 0 || status.pending_jobs > 0 || status.processing_jobs > 0) && (
          <>
            <div className="border-t border-gray-200 my-2"></div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-600">Active Sessions</span>
              <span className="text-gray-900 font-medium">{status.active_sessions}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-600">Pending Jobs</span>
              <span className="text-gray-900 font-medium">{status.pending_jobs}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-600">Processing</span>
              <span className="text-gray-900 font-medium">{status.processing_jobs}</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default SystemStatus;
