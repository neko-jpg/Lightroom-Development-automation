"""
Test suite for File Import Processor

Tests file import functionality including:
- Single file import
- Batch import
- Duplicate detection
- File copy/move operations
- Error handling
"""

import os
import shutil
import pathlib
import tempfile
import unittest
from datetime import datetime

from file_import_processor import (
    FileImportProcessor,
    DuplicateFileError,
    ImportError as FileImportError
)
from models.database import init_db, get_session, Photo, Session


class TestFileImportProcessor(unittest.TestCase):
    """Test cases for FileImportProcessor"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        cls.test_db_path = tempfile.mktemp(suffix='.db')
        init_db(f'sqlite:///{cls.test_db_path}')
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directories
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = pathlib.Path(self.test_dir) / "source"
        self.dest_dir = pathlib.Path(self.test_dir) / "dest"
        self.source_dir.mkdir()
        self.dest_dir.mkdir()
        
        # Create test files
        self.test_file1 = self.source_dir / "test_photo1.jpg"
        self.test_file2 = self.source_dir / "test_photo2.cr3"
        self.test_file3 = self.source_dir / "test_photo3.nef"
        
        self.test_file1.write_text("test photo 1 data content")
        self.test_file2.write_text("test photo 2 raw data content")
        self.test_file3.write_text("test photo 3 nikon raw data")
        
        # Clear database
        db_session = get_session()
        try:
            db_session.query(Photo).delete()
            db_session.query(Session).delete()
            db_session.commit()
        finally:
            db_session.close()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_processor_initialization(self):
        """Test processor initialization with different modes"""
        # Test copy mode
        processor = FileImportProcessor(
            import_mode='copy',
            destination_folder=str(self.dest_dir)
        )
        self.assertEqual(processor.import_mode, 'copy')
        self.assertEqual(processor.destination_folder, str(self.dest_dir))
        
        # Test move mode
        processor = FileImportProcessor(
            import_mode='move',
            destination_folder=str(self.dest_dir)
        )
        self.assertEqual(processor.import_mode, 'move')
        
        # Test add mode (in-place)
        processor = FileImportProcessor(import_mode='add')
        self.assertEqual(processor.import_mode, 'add')
        
        # Test invalid mode
        with self.assertRaises(ValueError):
            FileImportProcessor(import_mode='invalid')
        
        # Test missing destination for copy mode
        with self.assertRaises(ValueError):
            FileImportProcessor(import_mode='copy')
    
    def test_file_hash_calculation(self):
        """Test file hash calculation"""
        processor = FileImportProcessor(import_mode='add')
        
        # Calculate hash
        hash1 = processor.calculate_file_hash(str(self.test_file1))
        self.assertIsNotNone(hash1)
        self.assertEqual(len(hash1), 32)  # MD5 hash length
        
        # Same file should produce same hash
        hash2 = processor.calculate_file_hash(str(self.test_file1))
        self.assertEqual(hash1, hash2)
        
        # Different file should produce different hash
        hash3 = processor.calculate_file_hash(str(self.test_file2))
        self.assertNotEqual(hash1, hash3)
    
    def test_single_file_import_copy_mode(self):
        """Test importing a single file in copy mode"""
        processor = FileImportProcessor(
            import_mode='copy',
            destination_folder=str(self.dest_dir)
        )
        
        # Import file
        photo, final_path = processor.import_file(str(self.test_file1))
        
        # Verify photo record
        self.assertIsNotNone(photo)
        self.assertIsNotNone(photo.id)
        self.assertEqual(photo.file_name, "test_photo1.jpg")
        self.assertEqual(photo.status, 'imported')
        
        # Verify file was copied
        self.assertTrue(os.path.exists(final_path))
        self.assertTrue(os.path.exists(str(self.test_file1)))  # Original still exists
        
        # Verify file content
        with open(final_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, "test photo 1 data content")
    
    def test_single_file_import_move_mode(self):
        """Test importing a single file in move mode"""
        processor = FileImportProcessor(
            import_mode='move',
            destination_folder=str(self.dest_dir)
        )
        
        original_path = str(self.test_file1)
        
        # Import file
        photo, final_path = processor.import_file(original_path)
        
        # Verify photo record
        self.assertIsNotNone(photo)
        self.assertEqual(photo.file_name, "test_photo1.jpg")
        
        # Verify file was moved
        self.assertTrue(os.path.exists(final_path))
        self.assertFalse(os.path.exists(original_path))  # Original no longer exists
    
    def test_single_file_import_add_mode(self):
        """Test importing a single file in add mode (in-place)"""
        processor = FileImportProcessor(import_mode='add')
        
        original_path = str(self.test_file1)
        
        # Import file
        photo, final_path = processor.import_file(original_path)
        
        # Verify photo record
        self.assertIsNotNone(photo)
        self.assertEqual(photo.file_name, "test_photo1.jpg")
        
        # Verify file path is same as original (in-place)
        self.assertEqual(final_path, str(pathlib.Path(original_path).absolute()))
        self.assertTrue(os.path.exists(original_path))
    
    def test_duplicate_detection_by_path(self):
        """Test duplicate detection by file path"""
        processor = FileImportProcessor(import_mode='add')
        
        # Import file first time
        photo1, _ = processor.import_file(str(self.test_file1))
        self.assertIsNotNone(photo1)
        
        # Try to import same file again
        with self.assertRaises(DuplicateFileError):
            processor.import_file(str(self.test_file1), check_duplicates=True)
        
        # Should succeed if duplicate check is disabled
        photo2, _ = processor.import_file(str(self.test_file1), check_duplicates=False)
        self.assertIsNotNone(photo2)
    
    def test_duplicate_detection_by_hash(self):
        """Test duplicate detection by file hash"""
        # Use 'add' mode to test hash-based duplicate detection
        # (copy mode creates new files with different paths)
        processor = FileImportProcessor(import_mode='add')
        
        # Import file
        photo1, final_path1 = processor.import_file(str(self.test_file1))
        
        # Create a copy with different name in same directory
        test_file_copy = self.source_dir / "test_photo1_copy.jpg"
        shutil.copy2(str(self.test_file1), str(test_file_copy))
        
        # Try to import the copy (same content, different name and path)
        with self.assertRaises(DuplicateFileError):
            processor.import_file(str(test_file_copy), check_duplicates=True)
    
    def test_batch_import(self):
        """Test batch import of multiple files"""
        processor = FileImportProcessor(
            import_mode='copy',
            destination_folder=str(self.dest_dir)
        )
        
        file_paths = [
            str(self.test_file1),
            str(self.test_file2),
            str(self.test_file3)
        ]
        
        # Import batch
        results = processor.import_batch(file_paths)
        
        # Verify results
        self.assertEqual(results['total'], 3)
        self.assertEqual(results['imported'], 3)
        self.assertEqual(len(results['success']), 3)
        self.assertEqual(len(results['duplicates']), 0)
        self.assertEqual(len(results['errors']), 0)
        
        # Verify all files were imported
        for result in results['success']:
            self.assertIsNotNone(result['photo_id'])
            self.assertTrue(os.path.exists(result['final_path']))
    
    def test_batch_import_with_duplicates(self):
        """Test batch import with duplicate files"""
        processor = FileImportProcessor(
            import_mode='copy',
            destination_folder=str(self.dest_dir)
        )
        
        # Import first file
        processor.import_file(str(self.test_file1))
        
        # Try to import batch including duplicate
        file_paths = [
            str(self.test_file1),  # Duplicate
            str(self.test_file2),  # New
            str(self.test_file3)   # New
        ]
        
        results = processor.import_batch(file_paths, skip_on_error=True)
        
        # Verify results
        self.assertEqual(results['total'], 3)
        self.assertEqual(results['imported'], 2)  # Only 2 new files
        self.assertEqual(len(results['duplicates']), 1)
        self.assertEqual(len(results['errors']), 0)
    
    def test_batch_import_with_errors(self):
        """Test batch import with error handling"""
        processor = FileImportProcessor(
            import_mode='copy',
            destination_folder=str(self.dest_dir)
        )
        
        file_paths = [
            str(self.test_file1),  # Valid
            "/nonexistent/file.jpg",  # Invalid
            str(self.test_file2)   # Valid
        ]
        
        results = processor.import_batch(file_paths, skip_on_error=True)
        
        # Verify results
        self.assertEqual(results['total'], 3)
        self.assertEqual(results['imported'], 2)
        self.assertEqual(len(results['errors']), 1)
        
        # Verify error details
        error_path, error_msg = results['errors'][0]
        self.assertEqual(error_path, "/nonexistent/file.jpg")
    
    def test_session_creation(self):
        """Test session creation and retrieval"""
        processor = FileImportProcessor(import_mode='add')
        
        # Create session
        session = processor.get_or_create_session(
            session_name="Test Session",
            import_folder=str(self.source_dir)
        )
        
        self.assertIsNotNone(session)
        self.assertIsNotNone(session.id)
        self.assertEqual(session.name, "Test Session")
        self.assertEqual(session.import_folder, str(self.source_dir))
        self.assertEqual(session.status, 'importing')
        
        # Get same session again
        session2 = processor.get_or_create_session(
            session_name="Test Session",
            import_folder=str(self.source_dir)
        )
        
        # Should return same session
        self.assertEqual(session.id, session2.id)
    
    def test_import_with_session(self):
        """Test importing files associated with a session"""
        processor = FileImportProcessor(
            import_mode='copy',
            destination_folder=str(self.dest_dir)
        )
        
        # Create session
        session = processor.get_or_create_session(
            session_name="Test Session",
            import_folder=str(self.source_dir)
        )
        
        # Import file with session
        photo, _ = processor.import_file(
            str(self.test_file1),
            session_id=session.id
        )
        
        # Verify photo is associated with session
        self.assertEqual(photo.session_id, session.id)
        
        # Verify session relationship
        db_session = get_session()
        try:
            session_from_db = db_session.query(Session).filter(Session.id == session.id).first()
            self.assertEqual(len(session_from_db.photos), 1)
            self.assertEqual(session_from_db.photos[0].id, photo.id)
        finally:
            db_session.close()
    
    def test_file_copy_with_name_collision(self):
        """Test file copy handles name collisions"""
        processor = FileImportProcessor(
            import_mode='copy',
            destination_folder=str(self.dest_dir)
        )
        
        # Import file first time
        photo1, final_path1 = processor.import_file(str(self.test_file1), check_duplicates=False)
        
        # Modify original file content
        self.test_file1.write_text("modified content")
        
        # Import again (different content, same name)
        photo2, final_path2 = processor.import_file(str(self.test_file1), check_duplicates=False)
        
        # Verify both files exist with different names
        self.assertTrue(os.path.exists(final_path1))
        self.assertTrue(os.path.exists(final_path2))
        self.assertNotEqual(final_path1, final_path2)
        
        # Verify file names
        self.assertTrue("test_photo1" in final_path1)
        self.assertTrue("test_photo1_1" in final_path2)
    
    def test_import_nonexistent_file(self):
        """Test importing a nonexistent file raises error"""
        processor = FileImportProcessor(import_mode='add')
        
        with self.assertRaises(FileImportError):
            processor.import_file("/nonexistent/file.jpg")
    
    def test_photo_record_fields(self):
        """Test photo record contains correct fields"""
        processor = FileImportProcessor(
            import_mode='copy',
            destination_folder=str(self.dest_dir)
        )
        
        # Import file
        photo, final_path = processor.import_file(str(self.test_file1))
        
        # Verify photo fields
        self.assertIsNotNone(photo.id)
        self.assertEqual(photo.file_name, "test_photo1.jpg")
        self.assertIsNotNone(photo.file_size)
        self.assertGreater(photo.file_size, 0)
        self.assertIsNotNone(photo.import_time)
        self.assertEqual(photo.status, 'imported')
        self.assertFalse(photo.approved)
        
        # Verify file path is absolute
        self.assertTrue(os.path.isabs(photo.file_path))


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
