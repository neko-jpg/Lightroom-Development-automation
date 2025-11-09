# Cloud Sync Integration Checklist

## Pre-Integration Requirements

### System Requirements
- [ ] Python 3.8+ installed
- [ ] rclone installed and in PATH
- [ ] Cloud provider account (Dropbox/Google Drive/OneDrive)
- [ ] rclone configured for cloud provider

### Verification Steps

```bash
# Check Python version
python --version

# Check rclone installation
rclone version

# List configured remotes
rclone listremotes

# Test remote connection
rclone lsd dropbox:
```

## Integration Steps

### 1. Install Dependencies

```bash
# No additional Python dependencies required
# cloud_sync_manager.py uses only standard library
```

### 2. Configure rclone

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

### 3. Update System Configuration

Edit `config/config.json`:

```json
{
  "export": {
    "cloud_sync": {
      "enabled": true,
      "provider": "dropbox",
      "remote_path": "/Photos/Processed"
    }
  }
}
```

### 4. Import Cloud Sync Manager

```python
from cloud_sync_manager import CloudSyncManager
from config_manager import ConfigManager

# Load configuration
config_mgr = ConfigManager()
config_mgr.load()

# Initialize cloud sync
cloud_config = config_mgr.get('export.cloud_sync')
cloud_manager = CloudSyncManager(cloud_config)
```

### 5. Integrate with Auto Export

```python
from auto_export_engine import AutoExportEngine
from cloud_sync_manager import CloudSyncManager

# Initialize components
export_engine = AutoExportEngine()
cloud_manager = CloudSyncManager(cloud_config)

# Export and upload workflow
def export_and_upload(photo_id):
    # Export photo
    export_jobs = export_engine.trigger_auto_export(photo_id)
    
    for export_job in export_jobs:
        # Process export
        success, error = export_engine.process_export_job(export_job.id)
        
        if success and export_job.output_path:
            # Upload to cloud
            output_path = pathlib.Path(export_job.output_path)
            upload_job = cloud_manager.upload_file(output_path)
            
            if upload_job:
                cloud_manager.process_upload_job(upload_job.id)
```

### 6. Add to Flask API

Add endpoints to `app.py`:

```python
from cloud_sync_manager import CloudSyncManager

# Initialize cloud sync manager
cloud_manager = CloudSyncManager(config['export']['cloud_sync'])

@app.route('/api/cloud/status', methods=['GET'])
def get_cloud_status():
    """Get cloud sync status"""
    status = cloud_manager.get_queue_status()
    return jsonify(status)

@app.route('/api/cloud/upload', methods=['POST'])
def upload_to_cloud():
    """Upload file to cloud"""
    data = request.json
    file_path = pathlib.Path(data['file_path'])
    
    job = cloud_manager.upload_file(file_path)
    
    if job:
        cloud_manager.process_upload_job(job.id)
        return jsonify({'success': True, 'job_id': job.id})
    else:
        return jsonify({'success': False, 'error': 'Failed to queue upload'}), 400

@app.route('/api/cloud/retry', methods=['POST'])
def retry_failed_uploads():
    """Retry all failed uploads"""
    count = cloud_manager.retry_all_failed_uploads()
    return jsonify({'success': True, 'retried': count})
```

## Testing Checklist

### Unit Tests
- [ ] Run unit tests: `pytest test_cloud_sync_manager.py -v`
- [ ] Verify all 32 tests pass
- [ ] Check test coverage

### Integration Tests
- [ ] Test with actual cloud provider
- [ ] Upload small test file
- [ ] Upload large file (>10MB)
- [ ] Test batch upload
- [ ] Test progress monitoring
- [ ] Test error handling
- [ ] Test retry logic

### Performance Tests
- [ ] Upload 10 files simultaneously
- [ ] Monitor memory usage
- [ ] Monitor network bandwidth
- [ ] Check upload speeds

## Verification Steps

### 1. Basic Upload Test

```python
from cloud_sync_manager import CloudSyncManager
import pathlib

config = {
    'enabled': True,
    'provider': 'dropbox',
    'remote_path': '/Photos/Test'
}

manager = CloudSyncManager(config)

# Test connection
success, error = manager.test_connection()
assert success, f"Connection failed: {error}"

# Upload test file
test_file = pathlib.Path('test.txt')
test_file.write_text('Test content')

job = manager.upload_file(test_file)
assert job is not None, "Failed to queue upload"

success, error = manager.process_upload_job(job.id)
assert success, f"Upload failed: {error}"

print("✓ Basic upload test passed")
```

### 2. Batch Upload Test

```python
# Create multiple test files
files = []
for i in range(3):
    f = pathlib.Path(f'test_{i}.txt')
    f.write_text(f'Test content {i}')
    files.append(f)

# Batch upload
jobs = manager.upload_batch(files)
assert len(jobs) == 3, "Failed to queue all files"

# Process queue
result = manager.process_upload_queue(max_concurrent=2)
assert result['succeeded'] == 3, f"Not all uploads succeeded: {result}"

print("✓ Batch upload test passed")
```

### 3. Error Handling Test

```python
# Test with non-existent file
job = manager.upload_file(pathlib.Path('/nonexistent/file.txt'))
assert job is None, "Should not queue non-existent file"

# Test retry logic
# (Simulate failure by disconnecting network, then retry)

print("✓ Error handling test passed")
```

## Post-Integration Checklist

### Functionality
- [ ] Cloud sync can be enabled/disabled
- [ ] Files upload successfully
- [ ] Progress is tracked accurately
- [ ] Failed uploads are retried
- [ ] Queue status is accurate
- [ ] Multiple providers work

### Performance
- [ ] Upload speed is acceptable
- [ ] Memory usage is reasonable
- [ ] CPU usage is low
- [ ] Network bandwidth is managed

### Error Handling
- [ ] Network errors are handled
- [ ] rclone errors are caught
- [ ] Retry logic works
- [ ] Failed uploads are tracked

### User Experience
- [ ] Upload progress is visible
- [ ] Errors are reported clearly
- [ ] Queue status is accessible
- [ ] Configuration is easy

## Monitoring

### Metrics to Track
- Upload success rate
- Average upload time
- Failed upload count
- Retry success rate
- Queue size
- Network bandwidth usage

### Logging

Enable appropriate logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# For debugging
logging.getLogger('cloud_sync_manager').setLevel(logging.DEBUG)
```

### Health Checks

```python
# Periodic health check
def check_cloud_sync_health():
    # Test connection
    success, error = cloud_manager.test_connection()
    
    if not success:
        logger.error(f"Cloud sync health check failed: {error}")
        return False
    
    # Check queue status
    status = cloud_manager.get_queue_status()
    
    if status['failed_count'] > 10:
        logger.warning(f"High number of failed uploads: {status['failed_count']}")
    
    return True
```

## Troubleshooting

### Common Issues

**Issue: rclone not found**
```bash
# Solution: Install rclone
choco install rclone  # Windows
brew install rclone   # macOS
```

**Issue: Connection failed**
```bash
# Solution: Reconfigure rclone
rclone config
```

**Issue: Uploads are slow**
```python
# Solution: Reduce concurrent uploads
manager.process_upload_queue(max_concurrent=2)
```

**Issue: High failure rate**
```python
# Solution: Check network and retry
manager.retry_all_failed_uploads()
```

## Rollback Plan

If integration causes issues:

1. Disable cloud sync in configuration:
   ```json
   {
     "export": {
       "cloud_sync": {
         "enabled": false
       }
     }
   }
   ```

2. Remove cloud sync calls from code

3. Restart application

4. Investigate issues

5. Re-enable when fixed

## Support Resources

- rclone documentation: https://rclone.org/docs/
- Cloud Sync Implementation: [CLOUD_SYNC_IMPLEMENTATION.md](CLOUD_SYNC_IMPLEMENTATION.md)
- Quick Start Guide: [CLOUD_SYNC_QUICK_START.md](CLOUD_SYNC_QUICK_START.md)
- Example Usage: [example_cloud_sync_usage.py](example_cloud_sync_usage.py)
- Unit Tests: [test_cloud_sync_manager.py](test_cloud_sync_manager.py)

## Sign-Off

- [ ] All pre-integration requirements met
- [ ] Integration steps completed
- [ ] All tests passing
- [ ] Verification steps completed
- [ ] Post-integration checklist complete
- [ ] Monitoring in place
- [ ] Documentation reviewed
- [ ] Team trained on new functionality

**Integration Date**: _________________

**Integrated By**: _________________

**Approved By**: _________________

**Notes**: _________________
