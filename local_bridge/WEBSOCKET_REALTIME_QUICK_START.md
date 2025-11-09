# WebSocket Real-time Updates - Quick Start Guide
# WebSocketリアルタイム更新 - クイックスタートガイド

## 5-Minute Quick Start

### 1. Server Setup (Already Done!)

The WebSocket server is automatically initialized when the Flask app starts:

```python
# In app.py
from websocket_server import init_websocket_server
websocket_server = init_websocket_server(app)
```

### 2. Connect from JavaScript Client

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:5100/ws');

// Handle connection
ws.onopen = () => {
  console.log('Connected to WebSocket');
  
  // Register client
  ws.send(JSON.stringify({
    type: 'register',
    client_type: 'web',
    client_name: 'My Web App'
  }));
  
  // Subscribe to events
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['jobs', 'photos', 'sessions']
  }));
};

// Handle messages
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
  
  // Handle different event types
  switch(message.type) {
    case 'job_progress':
      console.log(`Job ${message.job_id}: ${message.progress}%`);
      break;
    case 'photo_approved':
      console.log(`Photo ${message.photo_id} approved!`);
      break;
    case 'session_updated':
      console.log(`Session ${message.session_id}: ${message.progress_percent}%`);
      break;
  }
};

// Handle errors
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Handle close
ws.onclose = () => {
  console.log('WebSocket connection closed');
};
```

### 3. Broadcast Events from Python

```python
# Import event broadcasting functions
from websocket_events import (
    broadcast_job_progress,
    broadcast_photo_approved,
    broadcast_session_updated
)

# Broadcast job progress
broadcast_job_progress(
    job_id="abc123",
    stage="analyzing",
    progress=50.0,
    message="Halfway done!"
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
    processed_photos=50,
    status="processing"
)
```

## Common Event Types

### Job Events
```python
# Job created
broadcast_job_created(job_id, photo_id, priority)

# Job started
broadcast_job_started(job_id, photo_id)

# Job progress (use this frequently!)
broadcast_job_progress(job_id, stage, progress, message)

# Job completed
broadcast_job_completed(job_id, photo_id, result)

# Job failed
broadcast_job_failed(job_id, photo_id, error_message, error_details)
```

### Photo Events
```python
# Photo imported
broadcast_photo_imported(photo_id, session_id, file_name, file_path)

# Photo analyzed
broadcast_photo_analyzed(photo_id, ai_score, analysis_results)

# Photo approved
broadcast_photo_approved(photo_id, session_id)

# Photo rejected
broadcast_photo_rejected(photo_id, session_id, reason)
```

### Session Events
```python
# Session created
broadcast_session_created(session_id, session_name, import_folder)

# Session updated (use this for progress!)
broadcast_session_updated(session_id, total_photos, processed_photos, status)

# Session completed
broadcast_session_completed(session_id, session_name, total_photos, approved_photos)
```

## Testing Your Connection

### Using Browser Console

```javascript
// Open browser console (F12) and paste:
const ws = new WebSocket('ws://localhost:5100/ws');
ws.onopen = () => console.log('Connected!');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
ws.send(JSON.stringify({type: 'register', client_type: 'test', client_name: 'Browser Test'}));
ws.send(JSON.stringify({type: 'subscribe', channels: ['jobs', 'photos', 'sessions']}));
```

### Using Python

```python
# test_websocket_connection.py
import asyncio
import websockets
import json

async def test_connection():
    uri = "ws://localhost:5100/ws"
    async with websockets.connect(uri) as websocket:
        # Register
        await websocket.send(json.dumps({
            'type': 'register',
            'client_type': 'test',
            'client_name': 'Python Test'
        }))
        
        # Subscribe
        await websocket.send(json.dumps({
            'type': 'subscribe',
            'channels': ['jobs', 'photos', 'sessions']
        }))
        
        # Listen for messages
        while True:
            message = await websocket.recv()
            print(f"Received: {message}")

asyncio.run(test_connection())
```

## React Hook Example

```javascript
import { useEffect, useState } from 'react';

export function useWebSocket() {
  const [ws, setWs] = useState(null);
  const [lastMessage, setLastMessage] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  
  useEffect(() => {
    const websocket = new WebSocket('ws://localhost:5100/ws');
    
    websocket.onopen = () => {
      setIsConnected(true);
      
      // Register
      websocket.send(JSON.stringify({
        type: 'register',
        client_type: 'web',
        client_name: 'React App'
      }));
      
      // Subscribe
      websocket.send(JSON.stringify({
        type: 'subscribe',
        channels: ['jobs', 'photos', 'sessions', 'system']
      }));
    };
    
    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setLastMessage(message);
    };
    
    websocket.onclose = () => {
      setIsConnected(false);
    };
    
    setWs(websocket);
    
    return () => websocket.close();
  }, []);
  
  return { ws, lastMessage, isConnected };
}

// Usage in component
function Dashboard() {
  const { lastMessage, isConnected } = useWebSocket();
  
  useEffect(() => {
    if (lastMessage?.type === 'job_progress') {
      console.log(`Progress: ${lastMessage.progress}%`);
    }
  }, [lastMessage]);
  
  return (
    <div>
      <p>Status: {isConnected ? 'Connected' : 'Disconnected'}</p>
      {lastMessage && <p>Last event: {lastMessage.type}</p>}
    </div>
  );
}
```

## PyQt6 Example

```python
from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtWebSockets import QWebSocket
import json

class WebSocketClient(QObject):
    message_received = pyqtSignal(dict)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.ws = QWebSocket()
        self.ws.connected.connect(self.on_connected)
        self.ws.disconnected.connect(self.on_disconnected)
        self.ws.textMessageReceived.connect(self.on_message)
    
    def connect(self):
        self.ws.open(QUrl("ws://localhost:5100/ws"))
    
    def on_connected(self):
        print("WebSocket connected")
        self.connected.emit()
        
        # Register
        self.send({
            'type': 'register',
            'client_type': 'gui',
            'client_name': 'PyQt6 GUI'
        })
        
        # Subscribe
        self.send({
            'type': 'subscribe',
            'channels': ['jobs', 'photos', 'sessions']
        })
    
    def on_disconnected(self):
        print("WebSocket disconnected")
        self.disconnected.emit()
    
    def on_message(self, message):
        data = json.loads(message)
        print(f"Received: {data['type']}")
        self.message_received.emit(data)
    
    def send(self, data):
        self.ws.sendTextMessage(json.dumps(data))

# Usage
ws_client = WebSocketClient()
ws_client.message_received.connect(lambda msg: print(f"Event: {msg['type']}"))
ws_client.connect()
```

## API Endpoints

### Get Connected Clients

```bash
curl http://localhost:5100/api/websocket/clients
```

Response:
```json
{
  "clients": [
    {
      "id": 12345,
      "client_type": "gui",
      "client_name": "Desktop GUI",
      "connected_at": "2025-11-08T14:30:00",
      "last_ping": "2025-11-08T14:35:00",
      "subscriptions": ["jobs", "photos", "sessions"]
    }
  ],
  "count": 1
}
```

### Broadcast Custom Message

```bash
curl -X POST http://localhost:5100/api/websocket/broadcast \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "type": "custom_event",
      "data": "Hello from API!"
    },
    "channel": "system"
  }'
```

### Disconnect Client

```bash
curl -X POST http://localhost:5100/api/websocket/disconnect/12345
```

## Channels

Subscribe to specific channels to receive only relevant events:

| Channel | Events |
|---------|--------|
| `jobs` | Job lifecycle events |
| `photos` | Photo processing events |
| `sessions` | Session management events |
| `system` | System status and errors |
| `queue` | Queue status updates |
| `approval` | Approval queue updates |
| `export` | Export progress events |

## Troubleshooting

### Can't Connect

1. Check server is running: `curl http://localhost:5100/api/system/health`
2. Verify WebSocket URL: `ws://localhost:5100/ws` (not `wss://`)
3. Check firewall settings

### Not Receiving Events

1. Verify registration: Check server logs
2. Confirm subscription: Send subscribe message with correct channels
3. Test with ping: `ws.send(JSON.stringify({type: 'ping'}))`

### Connection Drops

1. Implement reconnection logic
2. Send periodic pings (every 30 seconds)
3. Handle `onclose` event and reconnect

## Next Steps

1. Read full documentation: `WEBSOCKET_REALTIME_IMPLEMENTATION.md`
2. Run tests: `python local_bridge/validate_websocket_realtime.py`
3. Integrate with your GUI/Web app
4. Add custom event handlers as needed

## Support

For issues or questions:
1. Check logs: `local_bridge/logs/main.log`
2. Review implementation: `local_bridge/websocket_server.py`
3. Test connection: `local_bridge/validate_websocket_realtime.py`
