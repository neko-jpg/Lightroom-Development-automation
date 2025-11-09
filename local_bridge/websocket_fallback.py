# websocket_fallback.py
#
# HTTP fallback endpoints for WebSocket communication
# Provides polling-based communication for clients that don't support WebSocket

import uuid
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque
from threading import Lock
from flask import Flask, request, jsonify

logger = logging.getLogger('junmai_autodev.websocket_fallback')


class WebSocketFallbackServer:
    """
    HTTP-based fallback for WebSocket communication
    
    Provides polling-based bidirectional communication for clients
    that cannot use native WebSocket (like Lightroom Lua SDK)
    
    Requirements: 4.5
    """
    
    def __init__(self, app: Flask, max_message_queue_size: int = 100):
        """
        Initialize fallback server
        
        Args:
            app: Flask application instance
            max_message_queue_size: Maximum messages to queue per client
        """
        self.app = app
        self.max_queue_size = max_message_queue_size
        self.clients: Dict[str, Dict] = {}
        self.message_queues: Dict[str, deque] = {}
        self.lock = Lock()
        
        # Register routes
        self._register_routes()
        
        logger.info("WebSocket fallback server initialized")
    
    def _register_routes(self):
        """Register HTTP fallback routes"""
        
        @self.app.route('/ws/handshake', methods=['POST'])
        def handshake():
            """
            Establish connection via HTTP handshake
            
            Request body:
            - client_type: Type of client (e.g., 'lightroom')
            - protocol_version: Protocol version
            
            Returns:
                JSON with client_id and connection info
            """
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': 'Invalid request'}), 400
            
            client_type = data.get('client_type', 'unknown')
            protocol_version = data.get('protocol_version', '1.0')
            
            # Generate client ID
            client_id = str(uuid.uuid4())
            
            with self.lock:
                self.clients[client_id] = {
                    'id': client_id,
                    'client_type': client_type,
                    'protocol_version': protocol_version,
                    'connected_at': datetime.now(),
                    'last_poll': datetime.now(),
                    'subscriptions': set()
                }
                self.message_queues[client_id] = deque(maxlen=self.max_queue_size)
            
            logger.info(f"Client connected via handshake: {client_id} ({client_type})")
            
            # Send welcome message
            self._queue_message(client_id, {
                'type': 'connection_established',
                'client_id': client_id,
                'server_time': datetime.now().isoformat()
            })
            
            return jsonify({
                'success': True,
                'client_id': client_id,
                'protocol_version': protocol_version,
                'server_time': datetime.now().isoformat()
            }), 200
        
        @self.app.route('/ws/poll', methods=['GET'])
        def poll():
            """
            Poll for new messages
            
            Query parameters:
            - client_id: Client identifier
            
            Returns:
                JSON with queued messages
            """
            client_id = request.args.get('client_id')
            
            if not client_id:
                return jsonify({'success': False, 'error': 'client_id required'}), 400
            
            with self.lock:
                if client_id not in self.clients:
                    return jsonify({'success': False, 'error': 'Invalid client_id'}), 404
                
                # Update last poll time
                self.clients[client_id]['last_poll'] = datetime.now()
                
                # Get queued messages
                messages = []
                if client_id in self.message_queues:
                    while self.message_queues[client_id]:
                        messages.append(self.message_queues[client_id].popleft())
            
            return jsonify({
                'success': True,
                'messages': messages,
                'timestamp': datetime.now().isoformat()
            }), 200
        
        @self.app.route('/ws/send', methods=['POST'])
        def send():
            """
            Send message from client to server
            
            Request body:
            - client_id: Client identifier
            - message: Message object
            
            Returns:
                JSON with success status
            """
            data = request.get_json()
            
            if not data or 'client_id' not in data or 'message' not in data:
                return jsonify({'success': False, 'error': 'Invalid request'}), 400
            
            client_id = data['client_id']
            message = data['message']
            
            with self.lock:
                if client_id not in self.clients:
                    return jsonify({'success': False, 'error': 'Invalid client_id'}), 404
            
            # Handle message
            response = self._handle_client_message(client_id, message)
            
            return jsonify({
                'success': True,
                'response': response,
                'timestamp': datetime.now().isoformat()
            }), 200
        
        @self.app.route('/ws/disconnect', methods=['POST'])
        def disconnect():
            """
            Disconnect client
            
            Request body:
            - client_id: Client identifier
            
            Returns:
                JSON with success status
            """
            data = request.get_json()
            
            if not data or 'client_id' not in data:
                return jsonify({'success': False, 'error': 'Invalid request'}), 400
            
            client_id = data['client_id']
            
            with self.lock:
                if client_id in self.clients:
                    del self.clients[client_id]
                if client_id in self.message_queues:
                    del self.message_queues[client_id]
            
            logger.info(f"Client disconnected: {client_id}")
            
            return jsonify({
                'success': True,
                'message': 'Disconnected successfully'
            }), 200
        
        @self.app.route('/ws/clients', methods=['GET'])
        def get_clients():
            """
            Get list of connected clients
            
            Returns:
                JSON with client list
            """
            with self.lock:
                clients_list = [
                    {
                        'id': info['id'],
                        'client_type': info['client_type'],
                        'connected_at': info['connected_at'].isoformat(),
                        'last_poll': info['last_poll'].isoformat(),
                        'subscriptions': list(info['subscriptions'])
                    }
                    for info in self.clients.values()
                ]
            
            return jsonify({
                'success': True,
                'clients': clients_list,
                'count': len(clients_list)
            }), 200
    
    def _handle_client_message(self, client_id: str, message: Dict) -> Optional[Dict]:
        """
        Handle message from client
        
        Args:
            client_id: Client identifier
            message: Message dictionary
            
        Returns:
            Optional response dictionary
        """
        msg_type = message.get('type')
        
        if not msg_type:
            return {'error': 'Message type required'}
        
        logger.debug(f"Received message from {client_id}: {msg_type}")
        
        # Handle built-in message types
        if msg_type == 'ping':
            return {'type': 'pong', 'timestamp': datetime.now().isoformat()}
        
        elif msg_type == 'register':
            with self.lock:
                if client_id in self.clients:
                    self.clients[client_id]['client_type'] = message.get('client_type', 'unknown')
                    self.clients[client_id]['client_name'] = message.get('client_name', 'unnamed')
            
            return {
                'type': 'registration_confirmed',
                'client_type': message.get('client_type'),
                'client_name': message.get('client_name')
            }
        
        elif msg_type == 'subscribe':
            channels = message.get('channels', [])
            with self.lock:
                if client_id in self.clients:
                    self.clients[client_id]['subscriptions'].update(channels)
            
            return {
                'type': 'subscription_confirmed',
                'channels': channels
            }
        
        elif msg_type == 'unsubscribe':
            channels = message.get('channels', [])
            with self.lock:
                if client_id in self.clients:
                    self.clients[client_id]['subscriptions'].difference_update(channels)
            
            return {
                'type': 'unsubscription_confirmed',
                'channels': channels
            }
        
        # Delegate to external handlers if registered
        # (This will be extended by the main application)
        return None
    
    def _queue_message(self, client_id: str, message: Dict):
        """
        Queue message for client
        
        Args:
            client_id: Client identifier
            message: Message to queue
        """
        with self.lock:
            if client_id in self.message_queues:
                self.message_queues[client_id].append(message)
                logger.debug(f"Queued message for {client_id}: {message.get('type')}")
    
    def broadcast(self, message: Dict, channel: Optional[str] = None):
        """
        Broadcast message to all clients or specific channel
        
        Args:
            message: Message to broadcast
            channel: Optional channel filter
        """
        with self.lock:
            for client_id, client_info in self.clients.items():
                # Filter by channel if specified
                if channel and channel not in client_info['subscriptions']:
                    continue
                
                self._queue_message(client_id, message)
        
        logger.debug(f"Broadcast message: {message.get('type')} (channel: {channel})")
    
    def send_to_client(self, client_id: str, message: Dict):
        """
        Send message to specific client
        
        Args:
            client_id: Client identifier
            message: Message to send
        """
        self._queue_message(client_id, message)
    
    def send_to_client_type(self, client_type: str, message: Dict):
        """
        Send message to all clients of specific type
        
        Args:
            client_type: Type of client
            message: Message to send
        """
        with self.lock:
            for client_id, client_info in self.clients.items():
                if client_info['client_type'] == client_type:
                    self._queue_message(client_id, message)
    
    def get_connected_clients(self) -> List[Dict]:
        """
        Get list of connected clients
        
        Returns:
            List of client information dictionaries
        """
        with self.lock:
            return [
                {
                    'id': info['id'],
                    'client_type': info['client_type'],
                    'connected_at': info['connected_at'].isoformat(),
                    'last_poll': info['last_poll'].isoformat(),
                    'subscriptions': list(info['subscriptions'])
                }
                for info in self.clients.values()
            ]
    
    def cleanup_stale_clients(self, timeout_minutes: int = 5):
        """
        Remove clients that haven't polled recently
        
        Args:
            timeout_minutes: Minutes of inactivity before cleanup
        """
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        
        with self.lock:
            stale_clients = [
                client_id for client_id, info in self.clients.items()
                if info['last_poll'] < cutoff_time
            ]
            
            for client_id in stale_clients:
                logger.info(f"Removing stale client: {client_id}")
                del self.clients[client_id]
                if client_id in self.message_queues:
                    del self.message_queues[client_id]
        
        return len(stale_clients)


# Global fallback server instance
_fallback_server: Optional[WebSocketFallbackServer] = None


def init_websocket_fallback(app: Flask) -> WebSocketFallbackServer:
    """
    Initialize global WebSocket fallback server
    
    Args:
        app: Flask application instance
        
    Returns:
        WebSocketFallbackServer instance
    """
    global _fallback_server
    _fallback_server = WebSocketFallbackServer(app)
    return _fallback_server


def get_websocket_fallback() -> Optional[WebSocketFallbackServer]:
    """
    Get global WebSocket fallback server instance
    
    Returns:
        WebSocketFallbackServer instance or None if not initialized
    """
    return _fallback_server
