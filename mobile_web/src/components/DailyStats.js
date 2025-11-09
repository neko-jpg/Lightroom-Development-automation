/**
 * DailyStats Component
 * Displays today's statistics (photos processed, success rate, avg time)
 */

import React, { useState, useEffect } from 'react';
import apiService from '../services/api';

const DailyStats = () => {
  const [stats, setStats] = useState({
    total_imported: 0,
    total_processed: 0,
    total_approved: 0,
    success_rate: 0,
    avg_processing_time: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats();
    // Refresh every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const data = await apiService.getDailyStatistics();
      if (data.today) {
        setStats(data.today);
      }
      setError(null);
    } catch (err) {
      console.error('Failed to fetch daily statistics:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-3">Today</h2>
        <div className="text-center py-4 text-gray-500">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-3">Today</h2>
        <div className="text-center py-4 text-red-600">
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  const successRate = Math.round(stats.success_rate * 100);
  const avgTime = stats.avg_processing_time.toFixed(1);

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-3">Today</h2>
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold text-primary-600">
            {stats.total_processed}
          </div>
          <div className="text-xs text-gray-600 mt-1">Photos</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-green-600">
            {successRate}%
          </div>
          <div className="text-xs text-gray-600 mt-1">Success</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-gray-600">
            {avgTime}s
          </div>
          <div className="text-xs text-gray-600 mt-1">Avg Time</div>
        </div>
      </div>
      
      {stats.total_imported > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Imported</span>
            <span className="text-gray-900 font-medium">{stats.total_imported}</span>
          </div>
          <div className="flex justify-between text-sm mt-1">
            <span className="text-gray-600">Approved</span>
            <span className="text-gray-900 font-medium">{stats.total_approved}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default DailyStats;
