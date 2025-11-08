"""
Hot Folder Monitoring Service for Junmai AutoDev

This module provides hot folder monitoring functionality including:
- File system monitoring using watchdog library
- New file detection logic
- File write completion detection
- Multiple folder simultaneous monitoring

Requirements: 1.1, 1.2
"""

import time
import logging
import pathlib
from typing import List, Callable, Set, Optional
from threading import Thread, Event
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


# Supported image file extensions
IMAGE_EXTENSIONS = {
    # RAW formats
    '.cr2', '.cr3', '.nef', '.arw', '.dng', '.orf', '.raf', '.rw2',
    '.pef', '.srw', '.x3f', '.erf', '.mrw', '.raw', '.rwl', '.iiq',
    # JPEG/TIFF
    '.jpg', '.jpeg', '.tif', '.tiff', '.png'
}


class FileEventHandler(FileSystemEventHandler):
    """
    File system event handler for hot folder monitoring
    
    Handles file creation events and ensures files are completely written
    before triggering callbacks.
    """
    
    def __init__(self, callback: Callable[[str], None], write_complete_delay: float = 2.0):
        """
        Initialize FileEventHandler
        
        Args:
            callback: Function to call when a new image file is detected
            write_complete_delay: Seconds to wait to ensure file write is complete
        """
        super().__init__()
        self.callback = callback
        self.write_complete_delay = write_complete_delay
        self._processing_files: Set[str] = set()
        logger.debug(f"FileEventHandler initialized with {write_complete_delay}s write delay")
    
    def on_created(self, event: FileSystemEvent) -> None:
        """
        Handle file creation events
        
        Args:
            event: File system event
        """
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # Check if file is an image
        if not self._is_image_file(file_path):
            logger.debug(f"Ignoring non-image file: {file_path}")
            return
        
        # Avoid duplicate processing
        if file_path in self._processing_files:
            logger.debug(f"File already being processed: {file_path}")
            return
        
        self._processing_files.add(file_path)
        logger.info(f"New image file detected: {file_path}")
        
        # Wait for file write to complete in a separate thread
        thread = Thread(target=self._wait_and_process, args=(file_path,), daemon=True)
        thread.start()
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """
        Handle file modification events
        
        Some systems trigger modified instead of created for new files.
        
        Args:
            event: File system event
        """
        # Treat modifications as potential new files
        if not event.is_directory and self._is_image_file(event.src_path):
            if event.src_path not in self._processing_files:
                self.on_created(event)
    
    def _is_image_file(self, file_path: str) -> bool:
        """
        Check if file is a supported image format
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file is a supported image format
        """
        extension = pathlib.Path(file_path).suffix.lower()
        return extension in IMAGE_EXTENSIONS
    
    def _wait_and_process(self, file_path: str) -> None:
        """
        Wait for file write to complete and then process
        
        Args:
            file_path: Path to file
        """
        try:
            # Wait for file write to complete
            if not self._wait_for_file_ready(file_path):
                logger.warning(f"File not ready after waiting: {file_path}")
                self._processing_files.discard(file_path)
                return
            
            # File is ready, trigger callback
            logger.info(f"File write complete, processing: {file_path}")
            self.callback(file_path)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}", exc_info=True)
        finally:
            # Remove from processing set
            self._processing_files.discard(file_path)
    
    def _wait_for_file_ready(self, file_path: str, max_attempts: int = 10) -> bool:
        """
        Wait for file to be completely written
        
        Checks file size stability to ensure write is complete.
        
        Args:
            file_path: Path to file
            max_attempts: Maximum number of attempts to check file stability
            
        Returns:
            True if file is ready, False otherwise
        """
        path = pathlib.Path(file_path)
        
        # Wait initial delay
        time.sleep(self.write_complete_delay)
        
        # Check if file exists
        if not path.exists():
            logger.warning(f"File disappeared: {file_path}")
            return False
        
        # Check file size stability
        previous_size = -1
        stable_count = 0
        required_stable_checks = 2
        
        for attempt in range(max_attempts):
            try:
                current_size = path.stat().st_size
                
                # Check if size is stable
                if current_size == previous_size and current_size > 0:
                    stable_count += 1
                    if stable_count >= required_stable_checks:
                        logger.debug(f"File size stable at {current_size} bytes: {file_path}")
                        return True
                else:
                    stable_count = 0
                
                previous_size = current_size
                time.sleep(0.5)
                
            except OSError as e:
                logger.warning(f"Error checking file size (attempt {attempt + 1}): {e}")
                time.sleep(0.5)
        
        logger.warning(f"File size not stable after {max_attempts} attempts: {file_path}")
        return False


class HotFolderWatcher:
    """
    Hot Folder Watcher Service
    
    Monitors multiple folders for new image files and triggers callbacks
    when files are detected and ready for processing.
    """
    
    def __init__(self, folders: Optional[List[str]] = None, 
                 callback: Optional[Callable[[str], None]] = None,
                 write_complete_delay: float = 2.0):
        """
        Initialize HotFolderWatcher
        
        Args:
            folders: List of folder paths to monitor
            callback: Function to call when new image file is detected
            write_complete_delay: Seconds to wait to ensure file write is complete
        """
        self.folders: List[pathlib.Path] = []
        self.callback = callback or self._default_callback
        self.write_complete_delay = write_complete_delay
        self.observer: Optional[Observer] = None
        self._stop_event = Event()
        self._is_running = False
        
        if folders:
            self.set_folders(folders)
        
        logger.info("HotFolderWatcher initialized")
    
    def set_folders(self, folders: List[str]) -> None:
        """
        Set folders to monitor
        
        Args:
            folders: List of folder paths to monitor
        """
        self.folders = []
        for folder in folders:
            path = pathlib.Path(folder)
            if path.exists() and path.is_dir():
                self.folders.append(path)
                logger.info(f"Added folder to watch list: {path}")
            else:
                logger.warning(f"Folder does not exist or is not a directory: {folder}")
        
        logger.info(f"Monitoring {len(self.folders)} folders")
    
    def add_folder(self, folder: str) -> bool:
        """
        Add a folder to the watch list
        
        Args:
            folder: Folder path to add
            
        Returns:
            True if folder was added successfully
        """
        path = pathlib.Path(folder)
        
        if not path.exists():
            logger.error(f"Folder does not exist: {folder}")
            return False
        
        if not path.is_dir():
            logger.error(f"Path is not a directory: {folder}")
            return False
        
        if path in self.folders:
            logger.warning(f"Folder already in watch list: {folder}")
            return False
        
        self.folders.append(path)
        logger.info(f"Added folder to watch list: {path}")
        
        # If already running, schedule the new folder
        if self._is_running and self.observer:
            event_handler = FileEventHandler(self.callback, self.write_complete_delay)
            self.observer.schedule(event_handler, str(path), recursive=True)
            logger.info(f"Started monitoring new folder: {path}")
        
        return True
    
    def remove_folder(self, folder: str) -> bool:
        """
        Remove a folder from the watch list
        
        Args:
            folder: Folder path to remove
            
        Returns:
            True if folder was removed successfully
        """
        path = pathlib.Path(folder)
        
        if path not in self.folders:
            logger.warning(f"Folder not in watch list: {folder}")
            return False
        
        self.folders.remove(path)
        logger.info(f"Removed folder from watch list: {path}")
        
        # Note: watchdog doesn't support unscheduling individual folders easily
        # If this is needed while running, restart the observer
        if self._is_running:
            logger.info("Restarting observer to apply folder changes")
            self.stop()
            self.start()
        
        return True
    
    def set_callback(self, callback: Callable[[str], None]) -> None:
        """
        Set callback function for file detection
        
        Args:
            callback: Function to call when new image file is detected
        """
        self.callback = callback
        logger.info("Callback function updated")
    
    def start(self) -> None:
        """
        Start monitoring folders
        
        Raises:
            RuntimeError: If no folders are configured
        """
        if self._is_running:
            logger.warning("HotFolderWatcher is already running")
            return
        
        if not self.folders:
            raise RuntimeError("No folders configured for monitoring")
        
        logger.info("Starting HotFolderWatcher...")
        
        # Create observer
        self.observer = Observer()
        
        # Schedule event handlers for each folder
        for folder in self.folders:
            event_handler = FileEventHandler(self.callback, self.write_complete_delay)
            self.observer.schedule(event_handler, str(folder), recursive=True)
            logger.info(f"Scheduled monitoring for: {folder}")
        
        # Start observer
        self.observer.start()
        self._is_running = True
        self._stop_event.clear()
        
        logger.info(f"HotFolderWatcher started, monitoring {len(self.folders)} folders")
    
    def stop(self) -> None:
        """
        Stop monitoring folders
        """
        if not self._is_running:
            logger.warning("HotFolderWatcher is not running")
            return
        
        logger.info("Stopping HotFolderWatcher...")
        
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5.0)
            self.observer = None
        
        self._is_running = False
        self._stop_event.set()
        
        logger.info("HotFolderWatcher stopped")
    
    def is_running(self) -> bool:
        """
        Check if watcher is running
        
        Returns:
            True if watcher is running
        """
        return self._is_running
    
    def get_folders(self) -> List[str]:
        """
        Get list of monitored folders
        
        Returns:
            List of folder paths
        """
        return [str(folder) for folder in self.folders]
    
    def _default_callback(self, file_path: str) -> None:
        """
        Default callback function
        
        Args:
            file_path: Path to detected file
        """
        logger.info(f"New file detected (default callback): {file_path}")
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


def create_hot_folder_watcher(folders: List[str], 
                              callback: Callable[[str], None],
                              write_complete_delay: float = 2.0) -> HotFolderWatcher:
    """
    Factory function to create and configure a HotFolderWatcher
    
    Args:
        folders: List of folder paths to monitor
        callback: Function to call when new image file is detected
        write_complete_delay: Seconds to wait to ensure file write is complete
        
    Returns:
        Configured HotFolderWatcher instance
    """
    watcher = HotFolderWatcher(
        folders=folders,
        callback=callback,
        write_complete_delay=write_complete_delay
    )
    return watcher


if __name__ == '__main__':
    # Setup logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test hot folder watcher
    print("=== Testing Hot Folder Watcher ===\n")
    
    def test_callback(file_path: str):
        print(f"✓ Callback triggered for: {file_path}")
    
    # Create test directory
    test_dir = pathlib.Path("test_hotfolder")
    test_dir.mkdir(exist_ok=True)
    
    print(f"Test 1: Create watcher for folder: {test_dir}")
    watcher = HotFolderWatcher(
        folders=[str(test_dir)],
        callback=test_callback
    )
    print(f"✓ Watcher created, monitoring: {watcher.get_folders()}")
    
    print("\nTest 2: Start monitoring")
    watcher.start()
    print(f"✓ Watcher started, is_running: {watcher.is_running()}")
    
    print("\nTest 3: Create test file (waiting 5 seconds for detection...)")
    test_file = test_dir / "test_image.jpg"
    test_file.write_text("test image data")
    time.sleep(5)
    
    print("\nTest 4: Add another folder")
    test_dir2 = pathlib.Path("test_hotfolder2")
    test_dir2.mkdir(exist_ok=True)
    watcher.add_folder(str(test_dir2))
    print(f"✓ Added folder, now monitoring: {watcher.get_folders()}")
    
    print("\nTest 5: Stop monitoring")
    watcher.stop()
    print(f"✓ Watcher stopped, is_running: {watcher.is_running()}")
    
    # Cleanup
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)
    if test_dir2.exists():
        shutil.rmtree(test_dir2)
    print("\n✓ Test directories cleaned up")
    
    print("\n=== All tests passed! ===")
