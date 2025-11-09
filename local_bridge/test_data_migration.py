"""
Tests for Data Migration Tool
"""

import os
import sys
import json
import sqlite3
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_migration_tool import DataMigrationTool
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


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def source_db(temp_dir):
    """Create a source database with test data."""
    db_path = temp_dir / 'source.db'
    db_url = f'sqlite:///{db_path}'
    
    # Initialize database
    init_db(db_url, echo=False)
    session = get_session()
    
    # Add test data
    # Session
    test_session = Session(
        name='Test Session',
        import_folder='/test/folder',
        total_photos=10,
        processed_photos=5,
        status='developing'
    )
    session.add(test_session)
    session.flush()
    
    # Photos
    for i in range(5):
        photo = Photo(
            session_id=test_session.id,
            file_path=f'/test/photo_{i}.cr3',
            file_name=f'photo_{i}.cr3',
            file_size=1024000 + i * 1000,
            camera_make='Canon',
            camera_model='EOS R5',
            iso=100 + i * 100,
            ai_score=3.0 + i * 0.3,
            status='completed'
        )
        session.add(photo)
    
    session.flush()
    
    # Jobs
    job = Job(
        id='test-job-001',
        photo_id=1,
        priority=2,
        config_json='{"test": "config"}',
        status='completed'
    )
    session.add(job)
    
    # Presets
    preset = Preset(
        name='Test Preset',
        version='v1',
        config_template='{"test": "template"}'
    )
    preset.set_context_tags(['portrait', 'outdoor'])
    session.add(preset)
    
    # Statistics
    stat = Statistic(
        date=datetime.now(),
        session_id=test_session.id,
        total_imported=10,
        total_processed=5,
        success_rate=0.95
    )
    session.add(stat)
    
    # Learning data
    learning = LearningData(
        photo_id=1,
        action='approved',
        original_preset='Test Preset',
        final_preset='Test Preset'
    )
    learning.set_parameter_adjustments({'exposure': 0.5})
    session.add(learning)
    
    session.commit()
    session.close()
    
    return db_path


def test_create_backup(source_db, temp_dir):
    """Test backup creation."""
    tool = DataMigrationTool(
        source_db_path=str(source_db),
        backup_dir=str(temp_dir / 'backups')
    )
    
    backup_path = tool.create_backup()
    
    # Verify backup exists
    assert Path(backup_path).exists()
    
    # Verify metadata exists
    metadata_path = Path(backup_path).with_suffix('.json')
    assert metadata_path.exists()
    
    # Verify metadata content
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert 'checksum' in metadata
    assert 'timestamp' in metadata
    assert metadata['original_path'] == str(source_db)
    
    # Verify backup is identical to source
    assert Path(backup_path).stat().st_size == source_db.stat().st_size


def test_migrate_data(source_db, temp_dir):
    """Test data migration."""
    target_db = temp_dir / 'target.db'
    
    tool = DataMigrationTool(
        source_db_path=str(source_db),
        target_db_path=str(target_db),
        backup_dir=str(temp_dir / 'backups')
    )
    
    # Migrate data
    success = tool.migrate_data()
    assert success
    
    # Verify target database exists
    assert target_db.exists()
    
    # Verify data was migrated
    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()
    
    # Check sessions
    sessions_count = cursor.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    assert sessions_count == 1
    
    # Check photos
    photos_count = cursor.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
    assert photos_count == 5
    
    # Check jobs
    jobs_count = cursor.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    assert jobs_count == 1
    
    # Check presets
    presets_count = cursor.execute("SELECT COUNT(*) FROM presets").fetchone()[0]
    assert presets_count == 1
    
    # Check statistics
    stats_count = cursor.execute("SELECT COUNT(*) FROM statistics").fetchone()[0]
    assert stats_count == 1
    
    # Check learning data
    learning_count = cursor.execute("SELECT COUNT(*) FROM learning_data").fetchone()[0]
    assert learning_count == 1
    
    conn.close()


def test_verify_migration(source_db, temp_dir):
    """Test migration verification."""
    target_db = temp_dir / 'target.db'
    
    tool = DataMigrationTool(
        source_db_path=str(source_db),
        target_db_path=str(target_db),
        backup_dir=str(temp_dir / 'backups')
    )
    
    # Migrate data
    tool.migrate_data()
    
    # Verify migration
    results = tool.verify_migration()
    
    assert results['success']
    assert len(results['errors']) == 0
    
    # Check all tables
    for table in ['sessions', 'photos', 'jobs', 'presets', 'statistics', 'learning_data']:
        assert table in results['checks']
        assert results['checks'][table]['match']


def test_restore_from_backup(source_db, temp_dir):
    """Test database restore from backup."""
    tool = DataMigrationTool(
        source_db_path=str(source_db),
        backup_dir=str(temp_dir / 'backups')
    )
    
    # Create backup
    backup_path = tool.create_backup()
    
    # Modify source database
    conn = sqlite3.connect(source_db)
    conn.execute("DELETE FROM photos")
    conn.commit()
    conn.close()
    
    # Verify photos were deleted
    conn = sqlite3.connect(source_db)
    photos_count = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
    conn.close()
    assert photos_count == 0
    
    # Restore from backup
    success = tool.restore_from_backup(backup_path)
    assert success
    
    # Verify photos were restored
    conn = sqlite3.connect(source_db)
    photos_count = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
    conn.close()
    assert photos_count == 5


def test_migration_log(source_db, temp_dir):
    """Test migration log creation."""
    target_db = temp_dir / 'target.db'
    
    tool = DataMigrationTool(
        source_db_path=str(source_db),
        target_db_path=str(target_db),
        backup_dir=str(temp_dir / 'backups')
    )
    
    # Perform migration
    tool.create_backup()
    tool.migrate_data()
    tool.verify_migration()
    
    # Save log
    tool.save_migration_log()
    
    # Find log file
    log_files = list((temp_dir / 'backups').glob('migration_log_*.json'))
    assert len(log_files) > 0
    
    # Verify log content
    with open(log_files[0], 'r') as f:
        log_data = json.load(f)
    
    assert 'source_db' in log_data
    assert 'target_db' in log_data
    assert 'migration_log' in log_data
    assert 'verification_results' in log_data
    
    # Check migration steps
    steps = [entry['step'] for entry in log_data['migration_log']]
    assert 'backup' in steps
    assert 'migration' in steps
    assert 'verification' in steps


def test_foreign_key_integrity(source_db, temp_dir):
    """Test foreign key integrity after migration."""
    target_db = temp_dir / 'target.db'
    
    tool = DataMigrationTool(
        source_db_path=str(source_db),
        target_db_path=str(target_db),
        backup_dir=str(temp_dir / 'backups')
    )
    
    # Migrate data
    tool.migrate_data()
    
    # Verify foreign keys
    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()
    
    # Check photos -> sessions
    orphaned_photos = cursor.execute("""
        SELECT COUNT(*) FROM photos 
        WHERE session_id IS NOT NULL 
        AND session_id NOT IN (SELECT id FROM sessions)
    """).fetchone()[0]
    assert orphaned_photos == 0
    
    # Check jobs -> photos
    orphaned_jobs = cursor.execute("""
        SELECT COUNT(*) FROM jobs 
        WHERE photo_id IS NOT NULL 
        AND photo_id NOT IN (SELECT id FROM photos)
    """).fetchone()[0]
    assert orphaned_jobs == 0
    
    conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
