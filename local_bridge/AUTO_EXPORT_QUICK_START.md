# Auto Export Quick Start Guide

## Overview

The Auto Export Engine provides automatic export functionality that triggers after photo approval. It supports multiple format simultaneous export, automatic filename generation, and export queue management.

**Requirements:** 6.1, 6.4

## Key Features

1. **Approval-Triggered Auto-Export**: Automatically export photos when approved
2. **Multiple Format Export**: Export in multiple formats simultaneously
3. **Automatic Filename Generation**: Generate filenames based on templates
4. **Export Queue Management**: Manage pending and processing export jobs

## Quick Start

### 1. Basic Setup

```python
from auto_export_engine import AutoExportEngine
from export_preset_manager import ExportPresetManager

# Initialize components
preset_manager = ExportPresetManager()
auto_export_engine = AutoExportEngine(preset_manager)
```

### 2. Trigger Auto-Export After Approval

```python
from models.database import get_session

# Get database session
db_session = get_session()

try:
    # Trigger auto-export for an approved photo
    photo_id = 123
    export_jobs = auto_export_engine.trigger_auto_export(photo_id, db_session)
    
    print(f"Created {len(export_jobs)} export jobs")
    for job in export_jobs:
        print(f"  - {job.preset_name}: {job.id}")
        
finally:
    db_session.close()
```

### 3. Export in Multiple Formats

```python
# Export a photo in specific formats
photo_id = 123
preset_names = ["SNS", "Print", "Web_Portfolio"]

export_jobs = auto_export_engine.export_multiple_formats(
    photo_id,
    preset_names,
    db_session
)

print(f"Created {len(export_jobs)} export jobs")
```

### 4. Manage Export Queue

```python
# Get queue status
status = auto_export_engine.get_export_queue_status()
print(f"Pending: {status['pending_count']}")
print(f"Processing: {status['processing_count']}")

# Get next job
next_job = auto_export_engine.get_next_export_job()
if next_job:
    print(f"Next job: {next_job.id} - {next_job.preset_name}")
    
    # Process the job
    success, error = auto_export_engine.process_export_job(next_job.id, db_session)
    
    if success:
        # Simulate Lightroom completing the export
        auto_export_engine.complete_export_job(next_job.id, True)
```

## API Endpoints

### Trigger Auto-Export

```bash
POST /export/auto/trigger
Content-Type: application/json

{
  "photo_id": 123
}
```

**Response:**
```json
{
  "success": true,
  "message": "Created 3 export jobs",
  "job_count": 3,
  "jobs": [
    {
      "id": "abc123",
      "photo_id": 123,
      "preset_name": "SNS",
      "status": "pending",
      "created_at": "2025-11-08T14:30:00"
    }
  ]
}
```

### Export Multiple Formats

```bash
POST /export/auto/multiple
Content-Type: application/json

{
  "photo_id": 123,
  "preset_names": ["SNS", "Print", "Web_Portfolio"]
}
```

### Get Export Queue Status

```bash
GET /export/auto/queue
```

**Response:**
```json
{
  "success": true,
  "pending_count": 5,
  "processing_count": 1,
  "pending_jobs": [...],
  "processing_jobs": [...]
}
```

### Get Next Export Job

```bash
GET /export/auto/job/next
```

**Response:**
```json
{
  "success": true,
  "job": {
    "id": "abc123",
    "photo_id": 123,
    "preset_name": "SNS",
    "status": "processing",
    "output_path": "D:/Export/SNS/2025-11-08_0001.jpg"
  },
  "config": {
    "job_id": "abc123",
    "photo_id": 123,
    "photo_path": "D:/Photos/IMG_1234.CR3",
    "export_path": "D:/Export/SNS/2025-11-08_0001.jpg",
    "format": "JPEG",
    "quality": 85,
    "max_dimension": 2048,
    "color_space": "sRGB"
  }
}
```

### Complete Export Job

```bash
POST /export/auto/job/{job_id}/complete
Content-Type: application/json

{
  "success": true
}
```

### Cancel Export Job

```bash
POST /export/auto/job/{job_id}/cancel
```

### Clear Export Queue

```bash
POST /export/auto/queue/clear
```

## Photo Approval Endpoints

### Approve Photo (with Auto-Export)

```bash
POST /photos/{photo_id}/approve
Content-Type: application/json

{
  "auto_export": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Photo approved successfully",
  "photo": {...},
  "export_jobs": [...]
}
```

### Reject Photo

```bash
POST /photos/{photo_id}/reject
Content-Type: application/json

{
  "reason": "Out of focus"
}
```

### Get Approval Queue

```bash
GET /photos/approval/queue?limit=50&offset=0
```

**Response:**
```json
{
  "success": true,
  "photos": [...],
  "count": 12,
  "total_count": 45,
  "limit": 50,
  "offset": 0
}
```

## Filename Templates

The auto-export engine supports the following template variables for automatic filename generation:

- `{date}`: Capture date (YYYY-MM-DD)
- `{time}`: Capture time (HHMMSS)
- `{sequence}`: Sequence number (4 digits, e.g., 0001)
- `{original}`: Original filename (without extension)
- `{year}`: Year (YYYY)
- `{month}`: Month (MM)
- `{day}`: Day (DD)
- `{preset}`: Preset name

### Example Templates

```python
# Date and sequence
"{date}_{sequence}"
# Output: 2025-11-08_0001.jpg

# Full timestamp with original name
"{year}{month}{day}_{time}_{original}"
# Output: 20251108_143000_IMG_1234.jpg

# Preset-specific naming
"{preset}_{date}_{sequence}"
# Output: SNS_2025-11-08_0001.jpg

# Client delivery format
"{year}_{month}_{day}_{original}_{preset}"
# Output: 2025_11_08_IMG_1234_Client_Delivery.jpg
```

## Workflow Integration

### Typical Workflow

1. **Photo Processing**: Photo is processed and marked as 'completed'
2. **User Approval**: User reviews and approves the photo
3. **Auto-Export Trigger**: System automatically creates export jobs for all enabled presets
4. **Queue Management**: Export jobs are queued and processed in order
5. **Lightroom Export**: Lightroom polls for next job and executes export
6. **Completion**: Job is marked as completed and removed from queue

### Lightroom Integration

```lua
-- Lightroom Lua plugin polls for export jobs
function pollForExportJobs()
    local response = LrHttp.get("http://localhost:5100/export/auto/job/next")
    
    if response.success and response.job then
        local config = response.config
        
        -- Execute export using Lightroom SDK
        local exportSession = LrExportSession({
            photosToExport = {findPhotoById(config.photo_id)},
            exportSettings = {
                LR_format = config.format,
                LR_jpeg_quality = config.quality / 100,
                LR_size_maxWidth = config.max_dimension,
                LR_size_maxHeight = config.max_dimension,
                LR_export_destinationPathPrefix = config.export_path
            }
        })
        
        exportSession:doExportOnCurrentTask()
        
        -- Report completion
        LrHttp.post("http://localhost:5100/export/auto/job/" .. config.job_id .. "/complete", {
            success = true
        })
    end
end
```

## Error Handling

### Common Errors

1. **Photo Not Found**
   - Error: `Photo not found: photo_id=123`
   - Solution: Verify photo exists in database

2. **Photo Not Approved**
   - Error: `Photo not approved: photo_id=123`
   - Solution: Approve photo before triggering export

3. **Preset Not Found**
   - Error: `Preset not found: SNS`
   - Solution: Verify preset exists and is configured

4. **Export Failure**
   - Error: `Export failed: disk full`
   - Solution: Check disk space and export destination

### Error Handling Example

```python
try:
    export_jobs = auto_export_engine.trigger_auto_export(photo_id, db_session)
except ValueError as e:
    print(f"Validation error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Testing

Run the test suite:

```bash
pytest test_auto_export_engine.py -v
```

Run example usage:

```bash
python example_auto_export_usage.py
```

## Configuration

Auto-export behavior can be configured through export presets:

```python
from export_preset_manager import ExportPreset

# Create a custom export preset
preset = ExportPreset(
    name="Custom_Export",
    enabled=True,
    format="JPEG",
    quality=90,
    max_dimension=3000,
    color_space="sRGB",
    destination="D:/Export/Custom",
    filename_template="{date}_{time}_{original}",
    sharpen_for_screen=True,
    sharpen_amount=40,
    watermark_enabled=True,
    watermark_text="© 2025 Your Name"
)

# Add to preset manager
preset_manager.add_preset(preset)
preset_manager.save()
```

## Best Practices

1. **Enable Only Needed Presets**: Only enable presets you regularly use to avoid unnecessary exports
2. **Use Descriptive Templates**: Use filename templates that make files easy to identify
3. **Monitor Queue**: Regularly check export queue status to ensure smooth operation
4. **Handle Errors**: Always handle errors gracefully and log failures
5. **Test First**: Test export settings with a few photos before batch processing

## Troubleshooting

### Export Jobs Not Created

- Check if presets are enabled: `preset_manager.get_enabled_presets()`
- Verify photo is approved: `photo.approved == True`
- Check logs for errors

### Filename Conflicts

- The system automatically resolves conflicts by appending `_1`, `_2`, etc.
- Use unique filename templates to minimize conflicts

### Slow Export Processing

- Check system resources (CPU, disk I/O)
- Reduce number of enabled presets
- Increase export quality settings may slow processing

## Support

For issues or questions:
- Check logs: `logs/main.log`, `logs/errors.log`
- Run tests: `pytest test_auto_export_engine.py -v`
- Review examples: `python example_auto_export_usage.py`

## Related Documentation

- [Export Preset Management](EXPORT_PRESET_QUICK_START.md)
- [Progress Reporting](PROGRESS_REPORTING_QUICK_START.md)
- [Batch Control](BATCH_CONTROL_QUICK_START.md)
