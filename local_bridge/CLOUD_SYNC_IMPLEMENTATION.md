# Cloud Sync Implementation

## Overview

The Cloud Sync Manager provides automatic cloud storage synchronization for exported photos using rclone. It supports multiple cloud providers (Dropbox, Google Drive, OneDrive) with robust error handling and retry logic.

## Features

- **rclone Integration**: Uses rclone for reliable cloud storage operations
- **Multi-Provider Support**: Dropbox, Google Drive, OneDrive
- **Upload Progress Tracking**: Real-time progress monitoring for uploads
- **Error Retry Logic**: Automatic retry with exponential backoff
- **Batch Operations**: Upload multiple files simultaneously
- **Queue Management**: FIFO queue with status tracking

## Requirements

### System Requirements

- Python 3.8+
- rclone installed and configured

### Installing rclone

**Windows:**
```powershell
# Using Chocolatey
choco install rclone

# Or download from https://rclone.org/downloads/
```

**macOS:**
```bash
brew install rclone
```

**Linux:**
```bash
curl https://rclone.org/install.sh | sudo bash
```

### Configuring rclone

Configure rclone for your cloud provider:

```bash
# Interactive configuration
rclone config

# For Dropbox
rclone config create dropbox dropbox

# For Google Drive
rclone config create gdrive drive

# For OneDrive
rclone config create onedrive onedrive
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Cloud Sync Manager                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │ Upload Queue │───▶│ Active Jobs  │                  │
│  └──────────────┘    └──────────────┘                  │
│         │                    │                          │
│         │                    ▼                          │
│         │            ┌──────────────┐                  │
│         │            │   rclone     │                  │
│         │            │  Integration │                  │
│         │            └──────────────┘                  │
│         │                    │                          │
│         ▼                    ▼                          │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │   Failed     │    │  Completed   │                  │
│  │   Uploads    │    │   Uploads    │                  │
│  └──────────────┘    └──────────────┘                  │
│         │                                                │
│         │ (Retry)                                       │
│         └────────────────────┐                          │
│                              │                          │
└──────────────────────────────┼──────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Cloud Storage       │
                    │  - Dropbox           │
                    │  - Google Drive      │
                    │  - OneDrive          │
                    └──────────────────────┘
```

## Usage

### Basic Usage

```python
from cloud_sync_manager import CloudSyncManager
import pathlib

# Initialize manager
config = {
    'enabled': True,
    'provider': 'dropbox',
    'remote_path': '/Photos/Processed'
}

manager = CloudSyncManager(config)

# Upload a file
local_file = pathlib.Path('D:/Export/SNS/photo_001.jpg')
job = manager.upload_file(local_file)

if job:
    print(f"Upload queued: {job.id}")
    
    # Process the upload
    success, error = manager.process_upload_job(job.id)
    
    if success:
        print("Upload completed successfully")
    else:
        print(f"Upload failed: {error}")
```

### Batch Upload

```python
# Upload multiple files
files = [
    pathlib.Path('D:/Export/SNS/photo_001.jpg'),
    pathlib.Path('D:/Export/SNS/photo_002.jpg'),
    pathlib.Path('D:/Export/SNS/photo_003.jpg')
]

jobs = manager.upload_batch(files, remote_subpath='2024/01')

print(f"Queued {len(jobs)} files for upload")

# Process queue
result = manager.process_upload_queue(max_concurrent=3)
print(f"Processed: {result['processed']}, Succeeded: {result['succeeded']}, Failed: {result['failed']}")
```

### Progress Monitoring

```python
# Get upload status
job_id = "abc123"
job = manager.get_upload_status(job_id)

if job:
    print(f"Status: {job.status}")
    print(f"Progress: {job.progress_percent:.1f}%")
    print(f"Uploaded: {job.bytes_uploaded} / {job.file_size} bytes")

# Get queue status
status = manager.get_queue_status()
print(f"Pending: {status['pending_count']}")
print(f"Active: {status['active_count']}")
print(f"Completed: {status['completed_count']}")
print(f"Failed: {status['failed_count']}")
```

### Error Handling and Retry

```python
# Retry a failed upload
job_id = "failed_job_123"
success = manager.retry_failed_upload(job_id)

if success:
    print("Job queued for retry")

# Retry all failed uploads
count = manager.retry_all_failed_uploads()
print(f"Queued {count} failed uploads for retry")
```

### Configuration Management

```python
# Update configuration
manager.configure(
    enabled=True,
    provider='google_drive',
    remote_path='/Photos/2024'
)

# Test connection
success, error = manager.test_connection()

if success:
    print("Connection successful")
else:
    print(f"Connection failed: {error}")
```

## Integration with Auto Export

```python
from auto_export_engine import AutoExportEngine
from cloud_sync_manager import CloudSyncManager
from export_preset_manager import ExportPresetManager

# Initialize components
preset_manager = ExportPresetManager()
export_engine = AutoExportEngine(preset_manager)

cloud_config = {
    'enabled': True,
    'provider': 'dropbox',
    'remote_path': '/Photos/Processed'
}
cloud_manager = CloudSyncManager(cloud_config)

# Export and upload workflow
def export_and_upload(photo_id):
    # Trigger export
    export_jobs = export_engine.trigger_auto_export(photo_id)
    
    for export_job in export_jobs:
        # Process export
        success, error = export_engine.process_export_job(export_job.id)
        
        if success:
            # Upload to cloud
            output_path = pathlib.Path(export_job.output_path)
            upload_job = cloud_manager.upload_file(output_path)
            
            if upload_job:
                # Process upload
                cloud_manager.process_upload_job(upload_job.id)
```

## API Reference

### CloudSyncManager

#### Methods

- `__init__(config)`: Initialize manager with configuration
- `is_enabled()`: Check if cloud sync is enabled
- `configure(enabled, provider, remote_path)`: Update configuration
- `upload_file(local_path, remote_subpath)`: Queue file for upload
- `upload_batch(local_paths, remote_subpath)`: Queue multiple files
- `process_upload_job(job_id)`: Process a single upload job
- `process_upload_queue(max_concurrent)`: Process upload queue
- `get_upload_status(job_id)`: Get status of an upload job
- `get_queue_status()`: Get overall queue status
- `cancel_upload(job_id)`: Cancel a pending upload
- `retry_failed_upload(job_id)`: Retry a failed upload
- `retry_all_failed_uploads()`: Retry all failed uploads
- `clear_completed_uploads()`: Clear completed upload history
- `test_connection()`: Test connection to cloud storage

### UploadJob

#### Properties

- `id`: Unique job identifier
- `local_path`: Path to local file
- `remote_path`: Path in cloud storage
- `provider`: Cloud provider name
- `status`: Current status (pending, uploading, completed, failed, retrying, cancelled)
- `file_size`: File size in bytes
- `bytes_uploaded`: Bytes uploaded so far
- `progress_percent`: Upload progress percentage
- `retry_count`: Number of retry attempts
- `error_message`: Error message if failed

## Error Handling

### Retry Logic

The manager implements exponential backoff for failed uploads:

1. **First retry**: 2 seconds delay
2. **Second retry**: 4 seconds delay
3. **Third retry**: 8 seconds delay
4. **Max delay**: 60 seconds

After 3 failed attempts, the job is moved to the failed queue.

### Common Errors

**rclone not found:**
```
Error: rclone is not installed or not in PATH
Solution: Install rclone and ensure it's in your system PATH
```

**Connection failed:**
```
Error: Connection test failed
Solution: Check rclone configuration and internet connection
```

**File not found:**
```
Error: Local file not found
Solution: Verify the file path exists before uploading
```

## Performance Considerations

### Concurrent Uploads

- Default: 3 concurrent uploads
- Recommended: 3-5 for optimal performance
- Higher values may cause rate limiting

### Network Bandwidth

- Monitor network usage during uploads
- Consider scheduling uploads during off-peak hours
- Use batch operations for efficiency

### Storage Quotas

- Check cloud storage quota before large uploads
- Monitor remaining space
- Implement quota checking in production

## Security

### Credentials

- rclone stores credentials securely
- Never commit rclone config to version control
- Use environment variables for sensitive data

### Data Privacy

- Files are encrypted during transfer (TLS)
- Cloud providers may scan uploaded content
- Consider client-side encryption for sensitive data

## Troubleshooting

### Debug Mode

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### Check rclone Configuration

```bash
# List configured remotes
rclone listremotes

# Test remote connection
rclone lsd dropbox:

# Check rclone version
rclone version
```

### Common Issues

**Issue: Uploads are slow**
- Check network connection
- Reduce concurrent uploads
- Check cloud provider rate limits

**Issue: Uploads fail intermittently**
- Check internet stability
- Increase retry count
- Check cloud provider status

**Issue: Progress not updating**
- rclone may buffer progress updates
- Check rclone version (update if old)
- Monitor rclone process directly

## Best Practices

1. **Test Configuration**: Always test connection before production use
2. **Monitor Queue**: Regularly check queue status and clear completed uploads
3. **Handle Failures**: Implement proper error handling and user notifications
4. **Batch Operations**: Use batch uploads for multiple files
5. **Resource Management**: Limit concurrent uploads to avoid overwhelming the system
6. **Logging**: Enable appropriate logging for debugging
7. **Retry Strategy**: Use the built-in retry logic for transient failures

## Requirements Mapping

This implementation satisfies **Requirement 6.3**:

> WHEN 書き出しが完了した場合、THE System SHALL 指定されたクラウドストレージ（Dropbox、Google Drive等）へ自動アップロードする

- ✅ rclone integration for cloud storage operations
- ✅ Dropbox/Google Drive/OneDrive support
- ✅ Upload progress tracking and management
- ✅ Error retry logic with exponential backoff
- ✅ Batch upload operations
- ✅ Queue management with status tracking

## Future Enhancements

- [ ] Resume interrupted uploads
- [ ] Bandwidth throttling
- [ ] Upload scheduling
- [ ] Conflict resolution
- [ ] Incremental sync
- [ ] Multi-destination uploads
- [ ] Compression before upload
- [ ] Client-side encryption

## License

Part of Junmai AutoDev System
© 2025 All Rights Reserved
