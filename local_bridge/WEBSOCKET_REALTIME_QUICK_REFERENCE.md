# WebSocket Real-time Updates - Quick Reference
# WebSocketリアルタイム更新 - クイックリファレンス

## Quick Start

### Connect to WebSocket Server

```javascript
const ws = new WebSocket('ws://localhost:5100/ws');

ws.onopen = () => {
  // Register client
  ws.send(JSON.stringify({
    type: 'register',
    client_type: 'gui',  // 'gui', 'mobile', or 'lightroom'
    client_name: 'My Client'
  }));
  
  // Subscribe to channels
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['jobs', 'photos', 'sessions']
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Event:', message.type, message);
};
```

## Event Types Reference

### Job Events (Channel: `jobs`)
| Event Type | Description | Key Fields |
|------------|-------------|------------|
| `job_created` | Job submitted | `job_id`, `photo_id`, `priority` |
| `job_started` | Job processing started | `job_id`, `photo_id` |
| `job_progress` | Progress update | `job_id`, `stage`, `progress`, `message` |
| `job_completed` | Job finished | `job_id`, `photo_id`, `result` |
| `job_failed` | Job failed | `job_id`, `photo_id`, `error_message` |

### Photo Events (Channel: `photos`)
| Event Type | Description | Key Fields |
|------------|-------------|------------|
| `photo_imported` | Photo imported | `photo_id`, `session_id`, `file_name` |
| `photo_analyzed` | Analysis complete | `photo_id`, `ai_score`, `analysis_results` |
| `photo_selected` | Selected for processing | `photo_id`, `context_tag`, `selected_preset` |
| `photo_approved` | User approved | `photo_id`, `session_id` |
| `photo_rejected` | User rejected | `photo_id`, `session_id`, `reason` |

### Session Events (Channel: `sessions`)
| Event Type | Description | Key Fields |
|------------|-------------|------------|
| `session_created` | New session | `session_id`, `session_name`, `import_folder` |
| `session_updated` | Progress update | `session_id`, `total_photos`, `processed_photos`, `progress_percent` |
| `session_completed` | Session done | `session_id`, `total_photos`, `approved_photos`, `approval_rate` |

### System Events (Channel: `system`)
| Event Type | Description | Key Fields |
|------------|-------------|------------|
| `system_status` | Status update | `status`, `details` |
| `resource_warning` | Resource alert | `resource_type`, `current_value`, `threshold` |
| `error_occurred` | Error happened | `error_type`, `error_message`, `error_details` |

### Queue Events (Channel: `queue`)
| Event Type | Description | Key Fields |
|------------|-------------|------------|
| `queue_status` | Queue stats | `pending`, `processing`, `completed`, `failed` |
| `priority_changed` | Priority adjusted | `job_id`, `old_priority`, `new_priority` |

## API Endpoints

### Get Connected Clients
```bash
curl http://localhost:5100/websocket/clients
```

### Broadcast Custom Message
```bash
curl -X POST http://localhost:5100/websocket/broadcast \
  -H "Content-Type: application/json" \
  -d '{
    "type": "custom_event",
    "data": {"message": "Hello"},
    "channel": "system"
  }'
```

### Get WebSocket Stats
```bash
curl http://localhost:5100/websocket/stats
```

## Broadcasting Events (Server-side)

```python
from websocket_events import (
    broadcast_photo_imported,
    broadcast_job_progress,
    broadcast_session_updated
)

# Photo imported
broadcast_photo_imported(
    photo_id=123,
    session_id=1,
    file_name="IMG_5432.CR3",
    file_path="/path/to/photo.cr3"
)

# Job progress
broadcast_job_progress(
    job_id="task-abc123",
    stage="developing",
    progress=75.5,
    message="Applying preset..."
)

# Session updated
broadcast_session_updated(
    session_id=1,
    total_photos=100,
    processed_photos=45,
    status='processing'
)
```

## Message Format

All messages include:
```json
{
  "type": "event_type",
  "timestamp": "2025-11-09T12:34:56.789Z",
  // ... event-specific fields
}
```

## Client Types

- `gui` - Desktop GUI application
- `mobile` - Mobile web application
- `lightroom` - Lightroom plugin
- `unknown` - Unregistered client

## Channels

- `jobs` - Job processing events
- `photos` - Photo-related events
- `sessions` - Session management events
- `system` - System status events
- `queue` - Queue management events
- `approval` - Approval queue events
- `export` - Export events

## Common Patterns

### Handle Job Progress
```javascript
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  if (msg.type === 'job_progress') {
    updateProgressBar(msg.job_id, msg.progress);
    showMessage(msg.message);
  }
};
```

### Handle Photo Import
```javascript
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  if (msg.type === 'photo_imported') {
    addPhotoToGallery({
      id: msg.photo_id,
      name: msg.file_name,
      sessionId: msg.session_id
    });
  }
};
```

### Handle Session Updates
```javascript
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  if (msg.type === 'session_updated') {
    updateSessionCard(msg.session_id, {
      progress: msg.progress_percent,
      processed: msg.processed_photos,
      total: msg.total_photos
    });
  }
};
```

## Troubleshooting

### Not Receiving Events?
1. Check subscription: `ws.send(JSON.stringify({type: 'subscribe', channels: ['jobs']}))`
2. Verify connection: Check `ws.readyState === WebSocket.OPEN`
3. Check server logs for errors

### Connection Drops?
1. Implement reconnection logic
2. Send periodic pings: `ws.send(JSON.stringify({type: 'ping'}))`
3. Check network stability

### High Latency?
1. Reduce event frequency
2. Check server resource usage
3. Optimize client-side event handling

## Testing

### Test Connection
```javascript
const ws = new WebSocket('ws://localhost:5100/ws');
ws.onopen = () => console.log('Connected!');
ws.onerror = (e) => console.error('Error:', e);
```

### Test Event Reception
```bash
# Terminal 1: Connect to WebSocket
wscat -c ws://localhost:5100/ws

# Terminal 2: Trigger event
curl -X POST http://localhost:5100/import/file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/test.jpg", "session_id": 1}'
```

## Requirements

- **4.5**: Real-time progress reporting
- **7.2**: Session progress tracking

## Files

- `websocket_server.py` - Server implementation
- `websocket_events.py` - Event broadcasting
- `app.py` - API integration
- `test_websocket_realtime_integration.py` - Tests
