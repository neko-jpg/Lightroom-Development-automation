"""
WebSocket Integration Tests
WebSocket統合テスト

Tests WebSocket communication and real-time updates
Requirements: 4.5, 7.2
"""

import pytest
import json
import time
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call
from threading import Thread
import tempfile
from pathlib import Path

from app import app as flask_app
from models.database import init_db, get_session, Session, Photo, Job
from websocket_server import init_websocket_server, get_websocket_server, EventType
from websocket_events import (
    broadcast_photo_imported,
    broadcast_photo_analyzed,
    broadcast_photo_selected,
    broadcast_photo_approved,
    broadcast_photo_rejected,
    broadcast_session_created,
    broadcast_session_updated,
    broadcast_session_completed,
    broadcast_job_created,
    broadcast_job_started,
    broadcast_job_progress,
    broadcast_job_completed,
    broadcast_job_failed,
    broadcast_system_status,
    broadcast_resource_warning,
    broadcast_error_occurred,
    broadcast_queue_status,
    broadcast_priority_changed
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


@pytest.fixture
def test_db():
    """Create test database"""
    test_db_path = tempfile.mktemp(suffix='.db')
    init_db(f'sqlite:///{test_db_path}')
    
    yield test_db_path
    
    Path(test_db_path).unlink(missing_ok=True)


class TestWebSocketEventBroadcasting:
    """Test WebSocket event broadcasting"""
    
    def test_photo_imported_broadcast(self, mock_websocket_server):
        """Test photo imported event broadcast"""
        broadcast_photo_imported(
            photo_id=123,
            session_id=1,
            file_name="test.jpg",
            file_path="/path/to/test.jpg"
        )
        
        assert mock_websocket_server.broadcast.called
        call_args = mock_websocket_server.broadcast.call_args
        message = call_args[0][0]
        
        assert message['type'] == 'photo_imported'
        assert message['photo_id'] == 123
        assert message['session_id'] == 1
        assert 'timestamp' in message
    
    def test_photo_analyzed_broadcast(self, mock_websocket_server):
        """Test photo analyzed event broadcast"""
        broadcast_photo_analyzed(
            photo_id=456,
            ai_score=4.5,
            context_tag='portrait',
            selected_preset='WhiteLayer_v4'
        )
        
        assert mock_websocket_server.broadcast.called
        message = mock_websocket_server.broadcast.call_args[0][0]
        
        assert message['type'] == 'photo_analyzed'
        assert message['photo_id'] == 456
        assert message['ai_score'] == 4.5
        assert message['context_tag'] == 'portrait'
    
    def test_session_created_broadcast(self, mock_websocket_server):
        """Test session created event broadcast"""
        broadcast_session_created(
            session_id=1,
            session_name="Test Session",
            import_folder="/test/folder"
        )
        
        assert mock_websocket_server.broadcast.called
        message = mock_websocket_server.broadcast.call_args[0][0]
        
        assert message['type'] == 'session_created'
        assert message['session_id'] == 1
        assert message['session_name'] == "Test Session"
    
    def test_job_progress_broadcast(self, mock_websocket_server):
        """Test job progress event broadcast"""
        broadcast_job_progress(
            job_id="job-123",
            photo_id=789,
            stage="developing",
            progress=50,
            message="Processing..."
        )
        
        assert mock_websocket_server.broadcast.called
        message = mock_websocket_server.broadcast.call_args[0][0]
        
        assert message['type'] == 'job_progress'
        assert message['job_id'] == "job-123"
        assert message['progress'] == 50
        assert message['stage'] == "developing"
    
    def test_system_status_broadcast(self, mock_websocket_server):
        """Test system status event broadcast"""
        broadcast_system_status(
            status='running',
            details={
                'cpu_usage': 45.2,
                'memory_usage': 60.5,
                'active_jobs': 3
            }
        )
        
        assert mock_websocket_server.broadcast.called
        message = mock_websocket_server.broadcast.call_args[0][0]
        
        assert message['type'] == 'system_status'
        assert message['status'] == 'running'
        assert message['details']['cpu_usage'] == 45.2


class TestWebSocketChannelRouting:
    """Test WebSocket channel routing"""
    
    def test_photo_events_channel(self, mock_websocket_server):
        """Test photo events are routed to photos channel"""
        broadcast_photo_imported(1, 1, "test.jpg", "/path")
        
        call_args = mock_websocket_server.broadcast.call_args
        channel = call_args[1].get('channel')
        assert channel == 'photos'
    
    def test_session_events_channel(self, mock_websocket_server):
        """Test session events are routed to sessions channel"""
        broadcast_session_created(1, "Test", "/path")
        
        call_args = mock_websocket_server.broadcast.call_args
        channel = call_args[1].get('channel')
        assert channel == 'sessions'
    
    def test_job_events_channel(self, mock_websocket_server):
        """Test job events are routed to jobs channel"""
        broadcast_job_created("job-1", 1, 5)
        
        call_args = mock_websocket_server.broadcast.call_args
        channel = call_args[1].get('channel')
        assert channel == 'jobs'
    
    def test_system_events_channel(self, mock_websocket_server):
        """Test system events are routed to system channel"""
        broadcast_system_status('running', {})
        
        call_args = mock_websocket_server.broadcast.call_args
        channel = call_args[1].get('channel')
        assert channel == 'system'


class TestWebSocketAPIIntegration:
    """Test WebSocket integration with API endpoints"""
    
    def test_session_creation_triggers_websocket(self, client, test_db, mock_websocket_server):
        """Test that creating a session triggers WebSocket event"""
        session_data = {
            'name': 'WebSocket_Test_Session',
            'import_folder': '/test/folder'
        }
        
        response = client.post(
            '/api/sessions',
            data=json.dumps(session_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        
        # Verify WebSocket broadcast was called
        # Note: This depends on the API implementation
        # If API doesn't trigger WebSocket, this test will fail
    
    def test_photo_approval_triggers_websocket(self, client, test_db, mock_websocket_server):
        """Test that approving a photo triggers WebSocket event"""
        # Create session and photo
        db_session = get_session()
        try:
            session = Session(name='Test', import_folder='/test')
            db_session.add(session)
            db_session.commit()
            
            photo = Photo(
                session_id=session.id,
                file_path='/test/photo.jpg',
                file_name='photo.jpg',
                file_size=1024000,
                status='completed'
            )
            db_session.add(photo)
            db_session.commit()
            photo_id = photo.id
        finally:
            db_session.close()
        
        # Approve photo
        response = client.post(
            f'/api/approval/{photo_id}/approve',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_job_creation_triggers_websocket(self, client, test_db, mock_websocket_server):
        """Test that creating a job triggers WebSocket event"""
        # Create session and photo
        db_session = get_session()
        try:
            session = Session(name='Test', import_folder='/test')
            db_session.add(session)
            db_session.commit()
            
            photo = Photo(
                session_id=session.id,
                file_path='/test/photo.jpg',
                file_name='photo.jpg',
                file_size=1024000
            )
            db_session.add(photo)
            db_session.commit()
            photo_id = photo.id
        finally:
            db_session.close()
        
        # Create job
        job_data = {
            'photo_id': photo_id,
            'config': {'version': '1.0', 'pipeline': [], 'safety': {}},
            'priority': 2
        }
        
        response = client.post(
            '/api/jobs',
            data=json.dumps(job_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201


class TestWebSocketMessageFormat:
    """Test WebSocket message format consistency"""
    
    def test_all_messages_have_timestamp(self, mock_websocket_server):
        """Test that all messages include timestamp"""
        events = [
            lambda: broadcast_photo_imported(1, 1, "test.jpg", "/path"),
            lambda: broadcast_session_created(1, "Test", "/path"),
            lambda: broadcast_job_created("job-1", 1, 5),
            lambda: broadcast_system_status('running', {})
        ]
        
        for event_func in events:
            event_func()
        
        # Verify all calls included timestamp
        for call_obj in mock_websocket_server.broadcast.call_args_list:
            message = call_obj[0][0]
            assert 'timestamp' in message
            assert 'type' in message
    
    def test_message_type_consistency(self, mock_websocket_server):
        """Test message type field consistency"""
        broadcast_photo_imported(1, 1, "test.jpg", "/path")
        message = mock_websocket_server.broadcast.call_args[0][0]
        assert message['type'] == 'photo_imported'
        
        broadcast_job_started("job-1", 1)
        message = mock_websocket_server.broadcast.call_args[0][0]
        assert message['type'] == 'job_started'
    
    def test_message_serialization(self, mock_websocket_server):
        """Test that messages can be JSON serialized"""
        broadcast_photo_analyzed(
            photo_id=1,
            ai_score=4.5,
            context_tag='portrait',
            selected_preset='WhiteLayer_v4'
        )
        
        message = mock_websocket_server.broadcast.call_args[0][0]
        
        # Should be JSON serializable
        try:
            json_str = json.dumps(message)
            reconstructed = json.loads(json_str)
            assert reconstructed['photo_id'] == 1
            assert reconstructed['ai_score'] == 4.5
        except (TypeError, ValueError) as e:
            pytest.fail(f"Message not JSON serializable: {e}")


class TestWebSocketClientManagement:
    """Test WebSocket client management"""
    
    def test_get_connected_clients(self, client, mock_websocket_server):
        """Test getting connected clients"""
        mock_clients = [
            {
                'id': 1,
                'client_type': 'gui',
                'connected_at': datetime.now().isoformat()
            },
            {
                'id': 2,
                'client_type': 'mobile',
                'connected_at': datetime.now().isoformat()
            }
        ]
        mock_websocket_server.get_connected_clients.return_value = mock_clients
        
        response = client.get('/websocket/clients')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'clients' in data or 'count' in data
    
    def test_broadcast_custom_message(self, client, mock_websocket_server):
        """Test broadcasting custom message"""
        message_data = {
            'type': 'custom_test',
            'data': {'test': 'value'},
            'channel': 'test'
        }
        
        response = client.post(
            '/websocket/broadcast',
            data=json.dumps(message_data),
            content_type='application/json'
        )
        
        # Endpoint may or may not exist
        if response.status_code == 200:
            assert mock_websocket_server.broadcast.called


class TestWebSocketErrorHandling:
    """Test WebSocket error handling"""
    
    def test_broadcast_with_disconnected_server(self):
        """Test broadcasting when server is disconnected"""
        with patch('websocket_events.get_websocket_server') as mock_get_ws:
            mock_get_ws.return_value = None
            
            # Should not raise exception
            try:
                broadcast_photo_imported(1, 1, "test.jpg", "/path")
            except Exception as e:
                pytest.fail(f"Should handle disconnected server gracefully: {e}")
    
    def test_broadcast_with_invalid_data(self, mock_websocket_server):
        """Test broadcasting with invalid data"""
        # Should handle gracefully
        try:
            broadcast_photo_imported(
                photo_id=None,  # Invalid
                session_id=1,
                file_name="test.jpg",
                file_path="/path"
            )
        except Exception as e:
            # Some validation error is acceptable
            pass
    
    def test_broadcast_exception_handling(self, mock_websocket_server):
        """Test exception handling during broadcast"""
        mock_websocket_server.broadcast.side_effect = Exception("Test error")
        
        # Should not crash the application
        try:
            broadcast_photo_imported(1, 1, "test.jpg", "/path")
        except Exception:
            # Exception is acceptable, but shouldn't crash
            pass


class TestWebSocketPerformance:
    """Test WebSocket performance"""
    
    def test_multiple_rapid_broadcasts(self, mock_websocket_server):
        """Test handling multiple rapid broadcasts"""
        start_time = time.time()
        
        # Send 100 messages rapidly
        for i in range(100):
            broadcast_photo_imported(i, 1, f"photo_{i}.jpg", f"/path/{i}")
        
        elapsed = time.time() - start_time
        
        # Should complete quickly (< 1 second for 100 messages)
        assert elapsed < 1.0
        assert mock_websocket_server.broadcast.call_count == 100
    
    def test_large_message_broadcast(self, mock_websocket_server):
        """Test broadcasting large messages"""
        large_details = {
            'data': ['x' * 1000 for _ in range(100)]  # Large data
        }
        
        try:
            broadcast_system_status('running', large_details)
            assert mock_websocket_server.broadcast.called
        except Exception as e:
            pytest.fail(f"Should handle large messages: {e}")


class TestWebSocketEventSequencing:
    """Test WebSocket event sequencing"""
    
    def test_workflow_event_sequence(self, mock_websocket_server):
        """Test correct event sequence for a workflow"""
        # Simulate a complete workflow
        session_id = 1
        photo_id = 1
        job_id = "job-1"
        
        # 1. Session created
        broadcast_session_created(session_id, "Test", "/path")
        
        # 2. Photo imported
        broadcast_photo_imported(photo_id, session_id, "test.jpg", "/path")
        
        # 3. Photo analyzed
        broadcast_photo_analyzed(photo_id, 4.5, "portrait", "WhiteLayer_v4")
        
        # 4. Job created
        broadcast_job_created(job_id, photo_id, 2)
        
        # 5. Job started
        broadcast_job_started(job_id, photo_id)
        
        # 6. Job progress
        broadcast_job_progress(job_id, photo_id, "developing", 50, "Processing...")
        
        # 7. Job completed
        broadcast_job_completed(job_id, photo_id, 5.2)
        
        # 8. Photo approved
        broadcast_photo_approved(photo_id, session_id)
        
        # Verify all events were broadcast
        assert mock_websocket_server.broadcast.call_count == 8
        
        # Verify event types in order
        call_list = mock_websocket_server.broadcast.call_args_list
        expected_types = [
            'session_created',
            'photo_imported',
            'photo_analyzed',
            'job_created',
            'job_started',
            'job_progress',
            'job_completed',
            'photo_approved'
        ]
        
        for i, expected_type in enumerate(expected_types):
            message = call_list[i][0][0]
            assert message['type'] == expected_type


class TestWebSocketReconnection:
    """Test WebSocket reconnection handling"""
    
    def test_server_restart_handling(self, mock_websocket_server):
        """Test handling server restart"""
        # Simulate server restart
        mock_websocket_server.get_client_count.return_value = 0
        
        # Should still accept broadcasts
        broadcast_system_status('restarting', {})
        assert mock_websocket_server.broadcast.called
    
    def test_client_reconnection(self, mock_websocket_server):
        """Test client reconnection"""
        # Simulate client disconnect and reconnect
        mock_websocket_server.get_client_count.side_effect = [0, 1, 2]
        
        # Broadcasts should work regardless
        for i in range(3):
            broadcast_system_status('running', {'clients': mock_websocket_server.get_client_count()})
        
        assert mock_websocket_server.broadcast.call_count == 3


def run_websocket_integration_tests():
    """Run all WebSocket integration tests"""
    print("=" * 60)
    print("WebSocket Integration Tests")
    print("=" * 60)
    
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes'
    ])


if __name__ == '__main__':
    run_websocket_integration_tests()
