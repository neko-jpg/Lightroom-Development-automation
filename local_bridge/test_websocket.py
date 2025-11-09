# test_websocket.py
#
# Tests for WebSocket communication system

import pytest
import json
import time
from flask import Flask
from websocket_fallback import init_websocket_fallback, get_websocket_fallback


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def websocket_fallback(app):
    """Initialize WebSocket fallback server"""
    return init_websocket_fallback(app)


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


def test_websocket_fallback_initialization(websocket_fallback):
    """Test WebSocket fallback server initialization"""
    assert websocket_fallback is not None
    assert len(websocket_fallback.clients) == 0
    assert len(websocket_fallback.message_queues) == 0


def test_handshake(client):
    """Test WebSocket handshake"""
    response = client.post('/ws/handshake', 
                          json={
                              'client_type': 'lightroom',
                              'protocol_version': '1.0'
                          })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'client_id' in data
    assert data['protocol_version'] == '1.0'


def test_handshake_invalid_request(client):
    """Test handshake with invalid request"""
    response = client.post('/ws/handshake')
    assert response.status_code == 400


def test_poll_without_handshake(client):
    """Test polling without handshake"""
    response = client.get('/ws/poll?client_id=invalid')
    assert response.status_code == 404


def test_poll_with_valid_client(client, websocket_fallback):
    """Test polling with valid client"""
    # First handshake
    handshake_response = client.post('/ws/handshake',
                                     json={'client_type': 'test'})
    client_id = json.loads(handshake_response.data)['client_id']
    
    # Poll for messages
    response = client.get(f'/ws/poll?client_id={client_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'messages' in data
    # Should have welcome message
    assert len(data['messages']) > 0


def test_send_message(client):
    """Test sending message from client"""
    # Handshake
    handshake_response = client.post('/ws/handshake',
                                     json={'client_type': 'test'})
    client_id = json.loads(handshake_response.data)['client_id']
    
    # Send message
    response = client.post('/ws/send',
                          json={
                              'client_id': client_id,
                              'message': {
                                  'type': 'ping'
                              }
                          })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'response' in data


def test_ping_pong(client):
    """Test ping-pong mechanism"""
    # Handshake
    handshake_response = client.post('/ws/handshake',
                                     json={'client_type': 'test'})
    client_id = json.loads(handshake_response.data)['client_id']
    
    # Send ping
    response = client.post('/ws/send',
                          json={
                              'client_id': client_id,
                              'message': {'type': 'ping'}
                          })
    
    data = json.loads(response.data)
    assert data['response']['type'] == 'pong'


def test_register_client(client):
    """Test client registration"""
    # Handshake
    handshake_response = client.post('/ws/handshake',
                                     json={'client_type': 'test'})
    client_id = json.loads(handshake_response.data)['client_id']
    
    # Register
    response = client.post('/ws/send',
                          json={
                              'client_id': client_id,
                              'message': {
                                  'type': 'register',
                                  'client_type': 'lightroom',
                                  'client_name': 'Test Client'
                              }
                          })
    
    data = json.loads(response.data)
    assert data['response']['type'] == 'registration_confirmed'


def test_subscribe_channels(client):
    """Test channel subscription"""
    # Handshake
    handshake_response = client.post('/ws/handshake',
                                     json={'client_type': 'test'})
    client_id = json.loads(handshake_response.data)['client_id']
    
    # Subscribe
    response = client.post('/ws/send',
                          json={
                              'client_id': client_id,
                              'message': {
                                  'type': 'subscribe',
                                  'channels': ['jobs', 'system']
                              }
                          })
    
    data = json.loads(response.data)
    assert data['response']['type'] == 'subscription_confirmed'
    assert 'jobs' in data['response']['channels']


def test_broadcast(client, websocket_fallback):
    """Test message broadcasting"""
    # Create two clients
    client1_response = client.post('/ws/handshake',
                                   json={'client_type': 'test1'})
    client1_id = json.loads(client1_response.data)['client_id']
    
    client2_response = client.post('/ws/handshake',
                                   json={'client_type': 'test2'})
    client2_id = json.loads(client2_response.data)['client_id']
    
    # Clear welcome messages
    client.get(f'/ws/poll?client_id={client1_id}')
    client.get(f'/ws/poll?client_id={client2_id}')
    
    # Broadcast message
    test_message = {'type': 'test_broadcast', 'data': 'hello'}
    websocket_fallback.broadcast(test_message)
    
    # Both clients should receive the message
    response1 = client.get(f'/ws/poll?client_id={client1_id}')
    data1 = json.loads(response1.data)
    assert len(data1['messages']) > 0
    assert data1['messages'][0]['type'] == 'test_broadcast'
    
    response2 = client.get(f'/ws/poll?client_id={client2_id}')
    data2 = json.loads(response2.data)
    assert len(data2['messages']) > 0
    assert data2['messages'][0]['type'] == 'test_broadcast'


def test_channel_filtered_broadcast(client, websocket_fallback):
    """Test channel-filtered broadcasting"""
    # Create two clients
    client1_response = client.post('/ws/handshake',
                                   json={'client_type': 'test1'})
    client1_id = json.loads(client1_response.data)['client_id']
    
    client2_response = client.post('/ws/handshake',
                                   json={'client_type': 'test2'})
    client2_id = json.loads(client2_response.data)['client_id']
    
    # Client 1 subscribes to 'jobs' channel
    client.post('/ws/send',
               json={
                   'client_id': client1_id,
                   'message': {
                       'type': 'subscribe',
                       'channels': ['jobs']
                   }
               })
    
    # Clear messages
    client.get(f'/ws/poll?client_id={client1_id}')
    client.get(f'/ws/poll?client_id={client2_id}')
    
    # Broadcast to 'jobs' channel
    test_message = {'type': 'job_update', 'data': 'test'}
    websocket_fallback.broadcast(test_message, channel='jobs')
    
    # Only client 1 should receive
    response1 = client.get(f'/ws/poll?client_id={client1_id}')
    data1 = json.loads(response1.data)
    assert len(data1['messages']) > 0
    
    response2 = client.get(f'/ws/poll?client_id={client2_id}')
    data2 = json.loads(response2.data)
    assert len(data2['messages']) == 0


def test_send_to_client_type(client, websocket_fallback):
    """Test sending to specific client type"""
    # Create clients of different types
    lr_response = client.post('/ws/handshake',
                              json={'client_type': 'lightroom'})
    lr_id = json.loads(lr_response.data)['client_id']
    
    gui_response = client.post('/ws/handshake',
                               json={'client_type': 'gui'})
    gui_id = json.loads(gui_response.data)['client_id']
    
    # Clear messages
    client.get(f'/ws/poll?client_id={lr_id}')
    client.get(f'/ws/poll?client_id={gui_id}')
    
    # Send to lightroom clients only
    test_message = {'type': 'lightroom_specific', 'data': 'test'}
    websocket_fallback.send_to_client_type('lightroom', test_message)
    
    # Only lightroom client should receive
    lr_poll = client.get(f'/ws/poll?client_id={lr_id}')
    lr_data = json.loads(lr_poll.data)
    assert len(lr_data['messages']) > 0
    
    gui_poll = client.get(f'/ws/poll?client_id={gui_id}')
    gui_data = json.loads(gui_poll.data)
    assert len(gui_data['messages']) == 0


def test_disconnect(client, websocket_fallback):
    """Test client disconnection"""
    # Handshake
    handshake_response = client.post('/ws/handshake',
                                     json={'client_type': 'test'})
    client_id = json.loads(handshake_response.data)['client_id']
    
    # Verify client exists
    assert len(websocket_fallback.clients) == 1
    
    # Disconnect
    response = client.post('/ws/disconnect',
                          json={'client_id': client_id})
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    
    # Verify client removed
    assert len(websocket_fallback.clients) == 0


def test_get_clients(client, websocket_fallback):
    """Test getting connected clients list"""
    # Create some clients
    client.post('/ws/handshake', json={'client_type': 'test1'})
    client.post('/ws/handshake', json={'client_type': 'test2'})
    
    # Get clients list
    response = client.get('/ws/clients')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['count'] == 2
    assert len(data['clients']) == 2


def test_cleanup_stale_clients(client, websocket_fallback):
    """Test cleanup of stale clients"""
    # Create client
    handshake_response = client.post('/ws/handshake',
                                     json={'client_type': 'test'})
    client_id = json.loads(handshake_response.data)['client_id']
    
    # Manually set last_poll to old time
    import datetime
    websocket_fallback.clients[client_id]['last_poll'] = \
        datetime.datetime.now() - datetime.timedelta(minutes=10)
    
    # Cleanup with 5 minute timeout
    removed = websocket_fallback.cleanup_stale_clients(timeout_minutes=5)
    
    assert removed == 1
    assert len(websocket_fallback.clients) == 0


def test_message_queue_limit(websocket_fallback):
    """Test message queue size limit"""
    # Create client
    client_id = 'test_client'
    websocket_fallback.clients[client_id] = {
        'id': client_id,
        'client_type': 'test',
        'protocol_version': '1.0',
        'connected_at': time.time(),
        'last_poll': time.time(),
        'subscriptions': set()
    }
    
    from collections import deque
    websocket_fallback.message_queues[client_id] = deque(maxlen=100)
    
    # Queue more than max messages
    for i in range(150):
        websocket_fallback._queue_message(client_id, {'type': 'test', 'index': i})
    
    # Should only have max messages
    assert len(websocket_fallback.message_queues[client_id]) == 100
    # Should have the latest messages
    assert websocket_fallback.message_queues[client_id][-1]['index'] == 149


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
