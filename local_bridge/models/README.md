# Database Models Documentation

## Overview

This module provides SQLAlchemy-based database models for the Junmai AutoDev system. The database stores information about photo sessions, photos, processing jobs, presets, statistics, and learning data.

## Database Schema

### Tables

1. **sessions** - Photo import/processing sessions
2. **photos** - Photo metadata and processing status
3. **jobs** - Processing job queue
4. **presets** - Development presets with context mapping
5. **statistics** - Daily/session statistics
6. **learning_data** - User approval/rejection learning data

## Usage

### Initialization

```python
from models.database import init_db, get_session

# Initialize database (creates tables if they don't exist)
init_db('sqlite:///data/junmai.db')

# Get a database session
db = get_session()
```

### Creating Records

```python
from models.database import Session, Photo, Job
from datetime import datetime

# Create a session
session = Session(
    name='Wedding 2025-11-08',
    import_folder='D:/Photos/Wedding',
    status='importing'
)
db.add(session)
db.commit()

# Create a photo
photo = Photo(
    session_id=session.id,
    file_path='D:/Photos/Wedding/IMG_001.CR3',
    file_name='IMG_001.CR3',
    camera_make='Canon',
    camera_model='EOS R5',
    status='imported'
)
db.add(photo)
db.commit()

# Create a job
job = Job(
    id='job-001',
    photo_id=photo.id,
    priority=2,
    status='pending'
)
job.set_config({
    'version': '1.0',
    'pipeline': [...],
    'safety': {'snapshot': True, 'dryRun': False}
})
db.add(job)
db.commit()
```

### Querying Records

```python
# Get all pending jobs
pending_jobs = db.query(Job).filter_by(status='pending').all()

# Get photos by session
photos = db.query(Photo).filter_by(session_id=1).all()

# Get photos with high AI scores
good_photos = db.query(Photo).filter(Photo.ai_score >= 4.0).all()

# Get session with relationships
session = db.query(Session).filter_by(id=1).first()
print(f"Session has {len(session.photos)} photos")
```

### Updating Records

```python
# Update photo status
photo = db.query(Photo).filter_by(id=1).first()
photo.status = 'processing'
photo.ai_score = 4.5
db.commit()

# Update job status
job = db.query(Job).filter_by(id='job-001').first()
job.status = 'completed'
job.completed_at = datetime.now()
db.commit()
```

### Working with JSON Fields

```python
from models.database import Preset, LearningData

# Preset with JSON fields
preset = Preset(name='MyPreset', version='v1')
preset.set_context_tags(['portrait', 'backlit'])
preset.set_config_template({
    'version': '1.0',
    'pipeline': [...]
})
db.add(preset)
db.commit()

# Retrieve JSON data
tags = preset.get_context_tags()  # Returns list
config = preset.get_config_template()  # Returns dict

# Learning data with adjustments
learning = LearningData(
    photo_id=1,
    action='modified',
    original_preset='Preset_v1',
    final_preset='Preset_v1'
)
learning.set_parameter_adjustments({
    'Exposure2012': 0.5,
    'Highlights2012': -10
})
db.add(learning)
db.commit()
```

## Model Reference

### Session

Represents a photo import/processing session.

**Fields:**
- `id` - Primary key
- `name` - Session name
- `created_at` - Creation timestamp
- `import_folder` - Source folder path
- `total_photos` - Total photo count
- `processed_photos` - Processed photo count
- `status` - Session status (importing, selecting, developing, exporting, completed)

**Relationships:**
- `photos` - List of photos in this session
- `statistics` - Statistics for this session

### Photo

Stores photo metadata and processing information.

**Fields:**
- `id` - Primary key
- `session_id` - Foreign key to session
- `file_path` - Full file path (unique)
- `file_name` - File name
- `file_size` - File size in bytes
- `import_time` - Import timestamp
- EXIF fields: `camera_make`, `camera_model`, `lens`, `focal_length`, `aperture`, `shutter_speed`, `iso`, `capture_time`, `gps_lat`, `gps_lon`
- AI evaluation: `ai_score`, `focus_score`, `exposure_score`, `composition_score`, `subject_type`, `detected_faces`
- Context: `context_tag`, `selected_preset`
- Processing: `status`, `lr_catalog_id`, `virtual_copy_id`
- Approval: `approved`, `approved_at`, `rejection_reason`

**Relationships:**
- `session` - Parent session
- `jobs` - Processing jobs for this photo
- `learning_data` - Learning records for this photo

**Methods:**
- `to_dict()` - Convert to dictionary for API responses

### Job

Represents a processing job in the queue.

**Fields:**
- `id` - Job ID (primary key)
- `photo_id` - Foreign key to photo
- `priority` - Priority (1=high, 2=medium, 3=low)
- `config_json` - Job configuration (JSON string)
- `status` - Job status (pending, processing, completed, failed)
- `created_at` - Creation timestamp
- `started_at` - Start timestamp
- `completed_at` - Completion timestamp
- `error_message` - Error message if failed
- `retry_count` - Number of retries

**Methods:**
- `get_config()` - Parse and return config as dict
- `set_config(dict)` - Set config from dictionary

### Preset

Stores development presets with context mapping.

**Fields:**
- `id` - Primary key
- `name` - Preset name (unique)
- `version` - Preset version
- `context_tags` - Context tags (JSON array)
- `config_template` - Configuration template (JSON)
- `blend_amount` - Blend amount (0-100)
- `usage_count` - Usage counter
- `avg_approval_rate` - Average approval rate
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

**Methods:**
- `get_context_tags()` - Parse and return tags as list
- `set_context_tags(list)` - Set tags from list
- `get_config_template()` - Parse and return config as dict
- `set_config_template(dict)` - Set config from dictionary

### Statistic

Stores daily/session statistics.

**Fields:**
- `id` - Primary key
- `date` - Statistics date
- `session_id` - Foreign key to session (optional)
- `total_imported` - Total imported photos
- `total_selected` - Total selected photos
- `total_processed` - Total processed photos
- `total_exported` - Total exported photos
- `avg_processing_time` - Average processing time
- `success_rate` - Success rate (0.0-1.0)
- `preset_usage` - Preset usage counts (JSON)

**Methods:**
- `get_preset_usage()` - Parse and return usage as dict
- `set_preset_usage(dict)` - Set usage from dictionary

### LearningData

Stores user approval/rejection learning data.

**Fields:**
- `id` - Primary key
- `photo_id` - Foreign key to photo
- `action` - User action (approved, rejected, modified)
- `original_preset` - Original preset name
- `final_preset` - Final preset name
- `parameter_adjustments` - Parameter adjustments (JSON)
- `timestamp` - Action timestamp

**Methods:**
- `get_parameter_adjustments()` - Parse and return adjustments as dict
- `set_parameter_adjustments(dict)` - Set adjustments from dictionary

## Database Migrations

This project uses Alembic for database migrations.

### Initialize Database

```bash
# Create database and seed initial data
python init_database.py

# Or without seeding
python init_database.py --no-seed
```

### Create Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1
```

### View Migration Status

```bash
# Show current version
alembic current

# Show migration history
alembic history
```

## Testing

Run the test script to verify database functionality:

```bash
python test_database.py
```

This will:
1. Create a test database
2. Create sample records for all tables
3. Test relationships
4. Test JSON field operations
5. Verify all operations

## Best Practices

1. **Always use sessions properly:**
   ```python
   db = get_session()
   try:
       # Your database operations
       db.commit()
   except Exception as e:
       db.rollback()
       raise
   finally:
       db.close()
   ```

2. **Use context managers for automatic cleanup:**
   ```python
   from contextlib import contextmanager
   
   @contextmanager
   def db_session():
       db = get_session()
       try:
           yield db
           db.commit()
       except Exception:
           db.rollback()
           raise
       finally:
           db.close()
   
   # Usage
   with db_session() as db:
       photo = Photo(...)
       db.add(photo)
   ```

3. **Index usage for performance:**
   - Photos are indexed by `session_id` and `status`
   - Jobs are indexed by `status` and `priority`
   - Statistics are indexed by `date`

4. **JSON field best practices:**
   - Always use the provided getter/setter methods
   - Don't modify JSON strings directly
   - Validate JSON structure before setting

## Troubleshooting

### Database locked error
SQLite can have locking issues with concurrent access. Use connection pooling or consider PostgreSQL for production.

### Migration conflicts
If migrations conflict with existing schema:
```bash
# Stamp current version without running migrations
alembic stamp head
```

### Reset database
To completely reset the database:
```bash
# Delete database file
rm data/junmai.db

# Reinitialize
python init_database.py
```
