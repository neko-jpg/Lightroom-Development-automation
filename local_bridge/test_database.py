"""
Test script to verify database functionality.
"""

import sys
import pathlib
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from models.database import (
    init_db,
    get_session,
    Session,
    Photo,
    Job,
    Preset,
    Statistic,
    LearningData
)


def test_database_operations():
    """Test basic database operations"""
    
    print("Testing database operations...")
    print("="*50)
    
    # Initialize database
    data_dir = pathlib.Path(__file__).parent / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    database_url = f'sqlite:///{data_dir}/junmai_test.db'
    
    print(f"\n1. Initializing test database: {database_url}")
    init_db(database_url, echo=False)
    print("   ✓ Database initialized")
    
    db = get_session()
    
    try:
        # Test 1: Create a session
        print("\n2. Creating a test session...")
        test_session = Session(
            name='Test Session 2025-11-08',
            import_folder='D:/Photos/Test',
            total_photos=0,
            processed_photos=0,
            status='importing'
        )
        db.add(test_session)
        db.commit()
        print(f"   ✓ Created session: {test_session}")
        
        # Test 2: Create a photo
        print("\n3. Creating a test photo...")
        test_photo = Photo(
            session_id=test_session.id,
            file_path='D:/Photos/Test/IMG_001.CR3',
            file_name='IMG_001.CR3',
            file_size=25000000,
            camera_make='Canon',
            camera_model='EOS R5',
            lens='RF 50mm F1.2',
            focal_length=50.0,
            aperture=1.2,
            shutter_speed='1/200',
            iso=100,
            capture_time=datetime.now(),
            status='imported'
        )
        db.add(test_photo)
        db.commit()
        print(f"   ✓ Created photo: {test_photo}")
        
        # Test 3: Create a job
        print("\n4. Creating a test job...")
        test_job = Job(
            id='test-job-001',
            photo_id=test_photo.id,
            priority=2,
            status='pending'
        )
        test_job.set_config({
            'version': '1.0',
            'pipeline': [
                {
                    'stage': 'base',
                    'settings': {
                        'Exposure2012': 0.5
                    }
                }
            ],
            'safety': {
                'snapshot': True,
                'dryRun': False
            }
        })
        db.add(test_job)
        db.commit()
        print(f"   ✓ Created job: {test_job}")
        print(f"   ✓ Job config: {test_job.get_config()}")
        
        # Test 4: Create a preset
        print("\n5. Creating a test preset...")
        test_preset = Preset(
            name='Test_Preset_v1',
            version='v1',
            blend_amount=70
        )
        test_preset.set_context_tags(['test', 'portrait'])
        test_preset.set_config_template({
            'version': '1.0',
            'pipeline': [
                {
                    'stage': 'base',
                    'settings': {
                        'Exposure2012': 0.0
                    }
                }
            ],
            'safety': {
                'snapshot': True,
                'dryRun': False
            }
        })
        db.add(test_preset)
        db.commit()
        print(f"   ✓ Created preset: {test_preset}")
        print(f"   ✓ Context tags: {test_preset.get_context_tags()}")
        
        # Test 5: Create statistics
        print("\n6. Creating test statistics...")
        test_stat = Statistic(
            date=datetime.now(),
            session_id=test_session.id,
            total_imported=10,
            total_selected=8,
            total_processed=5,
            total_exported=3,
            avg_processing_time=2.5,
            success_rate=0.95
        )
        test_stat.set_preset_usage({
            'Test_Preset_v1': 5
        })
        db.add(test_stat)
        db.commit()
        print(f"   ✓ Created statistic: {test_stat}")
        
        # Test 6: Create learning data
        print("\n7. Creating test learning data...")
        test_learning = LearningData(
            photo_id=test_photo.id,
            action='approved',
            original_preset='Test_Preset_v1',
            final_preset='Test_Preset_v1'
        )
        test_learning.set_parameter_adjustments({
            'Exposure2012': 0.1,
            'Highlights2012': -5
        })
        db.add(test_learning)
        db.commit()
        print(f"   ✓ Created learning data: {test_learning}")
        
        # Test 7: Query operations
        print("\n8. Testing query operations...")
        
        # Count records
        session_count = db.query(Session).count()
        photo_count = db.query(Photo).count()
        job_count = db.query(Job).count()
        preset_count = db.query(Preset).count()
        stat_count = db.query(Statistic).count()
        learning_count = db.query(LearningData).count()
        
        print(f"   ✓ Sessions: {session_count}")
        print(f"   ✓ Photos: {photo_count}")
        print(f"   ✓ Jobs: {job_count}")
        print(f"   ✓ Presets: {preset_count}")
        print(f"   ✓ Statistics: {stat_count}")
        print(f"   ✓ Learning data: {learning_count}")
        
        # Test relationships
        print("\n9. Testing relationships...")
        session_with_photos = db.query(Session).filter_by(id=test_session.id).first()
        print(f"   ✓ Session has {len(session_with_photos.photos)} photos")
        
        photo_with_jobs = db.query(Photo).filter_by(id=test_photo.id).first()
        print(f"   ✓ Photo has {len(photo_with_jobs.jobs)} jobs")
        print(f"   ✓ Photo has {len(photo_with_jobs.learning_data)} learning records")
        
        # Test photo.to_dict()
        print("\n10. Testing photo serialization...")
        photo_dict = test_photo.to_dict()
        print(f"   ✓ Photo serialized to dict with {len(photo_dict)} fields")
        
        print("\n" + "="*50)
        print("✓ All database tests passed!")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    test_database_operations()
