"""
File Import Processing for Junmai AutoDev

This module provides file import functionality including:
- Automatic import to Lightroom catalog
- File copy/move operations
- Duplicate file detection
- Import error handling

Requirements: 1.3, 1.4, 1.5
"""

import os
import shutil
import hashlib
import logging
import pathlib
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session as DBSession

from models.database import Session, Photo, get_session

logger = logging.getLogger(__name__)


class DuplicateFileError(Exception):
    """Exception raised when a duplicate file is detected"""
    pass


class ImportError(Exception):
    """Exception raised when file import fails"""
    pass


class FileImportProcessor:
    """
    File Import Processor
    
    Handles automatic import of photos to Lightroom catalog with
    duplicate detection and error handling.
    """
    
    def __init__(self, 
                 catalog_path: Optional[str] = None,
                 import_mode: str = 'copy',
                 destination_folder: Optional[str] = None):
        """
        Initialize FileImportProcessor
        
        Args:
            catalog_path: Path to Lightroom catalog (optional, for future integration)
            import_mode: Import mode - 'copy', 'move', or 'add' (in-place)
            destination_folder: Destination folder for copy/move operations
        """
        self.catalog_path = catalog_path
        self.import_mode = import_mode
        self.destination_folder = destination_folder
        
        # Validate import mode
        if import_mode not in ['copy', 'move', 'add']:
            raise ValueError(f"Invalid import mode: {import_mode}. Must be 'copy', 'move', or 'add'")
        
        # Validate destination folder for copy/move modes
        if import_mode in ['copy', 'move'] and not destination_folder:
            raise ValueError(f"Destination folder required for '{import_mode}' mode")
        
        # Create destination folder if it doesn't exist
        if destination_folder:
            pathlib.Path(destination_folder).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FileImportProcessor initialized: mode={import_mode}, dest={destination_folder}")
    
    def calculate_file_hash(self, file_path: str, algorithm: str = 'md5') -> str:
        """
        Calculate hash of file for duplicate detection
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm ('md5', 'sha256')
            
        Returns:
            Hex digest of file hash
        """
        hash_func = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_func.update(chunk)
            
            file_hash = hash_func.hexdigest()
            logger.debug(f"Calculated {algorithm} hash for {file_path}: {file_hash}")
            return file_hash
            
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            raise
    
    def check_duplicate(self, file_path: str, db_session: DBSession) -> Optional[Photo]:
        """
        Check if file already exists in database
        
        Checks by:
        1. File path (exact match)
        2. File name + size (potential duplicate)
        3. File hash (definitive duplicate)
        
        Args:
            file_path: Path to file to check
            db_session: Database session
            
        Returns:
            Existing Photo object if duplicate found, None otherwise
        """
        path = pathlib.Path(file_path)
        file_name = path.name
        
        try:
            file_size = path.stat().st_size
        except OSError as e:
            logger.error(f"Failed to get file size for {file_path}: {e}")
            raise
        
        # Check 1: Exact file path match
        existing = db_session.query(Photo).filter(Photo.file_path == str(path.absolute())).first()
        if existing:
            logger.info(f"Duplicate detected by path: {file_path}")
            return existing
        
        # Check 2: Same name and size (potential duplicate)
        potential_duplicates = db_session.query(Photo).filter(
            Photo.file_name == file_name,
            Photo.file_size == file_size
        ).all()
        
        if potential_duplicates:
            # Check 3: Calculate hash for definitive check
            try:
                file_hash = self.calculate_file_hash(file_path)
                
                for photo in potential_duplicates:
                    # Calculate hash of existing file if it still exists
                    if os.path.exists(photo.file_path):
                        existing_hash = self.calculate_file_hash(photo.file_path)
                        if file_hash == existing_hash:
                            logger.info(f"Duplicate detected by hash: {file_path} matches {photo.file_path}")
                            return photo
            except Exception as e:
                logger.warning(f"Hash comparison failed: {e}")
        
        logger.debug(f"No duplicate found for {file_path}")
        return None
    
    def copy_file(self, source_path: str, destination_folder: str) -> str:
        """
        Copy file to destination folder
        
        Args:
            source_path: Source file path
            destination_folder: Destination folder path
            
        Returns:
            Path to copied file
            
        Raises:
            ImportError: If copy operation fails
        """
        source = pathlib.Path(source_path)
        dest_folder = pathlib.Path(destination_folder)
        
        # Create destination folder if it doesn't exist
        dest_folder.mkdir(parents=True, exist_ok=True)
        
        # Generate destination path
        dest_path = dest_folder / source.name
        
        # Handle name collision
        counter = 1
        while dest_path.exists():
            stem = source.stem
            suffix = source.suffix
            dest_path = dest_folder / f"{stem}_{counter}{suffix}"
            counter += 1
        
        try:
            logger.info(f"Copying file: {source_path} -> {dest_path}")
            shutil.copy2(source_path, dest_path)
            
            # Verify copy
            if not dest_path.exists():
                raise ImportError(f"Copy verification failed: {dest_path} does not exist")
            
            source_size = source.stat().st_size
            dest_size = dest_path.stat().st_size
            
            if source_size != dest_size:
                raise ImportError(f"Copy verification failed: size mismatch ({source_size} != {dest_size})")
            
            logger.info(f"File copied successfully: {dest_path}")
            return str(dest_path)
            
        except Exception as e:
            logger.error(f"Failed to copy file {source_path}: {e}")
            # Clean up partial copy
            if dest_path.exists():
                try:
                    dest_path.unlink()
                except:
                    pass
            raise ImportError(f"Failed to copy file: {e}")
    
    def move_file(self, source_path: str, destination_folder: str) -> str:
        """
        Move file to destination folder
        
        Args:
            source_path: Source file path
            destination_folder: Destination folder path
            
        Returns:
            Path to moved file
            
        Raises:
            ImportError: If move operation fails
        """
        source = pathlib.Path(source_path)
        dest_folder = pathlib.Path(destination_folder)
        
        # Create destination folder if it doesn't exist
        dest_folder.mkdir(parents=True, exist_ok=True)
        
        # Generate destination path
        dest_path = dest_folder / source.name
        
        # Handle name collision
        counter = 1
        while dest_path.exists():
            stem = source.stem
            suffix = source.suffix
            dest_path = dest_folder / f"{stem}_{counter}{suffix}"
            counter += 1
        
        try:
            logger.info(f"Moving file: {source_path} -> {dest_path}")
            shutil.move(source_path, dest_path)
            
            # Verify move
            if not dest_path.exists():
                raise ImportError(f"Move verification failed: {dest_path} does not exist")
            
            if source.exists():
                raise ImportError(f"Move verification failed: source file still exists at {source_path}")
            
            logger.info(f"File moved successfully: {dest_path}")
            return str(dest_path)
            
        except Exception as e:
            logger.error(f"Failed to move file {source_path}: {e}")
            raise ImportError(f"Failed to move file: {e}")
    
    def create_photo_record(self, 
                           file_path: str, 
                           session_id: Optional[int] = None,
                           db_session: Optional[DBSession] = None) -> Photo:
        """
        Create photo record in database
        
        Args:
            file_path: Path to photo file
            session_id: Optional session ID to associate with
            db_session: Database session (will create new one if not provided)
            
        Returns:
            Created Photo object
        """
        close_session = False
        if db_session is None:
            db_session = get_session()
            close_session = True
        
        try:
            path = pathlib.Path(file_path)
            
            # Get file info
            file_stat = path.stat()
            
            # Create photo record
            photo = Photo(
                session_id=session_id,
                file_path=str(path.absolute()),
                file_name=path.name,
                file_size=file_stat.st_size,
                import_time=datetime.utcnow(),
                status='imported'
            )
            
            db_session.add(photo)
            db_session.commit()
            
            logger.info(f"Created photo record: id={photo.id}, file={photo.file_name}")
            
            return photo
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Failed to create photo record for {file_path}: {e}")
            raise
        finally:
            if close_session:
                db_session.close()
    
    def import_file(self, 
                   file_path: str, 
                   session_id: Optional[int] = None,
                   check_duplicates: bool = True,
                   db_session: Optional[DBSession] = None) -> Tuple[Photo, str]:
        """
        Import file to Lightroom catalog
        
        Performs the following steps:
        1. Check for duplicates (if enabled)
        2. Copy/move file to destination (if configured)
        3. Create photo record in database
        4. Return photo record and final file path
        
        Args:
            file_path: Path to file to import
            session_id: Optional session ID to associate with
            check_duplicates: Whether to check for duplicates
            db_session: Database session (will create new one if not provided)
            
        Returns:
            Tuple of (Photo object, final file path)
            
        Raises:
            DuplicateFileError: If duplicate is detected and check_duplicates is True
            ImportError: If import operation fails
        """
        close_session = False
        if db_session is None:
            db_session = get_session()
            close_session = True
        
        try:
            logger.info(f"Starting import for file: {file_path}")
            
            # Validate file exists
            if not os.path.exists(file_path):
                raise ImportError(f"File does not exist: {file_path}")
            
            # Check for duplicates BEFORE file operations
            if check_duplicates:
                duplicate = self.check_duplicate(file_path, db_session)
                if duplicate:
                    raise DuplicateFileError(
                        f"Duplicate file detected: {file_path} already exists as {duplicate.file_path}"
                    )
            
            # Perform file operation based on import mode
            final_path = file_path
            
            if self.import_mode == 'copy':
                final_path = self.copy_file(file_path, self.destination_folder)
                # After copying, check if the destination file already exists in database
                if check_duplicates:
                    existing = db_session.query(Photo).filter(
                        Photo.file_path == str(pathlib.Path(final_path).absolute())
                    ).first()
                    if existing:
                        # Clean up the copied file
                        try:
                            os.remove(final_path)
                        except:
                            pass
                        raise DuplicateFileError(
                            f"Duplicate file detected: destination {final_path} already exists in database"
                        )
            elif self.import_mode == 'move':
                final_path = self.move_file(file_path, self.destination_folder)
                # After moving, check if the destination file already exists in database
                if check_duplicates:
                    existing = db_session.query(Photo).filter(
                        Photo.file_path == str(pathlib.Path(final_path).absolute())
                    ).first()
                    if existing:
                        raise DuplicateFileError(
                            f"Duplicate file detected: destination {final_path} already exists in database"
                        )
            elif self.import_mode == 'add':
                # In-place import, no file operation needed
                final_path = str(pathlib.Path(file_path).absolute())
            
            # Create photo record
            photo = self.create_photo_record(final_path, session_id, db_session)
            
            logger.info(f"Successfully imported file: {file_path} -> {final_path} (photo_id={photo.id})")
            
            return photo, final_path
            
        except DuplicateFileError:
            # Re-raise duplicate errors
            raise
        except Exception as e:
            logger.error(f"Failed to import file {file_path}: {e}", exc_info=True)
            raise ImportError(f"Failed to import file: {e}")
        finally:
            if close_session:
                db_session.close()
    
    def import_batch(self, 
                    file_paths: List[str], 
                    session_id: Optional[int] = None,
                    check_duplicates: bool = True,
                    skip_on_error: bool = True) -> Dict[str, any]:
        """
        Import multiple files in batch
        
        Args:
            file_paths: List of file paths to import
            session_id: Optional session ID to associate with
            check_duplicates: Whether to check for duplicates
            skip_on_error: Whether to skip files that fail import
            
        Returns:
            Dictionary with import results:
            {
                'success': [list of successfully imported photos],
                'duplicates': [list of duplicate file paths],
                'errors': [list of (file_path, error_message) tuples],
                'total': total number of files,
                'imported': number of successfully imported files
            }
        """
        results = {
            'success': [],
            'duplicates': [],
            'errors': [],
            'total': len(file_paths),
            'imported': 0
        }
        
        db_session = get_session()
        
        try:
            for file_path in file_paths:
                try:
                    photo, final_path = self.import_file(
                        file_path, 
                        session_id, 
                        check_duplicates, 
                        db_session
                    )
                    results['success'].append({
                        'photo_id': photo.id,
                        'file_name': photo.file_name,
                        'original_path': file_path,
                        'final_path': final_path
                    })
                    results['imported'] += 1
                    
                except DuplicateFileError as e:
                    logger.warning(f"Duplicate file skipped: {file_path}")
                    results['duplicates'].append(file_path)
                    if not skip_on_error:
                        raise
                    
                except Exception as e:
                    logger.error(f"Failed to import {file_path}: {e}")
                    results['errors'].append((file_path, str(e)))
                    if not skip_on_error:
                        raise
            
            logger.info(f"Batch import completed: {results['imported']}/{results['total']} files imported")
            
            return results
            
        finally:
            db_session.close()
    
    def get_or_create_session(self, 
                             session_name: str, 
                             import_folder: str,
                             db_session: Optional[DBSession] = None) -> Session:
        """
        Get existing session or create new one
        
        Args:
            session_name: Name of session
            import_folder: Import folder path
            db_session: Database session (will create new one if not provided)
            
        Returns:
            Session object
        """
        close_session = False
        if db_session is None:
            db_session = get_session()
            close_session = True
        
        try:
            # Try to find existing session
            session = db_session.query(Session).filter(
                Session.name == session_name,
                Session.import_folder == import_folder
            ).first()
            
            if session:
                logger.info(f"Found existing session: {session_name} (id={session.id})")
                return session
            
            # Create new session
            session = Session(
                name=session_name,
                import_folder=import_folder,
                status='importing'
            )
            
            db_session.add(session)
            db_session.commit()
            
            logger.info(f"Created new session: {session_name} (id={session.id})")
            
            return session
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Failed to get or create session: {e}")
            raise
        finally:
            if close_session:
                db_session.close()


def create_file_import_processor(config: Dict) -> FileImportProcessor:
    """
    Factory function to create FileImportProcessor from configuration
    
    Args:
        config: Configuration dictionary with keys:
            - catalog_path: Path to Lightroom catalog (optional)
            - import_mode: Import mode ('copy', 'move', 'add')
            - destination_folder: Destination folder for copy/move
            
    Returns:
        Configured FileImportProcessor instance
    """
    return FileImportProcessor(
        catalog_path=config.get('catalog_path'),
        import_mode=config.get('import_mode', 'copy'),
        destination_folder=config.get('destination_folder')
    )


if __name__ == '__main__':
    # Setup logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize database
    from models.database import init_db
    init_db('sqlite:///data/junmai_test.db')
    
    print("=== Testing File Import Processor ===\n")
    
    # Create test directories
    test_source = pathlib.Path("test_import_source")
    test_dest = pathlib.Path("test_import_dest")
    test_source.mkdir(exist_ok=True)
    test_dest.mkdir(exist_ok=True)
    
    # Create test files
    test_file1 = test_source / "test_photo1.jpg"
    test_file2 = test_source / "test_photo2.jpg"
    test_file1.write_text("test photo 1 data")
    test_file2.write_text("test photo 2 data")
    
    print(f"Test 1: Create processor with copy mode")
    processor = FileImportProcessor(
        import_mode='copy',
        destination_folder=str(test_dest)
    )
    print(f"✓ Processor created: mode={processor.import_mode}")
    
    print(f"\nTest 2: Import single file")
    photo, final_path = processor.import_file(str(test_file1))
    print(f"✓ File imported: photo_id={photo.id}, path={final_path}")
    
    print(f"\nTest 3: Detect duplicate")
    try:
        processor.import_file(str(test_file1), check_duplicates=True)
        print("✗ Duplicate detection failed")
    except DuplicateFileError as e:
        print(f"✓ Duplicate detected: {e}")
    
    print(f"\nTest 4: Batch import")
    results = processor.import_batch([str(test_file2)])
    print(f"✓ Batch import: {results['imported']}/{results['total']} files imported")
    
    print(f"\nTest 5: Create session")
    session = processor.get_or_create_session("Test Session", str(test_source))
    print(f"✓ Session created: id={session.id}, name={session.name}")
    
    # Cleanup
    import shutil
    if test_source.exists():
        shutil.rmtree(test_source)
    if test_dest.exists():
        shutil.rmtree(test_dest)
    print("\n✓ Test directories cleaned up")
    
    print("\n=== All tests passed! ===")
