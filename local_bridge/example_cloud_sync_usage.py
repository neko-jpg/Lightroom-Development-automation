"""
Example Usage of Cloud Sync Manager

This script demonstrates various use cases for the Cloud Sync Manager,
including basic uploads, batch operations, progress monitoring, and error handling.

Requirements: 6.3
"""

import logging
import pathlib
import time
from cloud_sync_manager import CloudSyncManager, get_cloud_sync_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_1_basic_upload():
    """Example 1: Basic file upload"""
    print("\n" + "="*60)
    print("Example 1: Basic File Upload")
    print("="*60)
    
    # Configure cloud sync
    config = {
        'enabled': True,
        'provider': 'dropbox',  # Change to your provider
        'remote_path': '/Photos/Test'
    }
    
    manager = CloudSyncManager(config)
    
    # Check if enabled
    if not manager.is_enabled():
        print("❌ Cloud sync is not enabled or rclone is not available")
        print("   Please install rclone and configure your cloud provider")
        return
    
    print(f"✓ Cloud sync enabled: {manager.provider.value}")
    
    # Test connection
    print("\nTesting connection...")
    success, error = manager.test_connection()
    
    if success:
        print("✓ Connection successful")
    else:
        print(f"❌ Connection failed: {error}")
        return
    
    # Create a test file (in real usage, this would be an exported photo)
    test_file = pathlib.Path("test_upload.txt")
    test_file.write_text("This is a test file for cloud sync")
    
    try:
        # Upload file
        print(f"\nUploading file: {test_file}")
        job = manager.upload_file(test_file)
        
        if job:
            print(f"✓ Upload queued: job_id={job.id}")
            print(f"  Local: {job.local_path}")
            print(f"  Remote: {job.remote_path}")
            
            # Process upload
            print("\nProcessing upload...")
            success, error = manager.process_upload_job(job.id)
            
            if success:
                print("✓ Upload completed successfully")
            else:
                print(f"❌ Upload failed: {error}")
        else:
            print("❌ Failed to queue upload")
    
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


def example_2_batch_upload():
    """Example 2: Batch file upload"""
    print("\n" + "="*60)
    print("Example 2: Batch File Upload")
    print("="*60)
    
    config = {
        'enabled': True,
        'provider': 'dropbox',
        'remote_path': '/Photos/Batch'
    }
    
    manager = CloudSyncManager(config)
    
    if not manager.is_enabled():
        print("❌ Cloud sync is not enabled")
        return
    
    # Create multiple test files
    test_files = []
    for i in range(3):
        test_file = pathlib.Path(f"test_batch_{i}.txt")
        test_file.write_text(f"Test file {i}")
        test_files.append(test_file)
    
    try:
        # Batch upload
        print(f"\nUploading {len(test_files)} files...")
        jobs = manager.upload_batch(test_files, remote_subpath='2024/01')
        
        print(f"✓ Queued {len(jobs)} files for upload")
        
        # Process queue
        print("\nProcessing upload queue...")
        result = manager.process_upload_queue(max_concurrent=2)
        
        print(f"\nResults:")
        print(f"  Processed: {result['processed']}")
        print(f"  Succeeded: {result['succeeded']}")
        print(f"  Failed: {result['failed']}")
        print(f"  Pending: {result['pending']}")
    
    finally:
        # Cleanup
        for test_file in test_files:
            if test_file.exists():
                test_file.unlink()


def example_3_progress_monitoring():
    """Example 3: Upload progress monitoring"""
    print("\n" + "="*60)
    print("Example 3: Progress Monitoring")
    print("="*60)
    
    config = {
        'enabled': True,
        'provider': 'dropbox',
        'remote_path': '/Photos/Progress'
    }
    
    manager = CloudSyncManager(config)
    
    if not manager.is_enabled():
        print("❌ Cloud sync is not enabled")
        return
    
    # Create a larger test file
    test_file = pathlib.Path("test_large.txt")
    test_file.write_text("Large file content\n" * 10000)
    
    try:
        # Upload file
        print(f"\nUploading file: {test_file}")
        job = manager.upload_file(test_file)
        
        if job:
            print(f"✓ Upload queued: job_id={job.id}")
            
            # Start upload in background (in real usage, this would be async)
            print("\nMonitoring progress...")
            
            # Simulate progress monitoring
            for i in range(5):
                status = manager.get_upload_status(job.id)
                
                if status:
                    print(f"  Status: {status.status}")
                    print(f"  Progress: {status.progress_percent:.1f}%")
                    
                    if status.status in ['completed', 'failed']:
                        break
                
                time.sleep(1)
            
            # Get final status
            final_status = manager.get_upload_status(job.id)
            
            if final_status and final_status.status == 'completed':
                print("\n✓ Upload completed successfully")
            else:
                print(f"\n❌ Upload failed or incomplete")
    
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


def example_4_error_handling():
    """Example 4: Error handling and retry"""
    print("\n" + "="*60)
    print("Example 4: Error Handling and Retry")
    print("="*60)
    
    config = {
        'enabled': True,
        'provider': 'dropbox',
        'remote_path': '/Photos/Retry'
    }
    
    manager = CloudSyncManager(config)
    
    if not manager.is_enabled():
        print("❌ Cloud sync is not enabled")
        return
    
    # Get queue status
    print("\nQueue Status:")
    status = manager.get_queue_status()
    print(f"  Pending: {status['pending_count']}")
    print(f"  Active: {status['active_count']}")
    print(f"  Completed: {status['completed_count']}")
    print(f"  Failed: {status['failed_count']}")
    
    # Retry failed uploads
    if status['failed_count'] > 0:
        print(f"\nRetrying {status['failed_count']} failed uploads...")
        count = manager.retry_all_failed_uploads()
        print(f"✓ Queued {count} uploads for retry")
    else:
        print("\n✓ No failed uploads to retry")
    
    # Clear completed uploads
    if status['completed_count'] > 0:
        print(f"\nClearing {status['completed_count']} completed uploads...")
        count = manager.clear_completed_uploads()
        print(f"✓ Cleared {count} completed uploads")


def example_5_configuration():
    """Example 5: Configuration management"""
    print("\n" + "="*60)
    print("Example 5: Configuration Management")
    print("="*60)
    
    # Initial configuration
    config = {
        'enabled': True,
        'provider': 'dropbox',
        'remote_path': '/Photos/Initial'
    }
    
    manager = CloudSyncManager(config)
    
    print("\nInitial Configuration:")
    print(f"  Enabled: {manager.enabled}")
    print(f"  Provider: {manager.provider.value}")
    print(f"  Remote Path: {manager.remote_path}")
    
    # Update configuration
    print("\nUpdating configuration...")
    success = manager.configure(
        enabled=True,
        provider='google_drive',
        remote_path='/Photos/Updated'
    )
    
    if success:
        print("✓ Configuration updated")
        print(f"  New Provider: {manager.provider.value}")
        print(f"  New Remote Path: {manager.remote_path}")
    else:
        print("❌ Configuration update failed")
    
    # Test new configuration
    if manager.is_enabled():
        print("\nTesting new configuration...")
        success, error = manager.test_connection()
        
        if success:
            print("✓ Connection successful with new configuration")
        else:
            print(f"❌ Connection failed: {error}")


def example_6_integration_with_export():
    """Example 6: Integration with Auto Export Engine"""
    print("\n" + "="*60)
    print("Example 6: Integration with Auto Export")
    print("="*60)
    
    print("\nThis example shows how to integrate cloud sync with auto export:")
    print("""
    from auto_export_engine import AutoExportEngine
    from cloud_sync_manager import CloudSyncManager
    
    # Initialize components
    export_engine = AutoExportEngine()
    cloud_manager = CloudSyncManager({
        'enabled': True,
        'provider': 'dropbox',
        'remote_path': '/Photos/Processed'
    })
    
    # Export and upload workflow
    def export_and_upload(photo_id):
        # 1. Trigger export
        export_jobs = export_engine.trigger_auto_export(photo_id)
        
        for export_job in export_jobs:
            # 2. Process export
            success, error = export_engine.process_export_job(export_job.id)
            
            if success and export_job.output_path:
                # 3. Upload to cloud
                output_path = pathlib.Path(export_job.output_path)
                upload_job = cloud_manager.upload_file(output_path)
                
                if upload_job:
                    # 4. Process upload
                    cloud_manager.process_upload_job(upload_job.id)
                    print(f"Uploaded: {output_path.name}")
    
    # Use in approval workflow
    def on_photo_approved(photo_id):
        export_and_upload(photo_id)
    """)


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Cloud Sync Manager - Example Usage")
    print("="*60)
    
    print("\nNote: These examples require rclone to be installed and configured.")
    print("If rclone is not available, some examples will be skipped.")
    
    # Run examples
    try:
        example_1_basic_upload()
        example_2_batch_upload()
        example_3_progress_monitoring()
        example_4_error_handling()
        example_5_configuration()
        example_6_integration_with_export()
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60)
    
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")


if __name__ == '__main__':
    main()
