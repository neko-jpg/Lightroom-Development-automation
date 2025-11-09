# websocket_server.py
#
# WebSocket server for real-time bidirectional communication
# between the Python bridge and Lightroom plugin

import json
import logging
import threading
from typing import Dict, Set, Optional, Callable
from datetime import datetime
from flask import Flask
from flask_sock import Sock
from simple_websocket import Server, ConnectionClosed

logger = logging.getLogger('junmai_autodev.websocket')


class WebSocketServer:
    """
    WebSocket server for real-time communication with Lightroom plugin
    
    Provides bidirectional communication for:
    - Real-time progress updates
    - Job status notifications
    - System status broadcasts
    - Connection management with automatic reconnection
    
    Requirements: 4.5
    """
    
    def __init__(self, app: Flask):
        """
        Initialize WebSocket server
        
        Args:
            app: Flask application instance
        """
        self.app = app
        self.sock = Sock(app)
        self.clients: Set[Server] = set()
        self.client_info: Dict[Server, Dict] = {}
        self.lock = threading.Lock()
        self.message_handlers: Dict[str, Callable] = {}
        
        # Register WebSocket route
        self.sock.route('/ws')(self._handle_connection)
        
        logger.info("WebSocket server initialized")
    
    def _handle_connection(self, ws: Server):
        """
        Handle new WebSocket connection
        
        Args:
            ws: WebSocket connection object
        """
        client_id = id(ws)
        
        with self.lock:
            self.clients.add(ws)
            self.client_info[ws] = {
                'id': client_id,
                'connected_at': datetime.now(),
                'client_type': 'unknown',
                'last_ping': datetime.now()
            }
        
        logger.info(f"New WebSocket client connected: {client_id}")
        
        # Send welcome message
        self._send_to_client(ws, {
            'type': 'connection_established',
            'client_id': client_id,
            'server_time': datetime.now().isoformat()
        })
        
        try:
            while True:
                # Receive message from client
                data = ws.receive()
                
                if data is None:
                    break
                
                # Parse and handle message
                try:
                    message = json.loads(data)
                    self._handle_message(ws, message)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from client {client_id}: {e}")
                    self._send_error(ws, "Invalid JSON format")
                except Exception as e:
                    logger.error(f"Error handling message from client {client_id}: {e}")
                    self._send_error(ws, str(e))
        
        except ConnectionClosed:
            logger.info(f"Client {client_id} connection closed")
        except Exception as e:
            logger.error(f"Error in WebSocket connection {client_id}: {e}")
        finally:
            # Clean up on disconnect
            with self.lock:
                self.clients.discard(ws)
                self.client_info.pop(ws, None)
            
            logger.info(f"Client {client_id} disconnected. Active clients: {len(self.clients)}")
    
    def _handle_message(self, ws: Server, message: Dict):
        """
        Handle incoming message from client
        
        Args:
            ws: WebSocket connection
            message: Parsed message dictionary
        """
        msg_type = message.get('type')
        
        if not msg_type:
            self._send_error(ws, "Message type is required")
            return
        
        client_id = self.client_info.get(ws, {}).get('id', 'unknown')
        logger.debug(f"Received message from client {client_id}: {msg_type}")
        
        # Handle built-in message types
        if msg_type == 'ping':
            self._handle_ping(ws, message)
        elif msg_type == 'register':
            self._handle_register(ws, message)
        elif msg_type == 'subscribe':
            self._handle_subscribe(ws, message)
        elif msg_type == 'unsubscribe':
            self._handle_unsubscribe(ws, message)
        else:
            # Delegate to registered handlers
            handler = self.message_handlers.get(msg_type)
            if handler:
                try:
                    response = handler(ws, message)
                    if response:
                        self._send_to_client(ws, response)
                except Exception as e:
                    logger.error(f"Error in message handler for {msg_type}: {e}")
                    self._send_error(ws, f"Handler error: {str(e)}")
            else:
                logger.warning(f"No handler registered for message type: {msg_type}")
                self._send_error(ws, f"Unknown message type: {msg_type}")
    
    def _handle_ping(self, ws: Server, message: Dict):
        """Handle ping message"""
        with self.lock:
            if ws in self.client_info:
                self.client_info[ws]['last_ping'] = datetime.now()
        
        self._send_to_client(ws, {
            'type': 'pong',
            'timestamp': datetime.now().isoformat()
        })
    
    def _handle_register(self, ws: Server, message: Dict):
        """Handle client registration"""
        client_type = message.get('client_type', 'unknown')
        client_name = message.get('client_name', 'unnamed')
        
        with self.lock:
            if ws in self.client_info:
                self.client_info[ws]['client_type'] = client_type
                self.client_info[ws]['client_name'] = client_name
        
        logger.info(f"Client registered: {client_name} ({client_type})")
        
        self._send_to_client(ws, {
            'type': 'registration_confirmed',
            'client_type': client_type,
            'client_name': client_name
        })
    
    def _handle_subscribe(self, ws: Server, message: Dict):
        """Handle subscription to event channels"""
        channels = message.get('channels', [])
        
        with self.lock:
            if ws in self.client_info:
                if 'subscriptions' not in self.client_info[ws]:
                    self.client_info[ws]['subscriptions'] = set()
                self.client_info[ws]['subscriptions'].update(channels)
        
        logger.info(f"Client subscribed to channels: {channels}")
        
        self._send_to_client(ws, {
            'type': 'subscription_confirmed',
            'channels': channels
        })
    
    def _handle_unsubscribe(self, ws: Server, message: Dict):
        """Handle unsubscription from event channels"""
        channels = message.get('channels', [])
        
        with self.lock:
            if ws in self.client_info and 'subscriptions' in self.client_info[ws]:
                self.client_info[ws]['subscriptions'].difference_update(channels)
        
        logger.info(f"Client unsubscribed from channels: {channels}")
        
        self._send_to_client(ws, {
            'type': 'unsubscription_confirmed',
            'channels': channels
        })
    
    def _send_to_client(self, ws: Server, message: Dict):
        """
        Send message to specific client
        
        Args:
            ws: WebSocket connection
            message: Message dictionary to send
        """
        try:
            ws.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to client: {e}")
    
    def _send_error(self, ws: Server, error_message: str):
        """
        Send error message to client
        
        Args:
            ws: WebSocket connection
            error_message: Error description
        """
        self._send_to_client(ws, {
            'type': 'error',
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        })
    
    def broadcast(self, message: Dict, channel: Optional[str] = None):
        """
        Broadcast message to all connected clients or specific channel
        
        Args:
            message: Message dictionary to broadcast
            channel: Optional channel name for filtered broadcast
        """
        with self.lock:
            clients_to_send = []
            
            for ws in self.clients:
                # If channel specified, only send to subscribed clients
                if channel:
                    subscriptions = self.client_info.get(ws, {}).get('subscriptions', set())
                    if channel not in subscriptions:
                        continue
                
                clients_to_send.append(ws)
        
        # Send outside of lock to avoid blocking
        for ws in clients_to_send:
            try:
                ws.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to client: {e}")
    
    def send_to_client_type(self, client_type: str, message: Dict):
        """
        Send message to all clients of specific type
        
        Args:
            client_type: Type of client (e.g., 'lightroom', 'gui', 'mobile')
            message: Message dictionary to send
        """
        with self.lock:
            clients_to_send = [
                ws for ws, info in self.client_info.items()
                if info.get('client_type') == client_type
            ]
        
        for ws in clients_to_send:
            try:
                ws.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send to client type {client_type}: {e}")
    
    def register_handler(self, message_type: str, handler: Callable):
        """
        Register custom message handler
        
        Args:
            message_type: Type of message to handle
            handler: Callable that takes (ws, message) and returns optional response
        """
        self.message_handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")
    
    def get_connected_clients(self) -> list:
        """
        Get list of connected clients with their info
        
        Returns:
            List of client information dictionaries
        """
        with self.lock:
            return [
                {
                    'id': info['id'],
                    'client_type': info.get('client_type', 'unknown'),
                    'client_name': info.get('client_name', 'unnamed'),
                    'connected_at': info['connected_at'].isoformat(),
                    'last_ping': info['last_ping'].isoformat(),
                    'subscriptions': list(info.get('subscriptions', set()))
                }
                for info in self.client_info.values()
            ]
    
    def get_client_count(self) -> int:
        """Get number of connected clients"""
        with self.lock:
            return len(self.clients)
    
    def disconnect_client(self, client_id: int):
        """
        Disconnect specific client
        
        Args:
            client_id: Client ID to disconnect
        """
        with self.lock:
            for ws, info in self.client_info.items():
                if info['id'] == client_id:
                    try:
                        ws.close()
                        logger.info(f"Disconnected client {client_id}")
                    except Exception as e:
                        logger.error(f"Error disconnecting client {client_id}: {e}")
                    break


# Event types for standardized communication
class EventType:
    """Standard event types for WebSocket communication"""
    
    # Job events
    JOB_CREATED = 'job_created'
    JOB_STARTED = 'job_started'
    JOB_PROGRESS = 'job_progress'
    JOB_COMPLETED = 'job_completed'
    JOB_FAILED = 'job_failed'
    
    # Photo events
    PHOTO_IMPORTED = 'photo_imported'
    PHOTO_ANALYZED = 'photo_analyzed'
    PHOTO_SELECTED = 'photo_selected'
    PHOTO_APPROVED = 'photo_approved'
    PHOTO_REJECTED = 'photo_rejected'
    
    # Session events
    SESSION_CREATED = 'session_created'
    SESSION_UPDATED = 'session_updated'
    SESSION_COMPLETED = 'session_completed'
    
    # System events
    SYSTEM_STATUS = 'system_status'
    RESOURCE_WARNING = 'resource_warning'
    ERROR_OCCURRED = 'error_occurred'
    
    # Queue events
    QUEUE_STATUS = 'queue_status'
    PRIORITY_CHANGED = 'priority_changed'


# Global WebSocket server instance
_websocket_server: Optional[WebSocketServer] = None


def init_websocket_server(app: Flask) -> WebSocketServer:
    """
    Initialize global WebSocket server
    
    Args:
        app: Flask application instance
        
    Returns:
        WebSocketServer instance
    """
    global _websocket_server
    _websocket_server = WebSocketServer(app)
    return _websocket_server


def get_websocket_server() -> Optional[WebSocketServer]:
    """
    Get global WebSocket server instance
    
    Returns:
        WebSocketServer instance or None if not initialized
    """
    return _websocket_server


def broadcast_progress(job_id: str, stage: str, progress: float, message: str = ""):
    """
    Convenience function to broadcast job progress
    
    Args:
        job_id: Job identifier
        stage: Current processing stage
        progress: Progress percentage (0-100)
        message: Optional progress message
    """
    if _websocket_server:
        _websocket_server.broadcast({
            'type': 'job_progress',
            'job_id': job_id,
            'stage': stage,
            'progress': progress,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }, channel='jobs')


def broadcast_photo_info(job_id: str, photo_id: int, photo_data: Dict):
    """
    Convenience function to broadcast photo information
    
    Args:
        job_id: Job identifier
        photo_id: Photo database ID
        photo_data: Photo metadata and analysis results
    """
    if _websocket_server:
        _websocket_server.broadcast({
            'type': 'photo_info',
            'job_id': job_id,
            'photo_id': photo_id,
            'photo_data': photo_data,
            'timestamp': datetime.now().isoformat()
        }, channel='photos')


def broadcast_error(job_id: str, error_type: str, error_message: str, error_details: Dict = None):
    """
    Convenience function to broadcast error information
    
    Args:
        job_id: Job identifier
        error_type: Type of error
        error_message: Error message
        error_details: Optional detailed error information
    """
    if _websocket_server:
        _websocket_server.broadcast({
            'type': 'error_occurred',
            'job_id': job_id,
            'error_type': error_type,
            'error_message': error_message,
            'error_details': error_details or {},
            'timestamp': datetime.now().isoformat()
        }, channel='jobs')
