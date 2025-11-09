"""
Validation script for Priority Management System

This script validates the priority management implementation without requiring pytest.
"""

import sys
import tempfile
import os
from datetime import datetime, timedelta

# Add local_bridge to path
sys.path.insert(0, os.path.dirname(__file__))

from priority_manager import PriorityManager, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW
from models.database import init_db, get_session, Photo, Job, Session as DBSession


def setup_test_db():
    """Create a temporary test database"""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    db_url = f'sqlite:///{temp_db.name}'
    init_db(db_url)
    
    return temp_db.name


def create_test_data():
    """Create sample test data"""
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
        
        # Create photos with different characteristics
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
        
        for photo in photos:
            db_session.add(photo)
        
        db_session.commit()
        
        return session, photos
        
    finally:
        db_session.close()


def test_priority_calculation():
    """Test priority calculation"""
    print("\n=== Testing Priority Calculation ===")
    
    priority_mgr = PriorityManager()
    session, photos = create_test_data()
    
    # Test high score photo
    priority1 = priority_mgr.calculate_priority(photos[0].id)
    print(f"✓ High score photo (4.8): Priority = {priority1}")
    assert priority1 >= PRIORITY_HIGH - 1, "High score should get high priority"
    
    # Test medium score photo
    priority2 = priority_mgr.calculate_priority(photos[1].id)
    print(f"✓ Medium score photo (3.5): Priority = {priority2}")
    assert PRIORITY_MEDIUM - 2 <= priority2 <= PRIORITY_MEDIUM + 2, "Medium score should get medium priority"
    
    # Test low score photo
    priority3 = priority_mgr.calculate_priority(photos[2].id)
    print(f"✓ Low score photo (2.0): Priority = {priority3}")
    assert priority3 <= PRIORITY_LOW + 2, "Low score should get low priority"
    
    # Test user requested
    priority_user = priority_mgr.calculate_priority(photos[2].id, user_requested=True)
    print(f"✓ User requested (low score): Priority = {priority_user}")
    assert priority_user >= PRIORITY_HIGH, "User request should boost to high"
    
    print("✓ All priority calculation tests passed!")


def test_priority_adjustment():
    """Test priority adjustment"""
    print("\n=== Testing Priority Adjustment ===")
    
    priority_mgr = PriorityManager()
    session, photos = create_test_data()
    
    db_session = get_session()
    
    try:
        # Create a job
        job = Job(
            id="test_job_1",
            photo_id=photos[0].id,
            priority=PRIORITY_MEDIUM,
            config_json="{}",
            status="pending"
        )
        db_session.add(job)
        db_session.commit()
        
        # Adjust priority
        success = priority_mgr.adjust_job_priority("test_job_1", PRIORITY_HIGH)
        print(f"✓ Adjusted job priority: Success = {success}")
        assert success, "Priority adjustment should succeed"
        
        # Verify
        updated_job = db_session.query(Job).filter(Job.id == "test_job_1").first()
        print(f"✓ Verified new priority: {updated_job.priority}")
        assert updated_job.priority == PRIORITY_HIGH, "Priority should be updated"
        
        print("✓ All priority adjustment tests passed!")
        
    finally:
        db_session.close()


def test_queue_rebalancing():
    """Test queue rebalancing"""
    print("\n=== Testing Queue Rebalancing ===")
    
    priority_mgr = PriorityManager()
    session, photos = create_test_data()
    
    db_session = get_session()
    
    try:
        # Create jobs with same priority
        for i, photo in enumerate(photos):
            job = Job(
                id=f"test_job_rebalance_{i}",
                photo_id=photo.id,
                priority=PRIORITY_MEDIUM,
                config_json="{}",
                status="pending"
            )
            db_session.add(job)
        
        db_session.commit()
        
        # Rebalance
        stats = priority_mgr.rebalance_queue_priorities()
        print(f"✓ Rebalanced queue: {stats['adjusted_count']} jobs adjusted out of {stats['total_pending']}")
        assert stats['total_pending'] == len(photos), "Should process all jobs"
        
        # Verify priorities changed
        jobs = db_session.query(Job).filter(Job.status == "pending").all()
        priorities = [job.priority for job in jobs]
        print(f"✓ Priority distribution after rebalancing: {priorities}")
        assert len(set(priorities)) > 1, "Priorities should be different after rebalancing"
        
        print("✓ All queue rebalancing tests passed!")
        
    finally:
        db_session.close()


def test_priority_distribution():
    """Test priority distribution"""
    print("\n=== Testing Priority Distribution ===")
    
    priority_mgr = PriorityManager()
    session, photos = create_test_data()
    
    db_session = get_session()
    
    try:
        # Create jobs with different priorities
        priorities = [PRIORITY_HIGH, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW]
        
        for i, priority in enumerate(priorities):
            job = Job(
                id=f"test_job_dist_{i}",
                photo_id=photos[i % len(photos)].id,
                priority=priority,
                config_json="{}",
                status="pending"
            )
            db_session.add(job)
        
        db_session.commit()
        
        # Get distribution
        distribution = priority_mgr.get_priority_distribution()
        print(f"✓ Priority distribution: {distribution['by_priority']}")
        print(f"✓ Total pending: {distribution['total_pending']}")
        print(f"✓ Average priority: {distribution['average_priority']:.2f}")
        
        assert distribution['total_pending'] == len(priorities), "Should count all jobs"
        assert distribution['by_priority'][PRIORITY_HIGH] == 2, "Should have 2 high priority jobs"
        
        print("✓ All priority distribution tests passed!")
        
    finally:
        db_session.close()


def test_starvation_detection():
    """Test starvation detection"""
    print("\n=== Testing Starvation Detection ===")
    
    priority_mgr = PriorityManager()
    session, photos = create_test_data()
    
    db_session = get_session()
    
    try:
        # Create old job
        old_job = Job(
            id="test_job_old",
            photo_id=photos[0].id,
            priority=PRIORITY_MEDIUM,
            config_json="{}",
            status="pending",
            created_at=datetime.utcnow() - timedelta(hours=15)
        )
        
        # Create new job
        new_job = Job(
            id="test_job_new",
            photo_id=photos[1].id,
            priority=PRIORITY_MEDIUM,
            config_json="{}",
            status="pending",
            created_at=datetime.utcnow()
        )
        
        db_session.add(old_job)
        db_session.add(new_job)
        db_session.commit()
        
        # Detect starvation
        candidates = priority_mgr.get_starvation_candidates(age_threshold_hours=12)
        print(f"✓ Found {len(candidates)} starvation candidates")
        
        assert len(candidates) == 1, "Should find 1 starving job"
        assert candidates[0]['job_id'] == "test_job_old", "Should identify old job"
        print(f"✓ Starving job age: {candidates[0]['age_hours']:.1f} hours")
        
        # Auto-boost
        stats = priority_mgr.auto_boost_starving_jobs(age_threshold_hours=12)
        print(f"✓ Auto-boosted {stats['boosted_count']} jobs")
        
        assert stats['boosted_count'] == 1, "Should boost 1 job"
        
        # Verify boost
        updated_job = db_session.query(Job).filter(Job.id == "test_job_old").first()
        print(f"✓ Job priority after boost: {updated_job.priority}")
        assert updated_job.priority > PRIORITY_MEDIUM, "Priority should be boosted"
        
        print("✓ All starvation detection tests passed!")
        
    finally:
        db_session.close()


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("Priority Management System Validation")
    print("=" * 60)
    
    # Setup test database
    db_file = setup_test_db()
    print(f"\n✓ Test database created: {db_file}")
    
    try:
        # Run tests
        test_priority_calculation()
        test_priority_adjustment()
        test_queue_rebalancing()
        test_priority_distribution()
        test_starvation_detection()
        
        print("\n" + "=" * 60)
        print("✓ ALL VALIDATION TESTS PASSED!")
        print("=" * 60)
        
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Cleanup
        try:
            os.unlink(db_file)
            print(f"\n✓ Test database cleaned up")
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
