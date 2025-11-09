# Batch Processing Control - Quick Start Guide

## Overview

The Batch Processing Control system allows you to manage large-scale photo processing operations with pause/resume capabilities and automatic recovery from interruptions.

**Requirements**: 11.4, 14.3

## Quick Start

### 1. Starting a Batch

```python
import requests

BASE_URL = "http://localhost:5100"

# Start processing a batch of photos
response = requests.post(f"{BASE_URL}/batch/start", json={
    "photo_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "session_id": 123,  # Optional
    "config": {         # Optional processing config
        "preset": "WhiteLayer_v4",
        "blend": 60
    }
})

batch_id = response.json()["batch_id"]
print(f"Batch started: {batch_id}")
```

### 2. Monitoring Progress

```python
# Get batch status
status = requests.get(f"{BASE_URL}/batch/{batch_id}/status").json()

print(f"Status: {status['status']}")
print(f"Progress: {status['progress_percent']}%")
print(f"Processed: {status['processed_count']}/{status['total_photos']}")
print(f"Failed: {status['failed_count']}")
```

### 3. Pausing a Batch

```python
# Pause the batch (e.g., to free up resources)
response = requests.post(f"{BASE_URL}/batch/{batch_id}/pause")

if response.status_code == 200:
    print("Batch paused successfully")
```

### 4. Resuming a Batch

```python
# Resume the paused batch
response = requests.post(f"{BASE_URL}/batch/{batch_id}/resume")

if response.status_code == 200:
    print("Batch resumed successfully")
```

### 5. Cancelling a Batch

```python
# Cancel the batch if no longer needed
response = requests.post(f"{BASE_URL}/batch/{batch_id}/cancel")

if response.status_code == 200:
    print("Batch cancelled successfully")
```

## Common Use Cases

### Use Case 1: Long-Running Batch with Breaks

```python
# Start a large batch
batch_id = start_batch(photo_ids=range(1, 1001))  # 1000 photos

# Work on other tasks...
time.sleep(3600)  # 1 hour

# Pause for lunch break
pause_batch(batch_id)

# Resume after break
resume_batch(batch_id)

# Wait for completion
while True:
    status = get_batch_status(batch_id)
    if status['status'] == 'completed':
        break
    time.sleep(10)
```

### Use Case 2: System Restart Recovery

```python
# On application startup, recover interrupted batches
response = requests.post(f"{BASE_URL}/batch/recover")
result = response.json()

print(f"Recovered {result['recovered_count']} interrupted batches")

# List all batches
batches = requests.get(f"{BASE_URL}/batch/list").json()['batches']

# Resume paused batches
for batch in batches:
    if batch['status'] == 'paused':
        print(f"Resuming batch {batch['batch_id']}")
        requests.post(f"{BASE_URL}/batch/{batch['batch_id']}/resume")
```

### Use Case 3: Resource Management

```python
# Start batch during idle time
if is_system_idle():
    batch_id = start_batch(photo_ids=pending_photos)
    
    # Monitor system resources
    while True:
        status = get_batch_status(batch_id)
        
        if status['status'] == 'completed':
            break
        
        # Pause if system becomes busy
        if not is_system_idle():
            pause_batch(batch_id)
            print("System busy, batch paused")
            
            # Wait for idle
            wait_for_idle()
            
            # Resume
            resume_batch(batch_id)
            print("System idle, batch resumed")
        
        time.sleep(30)
```

### Use Case 4: Batch Cleanup

```python
# Clean up old completed batches (older than 7 days)
response = requests.post(f"{BASE_URL}/batch/cleanup", json={
    "days_old": 7
})

result = response.json()
print(f"Cleaned up {result['cleaned_count']} old batches")
```

## JavaScript/TypeScript Example

```javascript
const BASE_URL = "http://localhost:5100";

// Start batch
async function startBatch(photoIds, sessionId = null) {
  const response = await fetch(`${BASE_URL}/batch/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      photo_ids: photoIds,
      session_id: sessionId
    })
  });
  
  const data = await response.json();
  return data.batch_id;
}

// Monitor progress
async function monitorBatch(batchId) {
  const response = await fetch(`${BASE_URL}/batch/${batchId}/status`);
  const status = await response.json();
  
  console.log(`Progress: ${status.progress_percent}%`);
  console.log(`Status: ${status.status}`);
  
  return status;
}

// Pause batch
async function pauseBatch(batchId) {
  await fetch(`${BASE_URL}/batch/${batchId}/pause`, {
    method: 'POST'
  });
}

// Resume batch
async function resumeBatch(batchId) {
  await fetch(`${BASE_URL}/batch/${batchId}/resume`, {
    method: 'POST'
  });
}

// Usage
(async () => {
  const batchId = await startBatch([1, 2, 3, 4, 5]);
  console.log(`Batch started: ${batchId}`);
  
  // Monitor until complete
  while (true) {
    const status = await monitorBatch(batchId);
    
    if (status.status === 'completed') {
      console.log('Batch completed!');
      break;
    }
    
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
})();
```

## State Persistence

Batch states are automatically persisted to:
```
local_bridge/data/batch_states/{batch_id}.json
```

### State File Format

```json
{
  "batch_id": "batch_abc123def456",
  "session_id": 123,
  "photo_ids": [1, 2, 3, 4, 5],
  "processed_photo_ids": [1, 2, 3],
  "failed_photo_ids": [],
  "status": "paused",
  "created_at": "2025-11-09T10:00:00Z",
  "started_at": "2025-11-09T10:00:05Z",
  "paused_at": "2025-11-09T10:15:30Z",
  "completed_at": null,
  "total_photos": 5,
  "processed_count": 3,
  "failed_count": 0,
  "config": {
    "preset": "WhiteLayer_v4",
    "blend": 60
  },
  "task_ids": ["task1", "task2"]
}
```

## Batch Status Values

- `pending`: Batch created but not started
- `running`: Batch is actively processing
- `paused`: Batch is paused (can be resumed)
- `completed`: All photos processed successfully
- `failed`: Batch failed (check logs)
- `cancelled`: Batch was cancelled by user

## Best Practices

### 1. Regular Status Checks

```python
# Poll status every 5-10 seconds
while True:
    status = get_batch_status(batch_id)
    if status['status'] in ['completed', 'failed', 'cancelled']:
        break
    time.sleep(5)
```

### 2. Handle Interruptions

```python
# Always recover on startup
def on_startup():
    result = recover_interrupted_batches()
    
    # Resume or review paused batches
    batches = get_all_batches()
    for batch in batches:
        if batch['status'] == 'paused':
            # Review and decide whether to resume
            if should_resume(batch):
                resume_batch(batch['batch_id'])
```

### 3. Resource-Aware Processing

```python
# Pause during high load
if cpu_usage > 80:
    pause_batch(batch_id)
    wait_for_resources()
    resume_batch(batch_id)
```

### 4. Regular Cleanup

```python
# Schedule daily cleanup
import schedule

def cleanup_old_batches():
    cleanup_batches(days_old=7)

schedule.every().day.at("02:00").do(cleanup_old_batches)
```

## Troubleshooting

### Batch Won't Pause

**Problem**: `pause_batch()` returns error

**Solutions**:
1. Check batch exists: `GET /batch/{batch_id}/status`
2. Verify batch is in `running` state
3. Check logs for errors

### Batch Won't Resume

**Problem**: `resume_batch()` returns error

**Solutions**:
1. Verify batch is in `paused` state
2. Check if all photos are already processed
3. Review error logs

### State File Corruption

**Problem**: Batch state fails to load

**Solutions**:
1. Check JSON validity of state file
2. Delete corrupted file and restart batch
3. Restore from backup if available

## API Reference

### POST /batch/start
Start a new batch processing operation

**Request**:
```json
{
  "photo_ids": [1, 2, 3],
  "session_id": 123,
  "config": {}
}
```

**Response**:
```json
{
  "message": "Batch processing started",
  "batch_id": "batch_abc123",
  "photo_count": 3
}
```

### POST /batch/{batch_id}/pause
Pause a running batch

**Response**:
```json
{
  "message": "Batch paused successfully",
  "batch_id": "batch_abc123"
}
```

### POST /batch/{batch_id}/resume
Resume a paused batch

**Response**:
```json
{
  "message": "Batch resumed successfully",
  "batch_id": "batch_abc123"
}
```

### GET /batch/{batch_id}/status
Get batch status

**Response**:
```json
{
  "batch_id": "batch_abc123",
  "session_id": 123,
  "status": "running",
  "total_photos": 5,
  "processed_count": 3,
  "failed_count": 0,
  "progress_percent": 60.0,
  "created_at": "2025-11-09T10:00:00Z",
  "started_at": "2025-11-09T10:00:05Z",
  "paused_at": null,
  "completed_at": null
}
```

### GET /batch/list
List all active batches

**Response**:
```json
{
  "batches": [
    {
      "batch_id": "batch_abc123",
      "status": "running",
      "total_photos": 5,
      "processed_count": 3,
      "progress_percent": 60.0
    }
  ],
  "count": 1
}
```

### POST /batch/recover
Recover interrupted batches

**Response**:
```json
{
  "message": "Batch recovery completed",
  "recovered_count": 2,
  "failed_count": 0,
  "timestamp": "2025-11-09T10:30:00Z"
}
```

### POST /batch/cleanup
Clean up old completed batches

**Request**:
```json
{
  "days_old": 7
}
```

**Response**:
```json
{
  "message": "Batch cleanup completed",
  "cleaned_count": 5,
  "days_old": 7
}
```

## Integration with Other Systems

### With Job Queue

```python
# Batch controller automatically integrates with job queue
batch_id = start_batch(photo_ids=[1, 2, 3])

# Jobs are submitted to Celery queue
# Task IDs are tracked in batch state
```

### With Progress Reporter

```python
# Progress updates are automatically sent via WebSocket
# Clients can subscribe to batch progress events
```

### With Resource Manager

```python
# Batch processing respects resource limits
# Automatically pauses during high load
```

## Next Steps

1. Review the full documentation: `BATCH_CONTROL_IMPLEMENTATION.md`
2. Run the test suite: `pytest test_batch_controller.py -v`
3. Integrate with your application
4. Set up monitoring and alerts
5. Configure automatic recovery on startup

## Support

For issues or questions:
- Check logs in `local_bridge/logs/`
- Review state files in `local_bridge/data/batch_states/`
- Consult `BATCH_CONTROL_IMPLEMENTATION.md` for detailed information

---

**Requirements**: 11.4, 14.3  
**Version**: 1.0  
**Last Updated**: 2025-11-09
