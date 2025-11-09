# Data Migration Tool - Quick Reference

## Overview

The Data Migration Tool provides safe and reliable database migration functionality for Junmai AutoDev, including:
- **Automatic backup** before migration
- **Data integrity verification** after migration
- **Rollback capability** via backup restore
- **Detailed migration logging**

## Quick Start

### 1. Basic Migration (with automatic backup)

```bash
# Migrate from old database to new schema
py local_bridge/data_migration_tool.py --source data/junmai.db --target data/junmai_new.db
```

This will:
1. Create a timestamped backup in `data/backups/`
2. Migrate all data to the new database
3. Verify data integrity
4. Generate a migration log

### 2. Backup Only

```bash
# Create backup without migrating
py local_bridge/data_migration_tool.py --source data/junmai.db --backup-only
```

### 3. Restore from Backup

```bash
# Restore database from a specific backup
py local_bridge/data_migration_tool.py --source data/junmai.db --restore data/backups/junmai_backup_20250108_120000.db
```

### 4. Verify Existing Migration

```bash
# Verify data integrity of an existing migration
py local_bridge/data_migration_tool.py --source data/junmai.db --target data/junmai_new.db --verify-only
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--source PATH` | Path to source database (required) |
| `--target PATH` | Path to target database (default: source with .new.db suffix) |
| `--backup-dir PATH` | Directory for backups (default: ./data/backups) |
| `--backup-only` | Only create backup, do not migrate |
| `--restore BACKUP` | Restore from specified backup file |
| `--verify-only` | Only verify existing migration |
| `--no-backup` | Skip backup creation (not recommended) |

## Migration Process

### Step 1: Backup
- Creates timestamped backup file
- Calculates SHA256 checksum
- Saves metadata (timestamp, size, checksum)

### Step 2: Migration
Migrates the following tables in order:
1. **sessions** - Session management data
2. **photos** - Photo metadata and EXIF data
3. **jobs** - Job queue data
4. **presets** - Preset configurations
5. **statistics** - Usage statistics
6. **learning_data** - User learning data

### Step 3: Verification
- Compares record counts between source and target
- Verifies data integrity (sample checks)
- Checks foreign key relationships
- Detects orphaned records

### Step 4: Logging
- Saves detailed migration log
- Includes all steps, timestamps, and results
- Stores verification results

## Backup Files

### Backup Naming Convention
```
junmai_backup_YYYYMMDD_HHMMSS.db
```

### Backup Metadata
Each backup includes a JSON metadata file:
```json
{
  "original_path": "data/junmai.db",
  "backup_path": "data/backups/junmai_backup_20250108_120000.db",
  "timestamp": "20250108_120000",
  "checksum": "abc123...",
  "file_size": 1048576
}
```

## Migration Log

### Log File Location
```
data/backups/migration_log_YYYYMMDD_HHMMSS.json
```

### Log Structure
```json
{
  "source_db": "data/junmai.db",
  "target_db": "data/junmai_new.db",
  "backup_path": "data/backups/junmai_backup_20250108_120000.db",
  "migration_log": [
    {
      "step": "backup",
      "status": "success",
      "timestamp": "2025-01-08T12:00:00",
      "backup_path": "..."
    },
    {
      "step": "migration",
      "status": "success",
      "timestamp": "2025-01-08T12:00:30",
      "stats": {
        "sessions": 5,
        "photos": 127,
        "jobs": 45,
        "presets": 3,
        "statistics": 10,
        "learning_data": 89
      }
    },
    {
      "step": "verification",
      "status": "success",
      "timestamp": "2025-01-08T12:01:00",
      "results": {...}
    }
  ],
  "verification_results": {
    "success": true,
    "checks": {...},
    "errors": []
  }
}
```

## Common Scenarios

### Scenario 1: Upgrading to New Version

```bash
# 1. Create backup
py local_bridge/data_migration_tool.py --source data/junmai.db --backup-only

# 2. Perform migration
py local_bridge/data_migration_tool.py --source data/junmai.db --target data/junmai_new.db

# 3. Test new database
# ... test your application with junmai_new.db ...

# 4. If satisfied, replace old database
mv data/junmai.db data/junmai_old.db
mv data/junmai_new.db data/junmai.db
```

### Scenario 2: Rollback After Failed Migration

```bash
# If migration fails or has issues, restore from backup
py local_bridge/data_migration_tool.py --source data/junmai.db --restore data/backups/junmai_backup_20250108_120000.db
```

### Scenario 3: Regular Backups

```bash
# Create regular backups (e.g., via cron/scheduled task)
py local_bridge/data_migration_tool.py --source data/junmai.db --backup-only
```

### Scenario 4: Verify Data Integrity

```bash
# Verify existing database integrity
py local_bridge/data_migration_tool.py --source data/junmai.db --target data/junmai.db --verify-only
```

## Verification Checks

The tool performs the following verification checks:

### 1. Record Count Verification
- Compares total records in each table
- Ensures no data loss during migration

### 2. Data Integrity Checks
- Samples records from each table
- Verifies field values match between source and target

### 3. Foreign Key Integrity
- Checks for orphaned records
- Verifies all foreign key relationships

### 4. Checksum Verification
- Validates backup file integrity
- Detects file corruption

## Error Handling

### Migration Failures
- Automatic rollback on error
- Detailed error logging
- Backup remains intact

### Verification Failures
- Lists all detected issues
- Provides specific error messages
- Suggests corrective actions

## Best Practices

1. **Always create backups** before migration
2. **Test migrations** on a copy first
3. **Verify results** after migration
4. **Keep backups** for at least 30 days
5. **Review logs** for any warnings
6. **Test application** with new database before replacing old one

## Troubleshooting

### Issue: "Source database not found"
**Solution**: Check the path to your database file

### Issue: "Backup checksum mismatch"
**Solution**: Backup file may be corrupted, create a new backup

### Issue: "Record count mismatch"
**Solution**: Review migration log for errors, restore from backup if needed

### Issue: "Orphaned records detected"
**Solution**: Check foreign key relationships in source database

### Issue: "Migration failed"
**Solution**: 
1. Check error message in log
2. Restore from backup
3. Fix underlying issue
4. Retry migration

## Python API Usage

```python
from data_migration_tool import DataMigrationTool

# Initialize tool
tool = DataMigrationTool(
    source_db_path='data/junmai.db',
    target_db_path='data/junmai_new.db',
    backup_dir='data/backups'
)

# Create backup
backup_path = tool.create_backup()

# Migrate data
success = tool.migrate_data()

# Verify migration
results = tool.verify_migration()

# Save log
tool.save_migration_log()

# Restore if needed
if not success:
    tool.restore_from_backup(backup_path)
```

## Safety Features

- **Automatic backups** before any destructive operation
- **Checksum verification** for backup integrity
- **Pre-restore backup** when restoring from backup
- **Transaction rollback** on migration errors
- **Detailed logging** for audit trail

## Performance

- **Backup**: ~1-2 seconds for 100MB database
- **Migration**: ~5-10 seconds for 10,000 records
- **Verification**: ~2-3 seconds for 10,000 records

## File Locations

```
data/
├── junmai.db                           # Current database
├── junmai_new.db                       # Migrated database
└── backups/
    ├── junmai_backup_20250108_120000.db
    ├── junmai_backup_20250108_120000.json
    └── migration_log_20250108_120000.json
```

## Support

For issues or questions:
1. Check the migration log for detailed error information
2. Review the troubleshooting section
3. Consult the main documentation

## Related Documentation

- [Database Schema](models/database.py)
- [Installation Guide](../docs/INSTALLATION_GUIDE.md)
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
