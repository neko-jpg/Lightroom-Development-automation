# WebSocket Communication Implementation

## Overview

This document describes the WebSocket communication system implemented for real-time bidirectional communication between the Python bridge server and the Lightroom plugin.

**Requirements:** 4.5

## Architecture

### Components

1. **WebSocket Fallback Server** (`websocket_fallback.py`)
   - HTTP-based polling fallback for clients that don't support native WebSocket
   - Designed specifically for Lightroom Lua SDK limitations
   - Provides handshake, polling, and message sending endpoints

2. **WebSocket Client** (`WebSocketClient.lua`)
   - Lua client for Lightroom plugin
   - Implements HTTP polling fallback
   - Provides event-driven message handling
   - Automatic reconnection with exponential backoff

3. **Flask Integration** (`app.py`)
   - WebSocket endpoints integrated into main Flask application
   - Notification helpers for job progress, completion, and system status
   - Broadcast and targeted messaging support

## Protocol

### Connection Flow

```
1. Client → Server: POST /ws/handshake
   {
     "client_type": "lightroom",
     "protocol_version": "1.0"
   }

2. Server → Client: Response
   {
     "success": true,
     "client_id": "uuid",
     "server_time": "2025-11-09T..."
   }

3. Client → Server: POST /ws/send (register)
   {
     "client_id": "uuid",
     "message": {
       "type": "register",
       "client_type": "lightroom",
       "client_name": "Lightroom Classic Plugin"
     }
   }

4. Client → Server: POST /ws/send (subscribe)
   {
     "client_id": "uuid",
     "message": {
       "type": "subscribe",
       "channels": ["jobs", "system", "photos"]
     }
   }

5. Client → Server: GET /ws/poll?client_id=uuid (repeated)
   Server → Client: Response
   {
     "success": true,
     "messages": [
       {"type": "job_progress", "job_id": "...", ...},
       {"type": "system_status", ...}
     ]
   }
```

### Message Types

#### Built-in Messages

- **ping/pong**: Keep-alive mechanism
- **register**: Client registration with type and name
- **subscribe/unsubscribe**: Channel subscription management
- **connection_established**: Welcome message after handshake
- **error**: Error notifications

#### Application Messages

- **job_created**: New job created
- **job_started**: Job processing started
- **job_progress**: Job progress update
- **job_completed**: Job completed successfully
- **job_failed**: Job failed
- **photo_imported**: Photo imported to database
- **photo_analyzed**: Photo analysis completed
- **session_created**: New session created
- **system_status**: System status update
- **resource_warning**: Resource constraint warning

## API Endpoints

### WebSocket Fallback Endpoints

#### POST /ws/handshake
Establish connection and get client ID.

**Request:**
```json
{
  "client_type": "lightroom",
  "protocol_version": "1.0"
}
```

**Response:**
```json
{
  "success": true,
  "client_id": "uuid",
  "protocol_version": "1.0",
  "server_time": "2025-11-09T..."
}
```

#### GET /ws/poll
Poll for new messages.

**Query Parameters:**
- `client_id`: Client identifier (required)

**Response:**
```json
{
  "success": true,
  "messages": [
    {"type": "...", ...}
  ],
  "timestamp": "2025-11-09T..."
}
```

#### POST /ws/send
Send message from client to server.

**Request:**
```json
{
  "client_id": "uuid",
  "message": {
    "type": "ping"
  }
}
```

**Response:**
```json
{
  "success": true,
  "response": {
    "type": "pong",
    "timestamp": "..."
  }
}
```

#### POST /ws/disconnect
Disconnect client.

**Request:**
```json
{
  "client_id": "uuid"
}
```

#### GET /ws/clients
Get list of connected clients.

**Response:**
```json
{
  "success": true,
  "clients": [
    {
      "id": "uuid",
      "client_type": "lightroom",
      "connected_at": "...",
      "last_poll": "...",
      "subscriptions": ["jobs", "system"]
    }
  ],
  "count": 1
}
```

### Notification Endpoints

#### GET /ws/status
Get WebSocket server status.

#### POST /ws/broadcast
Broadcast message to all clients or specific channel.

**Request:**
```json
{
  "message": {
    "type": "system_status",
    "status": {...}
  },
  "channel": "system"
}
```

#### POST /ws/send/<client_id>
Send message to specific client.

#### POST /ws/notify/job_progress
Send job progress notification.

**Request:**
```json
{
  "job_id": "job123",
  "stage": "processing",
  "progress": 50,
  "message": "Applying settings..."
}
```

#### POST /ws/notify/job_complete
Send job completion notification.

**Request:**
```json
{
  "job_id": "job123",
  "success": true,
  "result": {...}
}
```

#### POST /ws/notify/system_status
Send system status update.

**Request:**
```json
{
  "status": {
    "cpu_usage": 45.2,
    "gpu_temp": 62,
    ...
  }
}
```

#### POST /ws/cleanup
Clean up stale clients.

**Request:**
```json
{
  "timeout_minutes": 5
}
```

## Lua Client Usage

### Initialization

```lua
local WebSocketClient = require 'WebSocketClient'

-- Initialize client
WebSocketClient.init()
```

### Sending Messages

```lua
-- Send custom message
WebSocketClient.send({
    type = 'custom_event',
    data = 'some data'
})

-- Send job progress
WebSocketClient.sendJobProgress(
    'job123',           -- job_id
    'processing',       -- stage
    50,                 -- progress (0-100)
    'Applying settings' -- message
)

-- Send job completion
WebSocketClient.sendJobComplete(
    'job123',  -- job_id
    true,      -- success
    {}         -- result data
)

-- Send error
WebSocketClient.sendError(
    'processing_error',
    'Failed to apply settings',
    {photo_id = 'photo123'}
)
```

### Event Listeners

```lua
-- Add event listener
WebSocketClient.addEventListener('job_created', function(data)
    log:info("New job: " .. data.job_id)
end)

-- Remove event listener
WebSocketClient.removeEventListener('job_created', listener_function)
```

### Message Handlers

```lua
-- Register custom message handler
WebSocketClient.registerHandler('custom_message', function(message)
    log:info("Received custom message: " .. message.data)
end)
```

### Connection Management

```lua
-- Check connection status
if WebSocketClient.isConnected() then
    log:info("Connected to server")
end

-- Get client ID
local client_id = WebSocketClient.getClientId()

-- Reconnect
WebSocketClient.reconnect()

-- Disconnect
WebSocketClient.disconnect()
```

## Python Server Usage

### Broadcasting Messages

```python
from websocket_fallback import get_websocket_fallback

ws = get_websocket_fallback()

# Broadcast to all clients
ws.broadcast({
    'type': 'system_status',
    'status': {...}
})

# Broadcast to specific channel
ws.broadcast({
    'type': 'job_progress',
    'job_id': 'job123',
    'progress': 50
}, channel='jobs')
```

### Targeted Messaging

```python
# Send to specific client
ws.send_to_client('client_id', {
    'type': 'notification',
    'message': 'Hello'
})

# Send to all clients of specific type
ws.send_to_client_type('lightroom', {
    'type': 'reload_config',
    'config': {...}
})
```

### Helper Function

```python
from app import send_websocket_notification

# Send notification from anywhere in the application
send_websocket_notification(
    'job_progress',
    {
        'job_id': 'job123',
        'stage': 'processing',
        'progress': 50
    },
    channel='jobs'
)
```

## Configuration

### Server Configuration

```python
# In app.py
websocket_fallback = init_websocket_fallback(
    app,
    max_message_queue_size=100  # Max messages per client
)
```

### Client Configuration

```lua
-- In WebSocketClient.lua
local WS_URL = "ws://127.0.0.1:5100/ws"
local HTTP_FALLBACK_URL = "http://127.0.0.1:5100"
local RECONNECT_DELAY = 5  -- seconds
local PING_INTERVAL = 30   -- seconds
local MAX_RECONNECT_ATTEMPTS = 10
```

## Error Handling

### Server-Side

- Invalid client_id returns 404
- Missing required fields returns 400
- Exceptions are logged and return 500
- Stale clients are automatically cleaned up

### Client-Side

- Automatic reconnection with exponential backoff
- Maximum reconnection attempts limit
- Graceful fallback to HTTP polling
- Error notifications sent to server

## Performance Considerations

### Message Queue

- Each client has a bounded message queue (default: 100 messages)
- Oldest messages are dropped when queue is full
- Prevents memory issues with slow/disconnected clients

### Polling Interval

- Default: 1 second between polls
- Configurable per client
- Balance between responsiveness and server load

### Stale Client Cleanup

- Clients inactive for 5+ minutes are removed
- Automatic cleanup can be triggered manually
- Prevents resource leaks

## Security

### Authentication

- Client ID is UUID-based
- No authentication required for local connections
- Can be extended with JWT tokens for remote access

### Rate Limiting

- Not implemented in current version
- Can be added using Flask-Limiter

### Data Validation

- All messages validated for required fields
- JSON parsing errors handled gracefully
- Invalid message types logged

## Testing

Run tests:
```bash
pytest test_websocket.py -v
```

Test coverage:
- Handshake and connection
- Message sending and receiving
- Broadcasting and filtering
- Channel subscriptions
- Client management
- Stale client cleanup
- Error handling

## Future Enhancements

1. **Native WebSocket Support**
   - Implement true WebSocket using flask-sock
   - Maintain HTTP fallback for compatibility

2. **Message Persistence**
   - Store messages in database for offline clients
   - Replay missed messages on reconnection

3. **Compression**
   - Compress large messages
   - Reduce bandwidth usage

4. **Encryption**
   - TLS/SSL support for remote connections
   - Message encryption for sensitive data

5. **Metrics**
   - Message throughput tracking
   - Client connection statistics
   - Performance monitoring

## Troubleshooting

### Client Cannot Connect

1. Check server is running: `curl http://localhost:5100/ws/status`
2. Verify firewall settings
3. Check logs: `logs/main.log`

### Messages Not Received

1. Verify client is polling: check `last_poll` timestamp
2. Check channel subscriptions
3. Verify message queue not full

### High Memory Usage

1. Check number of connected clients
2. Verify stale client cleanup is running
3. Reduce message queue size

### Connection Drops

1. Check network stability
2. Verify ping/pong mechanism working
3. Adjust reconnection parameters

## References

- Flask-Sock: https://flask-sock.readthedocs.io/
- WebSocket Protocol: https://tools.ietf.org/html/rfc6455
- Lightroom SDK: https://www.adobe.com/devnet/photoshoplightroom.html
