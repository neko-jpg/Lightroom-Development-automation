import React, { useState, useEffect, useRef } from 'react';
import apiService from '../services/api';

const ApprovalQueue = () => {
  const [queue, setQueue] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [swipeOffset, setSwipeOffset] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const touchStartX = useRef(0);
  const touchStartY = useRef(0);
  const cardRef = useRef(null);

  useEffect(() => {
    loadQueue();
  }, []);

  const loadQueue = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getApprovalQueue();
      setQueue(data.photos || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const currentPhoto = queue[currentIndex];

  // Touch event handlers for swipe gestures
  const handleTouchStart = (e) => {
    if (isProcessing) return;
    touchStartX.current = e.touches[0].clientX;
    touchStartY.current = e.touches[0].clientY;
  };

  const handleTouchMove = (e) => {
    if (isProcessing) return;
    const touchX = e.touches[0].clientX;
    const touchY = e.touches[0].clientY;
    const deltaX = touchX - touchStartX.current;
    const deltaY = touchY - touchStartY.current;

    // Only allow horizontal swipe if horizontal movement is greater than vertical
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      e.preventDefault();
      setSwipeOffset(deltaX);
    }
  };

  const handleTouchEnd = async () => {
    if (isProcessing) return;
    
    const threshold = 100; // Minimum swipe distance to trigger action

    if (swipeOffset > threshold) {
      // Swipe right - Approve
      await handleApprove();
    } else if (swipeOffset < -threshold) {
      // Swipe left - Reject
      await handleReject();
    } else {
      // Reset position if swipe was too short
      setSwipeOffset(0);
    }
  };

  const handleApprove = async () => {
    if (!currentPhoto || isProcessing) return;
    
    setIsProcessing(true);
    try {
      await apiService.approvePhoto(currentPhoto.id);
      moveToNext();
    } catch (err) {
      setError(`Failed to approve: ${err.message}`);
      setSwipeOffset(0);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!currentPhoto || isProcessing) return;
    
    setIsProcessing(true);
    try {
      await apiService.rejectPhoto(currentPhoto.id, 'Rejected via mobile');
      moveToNext();
    } catch (err) {
      setError(`Failed to reject: ${err.message}`);
      setSwipeOffset(0);
    } finally {
      setIsProcessing(false);
    }
  };

  const moveToNext = () => {
    setSwipeOffset(0);
    setShowDetails(false);
    
    if (currentIndex < queue.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      // Reload queue when reaching the end
      setCurrentIndex(0);
      loadQueue();
    }
  };

  const toggleDetails = () => {
    setShowDetails(!showDetails);
  };

  if (loading) {
    return (
      <div className="page-transition p-4">
        <div className="flex justify-center items-center h-64">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-transition p-4">
        <div className="card bg-red-50 border border-red-200">
          <p className="text-red-800">Error: {error}</p>
          <button 
            onClick={loadQueue}
            className="btn btn-primary mt-4"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!queue.length) {
    return (
      <div className="page-transition p-4">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Approval Queue</h1>
          <p className="text-gray-600">Review and approve processed photos</p>
        </div>

        {/* Empty State */}
        <div className="card text-center py-12">
          <div className="text-6xl mb-4">✅</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            All Caught Up!
          </h3>
          <p className="text-gray-600">
            No photos waiting for approval
          </p>
        </div>

        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-blue-900 mb-2">How to use:</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Swipe left to reject</li>
            <li>• Swipe right to approve</li>
            <li>• Tap for details</li>
          </ul>
        </div>
      </div>
    );
  }

  const swipeProgress = Math.abs(swipeOffset) / 100;
  const swipeOpacity = Math.min(swipeProgress, 1);

  return (
    <div className="page-transition p-4 pb-24">
      {/* Header */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <h1 className="text-2xl font-bold text-gray-900">Approval Queue</h1>
          <span className="badge badge-info">
            {currentIndex + 1} / {queue.length}
          </span>
        </div>
        <p className="text-gray-600">Swipe to approve or reject</p>
      </div>

      {/* Swipe Card Container */}
      <div className="relative mb-4" style={{ minHeight: '500px' }}>
        {/* Swipe Indicators */}
        <div 
          className="absolute left-4 top-1/2 transform -translate-y-1/2 z-10 pointer-events-none"
          style={{ opacity: swipeOffset > 0 ? swipeOpacity : 0 }}
        >
          <div className="bg-green-500 text-white rounded-full p-4 shadow-lg">
            <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        </div>

        <div 
          className="absolute right-4 top-1/2 transform -translate-y-1/2 z-10 pointer-events-none"
          style={{ opacity: swipeOffset < 0 ? swipeOpacity : 0 }}
        >
          <div className="bg-red-500 text-white rounded-full p-4 shadow-lg">
            <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        </div>

        {/* Photo Card */}
        <div
          ref={cardRef}
          className="card cursor-pointer select-none"
          style={{
            transform: `translateX(${swipeOffset}px) rotate(${swipeOffset * 0.05}deg)`,
            transition: swipeOffset === 0 ? 'transform 0.3s ease-out' : 'none',
            opacity: isProcessing ? 0.5 : 1
          }}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
          onClick={toggleDetails}
        >
          {/* Photo Preview */}
          <div className="relative bg-gray-200 rounded-lg overflow-hidden mb-4" style={{ height: '400px' }}>
            {currentPhoto.thumbnail_url ? (
              <img 
                src={currentPhoto.thumbnail_url} 
                alt={currentPhoto.file_name}
                className="w-full h-full object-contain"
                draggable="false"
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center text-gray-500">
                  <svg className="w-16 h-16 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <p className="text-sm">{currentPhoto.file_name}</p>
                </div>
              </div>
            )}
          </div>

          {/* Photo Info */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-gray-900">{currentPhoto.file_name}</span>
              <div className="flex items-center">
                {[...Array(5)].map((_, i) => (
                  <svg
                    key={i}
                    className={`w-5 h-5 ${i < Math.floor(currentPhoto.ai_score || 0) ? 'text-yellow-400' : 'text-gray-300'}`}
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ))}
                <span className="ml-2 text-sm text-gray-600">{currentPhoto.ai_score?.toFixed(1) || 'N/A'}</span>
              </div>
            </div>

            {currentPhoto.context_tag && (
              <div>
                <span className="badge badge-info">{currentPhoto.context_tag}</span>
              </div>
            )}

            {currentPhoto.selected_preset && (
              <div className="text-sm text-gray-600">
                <span className="font-medium">Preset:</span> {currentPhoto.selected_preset}
              </div>
            )}
          </div>

          {/* Details Section (Expandable) */}
          {showDetails && (
            <div className="mt-4 pt-4 border-t border-gray-200 space-y-2 text-sm">
              <div className="grid grid-cols-2 gap-2">
                {currentPhoto.camera_model && (
                  <div>
                    <span className="text-gray-500">Camera:</span>
                    <p className="font-medium">{currentPhoto.camera_model}</p>
                  </div>
                )}
                {currentPhoto.lens && (
                  <div>
                    <span className="text-gray-500">Lens:</span>
                    <p className="font-medium">{currentPhoto.lens}</p>
                  </div>
                )}
                {currentPhoto.iso && (
                  <div>
                    <span className="text-gray-500">ISO:</span>
                    <p className="font-medium">{currentPhoto.iso}</p>
                  </div>
                )}
                {currentPhoto.aperture && (
                  <div>
                    <span className="text-gray-500">Aperture:</span>
                    <p className="font-medium">f/{currentPhoto.aperture}</p>
                  </div>
                )}
                {currentPhoto.shutter_speed && (
                  <div>
                    <span className="text-gray-500">Shutter:</span>
                    <p className="font-medium">{currentPhoto.shutter_speed}</p>
                  </div>
                )}
                {currentPhoto.focal_length && (
                  <div>
                    <span className="text-gray-500">Focal Length:</span>
                    <p className="font-medium">{currentPhoto.focal_length}mm</p>
                  </div>
                )}
              </div>

              {currentPhoto.capture_time && (
                <div>
                  <span className="text-gray-500">Captured:</span>
                  <p className="font-medium">{new Date(currentPhoto.capture_time).toLocaleString()}</p>
                </div>
              )}

              {(currentPhoto.focus_score || currentPhoto.exposure_score || currentPhoto.composition_score) && (
                <div className="pt-2 border-t border-gray-100">
                  <p className="text-gray-500 mb-2">AI Analysis:</p>
                  <div className="space-y-1">
                    {currentPhoto.focus_score && (
                      <div className="flex justify-between">
                        <span>Focus:</span>
                        <span className="font-medium">{currentPhoto.focus_score.toFixed(1)}/5.0</span>
                      </div>
                    )}
                    {currentPhoto.exposure_score && (
                      <div className="flex justify-between">
                        <span>Exposure:</span>
                        <span className="font-medium">{currentPhoto.exposure_score.toFixed(1)}/5.0</span>
                      </div>
                    )}
                    {currentPhoto.composition_score && (
                      <div className="flex justify-between">
                        <span>Composition:</span>
                        <span className="font-medium">{currentPhoto.composition_score.toFixed(1)}/5.0</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tap for details hint */}
          {!showDetails && (
            <div className="mt-4 text-center text-sm text-gray-400">
              Tap to see details
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons (Fallback for non-swipe) */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 md:max-w-768 md:mx-auto">
        <div className="flex gap-4">
          <button
            onClick={handleReject}
            disabled={isProcessing}
            className="flex-1 btn btn-danger flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            Reject
          </button>
          <button
            onClick={handleApprove}
            disabled={isProcessing}
            className="flex-1 btn btn-primary flex items-center justify-center gap-2"
            style={{ backgroundColor: '#10b981' }}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Approve
          </button>
        </div>
      </div>
    </div>
  );
};

export default ApprovalQueue;
