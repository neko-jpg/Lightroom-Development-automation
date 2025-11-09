# WebSocket Real-time Updates Implementation
# WebSocketリアルタイム更新実装

## Overview

This document describes the implementation of WebSocket real-time updates for the Junmai AutoDev system. The implementation provides bidirectional real-time communication between the server and connected clients (GUI, mobile web, Lightroom plugin).

**Requirements**: 4.5, 7.2

## Architecture

### Components

1. **WebSocket Server** (`websocket_server.py`)
   - Manages WebSocket connections
   - Handles client registration and subscriptions
   - Broadcasts events to connected clients
   - Provides connection management

2. **Event Broadcasting** (`websocket_events.py`)
   - Provides convenience functions for broadcasting events
   - Standardizes event message formats
   - Routes events to appropriate channels

3. **API Integration** (`app.py`)
   - Integrates WebSocket broadcasting into API endpoints
   - Broadcasts events when actions occur
   - Provides WebSocket management endpoints

## Event Types

### Job Events
- `job_created` - New job submitted to queue
- `job_started` - Job processing started
- `job_progress` - Job progress update
- `job_completed` - Job completed successfully
- `job_failed` - Job failed with error

### Photo Events
- `photo_imported` - Photo imported to system
- `photo_analyzed` - Photo analysis completed
- `photo_selected` - Photo selected for processing
- `photo_approved` - Photo approved by user
- `photo_rejected` - Photo rejected by user

### Session Events
- `session_created` - New session created
- `session_updated` - Session progress updated
- `session_completed` - Session completed

### System Events
- `system_status` - System status update
- `resource_warning` - Resource usage warning
- `error_occurred` - Error occurred

### Queue Events
- `queue_status` - Queue status update
- `priority_changed` - Job priority changed

### Approval Queue Events
- `approval_queue_updated` - Approval queue count changed

### Export Events
- `export_started` - Export started
- `export_completed` - Export completed
- `export_failed` - Export failed

## Channel Subscription

Clients can subscribe to specific channels to receive filtered events:

- `jobs` - Job-related events
- `photos` - Photo-related events
- `sessions` - Session-related events
- `system` - System-related events
- `queue` - Queue-related events
- `approval` - Approval queue events
- `export` - Export-related events

## WebSocket Protocol

### Client Connection

```javascript
// Connect to WebSocket server
const ws = new WebSocket('ws://localhost:5100/ws');

ws.onopen = () => {
  console.log('Connected to WebSocket server');
  
  // Register client
  ws.send(JSON.stringify({
    type: 'register',
    client_type: 'gui',  // or 'mobile', 'lightroom'
    client_name: 'Desktop GUI'
  }));
  
  // Subscribe to channels
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['jobs', 'photos', 'sessions']
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
  
  // Handle different event types
  switch(message.type) {
    case 'job_progress':
      updateJobProgress(message.job_id, message.progress);
      break;
    case 'photo_imported':
      addPhotoToList(message.photo_id, message.file_name);
      break;
    case 'session_updated':
      updateSessionProgress(message.session_id, message.progress_percent);
      break;
    // ... handle other events
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from WebSocket server');
  // Implement reconnection logic
};
```

### Message Format

All WebSocket messages follow this format:

```json
{
  "type": "event_type",
  "timestamp": "2025-11-09T12:34:56.789Z",
  // ... event-specific fields
}
```

### Built-in Message Types

#### Ping/Pong
```json
// Client sends
{
  "type": "ping"
}

// Server responds
{
  "type": "pong",
  "timestamp": "2025-11-09T12:34:56.789Z"
}
```

#### Registration
```json
// Client sends
{
  "type": "register",
  "client_type": "gui",
  "client_name": "Desktop GUI"
}

// Server responds
{
  "type": "registration_confirmed",
  "client_type": "gui",
  "client_name": "Desktop GUI"
}
```

#### Subscription
```json
// Client sends
{
  "type": "subscribe",
  "channels": ["jobs", "photos"]
}

// Server responds
{
  "type": "subscription_confirmed",
  "channels": ["jobs", "photos"]
}
```

## API Integration

### Automatic Event Broadcasting

The following API endpoints automatically broadcast WebSocket events:

#### File Import
- `POST /import/file` → broadcasts `photo_imported`
- `POST /import/batch` → broadcasts `photo_imported` for each file
- `POST /import/session` → broadcasts `session_created`

#### Job Queue
- `POST /queue/submit` → broadcasts `job_created`
- `POST /queue/batch` → broadcasts `job_created` for each job
- `POST /queue/session/<id>` → broadcasts `job_created` for each photo

#### Batch Processing
- `POST /batch/start` → broadcasts `system_status` (batch_started)
- `POST /batch/<id>/pause` → broadcasts `system_status` (batch_paused)
- `POST /batch/<id>/resume` → broadcasts `system_status` (batch_resumed)

### Example: Photo Import with WebSocket Event

```python
# In app.py
@app.route("/import/file", methods=["POST"])
def import_single_file():
    # ... import file logic ...
    
    # Broadcast photo imported event via WebSocket
    broadcast_photo_imported(
        photo_id=photo.id,
        session_id=session_id,
        file_name=photo.file_name,
        file_path=final_path
    )
    
    return jsonify({...}), 200
```

## WebSocket Management API

### Get Connected Clients
```http
GET /websocket/clients
```

Response:
```json
{
  "success": true,
  "clients": [
    {
      "id": 12345,
      "client_type": "gui",
      "client_name": "Desktop GUI",
      "connected_at": "2025-11-09T12:00:00Z",
      "last_ping": "2025-11-09T12:34:56Z",
      "subscriptions": ["jobs", "photos", "sessions"]
    }
  ],
  "count": 1
}
```

### Broadcast Custom Message
```http
POST /websocket/broadcast
Content-Type: application/json

{
  "type": "custom_event",
  "data": {
    "message": "Custom message",
    "value": 42
  },
  "channel": "system"
}
```

### Get WebSocket Statistics
```http
GET /websocket/stats
```

Response:
```json
{
  "success": true,
  "stats": {
    "total_clients": 3,
    "clients_by_type": {
      "gui": 1,
      "mobile": 2
    },
    "active_channels": ["jobs", "photos", "sessions", "system"],
    "channel_count": 4
  }
}
```

### Disconnect Client
```http
POST /websocket/disconnect/<client_id>
```

## Event Broadcasting Functions

### Photo Events

```python
from websocket_events import broadcast_photo_imported

broadcast_photo_imported(
    photo_id=123,
    session_id=1,
    file_name="IMG_5432.CR3",
    file_path="/path/to/photo.cr3"
)
```

### Session Events

```python
from websocket_events import broadcast_session_updated

broadcast_session_updated(
    session_id=1,
    total_photos=100,
    processed_photos=45,
    status='processing'
)
```

### Job Events

```python
from websocket_events import broadcast_job_progress

broadcast_job_progress(
    job_id="task-abc123",
    stage="developing",
    progress=75.5,
    message="Applying preset..."
)
```

### System Events

```python
from websocket_events import broadcast_system_status

broadcast_system_status(
    status='running',
    details={
        'cpu_usage': 45.2,
        'memory_usage': 60.5,
        'active_jobs': 3
    }
)
```

## Client Implementation Examples

### React/JavaScript Client

```javascript
import { useEffect, useState } from 'react';

function useWebSocket(url) {
  const [ws, setWs] = useState(null);
  const [messages, setMessages] = useState([]);
  
  useEffect(() => {
    const websocket = new WebSocket(url);
    
    websocket.onopen = () => {
      console.log('WebSocket connected');
      
      // Register and subscribe
      websocket.send(JSON.stringify({
        type: 'register',
        client_type: 'mobile',
        client_name: 'Mobile Web'
      }));
      
      websocket.send(JSON.stringify({
        type: 'subscribe',
        channels: ['jobs', 'photos', 'sessions']
      }));
    };
    
    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages(prev => [...prev, message]);
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    websocket.onclose = () => {
      console.log('WebSocket disconnected');
      // Implement reconnection logic
      setTimeout(() => {
        setWs(new WebSocket(url));
      }, 5000);
    };
    
    setWs(websocket);
    
    return () => {
      websocket.close();
    };
  }, [url]);
  
  return { ws, messages };
}

// Usage in component
function Dashboard() {
  const { messages } = useWebSocket('ws://localhost:5100/ws');
  
  useEffect(() => {
    messages.forEach(message => {
      switch(message.type) {
        case 'job_progress':
          updateJobProgress(message);
          break;
        case 'photo_imported':
          addPhotoToList(message);
          break;
        // ... handle other events
      }
    });
  }, [messages]);
  
  return <div>Dashboard</div>;
}
```

### Python Client (PyQt6)

```python
from PyQt6.QtCore import QThread, pyqtSignal
from simple_websocket import Client
import json

class WebSocketThread(QThread):
    message_received = pyqtSignal(dict)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.running = True
    
    def run(self):
        try:
            ws = Client.connect(self.url)
            self.connected.emit()
            
            # Register and subscribe
            ws.send(json.dumps({
                'type': 'register',
                'client_type': 'gui',
                'client_name': 'Desktop GUI'
            }))
            
            ws.send(json.dumps({
                'type': 'subscribe',
                'channels': ['jobs', 'photos', 'sessions', 'system']
            }))
            
            while self.running:
                data = ws.receive()
                if data:
                    message = json.loads(data)
                    self.message_received.emit(message)
        
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            self.disconnected.emit()
    
    def stop(self):
        self.running = False

# Usage in main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Start WebSocket thread
        self.ws_thread = WebSocketThread('ws://localhost:5100/ws')
        self.ws_thread.message_received.connect(self.handle_websocket_message)
        self.ws_thread.connected.connect(self.on_websocket_connected)
        self.ws_thread.disconnected.connect(self.on_websocket_disconnected)
        self.ws_thread.start()
    
    def handle_websocket_message(self, message):
        msg_type = message.get('type')
        
        if msg_type == 'job_progress':
            self.update_job_progress(message)
        elif msg_type == 'photo_imported':
            self.add_photo_to_list(message)
        elif msg_type == 'session_updated':
            self.update_session_progress(message)
        # ... handle other events
    
    def closeEvent(self, event):
        self.ws_thread.stop()
        self.ws_thread.wait()
        super().closeEvent(event)
```

## Testing

### Unit Tests

Run the WebSocket integration tests:

```bash
python -m pytest local_bridge/test_websocket_realtime_integration.py -v
```

### Manual Testing

1. Start the server:
```bash
python local_bridge/app.py
```

2. Connect with a WebSocket client (e.g., using browser console):
```javascript
const ws = new WebSocket('ws://localhost:5100/ws');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.send(JSON.stringify({type: 'register', client_type: 'test', client_name: 'Test Client'}));
ws.send(JSON.stringify({type: 'subscribe', channels: ['jobs', 'photos']}));
```

3. Trigger events via API:
```bash
# Import a file (will broadcast photo_imported event)
curl -X POST http://localhost:5100/import/file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/photo.jpg", "session_id": 1}'

# Submit a job (will broadcast job_created event)
curl -X POST http://localhost:5100/queue/submit \
  -H "Content-Type: application/json" \
  -d '{"photo_id": 123}'
```

4. Check connected clients:
```bash
curl http://localhost:5100/websocket/clients
```

## Performance Considerations

### Connection Management
- Maximum connections: Limited by system resources
- Automatic cleanup of disconnected clients
- Heartbeat/ping mechanism to detect stale connections

### Message Broadcasting
- Efficient channel-based filtering
- Non-blocking broadcast to avoid delays
- Message queuing for slow clients (future enhancement)

### Resource Usage
- Minimal CPU overhead per connection
- Memory usage scales linearly with client count
- Network bandwidth depends on event frequency

## Security

### Authentication
- WebSocket connections can be authenticated via JWT tokens (future enhancement)
- Client registration required before receiving events
- Channel subscriptions control event access

### Rate Limiting
- Broadcast rate limiting to prevent flooding (future enhancement)
- Per-client message rate limiting (future enhancement)

## Troubleshooting

### Connection Issues

**Problem**: Client cannot connect to WebSocket server

**Solutions**:
- Verify server is running: `curl http://localhost:5100/websocket/stats`
- Check firewall settings
- Verify WebSocket URL is correct (`ws://` not `wss://`)

### Missing Events

**Problem**: Client not receiving expected events

**Solutions**:
- Verify client is subscribed to correct channels
- Check WebSocket connection status
- Review server logs for broadcast errors

### High Latency

**Problem**: Events arrive with significant delay

**Solutions**:
- Check network connectivity
- Monitor server resource usage
- Reduce event frequency if possible

## Future Enhancements

1. **WebSocket Authentication**
   - JWT token-based authentication
   - Per-channel access control

2. **Message Persistence**
   - Store recent events for new clients
   - Replay missed events on reconnection

3. **Compression**
   - Message compression for large payloads
   - Binary protocol support

4. **Clustering**
   - Multi-server WebSocket support
   - Redis pub/sub for event distribution

5. **Advanced Filtering**
   - Client-side event filtering
   - Custom subscription patterns

## References

- Requirements: 4.5 (Real-time progress reporting), 7.2 (Session progress tracking)
- Related Files:
  - `local_bridge/websocket_server.py` - WebSocket server implementation
  - `local_bridge/websocket_events.py` - Event broadcasting functions
  - `local_bridge/app.py` - API integration
  - `local_bridge/test_websocket_realtime_integration.py` - Integration tests

## Completion Status

✅ WebSocket server endpoint implemented  
✅ Event sending logic added  
✅ Client connection management implemented  
✅ Event type definitions created  
✅ API integration completed  
✅ Management endpoints added  
✅ Tests created  
✅ Documentation completed  

**Task 30: WebSocket リアルタイム更新の実装 - COMPLETED**
