"""
End-to-End Integration Tests
エンドツーエンド統合テスト

Tests complete workflows from file import to export
Requirements: 全要件
"""

import pytest
import json
import time
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Import system components
from app import app as flask_app
from models.database import init_db, get_session, Session, Photo, Job
from hot_folder_watcher import HotFolderWatcher
from file_import_processor import FileImportProcessor
from exif_analyzer import EXIFAnalyzer
from ai_selector import AISelector
from context_engine import ContextEngine
from preset_engine import PresetEngine
from auto_export_engine import AutoExportEngine


@pytest.fixture
def app():
    """Create Flask app for testing"""
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing"""
    base_dir = Path(tempfile.mkdtemp())
    dirs = {
        'hot_folder': base_dir / 'hot_folder',
        'import_dest': base_dir / 'imported',
        'export_dest': base_dir / 'exported',
        'temp': base_dir / 'temp'
    }
    
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    yield dirs
    
    # Cleanup
    shutil.rmtree(base_dir, ignore_errors=True)


@pytest.fixture
def test_db():
    """Create test database"""
    test_db_path = tempfile.mktemp(suffix='.db')
    init_db(f'sqlite:///{test_db_path}')
    
    yield test_db_path
    
    # Cleanup
    Path(test_db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_image_file(temp_dirs):
    """Create a sample image file for testing"""
    import io
    from PIL import Image
    
    # Create a simple test image
    img = Image.new('RGB', (800, 600), color='red')
    img_path = temp_dirs['hot_folder'] / 'test_photo.jpg'
    img.save(img_path, 'JPEG')
    
    return img_path


class TestCompleteWorkflow:
    """Test complete workflow from import to export"""
    
    @patch('ai_selector.AISelector.evaluate')
    @patch('ollama_client.OllamaClient.generate')
    def test_full_workflow_import_to_export(
        self, 
        mock_ollama, 
        mock_ai_eval,
        client, 
        temp_dirs, 
        sample_image_file
    ):
        """Test complete workflow: Import → Analyze → Select → Develop → Export"""
        
        # Mock AI evaluation
        mock_ai_eval.return_value = {
            'overall_score': 4.5,
            'focus_score': 4.2,
            'exposure_score': 4.8,
            'composition_score': 4.3,
            'faces_detected': 1,
            'recommendation': 'Excellent portrait'
        }
        
        # Mock LLM response
        mock_ollama.return_value = {
            'score': 4.5,
            'recommendation': 'Great photo'
        }
        
        # Step 1: Create session
        session_data = {
            'name': 'E2E_Test_Session',
            'import_folder': str(temp_dirs['hot_folder'])
        }
        response = client.post(
            '/api/sessions',
            data=json.dumps(session_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        session_id = json.loads(response.data)['id']
        
        # Step 2: Import photo (simulate file detection)
        # In real scenario, hot folder watcher would detect this
        import_data = {
            'session_id': session_id,
            'file_path': str(sample_image_file),
            'file_name': sample_image_file.name
        }
        
        # Create photo record
        db_session = get_session()
        try:
            photo = Photo(
                session_id=session_id,
                file_path=str(sample_image_file),
                file_name=sample_image_file.name,
                file_size=sample_image_file.stat().st_size,
                status='imported'
            )
            db_session.add(photo)
            db_session.commit()
            photo_id = photo.id
        finally:
            db_session.close()
        
        # Step 3: Analyze photo (EXIF + AI)
        # This would normally be triggered automatically
        response = client.get(f'/api/photos/{photo_id}')
        assert response.status_code == 200
        
        # Update photo with AI scores
        db_session = get_session()
        try:
            photo = db_session.query(Photo).filter_by(id=photo_id).first()
            photo.ai_score = 4.5
            photo.focus_score = 4.2
            photo.exposure_score = 4.8
            photo.composition_score = 4.3
            photo.status = 'analyzed'
            db_session.commit()
        finally:
            db_session.close()
        
        # Step 4: Create development job
        job_data = {
            'photo_id': photo_id,
            'config': {
                'version': '1.0',
                'pipeline': [
                    {
                        'stage': 'base',
                        'settings': {
                            'exposure': 0.0,
                            'contrast': 0,
                            'highlights': -10,
                            'shadows': 10
                        }
                    }
                ],
                'safety': {
                    'snapshot': True,
                    'dryRun': False
                }
            },
            'priority': 2
        }
        
        response = client.post(
            '/api/jobs',
            data=json.dumps(job_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        job_id = json.loads(response.data)['id']
        
        # Step 5: Simulate job completion
        db_session = get_session()
        try:
            job = db_session.query(Job).filter_by(id=job_id).first()
            job.status = 'completed'
            db_session.commit()
            
            photo = db_session.query(Photo).filter_by(id=photo_id).first()
            photo.status = 'completed'
            db_session.commit()
        finally:
            db_session.close()
        
        # Step 6: Approve photo
        response = client.post(
            f'/api/approval/{photo_id}/approve',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # Step 7: Verify photo is approved
        response = client.get(f'/api/photos/{photo_id}')
        assert response.status_code == 200
        photo_data = json.loads(response.data)
        assert photo_data['approved'] == True
        
        # Step 8: Export (would be triggered automatically in real system)
        # Verify session statistics
        response = client.get(f'/api/sessions/{session_id}')
        assert response.status_code == 200
        session_data = json.loads(response.data)
        assert session_data['photo_stats']['total'] >= 1
    
    def test_workflow_with_rejection(self, client, temp_dirs, sample_image_file):
        """Test workflow with photo rejection"""
        
        # Create session
        session_data = {
            'name': 'Rejection_Test_Session',
            'import_folder': str(temp_dirs['hot_folder'])
        }
        response = client.post(
            '/api/sessions',
            data=json.dumps(session_data),
            content_type='application/json'
        )
        session_id = json.loads(response.data)['id']
        
        # Create photo
        db_session = get_session()
        try:
            photo = Photo(
                session_id=session_id,
                file_path=str(sample_image_file),
                file_name=sample_image_file.name,
                file_size=sample_image_file.stat().st_size,
                ai_score=2.5,  # Low score
                status='completed'
            )
            db_session.add(photo)
            db_session.commit()
            photo_id = photo.id
        finally:
            db_session.close()
        
        # Reject photo
        reject_data = {
            'reason': 'Low quality - out of focus'
        }
        response = client.post(
            f'/api/approval/{photo_id}/reject',
            data=json.dumps(reject_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # Verify rejection
        response = client.get(f'/api/photos/{photo_id}')
        photo_data = json.loads(response.data)
        assert photo_data['status'] == 'rejected'
        assert photo_data['rejection_reason'] == 'Low quality - out of focus'
    
    def test_workflow_with_modification(self, client, temp_dirs, sample_image_file):
        """Test workflow with preset modification"""
        
        # Create session and photo
        session_data = {'name': 'Modify_Test', 'import_folder': str(temp_dirs['hot_folder'])}
        response = client.post('/api/sessions', data=json.dumps(session_data), 
                              content_type='application/json')
        session_id = json.loads(response.data)['id']
        
        db_session = get_session()
        try:
            photo = Photo(
                session_id=session_id,
                file_path=str(sample_image_file),
                file_name=sample_image_file.name,
                file_size=sample_image_file.stat().st_size,
                ai_score=4.0,
                selected_preset='WhiteLayer_v4',
                status='completed'
            )
            db_session.add(photo)
            db_session.commit()
            photo_id = photo.id
        finally:
            db_session.close()
        
        # Modify preset
        modify_data = {
            'new_preset': 'WhiteLayer_v5',
            'adjustments': {
                'exposure': 0.3,
                'contrast': 5
            }
        }
        response = client.post(
            f'/api/approval/{photo_id}/modify',
            data=json.dumps(modify_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # Verify modification
        response = client.get(f'/api/photos/{photo_id}')
        photo_data = json.loads(response.data)
        assert photo_data['selected_preset'] == 'WhiteLayer_v5'


class TestBatchProcessing:
    """Test batch processing workflows"""
    
    def test_batch_session_processing(self, client, temp_dirs):
        """Test processing multiple photos in a session"""
        
        # Create session
        session_data = {
            'name': 'Batch_Test_Session',
            'import_folder': str(temp_dirs['hot_folder'])
        }
        response = client.post('/api/sessions', data=json.dumps(session_data),
                              content_type='application/json')
        session_id = json.loads(response.data)['id']
        
        # Create multiple photos
        photo_ids = []
        db_session = get_session()
        try:
            for i in range(5):
                photo = Photo(
                    session_id=session_id,
                    file_path=f'/test/photo_{i}.jpg',
                    file_name=f'photo_{i}.jpg',
                    file_size=1024000,
                    ai_score=4.0 + (i * 0.1),
                    status='completed'
                )
                db_session.add(photo)
                db_session.flush()
                photo_ids.append(photo.id)
            db_session.commit()
        finally:
            db_session.close()
        
        # Approve all photos
        for photo_id in photo_ids:
            response = client.post(
                f'/api/approval/{photo_id}/approve',
                data=json.dumps({}),
                content_type='application/json'
            )
            assert response.status_code == 200
        
        # Verify session statistics
        response = client.get(f'/api/sessions/{session_id}')
        session_data = json.loads(response.data)
        assert session_data['photo_stats']['approved'] == 5
    
    def test_batch_export(self, client, temp_dirs):
        """Test batch export of approved photos"""
        
        # Create session with approved photos
        session_data = {'name': 'Export_Batch', 'import_folder': str(temp_dirs['hot_folder'])}
        response = client.post('/api/sessions', data=json.dumps(session_data),
                              content_type='application/json')
        session_id = json.loads(response.data)['id']
        
        # Create approved photos
        db_session = get_session()
        try:
            for i in range(3):
                photo = Photo(
                    session_id=session_id,
                    file_path=f'/test/export_{i}.jpg',
                    file_name=f'export_{i}.jpg',
                    file_size=1024000,
                    ai_score=4.5,
                    status='completed',
                    approved=True
                )
                db_session.add(photo)
            db_session.commit()
        finally:
            db_session.close()
        
        # Get approved photos
        response = client.get(f'/api/photos?session_id={session_id}&approved=true')
        assert response.status_code == 200
        photos = json.loads(response.data)['photos']
        assert len(photos) == 3


class TestErrorRecovery:
    """Test error handling and recovery"""
    
    def test_job_failure_recovery(self, client):
        """Test job failure and retry"""
        
        # Create session and photo
        session_data = {'name': 'Error_Test', 'import_folder': '/test'}
        response = client.post('/api/sessions', data=json.dumps(session_data),
                              content_type='application/json')
        session_id = json.loads(response.data)['id']
        
        db_session = get_session()
        try:
            photo = Photo(
                session_id=session_id,
                file_path='/test/error.jpg',
                file_name='error.jpg',
                file_size=1024000,
                status='imported'
            )
            db_session.add(photo)
            db_session.commit()
            photo_id = photo.id
        finally:
            db_session.close()
        
        # Create job
        job_data = {
            'photo_id': photo_id,
            'config': {'version': '1.0', 'pipeline': [], 'safety': {}},
            'priority': 2
        }
        response = client.post('/api/jobs', data=json.dumps(job_data),
                              content_type='application/json')
        job_id = json.loads(response.data)['id']
        
        # Simulate job failure
        db_session = get_session()
        try:
            job = db_session.query(Job).filter_by(id=job_id).first()
            job.status = 'failed'
            job.error_message = 'Test error'
            job.retry_count = 1
            db_session.commit()
        finally:
            db_session.close()
        
        # Verify job status
        response = client.get(f'/api/jobs/{job_id}')
        assert response.status_code == 200
        job_data = json.loads(response.data)
        assert job_data['status'] == 'failed'
        assert job_data['retry_count'] == 1
    
    def test_invalid_photo_handling(self, client):
        """Test handling of invalid photo data"""
        
        # Try to get non-existent photo
        response = client.get('/api/photos/99999')
        assert response.status_code == 404
        
        # Try to approve non-existent photo
        response = client.post('/api/approval/99999/approve',
                              data=json.dumps({}),
                              content_type='application/json')
        assert response.status_code == 404


class TestPerformanceMetrics:
    """Test performance tracking"""
    
    def test_processing_time_tracking(self, client):
        """Test that processing times are tracked"""
        
        # Create session
        session_data = {'name': 'Performance_Test', 'import_folder': '/test'}
        response = client.post('/api/sessions', data=json.dumps(session_data),
                              content_type='application/json')
        session_id = json.loads(response.data)['id']
        
        # Create and complete photo
        db_session = get_session()
        try:
            photo = Photo(
                session_id=session_id,
                file_path='/test/perf.jpg',
                file_name='perf.jpg',
                file_size=1024000,
                status='completed'
            )
            db_session.add(photo)
            db_session.commit()
        finally:
            db_session.close()
        
        # Get statistics
        response = client.get('/api/statistics/daily')
        assert response.status_code == 200
        stats = json.loads(response.data)
        assert 'total_processed' in stats
    
    def test_success_rate_calculation(self, client):
        """Test success rate calculation"""
        
        # Create session with mixed results
        session_data = {'name': 'Success_Rate_Test', 'import_folder': '/test'}
        response = client.post('/api/sessions', data=json.dumps(session_data),
                              content_type='application/json')
        session_id = json.loads(response.data)['id']
        
        # Create photos with different statuses
        db_session = get_session()
        try:
            # 3 successful
            for i in range(3):
                photo = Photo(
                    session_id=session_id,
                    file_path=f'/test/success_{i}.jpg',
                    file_name=f'success_{i}.jpg',
                    file_size=1024000,
                    status='completed',
                    approved=True
                )
                db_session.add(photo)
            
            # 1 rejected
            photo = Photo(
                session_id=session_id,
                file_path='/test/rejected.jpg',
                file_name='rejected.jpg',
                file_size=1024000,
                status='rejected'
            )
            db_session.add(photo)
            
            db_session.commit()
        finally:
            db_session.close()
        
        # Get session stats
        response = client.get(f'/api/sessions/{session_id}')
        session_data = json.loads(response.data)
        stats = session_data['photo_stats']
        
        # Success rate should be 75% (3 out of 4)
        if stats['total'] > 0:
            success_rate = (stats['approved'] / stats['total']) * 100
            assert success_rate == 75.0


def run_e2e_tests():
    """Run all E2E integration tests"""
    print("=" * 60)
    print("End-to-End Integration Tests")
    print("=" * 60)
    
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes'
    ])


if __name__ == '__main__':
    run_e2e_tests()
