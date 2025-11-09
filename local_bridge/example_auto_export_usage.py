"""
Example usage of Auto Export Engine

Demonstrates:
- Triggering auto-export after photo approval
- Exporting in multiple formats simultaneously
- Automatic filename generation
- Export queue management

Requirements: 6.1, 6.4
"""

import logging
from datetime import datetime
from pathlib import Path

from auto_export_engine import AutoExportEngine
from export_preset_manager import ExportPresetManager
from models.database import init_db, get_session, Photo, Session as DBSession

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_1_trigger_auto_export():
    """
    Example 1: Trigger auto-export after photo approval
    
    This is the most common use case - when a user approves a photo,
    automatically export it using all enabled presets.
    """
    print("\n=== Example 1: Trigger Auto-Export After Approval ===\n")
    
    # Initialize components
    preset_manager = ExportPresetManager()
    auto_export_engine = AutoExportEngine(preset_manager)
    
    # Get database session
    db_session = get_session()
    
    try:
        # Find an approved photo
        photo = db_session.query(Photo).filter(
            Photo.approved == True
        ).first()
        
        if not photo:
            print("No approved photos found. Please approve a photo first.")
            return
        
        print(f"Photo: {photo.file_name}")
        print(f"Approved at: {photo.approved_at}")
        
        # Trigger auto-export
        export_jobs = auto_export_engine.trigger_auto_export(photo.id, db_session)
        
        print(f"\n✓ Created {len(export_jobs)} export jobs:")
        for job in export_jobs:
            print(f"  - Job ID: {job.id}")
            print(f"    Preset: {job.preset_name}")
            print(f"    Status: {job.status}")
        
    finally:
        db_session.close()


def example_2_export_multiple_formats():
    """
    Example 2: Export a photo in multiple formats simultaneously
    
    Useful when you need specific export formats regardless of
    which presets are enabled.
    """
    print("\n=== Example 2: Export in Multiple Formats ===\n")
    
    # Initialize components
    preset_manager = ExportPresetManager()
    auto_export_engine = AutoExportEngine(preset_manager)
    
    # Get database session
    db_session = get_session()
    
    try:
        # Find a completed photo
        photo = db_session.query(Photo).filter(
            Photo.status == 'completed'
        ).first()
        
        if not photo:
            print("No completed photos found.")
            return
        
        print(f"Photo: {photo.file_name}")
        
        # Export in specific formats
        preset_names = ["SNS", "Print", "Web_Portfolio"]
        
        print(f"\nExporting in formats: {', '.join(preset_names)}")
        
        export_jobs = auto_export_engine.export_multiple_formats(
            photo.id,
            preset_names,
            db_session
        )
        
        print(f"\n✓ Created {len(export_jobs)} export jobs:")
        for job in export_jobs:
            print(f"  - {job.preset_name}: {job.id}")
        
    finally:
        db_session.close()


def example_3_filename_generation():
    """
    Example 3: Automatic filename generation
    
    Demonstrates how filenames are automatically generated based on
    template variables.
    """
    print("\n=== Example 3: Automatic Filename Generation ===\n")
    
    # Initialize components
    preset_manager = ExportPresetManager()
    auto_export_engine = AutoExportEngine(preset_manager)
    
    # Get database session
    db_session = get_session()
    
    try:
        # Find a photo
        photo = db_session.query(Photo).first()
        
        if not photo:
            print("No photos found.")
            return
        
        print(f"Photo: {photo.file_name}")
        print(f"Capture time: {photo.capture_time}")
        
        # Get presets
        presets = preset_manager.list_presets()
        
        print("\nGenerated filenames for each preset:")
        for preset in presets[:3]:  # Show first 3 presets
            filename = auto_export_engine.generate_filename(photo, preset, 1)
            export_path = auto_export_engine.get_export_path(photo, preset, 1)
            
            print(f"\n  Preset: {preset.name}")
            print(f"  Template: {preset.filename_template}")
            print(f"  Filename: {filename}")
            print(f"  Full path: {export_path}")
        
    finally:
        db_session.close()


def example_4_queue_management():
    """
    Example 4: Export queue management
    
    Shows how to monitor and manage the export queue.
    """
    print("\n=== Example 4: Export Queue Management ===\n")
    
    # Initialize components
    preset_manager = ExportPresetManager()
    auto_export_engine = AutoExportEngine(preset_manager)
    
    # Get database session
    db_session = get_session()
    
    try:
        # Create some export jobs
        photos = db_session.query(Photo).filter(
            Photo.approved == True
        ).limit(2).all()
        
        if not photos:
            print("No approved photos found.")
            return
        
        print("Creating export jobs...")
        for photo in photos:
            jobs = auto_export_engine.trigger_auto_export(photo.id, db_session)
            print(f"  ✓ Created {len(jobs)} jobs for {photo.file_name}")
        
        # Get queue status
        status = auto_export_engine.get_export_queue_status()
        
        print(f"\nQueue Status:")
        print(f"  Pending: {status['pending_count']}")
        print(f"  Processing: {status['processing_count']}")
        
        # Get next job
        next_job = auto_export_engine.get_next_export_job()
        
        if next_job:
            print(f"\nNext job to process:")
            print(f"  Job ID: {next_job.id}")
            print(f"  Photo ID: {next_job.photo_id}")
            print(f"  Preset: {next_job.preset_name}")
            
            # Process the job
            success, error = auto_export_engine.process_export_job(next_job.id, db_session)
            
            if success:
                print(f"  ✓ Job moved to processing")
                print(f"  Output path: {next_job.output_path}")
                
                # Simulate completion
                auto_export_engine.complete_export_job(next_job.id, True)
                print(f"  ✓ Job completed")
            else:
                print(f"  ✗ Failed to process job: {error}")
        
        # Get updated status
        status = auto_export_engine.get_export_queue_status()
        print(f"\nUpdated Queue Status:")
        print(f"  Pending: {status['pending_count']}")
        print(f"  Processing: {status['processing_count']}")
        
    finally:
        db_session.close()


def example_5_lightroom_integration():
    """
    Example 5: Lightroom integration workflow
    
    Shows how Lightroom would interact with the auto-export engine.
    """
    print("\n=== Example 5: Lightroom Integration Workflow ===\n")
    
    # Initialize components
    preset_manager = ExportPresetManager()
    auto_export_engine = AutoExportEngine(preset_manager)
    
    # Get database session
    db_session = get_session()
    
    try:
        # Simulate photo approval (would come from GUI)
        photo = db_session.query(Photo).filter(
            Photo.status == 'completed'
        ).first()
        
        if not photo:
            print("No completed photos found.")
            return
        
        print("Step 1: User approves photo in GUI")
        print(f"  Photo: {photo.file_name}")
        
        # Trigger auto-export
        export_jobs = auto_export_engine.trigger_auto_export(photo.id, db_session)
        print(f"\nStep 2: Auto-export triggered")
        print(f"  Created {len(export_jobs)} export jobs")
        
        # Lightroom polls for next job
        print("\nStep 3: Lightroom polls for next export job")
        next_job = auto_export_engine.get_next_export_job()
        
        if next_job:
            print(f"  Got job: {next_job.id}")
            
            # Get Lightroom export configuration
            config = auto_export_engine.get_export_config_for_lightroom(
                next_job.id,
                db_session
            )
            
            print(f"\nStep 4: Generate Lightroom export configuration")
            print(f"  Photo path: {config['photo_path']}")
            print(f"  Export path: {config['export_path']}")
            print(f"  Format: {config['format']}")
            print(f"  Quality: {config['quality']}%")
            print(f"  Max dimension: {config['max_dimension']}px")
            print(f"  Color space: {config['color_space']}")
            
            # Process the job
            success, error = auto_export_engine.process_export_job(next_job.id, db_session)
            
            print(f"\nStep 5: Lightroom executes export")
            print(f"  Status: Processing...")
            
            # Simulate Lightroom completing the export
            auto_export_engine.complete_export_job(next_job.id, True)
            
            print(f"\nStep 6: Export completed")
            print(f"  ✓ File exported to: {config['export_path']}")
        
    finally:
        db_session.close()


def example_6_error_handling():
    """
    Example 6: Error handling
    
    Demonstrates how to handle errors in the export process.
    """
    print("\n=== Example 6: Error Handling ===\n")
    
    # Initialize components
    preset_manager = ExportPresetManager()
    auto_export_engine = AutoExportEngine(preset_manager)
    
    # Get database session
    db_session = get_session()
    
    try:
        # Try to export a non-existent photo
        print("Test 1: Export non-existent photo")
        try:
            auto_export_engine.trigger_auto_export(99999, db_session)
            print("  ✗ Should have raised ValueError")
        except ValueError as e:
            print(f"  ✓ Caught expected error: {e}")
        
        # Try to export a non-approved photo
        print("\nTest 2: Export non-approved photo")
        photo = db_session.query(Photo).filter(
            Photo.approved == False
        ).first()
        
        if photo:
            try:
                auto_export_engine.trigger_auto_export(photo.id, db_session)
                print("  ✗ Should have raised ValueError")
            except ValueError as e:
                print(f"  ✓ Caught expected error: {e}")
        else:
            print("  (No non-approved photos to test)")
        
        # Simulate export failure
        print("\nTest 3: Handle export failure")
        photo = db_session.query(Photo).filter(
            Photo.approved == True
        ).first()
        
        if photo:
            jobs = auto_export_engine.trigger_auto_export(photo.id, db_session)
            if jobs:
                job = jobs[0]
                auto_export_engine.process_export_job(job.id, db_session)
                
                # Simulate failure
                error_msg = "Disk full - cannot write export file"
                auto_export_engine.complete_export_job(job.id, False, error_msg)
                
                print(f"  ✓ Job marked as failed")
                print(f"  Error: {job.error_message}")
        
    finally:
        db_session.close()


def main():
    """Run all examples"""
    print("=" * 60)
    print("Auto Export Engine - Example Usage")
    print("=" * 60)
    
    # Initialize database
    db_path = Path(__file__).parent / "data" / "junmai.db"
    if not db_path.exists():
        print("\nError: Database not found. Please run the system first.")
        return
    
    init_db(f'sqlite:///{db_path}')
    
    # Run examples
    try:
        example_1_trigger_auto_export()
        example_2_export_multiple_formats()
        example_3_filename_generation()
        example_4_queue_management()
        example_5_lightroom_integration()
        example_6_error_handling()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        logger.exception("Error running examples")
        print(f"\nError: {e}")


if __name__ == '__main__':
    main()
