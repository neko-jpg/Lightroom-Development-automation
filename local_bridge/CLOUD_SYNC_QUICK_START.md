# Cloud Sync Quick Start Guide

## 5-Minute Setup

### Step 1: Install rclone

**Windows (PowerShell as Administrator):**
```powershell
choco install rclone
```

**macOS:**
```bash
brew install rclone
```

**Linux:**
```bash
curl https://rclone.org/install.sh | sudo bash
```

### Step 2: Configure Cloud Provider

Choose your provider and run the configuration:

**For Dropbox:**
```bash
rclone config create dropbox dropbox
```

**For Google Drive:**
```bash
rclone config create gdrive drive
```

**For OneDrive:**
```bash
rclone config create onedrive onedrive
```

Follow the interactive prompts to authorize access.

### Step 3: Test Connection

```bash
# List directories in your cloud storage
rclone lsd dropbox:

# Or for Google Drive
rclone lsd gdrive:
```

### Step 4: Use in Python

```python
from cloud_sync_manager import CloudSyncManager
import pathlib

# Configure
config = {
    'enabled': True,
    'provider': 'dropbox',  # or 'google_drive', 'onedrive'
    'remote_path': '/Photos/Processed'
}

# Initialize
manager = CloudSyncManager(config)

# Test connection
success, error = manager.test_connection()
print(f"Connection: {'OK' if success else f'Failed - {error}'}")

# Upload a file
file_path = pathlib.Path('D:/Export/SNS/photo.jpg')
job = manager.upload_file(file_path)

if job:
    # Process upload
    success, error = manager.process_upload_job(job.id)
    print(f"Upload: {'Success' if success else f'Failed - {error}'}")
```

## Common Use Cases

### Auto-Upload After Export

```python
from auto_export_engine import AutoExportEngine
from cloud_sync_manager import CloudSyncManager

# Initialize
export_engine = AutoExportEngine()
cloud_manager = CloudSyncManager({
    'enabled': True,
    'provider': 'dropbox',
    'remote_path': '/Photos/Processed'
})

# Export and upload
def export_and_sync(photo_id):
    # Export photo
    jobs = export_engine.trigger_auto_export(photo_id)
    
    for job in jobs:
        export_engine.process_export_job(job.id)
        
        # Upload to cloud
        if job.output_path:
            upload_job = cloud_manager.upload_file(
                pathlib.Path(job.output_path)
            )
            cloud_manager.process_upload_job(upload_job.id)
```

### Batch Upload

```python
# Upload multiple files
files = [
    pathlib.Path('D:/Export/SNS/photo_001.jpg'),
    pathlib.Path('D:/Export/SNS/photo_002.jpg'),
    pathlib.Path('D:/Export/SNS/photo_003.jpg')
]

jobs = manager.upload_batch(files)

# Process all uploads
result = manager.process_upload_queue(max_concurrent=3)
print(f"Uploaded {result['succeeded']} of {result['processed']} files")
```

### Monitor Progress

```python
import time

# Start upload
job = manager.upload_file(file_path)

# Monitor progress
while True:
    status = manager.get_upload_status(job.id)
    
    if status.status == 'completed':
        print("Upload complete!")
        break
    elif status.status == 'failed':
        print(f"Upload failed: {status.error_message}")
        break
    else:
        print(f"Progress: {status.progress_percent:.1f}%")
        time.sleep(1)
```

## Troubleshooting

### rclone not found

```bash
# Check if rclone is installed
rclone version

# If not found, add to PATH or reinstall
```

### Connection failed

```bash
# Verify rclone configuration
rclone config show

# Test connection manually
rclone lsd dropbox:

# Reconfigure if needed
rclone config
```

### Upload stuck

```python
# Check queue status
status = manager.get_queue_status()
print(f"Active uploads: {status['active_count']}")
print(f"Failed uploads: {status['failed_count']}")

# Retry failed uploads
manager.retry_all_failed_uploads()
```

## Configuration Options

```python
config = {
    'enabled': True,              # Enable/disable cloud sync
    'provider': 'dropbox',        # dropbox, google_drive, onedrive
    'remote_path': '/Photos/2024' # Remote directory path
}

manager = CloudSyncManager(config)

# Update configuration
manager.configure(
    enabled=True,
    provider='google_drive',
    remote_path='/Photos/Processed'
)
```

## Best Practices

1. **Test First**: Always test connection before production use
2. **Monitor Queue**: Check queue status regularly
3. **Handle Errors**: Implement proper error handling
4. **Batch Uploads**: Use batch operations for multiple files
5. **Limit Concurrent**: Keep concurrent uploads to 3-5
6. **Clear History**: Periodically clear completed uploads

## Next Steps

- Read [CLOUD_SYNC_IMPLEMENTATION.md](CLOUD_SYNC_IMPLEMENTATION.md) for detailed documentation
- See [example_cloud_sync_usage.py](example_cloud_sync_usage.py) for more examples
- Check [test_cloud_sync_manager.py](test_cloud_sync_manager.py) for test cases

## Support

For issues or questions:
1. Check rclone documentation: https://rclone.org/docs/
2. Review test cases for usage examples
3. Enable debug logging for troubleshooting
