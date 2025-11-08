"""
Tests for A/B Testing System.
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.database import Base, Preset, Photo, Session as DBSession, ABTest, ABTestAssignment
from ab_test_manager import ABTestManager


@pytest.fixture
def db_session():
    """Create a temporary in-memory database for testing"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def sample_presets(db_session):
    """Create sample presets for testing"""
    preset_a = Preset(
        name='WhiteLayer_v4',
        version='v4',
        blend_amount=60
    )
    preset_a.set_config_template({
        'version': '1.0',
        'pipeline': [
            {'stage': 'base', 'settings': {'exposure': 0.0, 'contrast': 0}}
        ]
    })
    preset_a.set_context_tags(['backlit_portrait'])
    
    preset_b = Preset(
        name='WhiteLayer_v5',
        version='v5',
        blend_amount=70
    )
    preset_b.set_config_template({
        'version': '1.0',
        'pipeline': [
            {'stage': 'base', 'settings': {'exposure': 0.1, 'contrast': 5}}
        ]
    })
    preset_b.set_context_tags(['backlit_portrait'])
    
    db_session.add(preset_a)
    db_session.add(preset_b)
    db_session.commit()
    
    return preset_a, preset_b


@pytest.fixture
def sample_photos(db_session):
    """Create sample photos for testing"""
    photos = []
    for i in range(100):
        photo = Photo(
            file_path=f'/test/photo_{i}.cr3',
            file_name=f'photo_{i}.cr3',
            file_size=10000000,
            context_tag='backlit_portrait',
            status='imported'
        )
        db_session.add(photo)
        photos.append(photo)
    
    db_session.commit()
    return photos


def test_create_ab_test(db_session, sample_presets):
    """Test creating an A/B test"""
    manager = ABTestManager(db_session)
    preset_a, preset_b = sample_presets
    
    ab_test = manager.create_ab_test(
        name='WhiteLayer v4 vs v5',
        description='Testing new version of WhiteLayer preset',
        preset_a_id=preset_a.id,
        preset_b_id=preset_b.id,
        context_tag='backlit_portrait',
        target_sample_size=100,
        duration_days=30
    )
    
    assert ab_test.id is not None
    assert ab_test.name == 'WhiteLayer v4 vs v5'
    assert ab_test.status == 'active'
    assert ab_test.preset_a_id == preset_a.id
    assert ab_test.preset_b_id == preset_b.id


def test_assign_photo_to_variant(db_session, sample_presets, sample_photos):
    """Test assigning photos to A/B test variants"""
    manager = ABTestManager(db_session)
    preset_a, preset_b = sample_presets
    
    ab_test = manager.create_ab_test(
        name='Test Assignment',
        description='Testing photo assignment',
        preset_a_id=preset_a.id,
        preset_b_id=preset_b.id
    )
    
    # Assign first 10 photos
    assignments = []
    for i in range(10):
        assignment = manager.assign_photo_to_variant(
            test_id=ab_test.id,
            photo_id=sample_photos[i].id
        )
        assignments.append(assignment)
    
    # Check that assignments are balanced
    variant_a_count = sum(1 for a in assignments if a.variant == 'A')
    variant_b_count = sum(1 for a in assignments if a.variant == 'B')
    
    assert variant_a_count == 5
    assert variant_b_count == 5


def test_record_result(db_session, sample_presets, sample_photos):
    """Test recording A/B test results"""
    manager = ABTestManager(db_session)
    preset_a, preset_b = sample_presets
    
    ab_test = manager.create_ab_test(
        name='Test Results',
        description='Testing result recording',
        preset_a_id=preset_a.id,
        preset_b_id=preset_b.id
    )
    
    # Assign and record result
    assignment = manager.assign_photo_to_variant(
        test_id=ab_test.id,
        photo_id=sample_photos[0].id
    )
    
    manager.record_result(
        test_id=ab_test.id,
        photo_id=sample_photos[0].id,
        approved=True,
        processing_time=5.2
    )
    
    # Verify result was recorded
    db_session.refresh(assignment)
    assert assignment.approved is True
    assert assignment.processing_time == 5.2
    assert assignment.result_recorded_at is not None


def test_measure_effectiveness_insufficient_data(db_session, sample_presets, sample_photos):
    """Test effectiveness measurement with insufficient data"""
    manager = ABTestManager(db_session)
    preset_a, preset_b = sample_presets
    
    ab_test = manager.create_ab_test(
        name='Test Insufficient Data',
        description='Testing with too few samples',
        preset_a_id=preset_a.id,
        preset_b_id=preset_b.id
    )
    
    # Assign only 10 photos (less than min_samples_per_variant * 2)
    for i in range(10):
        assignment = manager.assign_photo_to_variant(
            test_id=ab_test.id,
            photo_id=sample_photos[i].id
        )
        manager.record_result(
            test_id=ab_test.id,
            photo_id=sample_photos[i].id,
            approved=True
        )
    
    result = manager.measure_effectiveness(ab_test.id)
    
    assert result['status'] == 'insufficient_data'
    assert result['min_required'] == manager.min_samples_per_variant


def test_measure_effectiveness_success(db_session, sample_presets, sample_photos):
    """Test effectiveness measurement with sufficient data"""
    manager = ABTestManager(db_session)
    preset_a, preset_b = sample_presets
    
    ab_test = manager.create_ab_test(
        name='Test Effectiveness',
        description='Testing effectiveness measurement',
        preset_a_id=preset_a.id,
        preset_b_id=preset_b.id
    )
    
    # Assign 60 photos (30 per variant)
    for i in range(60):
        assignment = manager.assign_photo_to_variant(
            test_id=ab_test.id,
            photo_id=sample_photos[i].id
        )
        
        # Variant B has higher approval rate (80% vs 60%)
        if assignment.variant == 'A':
            approved = i % 5 != 0  # 80% approval
        else:
            approved = i % 10 != 0  # 90% approval
        
        manager.record_result(
            test_id=ab_test.id,
            photo_id=sample_photos[i].id,
            approved=approved,
            processing_time=5.0 + (i % 3)
        )
    
    result = manager.measure_effectiveness(ab_test.id)
    
    assert result['status'] == 'success'
    assert 'variant_a' in result
    assert 'variant_b' in result
    assert result['variant_a']['samples'] == 30
    assert result['variant_b']['samples'] == 30
    assert result['variant_b']['approval_rate'] > result['variant_a']['approval_rate']


def test_statistical_significance(db_session, sample_presets, sample_photos):
    """Test statistical significance testing"""
    manager = ABTestManager(db_session)
    preset_a, preset_b = sample_presets
    
    ab_test = manager.create_ab_test(
        name='Test Significance',
        description='Testing statistical significance',
        preset_a_id=preset_a.id,
        preset_b_id=preset_b.id
    )
    
    # Assign 80 photos (40 per variant) with clear difference
    variant_a_count = 0
    variant_b_count = 0
    
    for i in range(80):
        assignment = manager.assign_photo_to_variant(
            test_id=ab_test.id,
            photo_id=sample_photos[i].id
        )
        
        # Variant B has much higher approval rate
        if assignment.variant == 'A':
            approved = variant_a_count % 2 == 0  # 50% approval
            variant_a_count += 1
        else:
            approved = variant_b_count % 10 != 0  # 90% approval
            variant_b_count += 1
        
        manager.record_result(
            test_id=ab_test.id,
            photo_id=sample_photos[i].id,
            approved=approved,
            processing_time=5.0
        )
    
    result = manager.test_statistical_significance(ab_test.id)
    
    assert result['status'] == 'success'
    assert 'approval_rate_test' in result
    assert result['approval_rate_test']['p_value'] < 0.05
    assert result['approval_rate_test']['significant'] is True
    assert result['winner'] == 'B'


def test_generate_report(db_session, sample_presets, sample_photos):
    """Test report generation"""
    manager = ABTestManager(db_session)
    preset_a, preset_b = sample_presets
    
    ab_test = manager.create_ab_test(
        name='Test Report',
        description='Testing report generation',
        preset_a_id=preset_a.id,
        preset_b_id=preset_b.id
    )
    
    # Assign 60 photos
    for i in range(60):
        assignment = manager.assign_photo_to_variant(
            test_id=ab_test.id,
            photo_id=sample_photos[i].id
        )
        manager.record_result(
            test_id=ab_test.id,
            photo_id=sample_photos[i].id,
            approved=i % 3 != 0,  # 67% approval
            processing_time=5.0
        )
    
    report = manager.generate_report(ab_test.id)
    
    assert 'report_generated_at' in report
    assert 'test_info' in report
    assert 'presets' in report
    assert 'effectiveness' in report
    assert 'statistical_significance' in report
    assert 'summary' in report
    
    # Test file output
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
    
    try:
        report = manager.generate_report(ab_test.id, output_path=temp_path)
        assert os.path.exists(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_get_test_progress(db_session, sample_presets, sample_photos):
    """Test getting test progress"""
    manager = ABTestManager(db_session)
    preset_a, preset_b = sample_presets
    
    ab_test = manager.create_ab_test(
        name='Test Progress',
        description='Testing progress tracking',
        preset_a_id=preset_a.id,
        preset_b_id=preset_b.id,
        target_sample_size=100
    )
    
    # Assign 50 photos, complete 30
    for i in range(50):
        assignment = manager.assign_photo_to_variant(
            test_id=ab_test.id,
            photo_id=sample_photos[i].id
        )
        
        if i < 30:
            manager.record_result(
                test_id=ab_test.id,
                photo_id=sample_photos[i].id,
                approved=True
            )
    
    progress = manager.get_test_progress(ab_test.id)
    
    assert progress['test_id'] == ab_test.id
    assert progress['total_assignments'] == 50
    assert progress['completed_assignments'] == 30
    assert progress['target_sample_size'] == 100
    assert progress['progress_percent'] == 30.0


def test_pause_resume_complete(db_session, sample_presets):
    """Test pausing, resuming, and completing A/B tests"""
    manager = ABTestManager(db_session)
    preset_a, preset_b = sample_presets
    
    ab_test = manager.create_ab_test(
        name='Test Lifecycle',
        description='Testing test lifecycle',
        preset_a_id=preset_a.id,
        preset_b_id=preset_b.id
    )
    
    assert ab_test.status == 'active'
    
    # Pause
    ab_test = manager.pause_ab_test(ab_test.id)
    assert ab_test.status == 'paused'
    
    # Resume
    ab_test = manager.resume_ab_test(ab_test.id)
    assert ab_test.status == 'active'
    
    # Complete
    ab_test = manager.complete_ab_test(ab_test.id)
    assert ab_test.status == 'completed'
    assert ab_test.end_date is not None


def test_list_ab_tests(db_session, sample_presets):
    """Test listing A/B tests with filters"""
    manager = ABTestManager(db_session)
    preset_a, preset_b = sample_presets
    
    # Create multiple tests
    test1 = manager.create_ab_test(
        name='Test 1',
        description='Active test',
        preset_a_id=preset_a.id,
        preset_b_id=preset_b.id,
        context_tag='backlit_portrait'
    )
    
    test2 = manager.create_ab_test(
        name='Test 2',
        description='Paused test',
        preset_a_id=preset_a.id,
        preset_b_id=preset_b.id,
        context_tag='low_light_indoor'
    )
    manager.pause_ab_test(test2.id)
    
    # List all tests
    all_tests = manager.list_ab_tests()
    assert len(all_tests) == 2
    
    # Filter by status
    active_tests = manager.list_ab_tests(status='active')
    assert len(active_tests) == 1
    assert active_tests[0].id == test1.id
    
    # Filter by context tag
    portrait_tests = manager.list_ab_tests(context_tag='backlit_portrait')
    assert len(portrait_tests) == 1
    assert portrait_tests[0].id == test1.id


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
