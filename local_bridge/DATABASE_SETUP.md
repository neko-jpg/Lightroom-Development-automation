# Database Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd local_bridge
pip install -r requirements.txt
```

This will install:
- SQLAlchemy 2.0.44 (ORM)
- Alembic 1.17.1 (Migrations)

### 2. Initialize Database

```bash
python init_database.py
```

This will:
- Create `data/junmai.db` SQLite database
- Create all tables (sessions, photos, jobs, presets, statistics, learning_data)
- Seed 3 default presets
- Verify the setup

**Output:**
```
Initializing database at: sqlite:///data/junmai.db
✓ Database schema created successfully
✓ Tables created: sessions, photos, jobs, presets, statistics, learning_data

Seeding initial data...
✓ Seeded 3 default presets

Verifying database...
  ✓ Table 'sessions': 0 records
  ✓ Table 'photos': 0 records
  ✓ Table 'jobs': 0 records
  ✓ Table 'presets': 3 records
  ✓ Table 'statistics': 0 records
  ✓ Table 'learning_data': 0 records

✓ Database verification complete
```

### 3. Test Database

```bash
python test_database.py
```

This will run comprehensive tests on all database operations.

## Database Structure

### Tables Overview

| Table | Purpose | Key Fields |
|-------|---------|------------|
| **sessions** | Photo import sessions | name, status, total_photos |
| **photos** | Photo metadata & AI scores | file_path, ai_score, status |
| **jobs** | Processing job queue | priority, config_json, status |
| **presets** | Development presets | name, version, context_tags |
| **statistics** | Daily/session stats | date, success_rate, preset_usage |
| **learning_data** | User learning data | action, parameter_adjustments |

### Relationships

```
Session (1) ──< (N) Photo
Photo (1) ──< (N) Job
Photo (1) ──< (N) LearningData
Session (1) ──< (N) Statistic
```

## Migration Management

### Current Migration Status

```bash
alembic current
```

### Create New Migration

When you modify models in `models/database.py`:

```bash
alembic revision --autogenerate -m "Add new field to photos table"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Downgrade one version
alembic downgrade -1
```

### Migration History

```bash
alembic history
```

## Usage Examples

### Basic Operations

```python
from models.database import init_db, get_session, Session, Photo

# Initialize
init_db('sqlite:///data/junmai.db')
db = get_session()

# Create session
session = Session(name='Wedding 2025-11-08', status='importing')
db.add(session)
db.commit()

# Create photo
photo = Photo(
    session_id=session.id,
    file_path='D:/Photos/IMG_001.CR3',
    file_name='IMG_001.CR3',
    status='imported'
)
db.add(photo)
db.commit()

# Query
pending_jobs = db.query(Job).filter_by(status='pending').all()
```

### JSON Field Operations

```python
from models.database import Preset, Job

# Preset with context tags
preset = Preset(name='MyPreset', version='v1')
preset.set_context_tags(['portrait', 'backlit'])
preset.set_config_template({
    'version': '1.0',
    'pipeline': [...]
})

# Job with config
job = Job(id='job-001', priority=2, status='pending')
job.set_config({
    'version': '1.0',
    'pipeline': [...],
    'safety': {'snapshot': True}
})
```

## Default Presets

The database is seeded with 3 default presets:

1. **WhiteLayer_Transparency_v4**
   - Context: backlit_portrait, soft_light, portrait
   - Blend: 60%
   - Use: Backlit portraits with soft skin tones

2. **LowLight_NR_v2**
   - Context: low_light_indoor, night, high_iso
   - Blend: 80%
   - Use: Indoor/night photography with noise reduction

3. **Landscape_Sky_v3**
   - Context: landscape_sky, outdoor, landscape
   - Blend: 70%
   - Use: Landscape photography with sky enhancement

## Configuration

### Database Location

Default: `local_bridge/data/junmai.db`

To change:
```python
init_db('sqlite:///path/to/custom.db')
```

Or in `alembic.ini`:
```ini
sqlalchemy.url = sqlite:///path/to/custom.db
```

### Connection Pooling

For SQLite, the system uses `StaticPool` to avoid threading issues.

For production with PostgreSQL:
```python
init_db('postgresql://user:pass@localhost/junmai')
```

## Troubleshooting

### Issue: "table already exists"

If you see this error during migration:

```bash
# Stamp the database with current version
alembic stamp head
```

### Issue: "Database is locked"

SQLite can lock with concurrent access. Solutions:
1. Ensure proper session cleanup (use `db.close()`)
2. Use connection pooling
3. Consider PostgreSQL for production

### Issue: Migration conflicts

If migrations are out of sync:

```bash
# Check current version
alembic current

# View history
alembic history

# Stamp to specific version
alembic stamp <revision_id>
```

### Reset Database

To start fresh:

```bash
# Windows
del data\junmai.db
python init_database.py

# Linux/Mac
rm data/junmai.db
python init_database.py
```

## Performance Tips

1. **Use indexes** - Already configured for common queries
2. **Batch operations** - Use `db.add_all()` for multiple records
3. **Connection pooling** - Reuse database connections
4. **Query optimization** - Use `filter()` instead of loading all records

## Security

1. **No sensitive data** - Database stores only photo metadata
2. **Local storage** - SQLite file is stored locally
3. **Backup recommended** - Regular backups of `data/junmai.db`
4. **Access control** - File system permissions protect the database

## Next Steps

After database setup:
1. Integrate with hot folder monitoring (Task 4)
2. Implement EXIF analyzer (Task 6)
3. Build AI selection engine (Task 8)
4. Create REST API endpoints (Task 29)

## Support

For issues or questions:
1. Check `models/README.md` for detailed API documentation
2. Run `python test_database.py` to verify setup
3. Review Alembic logs for migration issues
