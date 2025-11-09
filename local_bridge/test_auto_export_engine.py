"""
Test suite for Auto Export Engine

Tests the automatic export functionality including:
- Approval-triggered auto-export
- Multiple format simultaneous export
- Automatic filename generation
- Export queue management

Requirements: 6.1, 6.4
"""

import pytest
import pathlib
import tempfile
import shutil
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auto_export_engine import AutoExportEngine, ExportJob
from export_preset_manager import ExportPresetManager, ExportPreset
from models.database import Base, Photo, Session as DBSession


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = pathlib.Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def db_session(temp_dir):
    """Create a test database session"""
    db_path = temp_dir / "test.db"
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    engine.dispose()


@pytest.fixture
def preset_manager(temp_dir):
    """Create a test export preset manager"""
    presets_file = temp_dir / "test_presets.json"
    manager = ExportPresetManager(presets_file)
    return manager


@pytest.fixture
def auto_export_engine(preset_manager):
    """Create a test auto export engine"""
    return AutoExportEngine(preset_manager)


@pytest.fixture
def test_photo(db_session, temp_dir):
    """Create a test photo in the database"""
    # Create a test session
    session = DBSession(
        name="Test Session",
        import_folder=str(temp_dir),
        status='importing'
    )
    db_session.add(session)
    db_session.commit()
    
    # Create a test photo
    photo = Photo(
        session_id=session.id,
        file_path=str(temp_dir / "test_photo.cr3"),
        file_name="test_photo.cr3",
        file_size=1024000,
        import_time=datetime.now(),
        capture_time=datetime(2025, 11, 8, 14, 30, 0),
        camera_make="Canon",
        camera_model="EOS R5",
        iso=400,
        status='completed',
        approved=True,
        approved_at=datetime.now()
    )
    db_session.add(photo)
    db_session.commit()
    
    return photo


class TestAutoExportEngine:
    """Test suite for AutoExportEngine"""
    
    def test_initialization(self, auto_export_engine):
        """Test engine initialization"""
        assert auto_export_engine is not None
        assert auto_export_engine.preset_manager is not None
        assert len(auto_export_engine.export_queue) == 0
        assert len(auto_export_engine.processing_jobs) == 0
    
    def test_trigger_auto_export(self, auto_export_engine, test_photo, db_session):
        """Test triggering auto-export for an approved photo"""
        # Trigger auto-export
        jobs = auto_export_engine.trigger_auto_export(test_photo.id, db_session)
        
        # Should create jobs for all enabled presets
        assert len(jobs) > 0
        
        # Check job properties
        for job in jobs:
            assert job.photo_id == test_photo.id
            assert job.status == 'pending'
            assert job.created_at is not None
            assert job.preset_name is not None
        
        # Check queue
        assert len(auto_export_engine.export_queue) == len(jobs)
    
    def test_trigger_auto_export_not_approved(self, auto_export_engine, test_photo, db_session):
        """Test triggering auto-export for non-approved photo fails"""
        # Mark photo as not approved
        test_photo.approved = False
        db_session.commit()
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="not approved"):
            auto_export_engine.trigger_auto_export(test_photo.id, db_session)
    
    def test_trigger_auto_export_not_found(self, auto_export_engine, db_session):
        """Test triggering auto-export for non-existent photo fails"""
        # Should raise ValueError
        with pytest.raises(ValueError, match="not found"):
            auto_export_engine.trigger_auto_export(99999, db_session)
    
    def test_export_multiple_formats(self, auto_export_engine, test_photo, db_session):
        """Test exporting in multiple formats simultaneously"""
        # Get available presets
        presets = auto_export_engine.preset_manager.list_presets()
        preset_names = [p.name for p in presets[:3]]  # Use first 3 presets
        
        # Export in multiple formats
        jobs = auto_export_engine.export_multiple_formats(
            test_photo.id, 
            preset_names, 
            db_session
        )
        
        # Should create one job per preset
        assert len(jobs) == len(preset_names)
        
        # Check job properties
        for job, preset_name in zip(jobs, preset_names):
            assert job.photo_id == test_photo.id
            assert job.preset_name == preset_name
            assert job.status == 'pending'
    
    def test_generate_filename_basic(self, auto_export_engine, test_photo):
        """Test basic filename generation"""
        preset = ExportPreset(
            name="Test",
            enabled=True,
            format="JPEG",
            quality=85,
            max_dimension=2048,
            color_space="sRGB",
            destination="/tmp/export",
            filename_template="{date}_{sequence}"
        )
        
        filename = auto_export_engine.generate_filename(test_photo, preset, 1)
        
        # Should contain date and sequence
        assert "2025-11-08" in filename
        assert "0001" in filename
    
    def test_generate_filename_all_variables(self, auto_export_engine, test_photo):
        """Test filename generation with all template variables"""
        preset = ExportPreset(
            name="Test",
            enabled=True,
            format="JPEG",
            quality=85,
            max_dimension=2048,
            color_space="sRGB",
            destination="/tmp/export",
            filename_template="{year}_{month}_{day}_{time}_{original}_{preset}_{sequence}"
        )
        
        filename = auto_export_engine.generate_filename(test_photo, preset, 42)
        
        # Check all variables are replaced
        assert "2025" in filename
        assert "11" in filename
        assert "08" in filename
        assert "143000" in filename
        assert "test_photo" in filename
        assert "Test" in filename
        assert "0042" in filename
    
    def test_get_export_path(self, auto_export_engine, test_photo, temp_dir):
        """Test getting full export path"""
        preset = ExportPreset(
            name="Test",
            enabled=True,
            format="JPEG",
            quality=85,
            max_dimension=2048,
            color_space="sRGB",
            destination=str(temp_dir / "export"),
            filename_template="{date}_{sequence}"
        )
        
        export_path = auto_export_engine.get_export_path(test_photo, preset, 1)
        
        # Check path components
        assert export_path.parent == temp_dir / "export"
        assert export_path.suffix == ".jpg"
        assert "2025-11-08" in export_path.name
        
        # Check directory was created
        assert export_path.parent.exists()
    
    def test_get_export_path_conflict_resolution(self, auto_export_engine, test_photo, temp_dir):
        """Test filename conflict resolution"""
        preset = ExportPreset(
            name="Test",
            enabled=True,
            format="JPEG",
            quality=85,
            max_dimension=2048,
            color_space="sRGB",
            destination=str(temp_dir / "export"),
            filename_template="test"
        )
        
        # Create first file
        export_path1 = auto_export_engine.get_export_path(test_photo, preset)
        export_path1.parent.mkdir(parents=True, exist_ok=True)
        export_path1.touch()
        
        # Get path again - should resolve conflict
        export_path2 = auto_export_engine.get_export_path(test_photo, preset)
        
        # Should be different
        assert export_path1 != export_path2
        assert "_1" in export_path2.name
    
    def test_process_export_job(self, auto_export_engine, test_photo, db_session):
        """Test processing an export job"""
        # Create a job
        jobs = auto_export_engine.trigger_auto_export(test_photo.id, db_session)
        job = jobs[0]
        
        # Process the job
        success, error = auto_export_engine.process_export_job(job.id, db_session)
        
        # Should succeed
        assert success is True
        assert error is None
        
        # Job should be in processing
        assert job.id in auto_export_engine.processing_jobs
        assert job.status == 'processing'
        assert job.started_at is not None
        assert job.output_path is not None
    
    def test_complete_export_job(self, auto_export_engine, test_photo, db_session):
        """Test completing an export job"""
        # Create and process a job
        jobs = auto_export_engine.trigger_auto_export(test_photo.id, db_session)
        job = jobs[0]
        auto_export_engine.process_export_job(job.id, db_session)
        
        # Complete the job
        result = auto_export_engine.complete_export_job(job.id, True)
        
        # Should succeed
        assert result is True
        assert job.status == 'completed'
        assert job.completed_at is not None
        
        # Should be removed from processing
        assert job.id not in auto_export_engine.processing_jobs
    
    def test_complete_export_job_with_error(self, auto_export_engine, test_photo, db_session):
        """Test completing an export job with error"""
        # Create and process a job
        jobs = auto_export_engine.trigger_auto_export(test_photo.id, db_session)
        job = jobs[0]
        auto_export_engine.process_export_job(job.id, db_session)
        
        # Complete with error
        error_msg = "Export failed: disk full"
        result = auto_export_engine.complete_export_job(job.id, False, error_msg)
        
        # Should succeed
        assert result is True
        assert job.status == 'failed'
        assert job.error_message == error_msg
    
    def test_get_next_export_job(self, auto_export_engine, test_photo, db_session):
        """Test getting next export job from queue"""
        # Create multiple jobs
        jobs = auto_export_engine.trigger_auto_export(test_photo.id, db_session)
        
        # Get next job
        next_job = auto_export_engine.get_next_export_job()
        
        # Should return first job
        assert next_job is not None
        assert next_job.id == jobs[0].id
    
    def test_get_next_export_job_empty_queue(self, auto_export_engine):
        """Test getting next job from empty queue"""
        next_job = auto_export_engine.get_next_export_job()
        assert next_job is None
    
    def test_get_export_queue_status(self, auto_export_engine, test_photo, db_session):
        """Test getting export queue status"""
        # Create jobs
        jobs = auto_export_engine.trigger_auto_export(test_photo.id, db_session)
        
        # Process one job
        auto_export_engine.process_export_job(jobs[0].id, db_session)
        
        # Get status
        status = auto_export_engine.get_export_queue_status()
        
        # Check status
        assert status['pending_count'] == len(jobs) - 1
        assert status['processing_count'] == 1
        assert len(status['pending_jobs']) == len(jobs) - 1
        assert len(status['processing_jobs']) == 1
    
    def test_cancel_export_job(self, auto_export_engine, test_photo, db_session):
        """Test cancelling an export job"""
        # Create jobs
        jobs = auto_export_engine.trigger_auto_export(test_photo.id, db_session)
        job = jobs[0]
        
        # Cancel the job
        result = auto_export_engine.cancel_export_job(job.id)
        
        # Should succeed
        assert result is True
        
        # Job should be removed from queue
        assert job not in auto_export_engine.export_queue
    
    def test_cancel_processing_job_fails(self, auto_export_engine, test_photo, db_session):
        """Test that cancelling a processing job fails"""
        # Create and process a job
        jobs = auto_export_engine.trigger_auto_export(test_photo.id, db_session)
        job = jobs[0]
        auto_export_engine.process_export_job(job.id, db_session)
        
        # Try to cancel - should fail
        result = auto_export_engine.cancel_export_job(job.id)
        assert result is False
    
    def test_clear_export_queue(self, auto_export_engine, test_photo, db_session):
        """Test clearing export queue"""
        # Create jobs
        jobs = auto_export_engine.trigger_auto_export(test_photo.id, db_session)
        initial_count = len(jobs)
        
        # Clear queue
        cleared_count = auto_export_engine.clear_export_queue()
        
        # Should clear all jobs
        assert cleared_count == initial_count
        assert len(auto_export_engine.export_queue) == 0
    
    def test_get_export_config_for_lightroom(self, auto_export_engine, test_photo, db_session):
        """Test generating Lightroom export configuration"""
        # Create a job
        jobs = auto_export_engine.trigger_auto_export(test_photo.id, db_session)
        job = jobs[0]
        
        # Get Lightroom config
        config = auto_export_engine.get_export_config_for_lightroom(job.id, db_session)
        
        # Check config
        assert config is not None
        assert config['job_id'] == job.id
        assert config['photo_id'] == test_photo.id
        assert config['photo_path'] == test_photo.file_path
        assert 'export_path' in config
        assert 'format' in config
        assert 'quality' in config
        assert 'max_dimension' in config
        assert 'color_space' in config


class TestExportJob:
    """Test suite for ExportJob data class"""
    
    def test_export_job_creation(self):
        """Test creating an export job"""
        job = ExportJob(
            id="test123",
            photo_id=1,
            preset_name="SNS",
            status="pending",
            created_at=datetime.now().isoformat()
        )
        
        assert job.id == "test123"
        assert job.photo_id == 1
        assert job.preset_name == "SNS"
        assert job.status == "pending"
    
    def test_export_job_to_dict(self):
        """Test converting export job to dictionary"""
        job = ExportJob(
            id="test123",
            photo_id=1,
            preset_name="SNS",
            status="pending",
            created_at=datetime.now().isoformat()
        )
        
        job_dict = job.to_dict()
        
        assert job_dict['id'] == "test123"
        assert job_dict['photo_id'] == 1
        assert job_dict['preset_name'] == "SNS"
        assert job_dict['status'] == "pending"
    
    def test_export_job_from_dict(self):
        """Test creating export job from dictionary"""
        job_dict = {
            'id': "test123",
            'photo_id': 1,
            'preset_name': "SNS",
            'status': "pending",
            'created_at': datetime.now().isoformat()
        }
        
        job = ExportJob.from_dict(job_dict)
        
        assert job.id == "test123"
        assert job.photo_id == 1
        assert job.preset_name == "SNS"
        assert job.status == "pending"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
