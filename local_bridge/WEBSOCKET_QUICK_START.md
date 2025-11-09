# WebSocket Communication - Quick Start Guide

## Overview

This guide helps you quickly set up and use the WebSocket communication system for real-time updates between the Python bridge and Lightroom plugin.

**Requirements:** 4.5

## Installation

### Python Dependencies

```bash
pip install flask-sock simple-websocket
```

### Verify Installation

```bash
python -c "from websocket_fallback import init_websocket_fallback; print('WebSocket fallback ready')"
```

## Basic Usage

### 1. Server Setup (Already Integrated)

The WebSocket fallback server is automatically initialized in `app.py`:

```python
from websocket_fallback import init_websocket_fallback

# Initialize WebSocket fallback
websocket_fallback = init_websocket_fallback(app)
```

### 2. Start the Server

```bash
python app.py
```

The server will be available at `http://localhost:5100` with WebSocket endpoints at `/ws/*`.

### 3. Lightroom Plugin Setup (Already Integrated)

The WebSocket client is automatically initialized in `Main.lua`:

```lua
local WebSocketClient = require 'WebSocketClient'

-- Initialize on plugin load
WebSocketClient.init()
```

### 4. Verify Connection

Check WebSocket status:

```bash
curl http://localhost:5100/ws/status
```

Expected response:
```json
{
  "success": true,
  "enabled": true,
  "client_count": 0,
  "clients": []
}
```

## Common Use Cases

### Use Case 1: Send Job Progress Updates

**From Lightroom Plugin:**

```lua
-- Send progress update
WebSocketClient.sendJobProgress(
    'job_12345',        -- job_id
    'processing',       -- stage
    50,                 -- progress (0-100)
    'Applying HSL adjustments'  -- message
)
```

**From Python Server:**

```python
from app import send_websocket_notification

send_websocket_notification(
    'job_progress',
    {
        'job_id': 'job_12345',
        'stage': 'processing',
        'progress': 50,
        'message': 'Applying HSL adjustments'
    },
    channel='jobs'
)
```

### Use Case 2: Notify Job Completion

**From Lightroom Plugin:**

```lua
-- Notify completion
WebSocketClient.sendJobComplete(
    'job_12345',  -- job_id
    true,         -- success
    {             -- result data
        processing_time = 5.2,
        photos_processed = 1
    }
)
```

**From Python Server:**

```bash
curl -X POST http://localhost:5100/ws/notify/job_complete \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "job_12345",
    "success": true,
    "result": {
      "processing_time": 5.2,
      "photos_processed": 1
    }
  }'
```

### Use Case 3: Broadcast System Status

**From Python Server:**

```python
from websocket_fallback import get_websocket_fallback

ws = get_websocket_fallback()

# Broadcast to all clients subscribed to 'system' channel
ws.broadcast({
    'type': 'system_status',
    'cpu_usage': 45.2,
    'gpu_temp': 62,
    'queue_length': 5
}, channel='system')
```

**Receive in Lightroom Plugin:**

```lua
-- Add event listener
WebSocketClient.addEventListener('system_status', function(data)
    log:info("CPU: " .. data.cpu_usage .. "%, GPU: " .. data.gpu_temp .. "°C")
end)
```

### Use Case 4: Listen for New Jobs

**In Lightroom Plugin:**

```lua
-- Listen for job creation
WebSocketClient.addEventListener('job_created', function(data)
    log:info("New job created: " .. data.job_id)
    -- Trigger immediate polling
    Main.pollForNextJob()
end)
```

**Trigger from Python:**

```python
# When a new job is created
send_websocket_notification(
    'job_created',
    {
        'job_id': 'job_12345',
        'photo_id': 'photo_789',
        'priority': 5
    },
    channel='jobs'
)
```

## Testing

### Test WebSocket Connection

```bash
# Run tests
pytest test_websocket.py -v

# Test specific functionality
pytest test_websocket.py::test_handshake -v
pytest test_websocket.py::test_broadcast -v
```

### Manual Testing with curl

```bash
# 1. Handshake
curl -X POST http://localhost:5100/ws/handshake \
  -H "Content-Type: application/json" \
  -d '{"client_type": "test", "protocol_version": "1.0"}'

# Save the client_id from response

# 2. Poll for messages
curl "http://localhost:5100/ws/poll?client_id=YOUR_CLIENT_ID"

# 3. Send message
curl -X POST http://localhost:5100/ws/send \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "YOUR_CLIENT_ID",
    "message": {"type": "ping"}
  }'

# 4. Get connected clients
curl http://localhost:5100/ws/clients
```

## Monitoring

### Check Connected Clients

```bash
curl http://localhost:5100/ws/status | jq
```

### View Logs

```bash
# Main log
tail -f logs/main.log | grep WebSocket

# Filter for specific events
tail -f logs/main.log | grep "job_progress"
```

### Monitor in Real-Time

```python
# Python script to monitor WebSocket activity
import requests
import time

while True:
    response = requests.get('http://localhost:5100/ws/status')
    data = response.json()
    print(f"Connected clients: {data['client_count']}")
    time.sleep(5)
```

## Troubleshooting

### Problem: Client Cannot Connect

**Solution:**
```bash
# 1. Check server is running
curl http://localhost:5100/ws/status

# 2. Check firewall
# Windows: Allow port 5100 in Windows Firewall

# 3. Check logs
tail -f logs/main.log | grep "WebSocket"
```

### Problem: Messages Not Received

**Solution:**
```lua
-- In Lightroom plugin, verify subscription
WebSocketClient.send({
    type = 'subscribe',
    channels = {'jobs', 'system', 'photos'}
})

-- Check connection status
if WebSocketClient.isConnected() then
    log:info("Connected")
else
    log:warn("Not connected - reconnecting...")
    WebSocketClient.reconnect()
end
```

### Problem: Stale Connections

**Solution:**
```bash
# Clean up stale clients
curl -X POST http://localhost:5100/ws/cleanup \
  -H "Content-Type: application/json" \
  -d '{"timeout_minutes": 5}'
```

## Best Practices

### 1. Always Check Connection Status

```lua
if WebSocketClient.isConnected() then
    WebSocketClient.send({type = 'my_message'})
else
    log:warn("Not connected, message not sent")
end
```

### 2. Use Channels for Filtering

```python
# Send to specific channel
ws.broadcast(message, channel='jobs')  # Only to clients subscribed to 'jobs'
```

### 3. Handle Reconnection Gracefully

```lua
-- Add reconnection listener
WebSocketClient.addEventListener('disconnected', function()
    log:warn("Disconnected - will auto-reconnect")
end)

WebSocketClient.addEventListener('connected', function()
    log:info("Reconnected successfully")
end)
```

### 4. Keep Messages Small

```python
# Good: Small, focused message
ws.broadcast({
    'type': 'job_progress',
    'job_id': 'job123',
    'progress': 50
})

# Avoid: Large payloads
# Don't send entire photo data or large configs
```

### 5. Use Appropriate Channels

```lua
-- Subscribe only to needed channels
WebSocketClient.send({
    type = 'subscribe',
    channels = {'jobs'}  -- Only job-related events
})
```

## Performance Tips

1. **Polling Interval**: Default 1 second is good for most cases
2. **Message Queue**: Default 100 messages per client is sufficient
3. **Cleanup**: Run stale client cleanup periodically (every 5-10 minutes)
4. **Channels**: Use channels to reduce unnecessary message processing

## Next Steps

1. Read full documentation: `WEBSOCKET_IMPLEMENTATION.md`
2. Review example usage in `Main.lua` and `app.py`
3. Run tests: `pytest test_websocket.py -v`
4. Monitor logs during development
5. Implement custom message handlers as needed

## Support

For issues or questions:
1. Check logs: `logs/main.log`
2. Run tests: `pytest test_websocket.py -v`
3. Review documentation: `WEBSOCKET_IMPLEMENTATION.md`
4. Check server status: `curl http://localhost:5100/ws/status`
