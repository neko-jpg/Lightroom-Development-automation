import React from 'react';
import { useParams } from 'react-router-dom';

const Sessions = () => {
  const { id } = useParams();

  if (id) {
    // Session detail view
    return (
      <div className="page-transition p-4">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Session Details</h1>
          <p className="text-gray-600">Session ID: {id}</p>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-3">Session Info</h2>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Status</span>
              <span className="badge badge-info">Processing</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Photos</span>
              <span className="font-medium">0 / 0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Progress</span>
              <span className="font-medium">0%</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Sessions list view
  return (
    <div className="page-transition p-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Sessions</h1>
        <p className="text-gray-600">Manage your photo sessions</p>
      </div>

      {/* Empty State */}
      <div className="card text-center py-12">
        <div className="text-6xl mb-4">📁</div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          No Sessions Yet
        </h3>
        <p className="text-gray-600 mb-4">
          Start by importing photos to create a session
        </p>
        <button className="btn btn-primary">
          Create Session
        </button>
      </div>
    </div>
  );
};

export default Sessions;
