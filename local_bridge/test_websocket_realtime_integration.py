"""
Test WebSocket Real-time Updates Integration
WebSocketリアルタイム更新統合テスト

This test verifies that WebSocket events are properly broadcasted
when API endpoints are called.

Requirements: 4.5, 7.2
"""

import pytest
import json
import time
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from simple_websocket import Server

# Import modules to test
from app import app as flask_app
from websocket_server import init_websocket_server, get_websocket_server
from websocket_events import (
    broadcast_photo_imported,
    broadcast_session_created,
    broadcast_job_created,
    broadcast_system_status
)


@pytest.fixture
def app():
    """Create Flask app for testing"""
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_websocket_server():
    """Create mock WebSocket server"""
    with patch('websocket_events.get_websocket_server') as mock_get_ws:
        mock_ws = Mock()
        mock_ws.broadcast = Mock()
        mock_ws.get_connected_clients = Mock(return_value=[])
        mock_ws.get_client_count = Mock(return_value=0)
        mock_get_ws.return_value = mock_ws
        yield mock_ws


class TestWebSocketEventBroadcasting:
    """Test WebSocket event broadcasting from API endpoints"""
    
    def test_photo_imported_event(self, mock_websocket_server):
        """Test that photo imported event is broadcasted"""
        # Broadcast photo imported event
        broadcast_photo_imported(
            photo_id=123,
            session_id=1,
            file_name="test.jpg",
            file_path="/path/to/test.jpg"
        )
        
        # Verify broadcast was called
        assert mock_websocket_server.broadcast.called
        
        # Get the broadcasted message
        call_args = mock_websocket_server.broadcast.call_args
        message = call_args[0][0]
        channel = call_args[1].get('channel')
        
        # Verify message structure
        assert message['type'] == 'photo_imported'
        assert message['photo_id'] == 123
        assert message['session_id'] == 1
        assert message['file_name'] == "test.jpg"
        assert message['file_path'] == "/path/to/test.jpg"
        assert 'timestamp' in message
        
        # Verify channel
        assert channel == 'photos'
    
    def test_session_created_event(self, mock_websocket_server):
        """Test that session created event is broadcasted"""
        # Broadcast session created event
        broadcast_session_created(
            session_id=1,
            session_name="Test Session",
            import_folder="/path/to/folder"
        )
        
        # Verify broadcast was called
        assert mock_websocket_server.broadcast.called
        
        # Get the broadcasted message
        call_args = mock_websocket_server.broadcast.call_args
        message = call_args[0][0]
        channel = call_args[1].get('channel')
        
        # Verify message structure
        assert message['type'] == 'session_created'
        assert message['session_id'] == 1
        assert message['session_name'] == "Test Session"
        assert message['import_folder'] == "/path/to/folder"
        assert 'timestamp' in message
        
        # Verify channel
        assert channel == 'sessions'
    
    def test_job_created_event(self, mock_websocket_server):
        """Test that job created event is broadcasted"""
        # Broadcast job created event
        broadcast_job_created(
            job_id="test-job-123",
            photo_id=456,
            priority=5
        )
        
        # Verify broadcast was called
        assert mock_websocket_server.broadcast.called
        
        # Get the broadcasted message
        call_args = mock_websocket_server.broadcast.call_args
        message = call_args[0][0]
        channel = call_args[1].get('channel')
        
        # Verify message structure
        assert message['type'] == 'job_created'
        assert message['job_id'] == "test-job-123"
        assert message['photo_id'] == 456
        assert message['priority'] == 5
        assert 'timestamp' in message
        
        # Verify channel
        assert channel == 'jobs'
    
    def test_system_status_event(self, mock_websocket_server):
        """Test that system status event is broadcasted"""
        # Broadcast system status event
        broadcast_system_status(
            status='running',
            details={'cpu_usage': 45.2, 'memory_usage': 60.5}
        )
        
        # Verify broadcast was called
        assert mock_websocket_server.broadcast.called
        
        # Get the broadcasted message
        call_args = mock_websocket_server.broadcast.call_args
        message = call_args[0][0]
        channel = call_args[1].get('channel')
        
        # Verify message structure
        assert message['type'] == 'system_status'
        assert message['status'] == 'running'
        assert message['details']['cpu_usage'] == 45.2
        assert message['details']['memory_usage'] == 60.5
        assert 'timestamp' in message
        
        # Verify channel
        assert channel == 'system'


class TestWebSocketManagementEndpoints:
    """Test WebSocket management API endpoints"""
    
    def test_get_websocket_clients(self, client, mock_websocket_server):
        """Test GET /websocket/clients endpoint"""
        # Mock connected clients
        mock_clients = [
            {
                'id': 1,
                'client_type': 'gui',
                'client_name': 'Desktop GUI',
                'connected_at': datetime.now().isoformat(),
                'last_ping': datetime.now().isoformat(),
                'subscriptions': ['jobs', 'photos']
            },
            {
                'id': 2,
                'client_type': 'mobile',
                'client_name': 'Mobile Web',
                'connected_at': datetime.now().isoformat(),
                'last_ping': datetime.now().isoformat(),
                'subscriptions': ['sessions']
            }
        ]
        mock_websocket_server.get_connected_clients.return_value = mock_clients
        
        # Make request
        response = client.get('/websocket/clients')
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 2
        assert len(data['clients']) == 2
        assert data['clients'][0]['client_type'] == 'gui'
        assert data['clients'][1]['client_type'] == 'mobile'
    
    def test_broadcast_custom_message(self, client, mock_websocket_server):
        """Test POST /websocket/broadcast endpoint"""
        # Prepare request data
        request_data = {
            'type': 'custom_event',
            'data': {
                'message': 'Test message',
                'value': 42
            },
            'channel': 'test'
        }
        
        # Make request
        response = client.post(
            '/websocket/broadcast',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify broadcast was called
        assert mock_websocket_server.broadcast.called
        call_args = mock_websocket_server.broadcast.call_args
        message = call_args[0][0]
        channel = call_args[1].get('channel')
        
        assert message['type'] == 'custom_event'
        assert message['message'] == 'Test message'
        assert message['value'] == 42
        assert channel == 'test'
    
    def test_get_websocket_stats(self, client, mock_websocket_server):
        """Test GET /websocket/stats endpoint"""
        # Mock connected clients with different types
        mock_clients = [
            {
                'id': 1,
                'client_type': 'gui',
                'subscriptions': ['jobs', 'photos']
            },
            {
                'id': 2,
                'client_type': 'gui',
                'subscriptions': ['sessions']
            },
            {
                'id': 3,
                'client_type': 'mobile',
                'subscriptions': ['jobs', 'sessions']
            }
        ]
        mock_websocket_server.get_connected_clients.return_value = mock_clients
        
        # Make request
        response = client.get('/websocket/stats')
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        stats = data['stats']
        assert stats['total_clients'] == 3
        assert stats['clients_by_type']['gui'] == 2
        assert stats['clients_by_type']['mobile'] == 1
        assert 'jobs' in stats['active_channels']
        assert 'photos' in stats['active_channels']
        assert 'sessions' in stats['active_channels']
        assert stats['channel_count'] == 3


class TestWebSocketServerIntegration:
    """Test WebSocket server integration"""
    
    def test_websocket_server_initialization(self):
        """Test that WebSocket server is properly initialized"""
        ws_server = get_websocket_server()
        assert ws_server is not None
    
    def test_event_type_definitions(self):
        """Test that all event types are properly defined"""
        from websocket_server import EventType
        
        # Job events
        assert hasattr(EventType, 'JOB_CREATED')
        assert hasattr(EventType, 'JOB_STARTED')
        assert hasattr(EventType, 'JOB_PROGRESS')
        assert hasattr(EventType, 'JOB_COMPLETED')
        assert hasattr(EventType, 'JOB_FAILED')
        
        # Photo events
        assert hasattr(EventType, 'PHOTO_IMPORTED')
        assert hasattr(EventType, 'PHOTO_ANALYZED')
        assert hasattr(EventType, 'PHOTO_SELECTED')
        assert hasattr(EventType, 'PHOTO_APPROVED')
        assert hasattr(EventType, 'PHOTO_REJECTED')
        
        # Session events
        assert hasattr(EventType, 'SESSION_CREATED')
        assert hasattr(EventType, 'SESSION_UPDATED')
        assert hasattr(EventType, 'SESSION_COMPLETED')
        
        # System events
        assert hasattr(EventType, 'SYSTEM_STATUS')
        assert hasattr(EventType, 'RESOURCE_WARNING')
        assert hasattr(EventType, 'ERROR_OCCURRED')
        
        # Queue events
        assert hasattr(EventType, 'QUEUE_STATUS')
        assert hasattr(EventType, 'PRIORITY_CHANGED')


class TestWebSocketMessageFormat:
    """Test WebSocket message format consistency"""
    
    def test_message_has_timestamp(self, mock_websocket_server):
        """Test that all messages include timestamp"""
        # Test various event types
        broadcast_photo_imported(1, 1, "test.jpg", "/path")
        broadcast_session_created(1, "Test", "/path")
        broadcast_job_created("job-1", 1, 5)
        
        # Verify all calls included timestamp
        for call in mock_websocket_server.broadcast.call_args_list:
            message = call[0][0]
            assert 'timestamp' in message
            assert 'type' in message
    
    def test_message_channel_routing(self, mock_websocket_server):
        """Test that messages are routed to correct channels"""
        # Test photo events go to 'photos' channel
        broadcast_photo_imported(1, 1, "test.jpg", "/path")
        assert mock_websocket_server.broadcast.call_args[1]['channel'] == 'photos'
        
        # Test session events go to 'sessions' channel
        broadcast_session_created(1, "Test", "/path")
        assert mock_websocket_server.broadcast.call_args[1]['channel'] == 'sessions'
        
        # Test job events go to 'jobs' channel
        broadcast_job_created("job-1", 1, 5)
        assert mock_websocket_server.broadcast.call_args[1]['channel'] == 'jobs'
        
        # Test system events go to 'system' channel
        broadcast_system_status('running', {})
        assert mock_websocket_server.broadcast.call_args[1]['channel'] == 'system'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
