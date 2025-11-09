# WebSocket Real-time Updates Implementation
# WebSocketリアルタイム更新の実装

## Overview

This document describes the WebSocket real-time update system that provides bidirectional communication between the server and connected clients (GUI, Web UI, Mobile).

**Requirements:** 4.5, 7.2

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WebSocket Server                          │
│                  (websocket_server.py)                       │
├─────────────────────────────────────────────────────────────┤
│  - Connection Management                                     │
│  - Message Routing                                           │
│  - Channel-based Broadcasting                                │
│  - Client Type Filtering                                     │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│              Event Broadcasting Layer                        │
│               (websocket_events.py)                          │
├─────────────────────────────────────────────────────────────┤
│  - Job Events                                                │
│  - Photo Events                                              │
│  - Session Events                                            │
│  - System Events                                             │
│  - Queue Events                                              │
│  - Export Events                                             │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                  API Endpoints                               │
│                (api_extended.py)                             │
├─────────────────────────────────────────────────────────────┤
│  - Session Management → broadcast events                     │
│  - Photo Management → broadcast events                       │
│  - Job Management → broadcast events                         │
│  - Approval Queue → broadcast events                         │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    Clients                                   │
├─────────────────────────────────────────────────────────────┤
│  - Desktop GUI (PyQt6)                                       │
│  - Web UI (React PWA)                                        │
│  - Mobile App                                                │
│  - Lightroom Plugin (Lua)                                    │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. WebSocket Server (`websocket_server.py`)

The core WebSocket server that manages client connections and message routing.

**Key Features:**
- Connection management with automatic cleanup
- Channel-based message filtering
- Client type identification
- Custom message handler registration
- Ping/pong heartbeat support
- Subscription management

**Main Classes:**
- `WebSocketServer`: Main server class
- `EventType`: Standard event type constants

**Key Methods:**
```python
# Initialize server
ws_server = init_websocket_server(app)

# Broadcast to all clients
ws_server.broadcast(message, channel='jobs')

# Send to specific client type
ws_server.send_to_client_type('gui', message)

# Get connected clients
clients = ws_server.get_connected_clients()

# Register custom handler
ws_server.register_handler('custom_type', handler_func)
```

### 2. Event Broadcasting (`websocket_events.py`)

Convenience functions for broadcasting standardized events.

**Event Categories:**

#### Job Events
- `broadcast_job_created(job_id, photo_id, priority)`
- `broadcast_job_started(job_id, photo_id)`
- `broadcast_job_progress(job_id, stage, progress, message)`
- `broadcast_job_completed(job_id, photo_id, result)`
- `broadcast_job_failed(job_id, photo_id, error_message, error_details)`

#### Photo Events
- `broadcast_photo_imported(photo_id, session_id, file_name, file_path)`
- `broadcast_photo_analyzed(photo_id, ai_score, analysis_results)`
- `broadcast_photo_selected(photo_id, context_tag, selected_preset)`
- `broadcast_photo_approved(photo_id, session_id)`
- `broadcast_photo_rejected(photo_id, session_id, reason)`

#### Session Events
- `broadcast_session_created(session_id, session_name, import_folder)`
- `broadcast_session_updated(session_id, total_photos, processed_photos, status)`
- `broadcast_session_completed(session_id, session_name, total_photos, approved_photos)`

#### System Events
- `broadcast_system_status(status, details)`
- `broadcast_resource_warning(resource_type, current_value, threshold, message)`
- `broadcast_error_occurred(error_type, error_message, error_details, job_id, photo_id)`

#### Queue Events
- `broadcast_queue_status(pending_count, processing_count, completed_count, failed_count)`
- `broadcast_priority_changed(job_id, old_priority, new_priority, reason)`

#### Approval Queue Events
- `broadcast_approval_queue_updated(queue_count, session_id)`

#### Export Events
- `broadcast_export_started(photo_id, preset_name, destination)`
- `broadcast_export_completed(photo_id, preset_name, output_path, file_size)`
- `broadcast_export_failed(photo_id, preset_name, error_message)`

### 3. API Integration (`api_extended.py`)

REST API endpoints automatically broadcast events when actions occur.

**Integrated Endpoints:**
- `POST /api/sessions` → broadcasts `session_created`
- `PATCH /api/sessions/<id>` → broadcasts `session_updated`
- `POST /api/jobs` → broadcasts `job_created`
- `POST /api/approval/<id>/approve` → broadcasts `photo_approved` + `approval_queue_updated`
- `POST /api/approval/<id>/reject` → broadcasts `photo_rejected` + `approval_queue_updated`

**New WebSocket Management Endpoints:**
- `GET /api/websocket/clients` - Get list of connected clients
- `POST /api/websocket/broadcast` - Manually broadcast a message
- `POST /api/websocket/disconnect/<client_id>` - Disconnect a specific client

## Event Message Format

All WebSocket events follow a standardized format:

```json
{
  "type": "event_type",
  "timestamp": "2025-11-08T14:32:15.123456",
  ...event-specific data...
}
```

### Example: Job Progress Event

```json
{
  "type": "job_progress",
  "timestamp": "2025-11-08T14:32:15.123456",
  "job_id": "abc123def456",
  "stage": "analyzing",
  "progress": 45.5,
  "message": "Analyzing image quality"
}
```

### Example: Photo Approved Event

```json
{
  "type": "photo_approved",
  "timestamp": "2025-11-08T14:32:15.123456",
  "photo_id": 789,
  "session_id": 12
}
```

### Example: Session Updated Event

```json
{
  "type": "session_updated",
  "timestamp": "2025-11-08T14:32:15.123456",
  "session_id": 12,
  "total_photos": 100,
  "processed_photos": 45,
  "progress_percent": 45.0,
  "status": "processing"
}
```

## Client Connection Protocol

### 1. Connect to WebSocket

```javascript
const ws = new WebSocket('ws://localhost:5100/ws');
```

### 2. Register Client

```javascript
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'register',
    client_type: 'gui',  // or 'web', 'mobile', 'lightroom'
    client_name: 'Desktop GUI v2.0'
  }));
};
```

### 3. Subscribe to Channels

```javascript
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['jobs', 'photos', 'sessions', 'system']
}));
```

### 4. Handle Incoming Messages

```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch(message.type) {
    case 'job_progress':
      updateJobProgress(message.job_id, message.progress);
      break;
    case 'photo_approved':
      updatePhotoStatus(message.photo_id, 'approved');
      break;
    case 'session_updated':
      updateSessionProgress(message.session_id, message.progress_percent);
      break;
    // ... handle other event types
  }
};
```

### 5. Send Ping (Heartbeat)

```javascript
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping' }));
}, 30000);  // Every 30 seconds
```

## Channel System

Clients can subscribe to specific channels to receive only relevant events:

| Channel | Events |
|---------|--------|
| `jobs` | Job created, started, progress, completed, failed |
| `photos` | Photo imported, analyzed, selected, approved, rejected |
| `sessions` | Session created, updated, completed |
| `system` | System status, resource warnings, errors |
| `queue` | Queue status, priority changes |
| `approval` | Approval queue updates |
| `export` | Export started, completed, failed |

## Usage Examples

### Server-side: Broadcasting Events

```python
from websocket_events import (
    broadcast_job_progress,
    broadcast_photo_approved,
    broadcast_session_updated
)

# Broadcast job progress
broadcast_job_progress(
    job_id="abc123",
    stage="analyzing",
    progress=45.5,
    message="Analyzing image quality"
)

# Broadcast photo approval
broadcast_photo_approved(
    photo_id=789,
    session_id=12
)

# Broadcast session update
broadcast_session_updated(
    session_id=12,
    total_photos=100,
    processed_photos=45,
    status="processing"
)
```

### Client-side: React Example

```javascript
import { useEffect, useState } from 'react';

function useWebSocket() {
  const [ws, setWs] = useState(null);
  const [events, setEvents] = useState([]);
  
  useEffect(() => {
    const websocket = new WebSocket('ws://localhost:5100/ws');
    
    websocket.onopen = () => {
      // Register as web client
      websocket.send(JSON.stringify({
        type: 'register',
        client_type: 'web',
        client_name: 'Web UI'
      }));
      
      // Subscribe to channels
      websocket.send(JSON.stringify({
        type: 'subscribe',
        channels: ['jobs', 'photos', 'sessions']
      }));
    };
    
    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setEvents(prev => [...prev, message]);
    };
    
    setWs(websocket);
    
    return () => websocket.close();
  }, []);
  
  return { ws, events };
}

// Usage in component
function Dashboard() {
  const { events } = useWebSocket();
  
  useEffect(() => {
    events.forEach(event => {
      if (event.type === 'job_progress') {
        console.log(`Job ${event.job_id}: ${event.progress}%`);
      }
    });
  }, [events]);
  
  return <div>Dashboard</div>;
}
```

### Client-side: PyQt6 Example

```python
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWebSockets import QWebSocket
import json

class WebSocketClient(QThread):
    message_received = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.ws = QWebSocket()
        self.ws.textMessageReceived.connect(self.on_message)
    
    def run(self):
        self.ws.open(QUrl("ws://localhost:5100/ws"))
    
    def on_message(self, message):
        data = json.loads(message)
        self.message_received.emit(data)
    
    def register(self):
        self.ws.sendTextMessage(json.dumps({
            'type': 'register',
            'client_type': 'gui',
            'client_name': 'Desktop GUI'
        }))
    
    def subscribe(self, channels):
        self.ws.sendTextMessage(json.dumps({
            'type': 'subscribe',
            'channels': channels
        }))

# Usage
ws_client = WebSocketClient()
ws_client.message_received.connect(handle_message)
ws_client.start()
ws_client.register()
ws_client.subscribe(['jobs', 'photos', 'sessions'])
```

## Testing

### Unit Tests

Run the comprehensive test suite:

```bash
python -m pytest local_bridge/test_websocket_realtime.py -v
```

### Validation Script

Run the validation script without pytest:

```bash
python local_bridge/validate_websocket_realtime.py
```

### Manual Testing

1. Start the server:
```bash
python local_bridge/app.py
```

2. Connect with a WebSocket client (e.g., wscat):
```bash
wscat -c ws://localhost:5100/ws
```

3. Register and subscribe:
```json
{"type": "register", "client_type": "test", "client_name": "Test Client"}
{"type": "subscribe", "channels": ["jobs", "photos"]}
```

4. Trigger events via API:
```bash
curl -X POST http://localhost:5100/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Session", "import_folder": "/test"}'
```

5. Observe events in WebSocket client

## Performance Considerations

### Broadcasting Efficiency

- Events are broadcast asynchronously
- Channel filtering reduces unnecessary message delivery
- Client type filtering allows targeted updates
- No blocking on slow clients

### Connection Management

- Automatic cleanup of disconnected clients
- Heartbeat mechanism detects stale connections
- Thread-safe client list management
- Graceful handling of connection errors

### Scalability

- Current implementation supports ~100 concurrent clients
- For larger deployments, consider:
  - Redis pub/sub for multi-server setups
  - Message queue for event buffering
  - Load balancing across multiple WebSocket servers

## Security Considerations

### Authentication

Currently, WebSocket connections are unauthenticated. For production:

1. Implement JWT-based authentication
2. Validate tokens on connection
3. Restrict channels based on user permissions

### Rate Limiting

Implement rate limiting to prevent abuse:

```python
# Example rate limiter
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_messages=100, window_seconds=60):
        self.max_messages = max_messages
        self.window = timedelta(seconds=window_seconds)
        self.clients = defaultdict(list)
    
    def check(self, client_id):
        now = datetime.now()
        # Remove old messages
        self.clients[client_id] = [
            ts for ts in self.clients[client_id]
            if now - ts < self.window
        ]
        
        if len(self.clients[client_id]) >= self.max_messages:
            return False
        
        self.clients[client_id].append(now)
        return True
```

### Data Sanitization

- Validate all incoming messages
- Sanitize data before broadcasting
- Prevent injection attacks

## Troubleshooting

### Connection Issues

**Problem:** Client cannot connect to WebSocket

**Solutions:**
1. Check if server is running: `curl http://localhost:5100/api/system/health`
2. Verify WebSocket endpoint: `ws://localhost:5100/ws`
3. Check firewall settings
4. Verify Flask-Sock is installed: `pip install flask-sock`

### Missing Events

**Problem:** Client not receiving events

**Solutions:**
1. Verify client is registered: Check server logs
2. Confirm channel subscription: Send subscribe message
3. Check event broadcasting: Add debug logging
4. Verify WebSocket connection is active: Send ping

### High Latency

**Problem:** Events arrive with significant delay

**Solutions:**
1. Check network latency
2. Reduce event frequency
3. Implement event batching
4. Use channel filtering to reduce traffic

## Future Enhancements

1. **Event Persistence**: Store events for replay to reconnecting clients
2. **Event Filtering**: Allow clients to filter events by criteria
3. **Binary Protocol**: Use MessagePack for efficiency
4. **Compression**: Enable WebSocket compression
5. **Clustering**: Support multiple server instances with Redis
6. **Metrics**: Add Prometheus metrics for monitoring
7. **Authentication**: Implement JWT-based auth
8. **Authorization**: Channel-level access control

## References

- Flask-Sock Documentation: https://flask-sock.readthedocs.io/
- WebSocket Protocol: RFC 6455
- Requirements: 4.5 (Real-time communication), 7.2 (Progress tracking)
