# Progress Reporting Quick Start Guide

## Overview

The real-time progress reporting system provides detailed updates on photo processing jobs through WebSocket connections. This enables the Lightroom plugin, GUI, and mobile apps to display live progress information to users.

**Requirements:** 4.5

## Features

- **Real-time Updates**: Progress updates sent via WebSocket to all connected clients
- **Stage Tracking**: Detailed tracking of each processing stage
- **Error Reporting**: Comprehensive error capture and transmission
- **Photo Information**: Send detailed photo metadata and analysis results
- **Multi-client Support**: Broadcast to multiple connected clients simultaneously

## Processing Stages

The system tracks the following processing stages:

1. `importing` - Importing photo files
2. `exif_analysis` - Analyzing EXIF metadata
3. `ai_evaluation` - AI-based quality evaluation
4. `context_detection` - Detecting shooting context
5. `preset_selection` - Selecting appropriate preset
6. `applying_preset` - Applying development settings
7. `quality_check` - Verifying applied settings
8. `exporting` - Exporting processed photos
9. `completed` - Job completed successfully
10. `failed` - Job failed

## Python API Usage

### Initialize Progress Reporter

```python
from progress_reporter import init_progress_reporter, get_progress_reporter, ProcessingStage
from websocket_server import get_websocket_server

# Initialize with WebSocket server
ws_server = get_websocket_server()
progress_reporter = init_progress_reporter(ws_server)
```

### Start Tracking a Job

```python
job_id = "job_12345"
photo_id = 456
photo_info = {
    'file_name': 'IMG_001.CR3',
    'file_path': '/path/to/IMG_001.CR3',
    'file_size': 25600000
}

progress_reporter.start_job(job_id, photo_id, photo_info)
```

### Update Progress

```python
# Update progress with stage and percentage
progress_reporter.update_progress(
    job_id=job_id,
    stage=ProcessingStage.EXIF_ANALYSIS,
    progress=25.0,
    message="Analyzing camera settings...",
    details={'camera': 'Canon EOS R5', 'iso': 800}
)
```

### Complete a Stage

```python
# Mark a stage as completed with results
progress_reporter.complete_stage(
    job_id=job_id,
    stage=ProcessingStage.EXIF_ANALYSIS,
    result={
        'iso': 800,
        'aperture': 2.8,
        'shutter_speed': '1/250',
        'focal_length': 85
    }
)
```

### Report Errors

```python
# Report an error during processing
progress_reporter.report_error(
    job_id=job_id,
    error_type='validation_error',
    error_message='Invalid exposure value',
    error_details={'field': 'exposure', 'value': 999},
    stage=ProcessingStage.APPLYING_PRESET
)
```

### Send Photo Information

```python
# Send detailed photo data
photo_data = {
    'exif': {
        'camera_make': 'Canon',
        'camera_model': 'EOS R5',
        'iso': 800,
        'aperture': 2.8
    },
    'ai_evaluation': {
        'score': 4.2,
        'focus_score': 4.5,
        'exposure_score': 4.0
    },
    'context': 'portrait_backlit'
}

progress_reporter.send_photo_info(job_id, photo_data)
```

### Complete Job

```python
# Complete job successfully
progress_reporter.complete_job(
    job_id=job_id,
    success=True,
    result={
        'preset_applied': 'WhiteLayer_Transparency_v4',
        'blend_amount': 60,
        'stages_completed': 8
    }
)

# Or complete with failure
progress_reporter.complete_job(
    job_id=job_id,
    success=False,
    result={'error': 'File not found'}
)
```

### Get Job Status

```python
# Get current status of a job
status = progress_reporter.get_job_status(job_id)

if status:
    print(f"Job {job_id}:")
    print(f"  Stage: {status['current_stage']}")
    print(f"  Progress: {status['progress']}%")
    print(f"  Elapsed: {status['elapsed_seconds']}s")
```

### Get All Active Jobs

```python
# Get all active jobs
active_jobs = progress_reporter.get_active_jobs()

for job_id, job_info in active_jobs.items():
    print(f"{job_id}: {job_info['progress']}% - {job_info['current_stage']}")
```

## Lua Plugin Usage

### Send Job Start

```lua
local WebSocketClient = require 'WebSocketClient'

local jobId = "job_12345"
local photoId = 456
local photoInfo = {
    file_name = "IMG_001.CR3",
    file_path = "/path/to/IMG_001.CR3"
}

WebSocketClient.sendJobStart(jobId, photoId, photoInfo)
```

### Send Progress Updates

```lua
-- Send progress update
WebSocketClient.sendJobProgress(
    jobId,
    'exif_analysis',  -- stage
    25,               -- progress (0-100)
    'Analyzing EXIF data...',  -- message
    {camera = 'Canon EOS R5'}  -- details
)
```

### Send Stage Completion

```lua
-- Mark stage as completed
WebSocketClient.sendStageComplete(
    jobId,
    'exif_analysis',
    {iso = 800, aperture = 2.8}  -- result
)
```

### Send Photo Information

```lua
-- Send detailed photo data
local photoData = {
    exif = {
        camera_make = 'Canon',
        camera_model = 'EOS R5',
        iso = 800
    },
    ai_score = 4.2
}

WebSocketClient.sendPhotoInfo(jobId, photoId, photoData)
```

### Send Error

```lua
-- Report an error
WebSocketClient.sendError(
    jobId,
    'processing_error',
    'Failed to apply settings',
    {detail = 'Invalid parameter value'},
    'applying_preset'  -- stage
)
```

### Send Job Completion

```lua
-- Complete job successfully
WebSocketClient.sendJobComplete(
    jobId,
    true,  -- success
    {preset_applied = 'WhiteLayer_v4'},  -- result
    15.5   -- duration in seconds
)

-- Or complete with failure
WebSocketClient.sendJobComplete(
    jobId,
    false,  -- success
    {error = 'File not found'},
    5.2
)
```

## REST API Endpoints

### Get Job Progress

```bash
GET /progress/job/{job_id}

Response:
{
  "success": true,
  "job_status": {
    "job_id": "job_12345",
    "photo_id": 456,
    "current_stage": "exif_analysis",
    "progress": 25.0,
    "elapsed_seconds": 5.2,
    "stages_completed": [...]
  }
}
```

### Get All Active Jobs

```bash
GET /progress/active

Response:
{
  "success": true,
  "active_jobs": {
    "job_12345": {...},
    "job_12346": {...}
  },
  "count": 2
}
```

### Report Progress (Manual)

```bash
POST /progress/report

Body:
{
  "job_id": "job_12345",
  "stage": "exif_analysis",
  "progress": 25.0,
  "message": "Analyzing EXIF data...",
  "details": {"camera": "Canon EOS R5"}
}
```

### Report Error

```bash
POST /progress/error

Body:
{
  "job_id": "job_12345",
  "error_type": "validation_error",
  "error_message": "Invalid configuration",
  "error_details": {"field": "exposure"},
  "stage": "applying_preset"
}
```

## WebSocket Message Format

### Job Started

```json
{
  "type": "job_started",
  "job_id": "job_12345",
  "photo_id": 456,
  "photo_info": {
    "file_name": "IMG_001.CR3"
  },
  "timestamp": "2025-11-09T10:30:00Z"
}
```

### Job Progress

```json
{
  "type": "job_progress",
  "job_id": "job_12345",
  "photo_id": 456,
  "stage": "exif_analysis",
  "progress": 25.0,
  "message": "Analyzing EXIF data...",
  "details": {"camera": "Canon EOS R5"},
  "timestamp": "2025-11-09T10:30:05Z"
}
```

### Stage Completed

```json
{
  "type": "stage_completed",
  "job_id": "job_12345",
  "photo_id": 456,
  "stage": "exif_analysis",
  "result": {
    "iso": 800,
    "aperture": 2.8
  },
  "timestamp": "2025-11-09T10:30:10Z"
}
```

### Photo Information

```json
{
  "type": "photo_info",
  "job_id": "job_12345",
  "photo_id": 456,
  "photo_data": {
    "exif": {...},
    "ai_evaluation": {...}
  },
  "timestamp": "2025-11-09T10:30:15Z"
}
```

### Error Occurred

```json
{
  "type": "error_occurred",
  "job_id": "job_12345",
  "photo_id": 456,
  "error_type": "validation_error",
  "error_message": "Invalid configuration",
  "error_details": {"field": "exposure"},
  "stage": "applying_preset",
  "timestamp": "2025-11-09T10:30:20Z"
}
```

### Job Completed

```json
{
  "type": "job_completed",
  "job_id": "job_12345",
  "photo_id": 456,
  "success": true,
  "result": {
    "preset_applied": "WhiteLayer_v4"
  },
  "duration": 15.5,
  "stages_completed": [...],
  "timestamp": "2025-11-09T10:30:25Z"
}
```

### Job Failed

```json
{
  "type": "job_failed",
  "job_id": "job_12345",
  "photo_id": 456,
  "success": false,
  "result": {
    "error": "File not found"
  },
  "duration": 5.2,
  "timestamp": "2025-11-09T10:30:30Z"
}
```

## Client-Side Integration

### JavaScript/React Example

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:5100/ws');

// Subscribe to job updates
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['jobs', 'photos']
  }));
};

// Handle incoming messages
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch(message.type) {
    case 'job_started':
      console.log(`Job ${message.job_id} started`);
      break;
      
    case 'job_progress':
      updateProgressBar(message.job_id, message.progress);
      updateStatusText(message.message);
      break;
      
    case 'stage_completed':
      console.log(`Stage ${message.stage} completed`);
      break;
      
    case 'job_completed':
      console.log(`Job ${message.job_id} completed in ${message.duration}s`);
      break;
      
    case 'error_occurred':
      showError(message.error_message);
      break;
  }
};
```

## Testing

Run the test suite:

```bash
cd local_bridge
pytest test_progress_reporter.py -v
```

## Troubleshooting

### Progress Updates Not Received

1. Check WebSocket connection status:
   ```bash
   curl http://localhost:5100/ws/status
   ```

2. Verify client is subscribed to correct channels

3. Check server logs for errors

### Job Not Found

- Ensure `start_job()` is called before other progress methods
- Verify job_id is consistent across all calls

### Missing Progress Updates

- Check that progress values are between 0-100
- Verify stage names match ProcessingStage enum values
- Ensure WebSocket server is initialized before progress reporter

## Best Practices

1. **Always start jobs** before reporting progress
2. **Use appropriate stages** for each processing step
3. **Include meaningful messages** for user feedback
4. **Report errors immediately** when they occur
5. **Complete jobs** even if they fail
6. **Include duration** in completion messages
7. **Send photo info** after analysis stages
8. **Use channels** to filter broadcasts appropriately

## Performance Considerations

- Progress updates are lightweight and non-blocking
- WebSocket broadcasts are asynchronous
- Failed broadcasts don't block job processing
- Job tracking uses minimal memory
- Consider cleanup of completed jobs after retention period

## Security Notes

- Progress data may contain sensitive photo information
- Ensure WebSocket connections are authenticated in production
- Consider encrypting WebSocket traffic (WSS)
- Limit access to progress endpoints based on user permissions

---

For more information, see:
- `progress_reporter.py` - Core implementation
- `websocket_server.py` - WebSocket server
- `test_progress_reporter.py` - Test examples
