"""
Tests for Priority Management System

Requirements: 4.4
"""

import pytest
from datetime import datetime, timedelta
from priority_manager import PriorityManager, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW
from models.database import init_db, get_session, Photo, Job, Session as DBSession
import tempfile
import os


@pytest.fixture
def test_db():
    """Create a temporary test database"""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    db_url = f'sqlite:///{temp_db.name}'
    init_db(db_url)
    
    yield db_url
    
    # Cleanup
    os.unlink(temp_db.name)


@pytest.fixture
def priority_manager():
    """Create a priority manager instance"""
    return PriorityManager()


@pytest.fixture
def sample_photos(test_db):
    """Create sample photos for testing"""
    db_session = get_session()
    
    try:
        # Create a test session
        session = DBSession(
            name="Test Session",
            import_folder="/test/folder",
            status="importing"
        )
        db_session.add(session)
        db_session.commit()
        
        # Create photos with different AI scores and ages
        photos = []
        
        # High quality, recent photo
        photo1 = Photo(
            session_id=session.id,
            file_path="/test/photo1.jpg",
            file_name="photo1.jpg",
            ai_score=4.8,
            import_time=datetime.utcnow(),
            status="imported"
        )
        photos.append(photo1)
        
        # Medium quality, old photo
        photo2 = Photo(
            session_id=session.id,
            file_path="/test/photo2.jpg",
            file_name="photo2.jpg",
            ai_score=3.5,
            import_time=datetime.utcnow() - timedelta(hours=20),
            status="imported"
        )
        photos.append(photo2)
        
        # Low quality, recent photo
        photo3 = Photo(
            session_id=session.id,
            file_path="/test/photo3.jpg",
            file_name="photo3.jpg",
            ai_score=2.0,
            import_time=datetime.utcnow(),
            status="imported"
        )
        photos.append(photo3)
        
        # High quality, old photo
        photo4 = Photo(
            session_id=session.id,
            file_path="/test/photo4.jpg",
            file_name="photo4.jpg",
            ai_score=4.5,
            import_time=datetime.utcnow() - timedelta(hours=15),
            status="imported",
            context_tag="wedding"
        )
        photos.append(photo4)
        
        for photo in photos:
            db_session.add(photo)
        
        db_session.commit()
        
        return photos
        
    finally:
        db_session.close()


def test_calculate_priority_high_score(priority_manager, sample_photos):
    """Test priority calculation for high AI score"""
    photo = sample_photos[0]  # AI score 4.8
    
    priority = priority_manager.calculate_priority(photo.id)
    
    assert priority >= PRIORITY_HIGH - 1  # Should be high priority
    assert priority <= 10


def test_calculate_priority_medium_score(priority_manager, sample_photos):
    """Test priority calculation for medium AI score"""
    photo = sample_photos[1]  # AI score 3.5
    
    priority = priority_manager.calculate_priority(photo.id)
    
    assert priority >= PRIORITY_MEDIUM - 2
    assert priority <= PRIORITY_MEDIUM + 2


def test_calculate_priority_low_score(priority_manager, sample_photos):
    """Test priority calculation for low AI score"""
    photo = sample_photos[2]  # AI score 2.0
    
    priority = priority_manager.calculate_priority(photo.id)
    
    assert priority <= PRIORITY_LOW + 2  # Should be low priority


def test_calculate_priority_user_requested(priority_manager, sample_photos):
    """Test priority boost for user-requested jobs"""
    photo = sample_photos[2]  # Low score photo
    
    priority = priority_manager.calculate_priority(photo.id, user_requested=True)
    
    assert priority >= PRIORITY_HIGH  # User request should boost to high


def test_calculate_priority_age_boost(priority_manager, sample_photos):
    """Test priority boost based on photo age"""
    old_photo = sample_photos[1]  # 20 hours old
    recent_photo = sample_photos[0]  # Recent
    
    old_priority = priority_manager.calculate_priority(old_photo.id)
    recent_priority = priority_manager.calculate_priority(recent_photo.id)
    
    # Old photo should have higher priority due to age boost
    # (assuming similar AI scores)
    assert old_priority >= recent_priority - 2


def test_calculate_priority_context_boost(priority_manager, sample_photos):
    """Test priority boost based on context"""
    wedding_photo = sample_photos[3]  # Wedding context
    
    priority = priority_manager.calculate_priority(wedding_photo.id)
    
    # Wedding context should get high priority
    assert priority >= PRIORITY_HIGH - 1


def test_adjust_job_priority(priority_manager, sample_photos, test_db):
    """Test adjusting job priority"""
    db_session = get_session()
    
    try:
        # Create a job
        job = Job(
            id="test_job_1",
            photo_id=sample_photos[0].id,
            priority=PRIORITY_MEDIUM,
            config_json="{}",
            status="pending"
        )
        db_session.add(job)
        db_session.commit()
        
        # Adjust priority
        success = priority_manager.adjust_job_priority("test_job_1", PRIORITY_HIGH)
        
        assert success
        
        # Verify priority was updated
        updated_job = db_session.query(Job).filter(Job.id == "test_job_1").first()
        assert updated_job.priority == PRIORITY_HIGH
        
    finally:
        db_session.close()


def test_adjust_job_priority_clipping(priority_manager, sample_photos, test_db):
    """Test priority adjustment with value clipping"""
    db_session = get_session()
    
    try:
        # Create a job
        job = Job(
            id="test_job_2",
            photo_id=sample_photos[0].id,
            priority=PRIORITY_MEDIUM,
            config_json="{}",
            status="pending"
        )
        db_session.add(job)
        db_session.commit()
        
        # Try to set priority above max
        success = priority_manager.adjust_job_priority("test_job_2", 15)
        
        assert success
        
        # Verify priority was clipped to max
        updated_job = db_session.query(Job).filter(Job.id == "test_job_2").first()
        assert updated_job.priority == 10
        
    finally:
        db_session.close()


def test_rebalance_queue_priorities(priority_manager, sample_photos, test_db):
    """Test queue priority rebalancing"""
    db_session = get_session()
    
    try:
        # Create jobs with outdated priorities
        for i, photo in enumerate(sample_photos):
            job = Job(
                id=f"test_job_rebalance_{i}",
                photo_id=photo.id,
                priority=PRIORITY_MEDIUM,  # All same priority initially
                config_json="{}",
                status="pending"
            )
            db_session.add(job)
        
        db_session.commit()
        
        # Rebalance
        stats = priority_manager.rebalance_queue_priorities()
        
        assert 'adjusted_count' in stats
        assert 'total_pending' in stats
        assert stats['total_pending'] == len(sample_photos)
        
        # Verify priorities were adjusted
        jobs = db_session.query(Job).filter(Job.status == "pending").all()
        priorities = [job.priority for job in jobs]
        
        # Should have different priorities now
        assert len(set(priorities)) > 1
        
    finally:
        db_session.close()


def test_get_priority_distribution(priority_manager, sample_photos, test_db):
    """Test getting priority distribution"""
    db_session = get_session()
    
    try:
        # Create jobs with different priorities
        priorities = [PRIORITY_HIGH, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW]
        
        for i, priority in enumerate(priorities):
            job = Job(
                id=f"test_job_dist_{i}",
                photo_id=sample_photos[i % len(sample_photos)].id,
                priority=priority,
                config_json="{}",
                status="pending"
            )
            db_session.add(job)
        
        db_session.commit()
        
        # Get distribution
        distribution = priority_manager.get_priority_distribution()
        
        assert 'by_priority' in distribution
        assert 'total_pending' in distribution
        assert 'average_priority' in distribution
        
        assert distribution['total_pending'] == len(priorities)
        assert distribution['by_priority'][PRIORITY_HIGH] == 2
        assert distribution['by_priority'][PRIORITY_MEDIUM] == 1
        assert distribution['by_priority'][PRIORITY_LOW] == 1
        
    finally:
        db_session.close()


def test_boost_session_priority(priority_manager, sample_photos, test_db):
    """Test boosting priority for all jobs in a session"""
    db_session = get_session()
    
    try:
        session_id = sample_photos[0].session_id
        
        # Create jobs for photos in the session
        for i, photo in enumerate(sample_photos):
            job = Job(
                id=f"test_job_boost_{i}",
                photo_id=photo.id,
                priority=PRIORITY_LOW,
                config_json="{}",
                status="pending"
            )
            db_session.add(job)
        
        db_session.commit()
        
        # Boost session priority
        boost_amount = 3
        stats = priority_manager.boost_session_priority(session_id, boost_amount)
        
        assert 'boosted_count' in stats
        assert 'total_jobs' in stats
        assert stats['boosted_count'] == len(sample_photos)
        
        # Verify priorities were boosted
        jobs = db_session.query(Job).filter(Job.status == "pending").all()
        for job in jobs:
            assert job.priority >= PRIORITY_LOW + boost_amount
        
    finally:
        db_session.close()


def test_get_starvation_candidates(priority_manager, sample_photos, test_db):
    """Test identifying starving jobs"""
    db_session = get_session()
    
    try:
        # Create old and new jobs
        old_job = Job(
            id="test_job_old",
            photo_id=sample_photos[0].id,
            priority=PRIORITY_MEDIUM,
            config_json="{}",
            status="pending",
            created_at=datetime.utcnow() - timedelta(hours=15)
        )
        
        new_job = Job(
            id="test_job_new",
            photo_id=sample_photos[1].id,
            priority=PRIORITY_MEDIUM,
            config_json="{}",
            status="pending",
            created_at=datetime.utcnow()
        )
        
        db_session.add(old_job)
        db_session.add(new_job)
        db_session.commit()
        
        # Get starvation candidates (threshold: 12 hours)
        candidates = priority_manager.get_starvation_candidates(age_threshold_hours=12)
        
        assert len(candidates) == 1
        assert candidates[0]['job_id'] == "test_job_old"
        assert candidates[0]['age_hours'] >= 15
        
    finally:
        db_session.close()


def test_auto_boost_starving_jobs(priority_manager, sample_photos, test_db):
    """Test auto-boosting starving jobs"""
    db_session = get_session()
    
    try:
        # Create old job with low priority
        old_job = Job(
            id="test_job_starving",
            photo_id=sample_photos[0].id,
            priority=PRIORITY_LOW,
            config_json="{}",
            status="pending",
            created_at=datetime.utcnow() - timedelta(hours=15)
        )
        
        db_session.add(old_job)
        db_session.commit()
        
        # Auto-boost
        stats = priority_manager.auto_boost_starving_jobs(age_threshold_hours=12)
        
        assert 'boosted_count' in stats
        assert 'candidates' in stats
        assert stats['boosted_count'] == 1
        
        # Verify priority was boosted
        updated_job = db_session.query(Job).filter(
            Job.id == "test_job_starving"
        ).first()
        assert updated_job.priority > PRIORITY_LOW
        
    finally:
        db_session.close()


def test_update_config(priority_manager):
    """Test updating priority manager configuration"""
    original_weight = priority_manager.config['ai_score_weight']
    
    # Update config
    success = priority_manager.update_config({
        'ai_score_weight': 0.5,
        'age_weight': 0.25
    })
    
    assert success
    assert priority_manager.config['ai_score_weight'] == 0.5
    assert priority_manager.config['age_weight'] == 0.25
    
    # Restore original
    priority_manager.config['ai_score_weight'] = original_weight


def test_priority_calculation_edge_cases(priority_manager):
    """Test priority calculation with edge cases"""
    # Non-existent photo
    priority = priority_manager.calculate_priority(99999)
    assert priority == PRIORITY_MEDIUM  # Should return default
    
    # Override priority
    priority = priority_manager.calculate_priority(1, override_priority=7)
    assert priority == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
