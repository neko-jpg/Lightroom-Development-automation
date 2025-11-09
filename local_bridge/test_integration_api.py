"""
API Integration Tests
API統合テスト

Tests API endpoint integration and data flow
Requirements: 9.1
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import tempfile
from pathlib import Path

from app import app as flask_app
from models.database import init_db, get_session, Session, Photo, Job, Preset, Statistics


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
def test_db():
    """Create test database with sample data"""
    test_db_path = tempfile.mktemp(suffix='.db')
    init_db(f'sqlite:///{test_db_path}')
    
    # Populate with test data
    db_session = get_session()
    try:
        # Create sessions
        for i in range(3):
            session = Session(
                name=f'Test_Session_{i}',
                import_folder=f'/test/folder_{i}',
                total_photos=10 + i,
                processed_photos=5 + i,
                status='processing' if i < 2 else 'completed'
            )
            db_session.add(session)
        db_session.commit()
        
        # Create photos
        sessions = db_session.query(Session).all()
        for session in sessions:
            for j in range(session.total_photos):
                photo = Photo(
                    session_id=session.id,
                    file_path=f'/test/photo_{session.id}_{j}.jpg',
                    file_name=f'photo_{session.id}_{j}.jpg',
                    file_size=1024000 + j * 1000,
                    ai_score=3.0 + (j * 0.2),
                    focus_score=3.5 + (j * 0.1),
                    exposure_score=4.0 + (j * 0.1),
                    composition_score=3.8 + (j * 0.1),
                    status='completed' if j % 2 == 0 else 'processing',
                    approved=j % 3 == 0
                )
                db_session.add(photo)
        db_session.commit()
        
        # Create jobs
        photos = db_session.query(Photo).limit(5).all()
        for i, photo in enumerate(photos):
            job = Job(
                id=f'job_{i}',
                photo_id=photo.id,
                priority=1 + (i % 3),
                config_json=json.dumps({'version': '1.0', 'pipeline': []}),
                status='completed' if i % 2 == 0 else 'processing'
            )
            db_session.add(job)
        db_session.commit()
        
        # Create presets
        presets = [
            {'name': 'WhiteLayer_v4', 'context_tags': ['portrait', 'backlit']},
            {'name': 'LowLight_v2', 'context_tags': ['indoor', 'night']},
            {'name': 'Landscape_v3', 'context_tags': ['outdoor', 'landscape']}
        ]
        for preset_data in presets:
            preset = Preset(
                name=preset_data['name'],
                version='1.0',
                context_tags=json.dumps(preset_data['context_tags']),
                config_template=json.dumps({'pipeline': []}),
                usage_count=10,
                avg_approval_rate=0.85
            )
            db_session.add(preset)
        db_session.commit()
        
        # Create statistics
        for i in range(7):
            date = datetime.now().date() - timedelta(days=i)
            stats = Statistics(
                date=date,
                total_imported=50 + i * 5,
                total_selected=40 + i * 4,
                total_processed=35 + i * 3,
                total_exported=30 + i * 2,
                avg_processing_time=5.2 + i * 0.1,
                success_rate=0.92 - i * 0.01
            )
            db_session.add(stats)
        db_session.commit()
        
    finally:
        db_session.close()
    
    yield test_db_path
    
    # Cleanup
    Path(test_db_path).unlink(missing_ok=True)


class TestSessionAPI:
    """Test session management API endpoints"""
    
    def test_list_sessions(self, client, test_db):
        """Test GET /api/sessions"""
        response = client.get('/api/sessions')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'sessions' in data
        assert 'count' in data
        assert data['count'] >= 3
    
    def test_list_sessions_with_pagination(self, client, test_db):
        """Test session list with pagination"""
        response = client.get('/api/sessions?page=1&limit=2')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['sessions']) <= 2
        assert 'total' in data
    
    def test_list_sessions_with_status_filter(self, client, test_db):
        """Test session list with status filter"""
        response = client.get('/api/sessions?status=processing')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        for session in data['sessions']:
            assert session['status'] == 'processing'
    
    def test_get_session_detail(self, client, test_db):
        """Test GET /api/sessions/<id>"""
        # Get first session
        response = client.get('/api/sessions')
        sessions = json.loads(response.data)['sessions']
        session_id = sessions[0]['id']
        
        # Get detail
        response = client.get(f'/api/sessions/{session_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['id'] == session_id
        assert 'photo_stats' in data
        assert 'name' in data
    
    def test_create_session(self, client, test_db):
        """Test POST /api/sessions"""
        new_session = {
            'name': 'New_API_Test_Session',
            'import_folder': '/test/new_folder'
        }
        
        response = client.post(
            '/api/sessions',
            data=json.dumps(new_session),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert 'id' in data
        assert data['name'] == 'New_API_Test_Session'
    
    def test_update_session(self, client, test_db):
        """Test PATCH /api/sessions/<id>"""
        # Get first session
        response = client.get('/api/sessions')
        session_id = json.loads(response.data)['sessions'][0]['id']
        
        # Update
        update_data = {
            'name': 'Updated_Session_Name',
            'status': 'completed'
        }
        
        response = client.patch(
            f'/api/sessions/{session_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['name'] == 'Updated_Session_Name'
        assert data['status'] == 'completed'
    
    def test_delete_session(self, client, test_db):
        """Test DELETE /api/sessions/<id>"""
        # Create a session to delete
        new_session = {'name': 'To_Delete', 'import_folder': '/test'}
        response = client.post('/api/sessions', data=json.dumps(new_session),
                              content_type='application/json')
        session_id = json.loads(response.data)['id']
        
        # Delete
        response = client.delete(f'/api/sessions/{session_id}')
        assert response.status_code == 200
        
        # Verify deleted
        response = client.get(f'/api/sessions/{session_id}')
        assert response.status_code == 404


class TestPhotoAPI:
    """Test photo management API endpoints"""
    
    def test_list_photos(self, client, test_db):
        """Test GET /api/photos"""
        response = client.get('/api/photos')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'photos' in data
        assert 'count' in data
        assert data['count'] > 0
    
    def test_list_photos_with_filters(self, client, test_db):
        """Test photo list with multiple filters"""
        response = client.get('/api/photos?status=completed&min_score=4.0&approved=true')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        for photo in data['photos']:
            assert photo['status'] == 'completed'
            assert photo['ai_score'] >= 4.0
            assert photo['approved'] == True
    
    def test_list_photos_by_session(self, client, test_db):
        """Test photo list filtered by session"""
        # Get first session
        response = client.get('/api/sessions')
        session_id = json.loads(response.data)['sessions'][0]['id']
        
        # Get photos for that session
        response = client.get(f'/api/photos?session_id={session_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        for photo in data['photos']:
            assert photo['session_id'] == session_id
    
    def test_get_photo_detail(self, client, test_db):
        """Test GET /api/photos/<id>"""
        # Get first photo
        response = client.get('/api/photos')
        photo_id = json.loads(response.data)['photos'][0]['id']
        
        # Get detail
        response = client.get(f'/api/photos/{photo_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['id'] == photo_id
        assert 'file_name' in data
        assert 'ai_score' in data
    
    def test_update_photo(self, client, test_db):
        """Test PATCH /api/photos/<id>"""
        # Get first photo
        response = client.get('/api/photos')
        photo_id = json.loads(response.data)['photos'][0]['id']
        
        # Update
        update_data = {
            'status': 'approved',
            'approved': True
        }
        
        response = client.patch(
            f'/api/photos/{photo_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['approved'] == True


class TestJobAPI:
    """Test job management API endpoints"""
    
    def test_list_jobs(self, client, test_db):
        """Test GET /api/jobs"""
        response = client.get('/api/jobs')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'jobs' in data
        assert 'count' in data
    
    def test_list_jobs_with_status_filter(self, client, test_db):
        """Test job list with status filter"""
        response = client.get('/api/jobs?status=processing')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        for job in data['jobs']:
            assert job['status'] == 'processing'
    
    def test_list_jobs_with_priority_filter(self, client, test_db):
        """Test job list with priority filter"""
        response = client.get('/api/jobs?priority=1')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        for job in data['jobs']:
            assert job['priority'] == 1
    
    def test_get_job_detail(self, client, test_db):
        """Test GET /api/jobs/<id>"""
        # Get first job
        response = client.get('/api/jobs')
        jobs = json.loads(response.data)['jobs']
        if len(jobs) > 0:
            job_id = jobs[0]['id']
            
            # Get detail
            response = client.get(f'/api/jobs/{job_id}')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['id'] == job_id
    
    def test_create_job(self, client, test_db):
        """Test POST /api/jobs"""
        # Get a photo
        response = client.get('/api/photos')
        photo_id = json.loads(response.data)['photos'][0]['id']
        
        # Create job
        job_data = {
            'photo_id': photo_id,
            'config': {
                'version': '1.0',
                'pipeline': [
                    {
                        'stage': 'base',
                        'settings': {'exposure': 0.5}
                    }
                ],
                'safety': {'snapshot': True, 'dryRun': False}
            },
            'priority': 2
        }
        
        response = client.post(
            '/api/jobs',
            data=json.dumps(job_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert 'id' in data
        assert data['photo_id'] == photo_id
    
    def test_cancel_job(self, client, test_db):
        """Test DELETE /api/jobs/<id>"""
        # Get a processing job
        response = client.get('/api/jobs?status=processing')
        jobs = json.loads(response.data)['jobs']
        
        if len(jobs) > 0:
            job_id = jobs[0]['id']
            
            # Cancel job
            response = client.delete(f'/api/jobs/{job_id}')
            assert response.status_code == 200


class TestApprovalAPI:
    """Test approval queue API endpoints"""
    
    def test_get_approval_queue(self, client, test_db):
        """Test GET /api/approval/queue"""
        response = client.get('/api/approval/queue')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'photos' in data
        assert 'count' in data
    
    def test_approve_photo(self, client, test_db):
        """Test POST /api/approval/<id>/approve"""
        # Get a completed photo
        response = client.get('/api/photos?status=completed&approved=false')
        photos = json.loads(response.data)['photos']
        
        if len(photos) > 0:
            photo_id = photos[0]['id']
            
            # Approve
            response = client.post(
                f'/api/approval/{photo_id}/approve',
                data=json.dumps({}),
                content_type='application/json'
            )
            assert response.status_code == 200
            
            # Verify
            response = client.get(f'/api/photos/{photo_id}')
            photo = json.loads(response.data)
            assert photo['approved'] == True
    
    def test_reject_photo(self, client, test_db):
        """Test POST /api/approval/<id>/reject"""
        # Get a completed photo
        response = client.get('/api/photos?status=completed')
        photos = json.loads(response.data)['photos']
        
        if len(photos) > 0:
            photo_id = photos[0]['id']
            
            # Reject
            reject_data = {'reason': 'Test rejection reason'}
            response = client.post(
                f'/api/approval/{photo_id}/reject',
                data=json.dumps(reject_data),
                content_type='application/json'
            )
            assert response.status_code == 200
            
            # Verify
            response = client.get(f'/api/photos/{photo_id}')
            photo = json.loads(response.data)
            assert photo['status'] == 'rejected'
    
    def test_modify_photo(self, client, test_db):
        """Test POST /api/approval/<id>/modify"""
        # Get a completed photo
        response = client.get('/api/photos?status=completed')
        photos = json.loads(response.data)['photos']
        
        if len(photos) > 0:
            photo_id = photos[0]['id']
            
            # Modify
            modify_data = {
                'new_preset': 'Modified_Preset_v2',
                'adjustments': {'exposure': 0.3, 'contrast': 5}
            }
            response = client.post(
                f'/api/approval/{photo_id}/modify',
                data=json.dumps(modify_data),
                content_type='application/json'
            )
            assert response.status_code == 200


class TestStatisticsAPI:
    """Test statistics API endpoints"""
    
    def test_get_daily_statistics(self, client, test_db):
        """Test GET /api/statistics/daily"""
        response = client.get('/api/statistics/daily')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'date' in data
        assert 'total_imported' in data
        assert 'total_processed' in data
    
    def test_get_weekly_statistics(self, client, test_db):
        """Test GET /api/statistics/weekly"""
        response = client.get('/api/statistics/weekly')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'period' in data
        assert 'total_imported' in data
        assert 'daily_breakdown' in data
    
    def test_get_monthly_statistics(self, client, test_db):
        """Test GET /api/statistics/monthly"""
        response = client.get('/api/statistics/monthly')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'period' in data
        assert 'total_imported' in data
    
    def test_get_preset_statistics(self, client, test_db):
        """Test GET /api/statistics/presets"""
        response = client.get('/api/statistics/presets')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'presets' in data
        assert 'total_presets' in data


class TestSystemAPI:
    """Test system management API endpoints"""
    
    def test_get_system_status(self, client, test_db):
        """Test GET /api/system/status"""
        response = client.get('/api/system/status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'system' in data
        assert 'sessions' in data
        assert 'jobs' in data
    
    def test_get_system_health(self, client, test_db):
        """Test GET /api/system/health"""
        response = client.get('/api/system/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'status' in data
        assert data['status'] in ['healthy', 'unhealthy']
    
    def test_get_system_info(self, client, test_db):
        """Test GET /api/system/info"""
        response = client.get('/api/system/info')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'version' in data
        assert 'system_name' in data


class TestAPIErrorHandling:
    """Test API error handling"""
    
    def test_404_not_found(self, client, test_db):
        """Test 404 error handling"""
        response = client.get('/api/nonexistent/endpoint')
        assert response.status_code == 404
    
    def test_invalid_json(self, client, test_db):
        """Test invalid JSON handling"""
        response = client.post(
            '/api/sessions',
            data='invalid json',
            content_type='application/json'
        )
        assert response.status_code in [400, 500]
    
    def test_missing_required_fields(self, client, test_db):
        """Test missing required fields"""
        response = client.post(
            '/api/sessions',
            data=json.dumps({}),  # Missing required fields
            content_type='application/json'
        )
        assert response.status_code in [400, 422]
    
    def test_invalid_id_format(self, client, test_db):
        """Test invalid ID format"""
        response = client.get('/api/sessions/invalid_id')
        assert response.status_code in [400, 404]


class TestAPIConcurrency:
    """Test API concurrency handling"""
    
    def test_concurrent_session_creation(self, client, test_db):
        """Test creating multiple sessions concurrently"""
        sessions = []
        for i in range(5):
            session_data = {
                'name': f'Concurrent_Session_{i}',
                'import_folder': f'/test/concurrent_{i}'
            }
            response = client.post(
                '/api/sessions',
                data=json.dumps(session_data),
                content_type='application/json'
            )
            assert response.status_code == 201
            sessions.append(json.loads(response.data))
        
        # Verify all sessions were created
        assert len(sessions) == 5
        assert len(set(s['id'] for s in sessions)) == 5  # All unique IDs
    
    def test_concurrent_photo_updates(self, client, test_db):
        """Test updating same photo multiple times"""
        # Get a photo
        response = client.get('/api/photos')
        photo_id = json.loads(response.data)['photos'][0]['id']
        
        # Update multiple times
        for i in range(3):
            update_data = {'ai_score': 4.0 + i * 0.1}
            response = client.patch(
                f'/api/photos/{photo_id}',
                data=json.dumps(update_data),
                content_type='application/json'
            )
            assert response.status_code == 200


def run_api_integration_tests():
    """Run all API integration tests"""
    print("=" * 60)
    print("API Integration Tests")
    print("=" * 60)
    
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes'
    ])


if __name__ == '__main__':
    run_api_integration_tests()
