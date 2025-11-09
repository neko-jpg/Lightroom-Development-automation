/**
 * ProgressBar Component
 * Displays a progress bar with percentage
 */

import React from 'react';

const ProgressBar = ({ current, total, showLabel = true, className = '' }) => {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
  
  const getProgressColor = () => {
    if (percentage >= 100) return 'bg-green-500';
    if (percentage >= 75) return 'bg-blue-500';
    if (percentage >= 50) return 'bg-yellow-500';
    return 'bg-gray-400';
  };

  return (
    <div className={className}>
      {showLabel && (
        <div className="flex justify-between items-center mb-1 text-sm">
          <span className="text-gray-600">
            {current} / {total}
          </span>
          <span className="text-gray-900 font-medium">{percentage}%</span>
        </div>
      )}
      <div className="progress-bar">
        <div 
          className={`progress-bar-fill ${getProgressColor()}`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
};

export default ProgressBar;
