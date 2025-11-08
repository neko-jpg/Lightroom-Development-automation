"""
Test suite for Hot Folder Watcher

Tests the hot folder monitoring functionality including:
- File detection
- Write completion detection
- Multiple folder monitoring
- Callback triggering
"""

import time
import shutil
import pathlib
import logging
import unittest
from hot_folder_watcher import HotFolderWatcher, create_hot_folder_watcher


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class TestHotFolderWatcher(unittest.TestCase):
    """Test cases for HotFolderWatcher"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = pathlib.Path("test_hotfolder_temp")
        self.test_dir.mkdir(exist_ok=True)
        
        self.test_dir2 = pathlib.Path("test_hotfolder_temp2")
        self.test_dir2.mkdir(exist_ok=True)
        
        self.detected_files = []
        
    def tearDown(self):
        """Clean up test fixtures"""
        # Wait a bit for file handles to be released
        time.sleep(0.5)
        
        # Retry cleanup with error handling for Windows
        for test_dir in [self.test_dir, self.test_dir2]:
            if test_dir.exists():
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        shutil.rmtree(test_dir)
                        break
                    except PermissionError:
                        if attempt < max_retries - 1:
                            time.sleep(1)
                        else:
                            print(f"Warning: Could not clean up {test_dir}")
    
    def callback(self, file_path: str):
        """Test callback function"""
        self.detected_files.append(file_path)
        print(f"Callback triggered for: {file_path}")
    
    def test_initialization(self):
        """Test watcher initialization"""
        watcher = HotFolderWatcher(
            folders=[str(self.test_dir)],
            callback=self.callback
        )
        
        self.assertIsNotNone(watcher)
        self.assertEqual(len(watcher.get_folders()), 1)
        self.assertFalse(watcher.is_running())
    
    def test_start_stop(self):
        """Test starting and stopping the watcher"""
        watcher = HotFolderWatcher(
            folders=[str(self.test_dir)],
            callback=self.callback
        )
        
        # Start watcher
        watcher.start()
        self.assertTrue(watcher.is_running())
        
        # Stop watcher
        watcher.stop()
        self.assertFalse(watcher.is_running())
    
    def test_file_detection_jpg(self):
        """Test detection of JPEG files"""
        watcher = HotFolderWatcher(
            folders=[str(self.test_dir)],
            callback=self.callback,
            write_complete_delay=1.0
        )
        
        watcher.start()
        
        # Create test file
        test_file = self.test_dir / "test_image.jpg"
        test_file.write_text("test image data")
        
        # Wait for detection
        time.sleep(3)
        
        watcher.stop()
        
        # Check if file was detected
        self.assertEqual(len(self.detected_files), 1)
        self.assertIn("test_image.jpg", self.detected_files[0])
    
    def test_file_detection_raw(self):
        """Test detection of RAW files"""
        watcher = HotFolderWatcher(
            folders=[str(self.test_dir)],
            callback=self.callback,
            write_complete_delay=1.0
        )
        
        watcher.start()
        
        # Create test RAW files
        for ext in ['.cr3', '.nef', '.arw']:
            test_file = self.test_dir / f"test_image{ext}"
            test_file.write_text("test raw data")
        
        # Wait for detection
        time.sleep(4)
        
        watcher.stop()
        
        # Check if files were detected
        self.assertEqual(len(self.detected_files), 3)
    
    def test_ignore_non_image_files(self):
        """Test that non-image files are ignored"""
        watcher = HotFolderWatcher(
            folders=[str(self.test_dir)],
            callback=self.callback,
            write_complete_delay=1.0
        )
        
        watcher.start()
        
        # Create non-image files
        (self.test_dir / "test.txt").write_text("text file")
        (self.test_dir / "test.pdf").write_text("pdf file")
        (self.test_dir / "test.doc").write_text("doc file")
        
        # Create one image file
        (self.test_dir / "test_image.jpg").write_text("image file")
        
        # Wait for detection
        time.sleep(3)
        
        watcher.stop()
        
        # Only the image file should be detected
        self.assertEqual(len(self.detected_files), 1)
        self.assertIn("test_image.jpg", self.detected_files[0])
    
    def test_multiple_folders(self):
        """Test monitoring multiple folders simultaneously"""
        watcher = HotFolderWatcher(
            folders=[str(self.test_dir), str(self.test_dir2)],
            callback=self.callback,
            write_complete_delay=1.0
        )
        
        watcher.start()
        
        # Create files in both folders
        (self.test_dir / "image1.jpg").write_text("image 1")
        (self.test_dir2 / "image2.jpg").write_text("image 2")
        
        # Wait for detection
        time.sleep(3)
        
        watcher.stop()
        
        # Both files should be detected
        self.assertEqual(len(self.detected_files), 2)
    
    def test_add_folder_while_running(self):
        """Test adding a folder while watcher is running"""
        watcher = HotFolderWatcher(
            folders=[str(self.test_dir)],
            callback=self.callback,
            write_complete_delay=1.0
        )
        
        watcher.start()
        
        # Add second folder while running
        success = watcher.add_folder(str(self.test_dir2))
        self.assertTrue(success)
        
        # Create file in new folder
        (self.test_dir2 / "image.jpg").write_text("image")
        
        # Wait for detection
        time.sleep(3)
        
        watcher.stop()
        
        # File should be detected
        self.assertEqual(len(self.detected_files), 1)
    
    def test_remove_folder(self):
        """Test removing a folder from watch list"""
        watcher = HotFolderWatcher(
            folders=[str(self.test_dir), str(self.test_dir2)],
            callback=self.callback
        )
        
        # Remove one folder
        success = watcher.remove_folder(str(self.test_dir2))
        self.assertTrue(success)
        
        # Check folder list
        folders = watcher.get_folders()
        self.assertEqual(len(folders), 1)
        self.assertNotIn(str(self.test_dir2), folders)
    
    def test_context_manager(self):
        """Test using watcher as context manager"""
        with HotFolderWatcher(
            folders=[str(self.test_dir)],
            callback=self.callback,
            write_complete_delay=1.0
        ) as watcher:
            self.assertTrue(watcher.is_running())
            
            # Create test file
            (self.test_dir / "image.jpg").write_text("image")
            
            # Wait for detection
            time.sleep(3)
        
        # Watcher should be stopped after context
        self.assertFalse(watcher.is_running())
        self.assertEqual(len(self.detected_files), 1)
    
    def test_factory_function(self):
        """Test factory function"""
        watcher = create_hot_folder_watcher(
            folders=[str(self.test_dir)],
            callback=self.callback
        )
        
        self.assertIsNotNone(watcher)
        self.assertIsInstance(watcher, HotFolderWatcher)
    
    def test_invalid_folder(self):
        """Test handling of invalid folder paths"""
        watcher = HotFolderWatcher(callback=self.callback)
        
        # Try to add non-existent folder
        success = watcher.add_folder("/nonexistent/folder/path")
        self.assertFalse(success)
    
    def test_duplicate_folder(self):
        """Test handling of duplicate folder additions"""
        watcher = HotFolderWatcher(
            folders=[str(self.test_dir)],
            callback=self.callback
        )
        
        # Try to add same folder again
        success = watcher.add_folder(str(self.test_dir))
        self.assertFalse(success)


def run_tests():
    """Run all tests"""
    print("=== Running Hot Folder Watcher Tests ===\n")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHotFolderWatcher)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
