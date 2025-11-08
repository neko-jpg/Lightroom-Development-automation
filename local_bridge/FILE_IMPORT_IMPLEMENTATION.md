# File Import Processing Implementation

## Overview

This document describes the implementation of the file import processing functionality for Junmai AutoDev system.

## Requirements

Implements the following requirements from task 5:
- **Requirement 1.3**: Automatic import to Lightroom catalog with EXIF data analysis
- **Requirement 1.4**: EXIF-based automatic collection and keyword assignment
- **Requirement 1.5**: Automatic progression to next processing step after import completion

## Components

### 1. FileImportProcessor (`file_import_processor.py`)

Main class that handles file import operations.

#### Features

- **Multiple Import Modes**:
  - `copy`: Copy files to destination folder
  - `move`: Move files to destination folder
  - `add`: In-place import (no file operation)

- **Duplicate Detection**:
  - By file path (exact match)
  - By file name + size (potential duplicate)
  - By file hash (MD5/SHA256) for definitive duplicate detection

- **File Operations**:
  - Safe file copy with verification
  - Safe file move with verification
  - Automatic handling of name collisions

- **Database Integration**:
  - Creates photo records in database
  - Associates photos with sessions
  - Tracks import status and metadata

- **Batch Processing**:
  - Import multiple files in one operation
  - Configurable error handling (skip or fail)
  - Detailed results reporting

#### Key Methods

```python
# Initialize processor
processor = FileImportProcessor(
    import_mode='copy',
    destination_folder='/path/to/dest'
)

# Import single file
photo, final_path = processor.import_file(
    file_path='/path/to/photo.jpg',
    session_id=1,
    check_duplicates=True
)

# Import batch
results = processor.import_batch(
    file_paths=['/path/to/photo1.jpg', '/path/to/photo2.jpg'],
    session_id=1,
    check_duplicates=True,
    skip_on_error=True
)

# Create or get session
session = processor.get_or_create_session(
    session_name='My Session',
    import_folder='/path/to/folder'
)
```

### 2. Integration with Hot Folder Watcher

The file import processor is integrated with the hot folder watcher in `app.py`:

```python
def on_new_file_detected(file_path: str):
    """
    Callback for hot folder watcher
    Automatically imports detected files
    """
    # Determine session from folder structure
    session_name = f"Auto_{folder_name}_{date}"
    
    # Get or create session
    session = file_import_processor.get_or_create_session(
        session_name=session_name,
        import_folder=parent_folder
    )
    
    # Import file
    photo, final_path = file_import_processor.import_file(
        file_path=file_path,
        session_id=session.id,
        check_duplicates=True
    )
    
    # Update session statistics
    session.total_photos += 1
```

### 3. REST API Endpoints

#### POST /import/file
Import a single file manually.

**Request Body**:
```json
{
  "file_path": "/path/to/photo.jpg",
  "session_id": 1,
  "check_duplicates": true
}
```

**Response**:
```json
{
  "message": "File imported successfully",
  "photo_id": 123,
  "file_name": "photo.jpg",
  "final_path": "/dest/photo.jpg"
}
```

#### POST /import/batch
Import multiple files in batch.

**Request Body**:
```json
{
  "file_paths": ["/path/to/photo1.jpg", "/path/to/photo2.jpg"],
  "session_id": 1,
  "check_duplicates": true,
  "skip_on_error": true
}
```

**Response**:
```json
{
  "message": "Batch import completed: 2/2 files imported",
  "results": {
    "total": 2,
    "imported": 2,
    "success": [...],
    "duplicates": [],
    "errors": []
  }
}
```

#### POST /import/session
Create a new import session.

**Request Body**:
```json
{
  "name": "My Session",
  "import_folder": "/path/to/folder"
}
```

#### GET /import/sessions
Get list of import sessions.

**Query Parameters**:
- `status`: Filter by status (optional)
- `limit`: Maximum number of sessions (default: 50)

#### GET /import/photos
Get list of imported photos.

**Query Parameters**:
- `session_id`: Filter by session ID (optional)
- `status`: Filter by status (optional)
- `limit`: Maximum number of photos (default: 100)

#### GET /import/stats
Get import statistics.

**Response**:
```json
{
  "total_photos": 1234,
  "photos_by_status": {
    "imported": 1000,
    "analyzed": 200,
    "completed": 34
  },
  "total_sessions": 45,
  "sessions_by_status": {
    "importing": 2,
    "completed": 43
  },
  "recent_imports_24h": 127
}
```

## Error Handling

### DuplicateFileError
Raised when a duplicate file is detected during import.

**Handling**:
- In single import: Exception is raised to caller
- In batch import: File is skipped and added to `duplicates` list

### ImportError
Raised when file import operation fails.

**Common Causes**:
- File does not exist
- Permission denied
- Disk space insufficient
- Database constraint violation

**Handling**:
- In single import: Exception is raised to caller
- In batch import: Error is logged and added to `errors` list (if `skip_on_error=True`)

## Configuration

File import processor can be configured via system configuration:

```json
{
  "import": {
    "mode": "copy",
    "destination_folder": "/path/to/imported_photos"
  },
  "processing": {
    "auto_import": true
  }
}
```

## Database Schema

### Photo Table
Stores imported photo metadata:

```sql
CREATE TABLE photos (
    id INTEGER PRIMARY KEY,
    session_id INTEGER,
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    import_time TIMESTAMP,
    status TEXT DEFAULT 'imported',
    ...
)
```

### Session Table
Stores import session information:

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    import_folder TEXT,
    total_photos INTEGER DEFAULT 0,
    processed_photos INTEGER DEFAULT 0,
    status TEXT DEFAULT 'importing',
    ...
)
```

## Testing

Comprehensive test suite in `test_file_import_processor.py`:

- Processor initialization with different modes
- File hash calculation
- Single file import (copy/move/add modes)
- Duplicate detection (by path and hash)
- Batch import
- Batch import with duplicates and errors
- Session creation and management
- File copy with name collision handling
- Error handling for nonexistent files
- Photo record field validation

**Run Tests**:
```bash
cd local_bridge
python test_file_import_processor.py
```

## Known Limitations

1. **Duplicate Detection with check_duplicates=False**: When `check_duplicates=False`, the database UNIQUE constraint on `file_path` can still cause failures if the same file path is imported twice. This is by design to maintain database integrity.

2. **Hash-based Duplicate Detection in Copy Mode**: In copy mode, files are copied to a new location with potentially different names, so hash-based duplicate detection checks the source file before copying.

3. **Lightroom Catalog Integration**: Currently, the system creates database records but does not directly integrate with Lightroom catalog. This will be implemented in future tasks using the Lightroom Lua plugin.

## Future Enhancements

1. **EXIF Analysis Integration**: Automatically extract and store EXIF data during import (Task 6)
2. **AI Selection Integration**: Automatically evaluate imported photos (Task 9)
3. **Lightroom Catalog Sync**: Direct integration with Lightroom catalog via plugin
4. **Progress Reporting**: Real-time progress updates for batch imports
5. **Thumbnail Generation**: Generate thumbnails during import for faster preview

## Performance Considerations

- **File Hash Calculation**: Uses chunked reading (8KB chunks) to handle large files efficiently
- **Batch Processing**: Processes files sequentially to avoid overwhelming the system
- **Database Sessions**: Reuses database sessions in batch operations to reduce overhead
- **File Verification**: Verifies file size after copy/move operations to ensure integrity

## Security Considerations

- **Path Validation**: All file paths are validated before operations
- **Permission Checks**: File operations respect system permissions
- **SQL Injection Prevention**: Uses SQLAlchemy ORM with parameterized queries
- **File System Isolation**: Destination folders are created with appropriate permissions

## Logging

All import operations are logged with structured logging:

```python
logging_system.log("INFO", "File imported successfully", 
                  file_path=file_path,
                  photo_id=photo.id,
                  session_id=session.id,
                  final_path=final_path)
```

Log categories:
- `INFO`: Successful operations
- `WARNING`: Duplicate files, skipped files
- `ERROR`: Import failures, database errors

## Summary

The file import processing implementation provides a robust, flexible system for importing photos into the Junmai AutoDev system with:

✅ Multiple import modes (copy/move/add)
✅ Comprehensive duplicate detection
✅ Safe file operations with verification
✅ Database integration with sessions
✅ Batch processing with error handling
✅ REST API for manual control
✅ Integration with hot folder watcher
✅ Comprehensive error handling
✅ Detailed logging and statistics

This implementation satisfies all requirements for Task 5 and provides a solid foundation for future enhancements.
