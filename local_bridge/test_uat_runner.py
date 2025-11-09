"""
Unit tests for UAT Test Runner

Requirements: 全要件
"""

import os
import sys
import sqlite3
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from uat_test_runner import UATTestRunner


def test_database_initialization():
    """Test database initialization"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_uat.db")
        test_photos_dir = os.path.join(tmpdir, "photos")
        os.makedirs(test_photos_dir)
        
        runner = UATTestRunner(test_photos_dir, db_path)
        
        # Verify database exists
        assert os.path.exists(db_path), "Database file should exist"
        
        # Verify tables exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='uat_results'
        """)
        assert cursor.fetchone() is not None, "uat_results table should exist"
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='uat_test_runs'
        """)
        assert cursor.fetchone() is not None, "uat_test_runs table should exist"
        
        conn.close()
        print("✓ Database initialization test passed")


def test_photo_collection():
    """Test photo file collection"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_uat.db")
        test_photos_dir = Path(tmpdir) / "photos"
        test_photos_dir.mkdir()
        
        # Create dummy photo files
        (test_photos_dir / "photo1.jpg").touch()
        (test_photos_dir / "photo2.CR3").touch()
        (test_photos_dir / "photo3.nef").touch()
        (test_photos_dir / "not_photo.txt").touch()
        
        runner = UATTestRunner(str(test_photos_dir), db_path)
        photos = runner._collect_test_photos(10)
        
        # Should find at least 3 photos (may find more due to case-insensitive matching)
        assert len(photos) >= 3, f"Should find at least 3 photos, found {len(photos)}"
        # Should not include .txt files
        assert all(p.suffix.lower() in ['.jpg', '.jpeg', '.cr3', '.cr2', '.nef', '.arw', '.dng'] 
                  for p in photos), "Should only include image files"
        print("✓ Photo collection test passed")


def test_results_structure():
    """Test results data structure"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_uat.db")
        test_photos_dir = os.path.join(tmpdir, "photos")
        os.makedirs(test_photos_dir)
        
        runner = UATTestRunner(test_photos_dir, db_path)
        
        # Verify results structure
        assert 'test_start' in runner.results
        assert 'test_end' in runner.results
        assert 'total_photos' in runner.results
        assert 'processed_photos' in runner.results
        assert 'failed_photos' in runner.results
        assert 'approval_data' in runner.results
        assert 'timing_data' in runner.results
        assert 'error_log' in runner.results
        
        print("✓ Results structure test passed")


def test_save_photo_result():
    """Test saving photo result to database"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_uat.db")
        test_photos_dir = os.path.join(tmpdir, "photos")
        os.makedirs(test_photos_dir)
        
        runner = UATTestRunner(test_photos_dir, db_path)
        
        # Create test result
        test_result = {
            'photo_path': '/test/photo.jpg',
            'photo_name': 'photo.jpg',
            'exif_time': 0.1,
            'ai_time': 2.5,
            'context_time': 0.05,
            'preset_time': 0.02,
            'total_time': 2.67,
            'ai_score': 4.2,
            'focus_score': 4.0,
            'exposure_score': 4.5,
            'composition_score': 4.0,
            'context': 'portrait',
            'preset': 'WhiteLayer_v4'
        }
        
        runner._save_photo_result('TEST_RUN_001', test_result)
        
        # Verify saved
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM uat_results WHERE test_run_id = 'TEST_RUN_001'")
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 1, "Should have saved 1 result"
        print("✓ Save photo result test passed")


def test_summary_generation():
    """Test summary generation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_uat.db")
        test_photos_dir = os.path.join(tmpdir, "photos")
        os.makedirs(test_photos_dir)
        
        runner = UATTestRunner(test_photos_dir, db_path)
        runner.results['test_run_id'] = 'TEST_RUN_002'
        runner.results['test_start'] = runner.results['test_end'] = None
        runner.results['total_photos'] = 10
        runner.results['processed_photos'] = 9
        runner.results['failed_photos'] = 1
        
        # Add some test data
        for i in range(9):
            result = {
                'photo_path': f'/test/photo{i}.jpg',
                'photo_name': f'photo{i}.jpg',
                'total_time': 3.0 + i * 0.1,
                'ai_score': 3.5 + i * 0.1,
                'context': 'test',
                'preset': 'test_preset'
            }
            runner._save_photo_result('TEST_RUN_002', result)
        
        # Simulate approvals
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE uat_results 
            SET user_approved = 1, user_rating = 4
            WHERE test_run_id = 'TEST_RUN_002'
        """)
        conn.commit()
        conn.close()
        
        # Generate summary
        from datetime import datetime
        runner.results['test_start'] = datetime.now()
        runner.results['test_end'] = datetime.now()
        
        summary = runner._generate_summary()
        
        assert 'approval_rate' in summary
        assert 'time_savings_percent' in summary
        assert 'avg_processing_time' in summary
        assert summary['processed_photos'] == 9
        
        print("✓ Summary generation test passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("  UAT Test Runner - Unit Tests")
    print("="*60 + "\n")
    
    tests = [
        test_database_initialization,
        test_photo_collection,
        test_results_structure,
        test_save_photo_result,
        test_summary_generation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
