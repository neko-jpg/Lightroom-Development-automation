"""
Test WebSocket Real-time Updates
WebSocketリアルタイム更新のテスト

Tests for WebSocket server endpoints, event broadcasting, and client management.

Requirements: 4.5, 7.2
"""

import pytest
import json
import time
from datetime import datetime
from flask import Flask
from websocket_server import init_websocket_server, get_websocket_server, EventType
import websocket_events


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def ws_server(app):
    """Initialize WebSocket server"""
    server = init_websocket_server(app)
    return server


def test_websocket_server_initialization(ws_server):
    """Test WebSocket server initialization"""
    assert ws_server is not None
    assert ws_server.get_client_count() == 0


def test_event_type_constants():
    """Test EventType constants are defined"""
    assert hasattr(EventType, 'JOB_CREATED')
    assert hasattr(EventType, 'JOB_STARTED')
    assert hasattr(EventType, 'JOB_PROGRESS')
    assert hasattr(EventType, 'JOB_COMPLETED')
    assert hasattr(EventType, 'JOB_FAILED')
    
    assert hasattr(EventType, 'PHOTO_IMPORTED')
    assert hasattr(EventType, 'PHOTO_ANALYZED')
    assert hasattr(EventType, 'PHOTO_SELECTED')
    assert hasattr(EventType, 'PHOTO_APPROVED')
    assert hasattr(EventType, 'PHOTO_REJECTED')
    
    assert hasattr(EventType, 'SESSION_CREATED')
    assert hasattr(EventType, 'SESSION_UPDATED')
    assert hasattr(EventType, 'SESSION_COMPLETED')
    
    assert hasattr(EventType, 'SYSTEM_STATUS')
    assert hasattr(EventType, 'RESOURCE_WARNING')
    assert hasattr(EventType, 'ERROR_OCCURRED')
    
    assert hasattr(EventType, 'QUEUE_STATUS')
    assert hasattr(EventType, 'PRIORITY_CHANGED')


def test_broadcast_job_created(ws_server):
    """Test broadcasting job created event"""
    job_id = "test_job_123"
    photo_id = 456
    priority = 2
    
    # This should not raise an error even with no clients
    websocket_events.broadcast_job_created(job_id, photo_id, priority)


def test_broadcast_job_progress(ws_server):
    """Test broadcasting job progress event"""
    job_id = "test_job_123"
    stage = "analyzing"
    progress = 45.5
    message = "Analyzing image quality"
    
    websocket_events.broadcast_job_progress(job_id, stage, progress, message)


def test_broadcast_job_completed(ws_server):
    """Test broadcasting job completed event"""
    job_id = "test_job_123"
    photo_id = 456
    result = {
        'status': 'success',
        'processing_time': 2.3,
        'preset_applied': 'WhiteLayer_v4'
    }
    
    websocket_events.broadcast_job_completed(job_id, photo_id, result)


def test_broadcast_job_failed(ws_server):
    """Test broadcasting job failed event"""
    job_id = "test_job_123"
    photo_id = 456
    error_message = "Failed to apply preset"
    error_details = {
        'error_code': 'PRESET_NOT_FOUND',
        'preset_name': 'NonExistent_v1'
    }
    
    websocket_events.broadcast_job_failed(job_id, photo_id, error_message, error_details)


def test_broadcast_photo_imported(ws_server):
    """Test broadcasting photo imported event"""
    photo_id = 789
    session_id = 12
    file_name = "IMG_1234.CR3"
    file_path = "/path/to/IMG_1234.CR3"
    
    websocket_events.broadcast_photo_imported(photo_id, session_id, file_name, file_path)


def test_broadcast_photo_analyzed(ws_server):
    """Test broadcasting photo analyzed event"""
    photo_id = 789
    ai_score = 4.2
    analysis_results = {
        'focus_score': 4.5,
        'exposure_score': 4.0,
        'composition_score': 4.1,
        'faces_detected': 2
    }
    
    websocket_events.broadcast_photo_analyzed(photo_id, ai_score, analysis_results)


def test_broadcast_photo_approved(ws_server):
    """Test broadcasting photo approved event"""
    photo_id = 789
    session_id = 12
    
    websocket_events.broadcast_photo_approved(photo_id, session_id)


def test_broadcast_photo_rejected(ws_server):
    """Test broadcasting photo rejected event"""
    photo_id = 789
    session_id = 12
    reason = "Poor focus quality"
    
    websocket_events.broadcast_photo_rejected(photo_id, session_id, reason)


def test_broadcast_session_created(ws_server):
    """Test broadcasting session created event"""
    session_id = 12
    session_name = "Wedding_2025-11-08"
    import_folder = "/path/to/wedding/photos"
    
    websocket_events.broadcast_session_created(session_id, session_name, import_folder)


def test_broadcast_session_updated(ws_server):
    """Test broadcasting session updated event"""
    session_id = 12
    total_photos = 100
    processed_photos = 45
    status = "processing"
    
    websocket_events.broadcast_session_updated(session_id, total_photos, processed_photos, status)


def test_broadcast_session_completed(ws_server):
    """Test broadcasting session completed event"""
    session_id = 12
    session_name = "Wedding_2025-11-08"
    total_photos = 100
    approved_photos = 85
    
    websocket_events.broadcast_session_completed(session_id, session_name, total_photos, approved_photos)


def test_broadcast_system_status(ws_server):
    """Test broadcasting system status event"""
    status = "running"
    details = {
        'cpu_percent': 45.2,
        'memory_percent': 62.1,
        'active_jobs': 3
    }
    
    websocket_events.broadcast_system_status(status, details)


def test_broadcast_resource_warning(ws_server):
    """Test broadcasting resource warning event"""
    resource_type = "gpu"
    current_value = 78.5
    threshold = 75.0
    message = "GPU temperature exceeds threshold"
    
    websocket_events.broadcast_resource_warning(resource_type, current_value, threshold, message)


def test_broadcast_error_occurred(ws_server):
    """Test broadcasting error occurred event"""
    error_type = "PROCESSING_ERROR"
    error_message = "Failed to process photo"
    error_details = {
        'stage': 'preset_application',
        'retry_count': 2
    }
    job_id = "test_job_123"
    photo_id = 456
    
    websocket_events.broadcast_error_occurred(
        error_type, error_message, error_details, job_id, photo_id
    )


def test_broadcast_queue_status(ws_server):
    """Test broadcasting queue status event"""
    pending_count = 15
    processing_count = 3
    completed_count = 82
    failed_count = 2
    
    websocket_events.broadcast_queue_status(
        pending_count, processing_count, completed_count, failed_count
    )


def test_broadcast_priority_changed(ws_server):
    """Test broadcasting priority changed event"""
    job_id = "test_job_123"
    old_priority = 2
    new_priority = 1
    reason = "User requested high priority"
    
    websocket_events.broadcast_priority_changed(job_id, old_priority, new_priority, reason)


def test_broadcast_approval_queue_updated(ws_server):
    """Test broadcasting approval queue updated event"""
    queue_count = 12
    session_id = 5
    
    websocket_events.broadcast_approval_queue_updated(queue_count, session_id)


def test_broadcast_export_started(ws_server):
    """Test broadcasting export started event"""
    photo_id = 789
    preset_name = "SNS_2048"
    destination = "/path/to/export/folder"
    
    websocket_events.broadcast_export_started(photo_id, preset_name, destination)


def test_broadcast_export_completed(ws_server):
    """Test broadcasting export completed event"""
    photo_id = 789
    preset_name = "SNS_2048"
    output_path = "/path/to/export/IMG_1234.jpg"
    file_size = 2048576
    
    websocket_events.broadcast_export_completed(photo_id, preset_name, output_path, file_size)


def test_broadcast_export_failed(ws_server):
    """Test broadcasting export failed event"""
    photo_id = 789
    preset_name = "SNS_2048"
    error_message = "Disk space insufficient"
    
    websocket_events.broadcast_export_failed(photo_id, preset_name, error_message)


def test_get_connected_clients(ws_server):
    """Test getting connected clients list"""
    clients = ws_server.get_connected_clients()
    assert isinstance(clients, list)
    assert len(clients) == 0  # No clients connected in test


def test_get_client_count(ws_server):
    """Test getting client count"""
    count = ws_server.get_client_count()
    assert count == 0  # No clients connected in test


def test_broadcast_with_channel(ws_server):
    """Test broadcasting with specific channel"""
    message = {
        'type': 'test_event',
        'data': 'test_data'
    }
    
    # Should not raise error even with no clients
    ws_server.broadcast(message, channel='test_channel')


def test_send_to_client_type(ws_server):
    """Test sending to specific client type"""
    message = {
        'type': 'test_event',
        'data': 'test_data'
    }
    
    # Should not raise error even with no clients
    ws_server.send_to_client_type('gui', message)


def test_register_message_handler(ws_server):
    """Test registering custom message handler"""
    handler_called = []
    
    def custom_handler(ws, message):
        handler_called.append(True)
        return {'type': 'response', 'status': 'ok'}
    
    ws_server.register_handler('custom_message', custom_handler)
    
    # Verify handler is registered
    assert 'custom_message' in ws_server.message_handlers


def test_event_message_structure():
    """Test that event messages have correct structure"""
    # Test job event structure
    job_id = "test_123"
    photo_id = 456
    priority = 2
    
    # We can't easily test the actual broadcast without a real WebSocket connection,
    # but we can verify the function doesn't raise errors
    websocket_events.broadcast_job_created(job_id, photo_id, priority)


def test_multiple_event_broadcasts(ws_server):
    """Test broadcasting multiple events in sequence"""
    # Simulate a complete workflow
    session_id = 1
    photo_id = 100
    job_id = "job_100"
    
    # Session created
    websocket_events.broadcast_session_created(session_id, "Test_Session", "/test/path")
    
    # Photo imported
    websocket_events.broadcast_photo_imported(photo_id, session_id, "test.jpg", "/test/test.jpg")
    
    # Photo analyzed
    websocket_events.broadcast_photo_analyzed(photo_id, 4.5, {'focus_score': 4.5})
    
    # Job created
    websocket_events.broadcast_job_created(job_id, photo_id, 2)
    
    # Job started
    websocket_events.broadcast_job_started(job_id, photo_id)
    
    # Job progress
    websocket_events.broadcast_job_progress(job_id, "processing", 50.0, "Halfway done")
    
    # Job completed
    websocket_events.broadcast_job_completed(job_id, photo_id, {'status': 'success'})
    
    # Photo approved
    websocket_events.broadcast_photo_approved(photo_id, session_id)
    
    # Session updated
    websocket_events.broadcast_session_updated(session_id, 100, 50, "processing")
    
    # All events should broadcast without errors


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
