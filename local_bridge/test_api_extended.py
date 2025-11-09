"""
Test suite for Extended API Endpoints
拡張APIエンドポイントのテストスイート

Requirements: 9.1
"""

import pytest
import json
from datetime import datetime, timedelta
from app import app
from models.database import init_db, get_session, Session, Photo, Job
import tempfile
import os


@pytest.fixture
def client():
    """Create test client"""
    # Use in-memory database for testing
    test_db = tempfile.mktemp(suffix='.db')
    init_db(f'sqlite:///{test_db}')
    
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
    
    # Cleanup
    if os.path.exists(test_db):
        os.remove(test_db)


@pytest.fixture
def sample_session():
    """Create a sample session for testing"""
    db_session = get_session()
    try:
        session = Session(
            name="Test Session",
            import_folder="/test/folder",
            total_photos=10,
            processed_photos=5,
            status="processing"
        )
        db_session.add(session)
        db_session.commit()
        return session.id
    finally:
        db_session.close()


@pytest.fixture
def sample_photo(sample_session):
    """Create a sample photo for testing"""
    db_session = get_session()
    try:
        photo = Photo(
            session_id=sample_session,
            file_path="/test/photo.jpg",
            file_name="photo.jpg",
            file_size=1024000,
            ai_score=4.2,
            status="completed",
            approved=False
        )
        db_session.add(photo)
        db_session.commit()
        return photo.id
    finally:
        db_session.close()


# ============================================================================
# SESSION MANAGEMENT TESTS
# ============================================================================

def test_get_sessions(client, sample_session):
    """Test GET /api/sessions"""
    response = client.get('/api/sessions')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'sessions' in data
    assert 'count' in data
    assert 'total' in data
    assert data['count'] > 0


def test_get_sessions_with_filters(client, sample_session):
    """Test GET /api/sessions with filters"""
    response = client.get('/api/sessions?status=processing&limit=10')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'sessions' in data
    for session in data['sessions']:
        assert session['status'] == 'processing'


def test_get_session_detail(client, sample_session):
    """Test GET /api/sessions/<id>"""
    response = client.get(f'/api/sessions/{sample_session}')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['id'] == sample_session
    assert 'name' in data
    assert 'photo_stats' in data


def test_get_session_detail_not_found(client):
    """Test GET /api/sessions/<id> with non-existent ID"""
    response = client.get('/api/sessions/99999')
    assert response.status_code == 404


def test_create_session(client):
    """Test POST /api/sessions"""
    payload = {
        'name': 'New Test Session',
        'import_folder': '/test/new_folder'
    }
    
    response = client.post('/api/sessions',
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code == 201
    
    data = json.loads(response.data)
    assert 'id' in data
    assert data['name'] == 'New Test Session'


def test_update_session(client, sample_session):
    """Test PATCH /api/sessions/<id>"""
    payload = {
        'name': 'Updated Session Name',
        'status': 'completed'
    }
    
    response = client.patch(f'/api/sessions/{sample_session}',
                           data=json.dumps(payload),
                           content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['name'] == 'Updated Session Name'
    assert data['status'] == 'completed'


def test_delete_session(client, sample_session):
    """Test DELETE /api/sessions/<id>"""
    response = client.delete(f'/api/sessions/{sample_session}')
    assert response.status_code == 200
    
    # Verify session is deleted
    response = client.get(f'/api/sessions/{sample_session}')
    assert response.status_code == 404


# ============================================================================
# PHOTO MANAGEMENT TESTS
# ============================================================================

def test_get_photos(client, sample_photo):
    """Test GET /api/photos"""
    response = client.get('/api/photos')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'photos' in data
    assert 'count' in data
    assert data['count'] > 0


def test_get_photos_with_filters(client, sample_photo):
    """Test GET /api/photos with filters"""
    response = client.get('/api/photos?status=completed&min_score=4.0')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'photos' in data
    for photo in data['photos']:
        assert photo['status'] == 'completed'
        assert photo['ai_score'] >= 4.0


def test_get_photo_detail(client, sample_photo):
    """Test GET /api/photos/<id>"""
    response = client.get(f'/api/photos/{sample_photo}')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['id'] == sample_photo
    assert 'file_name' in data


def test_update_photo(client, sample_photo):
    """Test PATCH /api/photos/<id>"""
    payload = {
        'status': 'approved',
        'approved': True
    }
    
    response = client.patch(f'/api/photos/{sample_photo}',
                           data=json.dumps(payload),
                           content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['approved'] == True


# ============================================================================
# JOB MANAGEMENT TESTS
# ============================================================================

def test_get_jobs(client):
    """Test GET /api/jobs"""
    response = client.get('/api/jobs')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'jobs' in data
    assert 'count' in data


def test_create_job(client, sample_photo):
    """Test POST /api/jobs"""
    payload = {
        'photo_id': sample_photo,
        'config': {
            'version': '1.0',
            'pipeline': [],
            'safety': {'snapshot': True, 'dryRun': False}
        },
        'priority': 2
    }
    
    response = client.post('/api/jobs',
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code == 201
    
    data = json.loads(response.data)
    assert 'id' in data
    assert data['photo_id'] == sample_photo


# ============================================================================
# APPROVAL QUEUE TESTS
# ============================================================================

def test_get_approval_queue(client, sample_photo):
    """Test GET /api/approval/queue"""
    response = client.get('/api/approval/queue')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'photos' in data
    assert 'count' in data


def test_approve_photo(client, sample_photo):
    """Test POST /api/approval/<id>/approve"""
    response = client.post(f'/api/approval/{sample_photo}/approve',
                          data=json.dumps({}),
                          content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'message' in data
    assert data['photo_id'] == sample_photo


def test_reject_photo(client, sample_photo):
    """Test POST /api/approval/<id>/reject"""
    payload = {
        'reason': 'Test rejection'
    }
    
    response = client.post(f'/api/approval/{sample_photo}/reject',
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'message' in data


def test_modify_photo_preset(client, sample_photo):
    """Test POST /api/approval/<id>/modify"""
    payload = {
        'new_preset': 'NewPreset_v2',
        'adjustments': {'exposure': 0.5}
    }
    
    response = client.post(f'/api/approval/{sample_photo}/modify',
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['new_preset'] == 'NewPreset_v2'


# ============================================================================
# STATISTICS TESTS
# ============================================================================

def test_get_daily_statistics(client):
    """Test GET /api/statistics/daily"""
    response = client.get('/api/statistics/daily')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'date' in data
    assert 'total_imported' in data
    assert 'total_processed' in data


def test_get_weekly_statistics(client):
    """Test GET /api/statistics/weekly"""
    response = client.get('/api/statistics/weekly')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'period' in data
    assert 'total_imported' in data
    assert 'daily_breakdown' in data


def test_get_monthly_statistics(client):
    """Test GET /api/statistics/monthly"""
    response = client.get('/api/statistics/monthly')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'period' in data
    assert 'total_imported' in data


def test_get_preset_statistics(client):
    """Test GET /api/statistics/presets"""
    response = client.get('/api/statistics/presets')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'presets' in data
    assert 'total_presets' in data


# ============================================================================
# SYSTEM MANAGEMENT TESTS
# ============================================================================

def test_get_system_status(client):
    """Test GET /api/system/status"""
    response = client.get('/api/system/status')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'system' in data
    assert 'sessions' in data
    assert 'jobs' in data
    assert 'resources' in data


def test_get_system_health(client):
    """Test GET /api/system/health"""
    response = client.get('/api/system/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'


def test_get_system_info(client):
    """Test GET /api/system/info"""
    response = client.get('/api/system/info')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'version' in data
    assert 'system_name' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
