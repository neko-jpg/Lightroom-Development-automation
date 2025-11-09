"""
Data Migration Tool for Junmai AutoDev
Provides backup, migration, and verification functionality for database upgrades.
"""

import os
import sys
import json
import shutil
import sqlite3
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from models.database import (
    init_db,
    get_session,
    get_engine,
    Base,
    Session,
    Photo,
    Job,
    Preset,
    Statistic,
    LearningData,
    PhotoGroup,
    ABTest,
    ABTestAssignment,
    DesktopNotification,
    PushSubscription
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataMigrationTool:
    """
    Data migration tool for Junmai AutoDev database.
    Handles backup, migration, and verification of database upgrades.
    """
    
    def __init__(self, source_db_path: str, target_db_path: str = None, backup_dir: str = None):
        """
        Initialize the data migration tool.
        
        Args:
            source_db_path: Path to the source database file
            target_db_path: Path to the target database file (default: source_db_path with .new suffix)
            backup_dir: Directory for backups (default: ./data/backups)
        """
        self.source_db_path = Path(source_db_path)
        
        if target_db_path:
            self.target_db_path = Path(target_db_path)
        else:
            self.target_db_path = self.source_db_path.with_suffix('.new.db')
        
        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            self.backup_dir = self.source_db_path.parent / 'backups'
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.backup_path = None
        self.migration_log = []
        self.verification_results = {}
    
    def create_backup(self) -> str:
        """
        Create a backup of the source database.
        
        Returns:
            Path to the backup file
        """
        logger.info("Creating database backup...")
        
        if not self.source_db_path.exists():
            raise FileNotFoundError(f"Source database not found: {self.source_db_path}")
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{self.source_db_path.stem}_backup_{timestamp}.db"
        self.backup_path = self.backup_dir / backup_filename
        
        try:
            # Copy database file
            shutil.copy2(self.source_db_path, self.backup_path)
            
            # Calculate checksum
            checksum = self._calculate_checksum(self.backup_path)
            
            # Create metadata file
            metadata = {
                'original_path': str(self.source_db_path),
                'backup_path': str(self.backup_path),
                'timestamp': timestamp,
                'checksum': checksum,
                'file_size': self.backup_path.stat().st_size
            }
            
            metadata_path = self.backup_path.with_suffix('.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Backup created: {self.backup_path}")
            logger.info(f"  Size: {metadata['file_size']:,} bytes")
            logger.info(f"  Checksum: {checksum}")
            
            self.migration_log.append({
                'step': 'backup',
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'backup_path': str(self.backup_path)
            })
            
            return str(self.backup_path)
            
        except Exception as e:
            logger.error(f"✗ Backup failed: {e}")
            self.migration_log.append({
                'step': 'backup',
                'status': 'failed',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            })
            raise
    
    def migrate_data(self) -> bool:
        """
        Migrate data from source database to target database.
        
        Returns:
            True if migration successful, False otherwise
        """
        logger.info("Starting data migration...")
        
        try:
            # Initialize target database with new schema
            logger.info(f"Initializing target database: {self.target_db_path}")
            target_url = f'sqlite:///{self.target_db_path}'
            init_db(target_url, echo=False)
            
            # Connect to source database
            source_conn = sqlite3.connect(self.source_db_path)
            source_conn.row_factory = sqlite3.Row
            source_cursor = source_conn.cursor()
            
            # Get target session
            target_session = get_session()
            
            # Migrate each table
            migration_stats = {}
            
            # 1. Migrate sessions
            logger.info("Migrating sessions...")
            sessions_migrated = self._migrate_sessions(source_cursor, target_session)
            migration_stats['sessions'] = sessions_migrated
            
            # 2. Migrate photos
            logger.info("Migrating photos...")
            photos_migrated = self._migrate_photos(source_cursor, target_session)
            migration_stats['photos'] = photos_migrated
            
            # 3. Migrate jobs
            logger.info("Migrating jobs...")
            jobs_migrated = self._migrate_jobs(source_cursor, target_session)
            migration_stats['jobs'] = jobs_migrated
            
            # 4. Migrate presets
            logger.info("Migrating presets...")
            presets_migrated = self._migrate_presets(source_cursor, target_session)
            migration_stats['presets'] = presets_migrated
            
            # 5. Migrate statistics
            logger.info("Migrating statistics...")
            statistics_migrated = self._migrate_statistics(source_cursor, target_session)
            migration_stats['statistics'] = statistics_migrated
            
            # 6. Migrate learning data
            logger.info("Migrating learning data...")
            learning_data_migrated = self._migrate_learning_data(source_cursor, target_session)
            migration_stats['learning_data'] = learning_data_migrated
            
            # Commit all changes
            target_session.commit()
            
            # Close connections
            source_conn.close()
            target_session.close()
            
            logger.info("✓ Data migration completed successfully")
            for table, count in migration_stats.items():
                logger.info(f"  {table}: {count} records migrated")
            
            self.migration_log.append({
                'step': 'migration',
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'stats': migration_stats
            })
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Migration failed: {e}")
            if 'target_session' in locals():
                target_session.rollback()
                target_session.close()
            if 'source_conn' in locals():
                source_conn.close()
            
            self.migration_log.append({
                'step': 'migration',
                'status': 'failed',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            })
            
            return False
    
    def verify_migration(self) -> Dict:
        """
        Verify the migrated data integrity.
        
        Returns:
            Dictionary with verification results
        """
        logger.info("Verifying migration...")
        
        results = {
            'success': True,
            'checks': {},
            'errors': []
        }
        
        try:
            # Connect to both databases
            source_conn = sqlite3.connect(self.source_db_path)
            source_conn.row_factory = sqlite3.Row
            
            target_conn = sqlite3.connect(self.target_db_path)
            target_conn.row_factory = sqlite3.Row
            
            # Verify record counts
            tables = ['sessions', 'photos', 'jobs', 'presets', 'statistics', 'learning_data']
            
            for table in tables:
                source_count = source_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                target_count = target_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                
                match = source_count == target_count
                results['checks'][table] = {
                    'source_count': source_count,
                    'target_count': target_count,
                    'match': match
                }
                
                if match:
                    logger.info(f"  ✓ {table}: {source_count} records")
                else:
                    logger.warning(f"  ✗ {table}: source={source_count}, target={target_count}")
                    results['success'] = False
                    results['errors'].append(f"Record count mismatch in {table}")
            
            # Verify data integrity (sample checks)
            logger.info("Verifying data integrity...")
            
            # Check photos table
            source_photos = source_conn.execute(
                "SELECT id, file_path, file_name FROM photos ORDER BY id LIMIT 10"
            ).fetchall()
            
            for source_photo in source_photos:
                target_photo = target_conn.execute(
                    "SELECT id, file_path, file_name FROM photos WHERE id = ?",
                    (source_photo['id'],)
                ).fetchone()
                
                if not target_photo:
                    results['success'] = False
                    results['errors'].append(f"Photo {source_photo['id']} not found in target")
                elif (source_photo['file_path'] != target_photo['file_path'] or
                      source_photo['file_name'] != target_photo['file_name']):
                    results['success'] = False
                    results['errors'].append(f"Photo {source_photo['id']} data mismatch")
            
            # Check foreign key relationships
            logger.info("Verifying foreign key relationships...")
            
            # Photos -> Sessions
            orphaned_photos = target_conn.execute("""
                SELECT COUNT(*) FROM photos 
                WHERE session_id IS NOT NULL 
                AND session_id NOT IN (SELECT id FROM sessions)
            """).fetchone()[0]
            
            if orphaned_photos > 0:
                results['success'] = False
                results['errors'].append(f"{orphaned_photos} orphaned photos found")
            else:
                logger.info("  ✓ No orphaned photos")
            
            # Jobs -> Photos
            orphaned_jobs = target_conn.execute("""
                SELECT COUNT(*) FROM jobs 
                WHERE photo_id IS NOT NULL 
                AND photo_id NOT IN (SELECT id FROM photos)
            """).fetchone()[0]
            
            if orphaned_jobs > 0:
                results['success'] = False
                results['errors'].append(f"{orphaned_jobs} orphaned jobs found")
            else:
                logger.info("  ✓ No orphaned jobs")
            
            # Close connections
            source_conn.close()
            target_conn.close()
            
            if results['success']:
                logger.info("✓ Migration verification passed")
            else:
                logger.error("✗ Migration verification failed")
                for error in results['errors']:
                    logger.error(f"  - {error}")
            
            self.verification_results = results
            self.migration_log.append({
                'step': 'verification',
                'status': 'success' if results['success'] else 'failed',
                'timestamp': datetime.now().isoformat(),
                'results': results
            })
            
            return results
            
        except Exception as e:
            logger.error(f"✗ Verification failed: {e}")
            results['success'] = False
            results['errors'].append(str(e))
            
            self.migration_log.append({
                'step': 'verification',
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            })
            
            return results
    
    def restore_from_backup(self, backup_path: str = None) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file (default: use last created backup)
        
        Returns:
            True if restore successful, False otherwise
        """
        if backup_path:
            backup_file = Path(backup_path)
        elif self.backup_path:
            backup_file = self.backup_path
        else:
            raise ValueError("No backup path specified")
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        logger.info(f"Restoring from backup: {backup_file}")
        
        try:
            # Verify backup integrity
            metadata_path = backup_file.with_suffix('.json')
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                current_checksum = self._calculate_checksum(backup_file)
                if current_checksum != metadata['checksum']:
                    raise ValueError("Backup file checksum mismatch - file may be corrupted")
                
                logger.info("  ✓ Backup integrity verified")
            
            # Create backup of current database before restore
            if self.source_db_path.exists():
                pre_restore_backup = self.source_db_path.with_suffix('.pre_restore.db')
                shutil.copy2(self.source_db_path, pre_restore_backup)
                logger.info(f"  ✓ Current database backed up to: {pre_restore_backup}")
            
            # Restore from backup
            shutil.copy2(backup_file, self.source_db_path)
            
            logger.info("✓ Database restored successfully")
            
            self.migration_log.append({
                'step': 'restore',
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'backup_path': str(backup_file)
            })
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Restore failed: {e}")
            self.migration_log.append({
                'step': 'restore',
                'status': 'failed',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            })
            return False
    
    def save_migration_log(self, log_path: str = None):
        """
        Save migration log to file.
        
        Args:
            log_path: Path to log file (default: backup_dir/migration_log_<timestamp>.json)
        """
        if log_path:
            log_file = Path(log_path)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = self.backup_dir / f"migration_log_{timestamp}.json"
        
        log_data = {
            'source_db': str(self.source_db_path),
            'target_db': str(self.target_db_path),
            'backup_path': str(self.backup_path) if self.backup_path else None,
            'migration_log': self.migration_log,
            'verification_results': self.verification_results
        }
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Migration log saved to: {log_file}")
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _migrate_sessions(self, source_cursor, target_session) -> int:
        """Migrate sessions table."""
        source_cursor.execute("SELECT * FROM sessions")
        rows = source_cursor.fetchall()
        
        count = 0
        for row in rows:
            session = Session(
                id=row['id'],
                name=row['name'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                import_folder=row['import_folder'],
                total_photos=row['total_photos'] or 0,
                processed_photos=row['processed_photos'] or 0,
                status=row['status'] or 'importing'
            )
            target_session.add(session)
            count += 1
        
        target_session.flush()
        return count
    
    def _migrate_photos(self, source_cursor, target_session) -> int:
        """Migrate photos table."""
        source_cursor.execute("SELECT * FROM photos")
        rows = source_cursor.fetchall()
        
        count = 0
        for row in rows:
            # Convert Row to dict for easier access
            row_dict = dict(row)
            
            photo = Photo(
                id=row_dict['id'],
                session_id=row_dict['session_id'],
                file_path=row_dict['file_path'],
                file_name=row_dict['file_name'],
                file_size=row_dict['file_size'],
                import_time=datetime.fromisoformat(row_dict['import_time']) if row_dict['import_time'] else datetime.utcnow(),
                camera_make=row_dict['camera_make'],
                camera_model=row_dict['camera_model'],
                lens=row_dict['lens'],
                focal_length=row_dict['focal_length'],
                aperture=row_dict['aperture'],
                shutter_speed=row_dict['shutter_speed'],
                iso=row_dict['iso'],
                capture_time=datetime.fromisoformat(row_dict['capture_time']) if row_dict.get('capture_time') else None,
                gps_lat=row_dict['gps_lat'],
                gps_lon=row_dict['gps_lon'],
                ai_score=row_dict['ai_score'],
                focus_score=row_dict['focus_score'],
                exposure_score=row_dict['exposure_score'],
                composition_score=row_dict['composition_score'],
                subject_type=row_dict['subject_type'],
                detected_faces=row_dict['detected_faces'] or 0,
                context_tag=row_dict['context_tag'],
                selected_preset=row_dict['selected_preset'],
                status=row_dict['status'] or 'imported',
                lr_catalog_id=row_dict['lr_catalog_id'],
                virtual_copy_id=row_dict['virtual_copy_id'],
                approved=bool(row_dict['approved']) if row_dict['approved'] is not None else False,
                approved_at=datetime.fromisoformat(row_dict['approved_at']) if row_dict.get('approved_at') else None,
                rejection_reason=row_dict['rejection_reason']
            )
            
            # Handle new fields that may not exist in old schema
            if 'phash' in row_dict:
                photo.phash = row_dict['phash']
            if 'photo_group_id' in row_dict:
                photo.photo_group_id = row_dict['photo_group_id']
            if 'is_best_in_group' in row_dict:
                photo.is_best_in_group = bool(row_dict['is_best_in_group'])
            
            target_session.add(photo)
            count += 1
        
        target_session.flush()
        return count
    
    def _migrate_jobs(self, source_cursor, target_session) -> int:
        """Migrate jobs table."""
        source_cursor.execute("SELECT * FROM jobs")
        rows = source_cursor.fetchall()
        
        count = 0
        for row in rows:
            job = Job(
                id=row['id'],
                photo_id=row['photo_id'],
                priority=row['priority'] or 2,
                config_json=row['config_json'],
                status=row['status'] or 'pending',
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                started_at=datetime.fromisoformat(row['started_at']) if row.get('started_at') else None,
                completed_at=datetime.fromisoformat(row['completed_at']) if row.get('completed_at') else None,
                error_message=row['error_message'],
                retry_count=row['retry_count'] or 0
            )
            target_session.add(job)
            count += 1
        
        target_session.flush()
        return count
    
    def _migrate_presets(self, source_cursor, target_session) -> int:
        """Migrate presets table."""
        source_cursor.execute("SELECT * FROM presets")
        rows = source_cursor.fetchall()
        
        count = 0
        for row in rows:
            preset = Preset(
                id=row['id'],
                name=row['name'],
                version=row['version'],
                context_tags=row['context_tags'],
                config_template=row['config_template'],
                blend_amount=row['blend_amount'] or 100,
                usage_count=row['usage_count'] or 0,
                avg_approval_rate=row['avg_approval_rate'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.utcnow()
            )
            target_session.add(preset)
            count += 1
        
        target_session.flush()
        return count
    
    def _migrate_statistics(self, source_cursor, target_session) -> int:
        """Migrate statistics table."""
        source_cursor.execute("SELECT * FROM statistics")
        rows = source_cursor.fetchall()
        
        count = 0
        for row in rows:
            statistic = Statistic(
                id=row['id'],
                date=datetime.fromisoformat(row['date']) if row['date'] else datetime.utcnow(),
                session_id=row['session_id'],
                total_imported=row['total_imported'] or 0,
                total_selected=row['total_selected'] or 0,
                total_processed=row['total_processed'] or 0,
                total_exported=row['total_exported'] or 0,
                avg_processing_time=row['avg_processing_time'],
                success_rate=row['success_rate'],
                preset_usage=row['preset_usage']
            )
            target_session.add(statistic)
            count += 1
        
        target_session.flush()
        return count
    
    def _migrate_learning_data(self, source_cursor, target_session) -> int:
        """Migrate learning_data table."""
        source_cursor.execute("SELECT * FROM learning_data")
        rows = source_cursor.fetchall()
        
        count = 0
        for row in rows:
            learning_data = LearningData(
                id=row['id'],
                photo_id=row['photo_id'],
                action=row['action'],
                original_preset=row['original_preset'],
                final_preset=row['final_preset'],
                parameter_adjustments=row['parameter_adjustments'],
                timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else datetime.utcnow()
            )
            target_session.add(learning_data)
            count += 1
        
        target_session.flush()
        return count


def main():
    """Main entry point for data migration tool."""
    parser = argparse.ArgumentParser(
        description='Junmai AutoDev Data Migration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create backup only
  python data_migration_tool.py --source data/junmai.db --backup-only
  
  # Full migration with backup
  python data_migration_tool.py --source data/junmai.db --target data/junmai_new.db
  
  # Restore from backup
  python data_migration_tool.py --source data/junmai.db --restore data/backups/junmai_backup_20250108_120000.db
  
  # Verify existing migration
  python data_migration_tool.py --source data/junmai.db --target data/junmai_new.db --verify-only
        """
    )
    
    parser.add_argument(
        '--source',
        type=str,
        required=True,
        help='Path to source database file'
    )
    parser.add_argument(
        '--target',
        type=str,
        help='Path to target database file (default: source with .new.db suffix)'
    )
    parser.add_argument(
        '--backup-dir',
        type=str,
        help='Directory for backups (default: ./data/backups)'
    )
    parser.add_argument(
        '--backup-only',
        action='store_true',
        help='Only create backup, do not migrate'
    )
    parser.add_argument(
        '--restore',
        type=str,
        metavar='BACKUP_FILE',
        help='Restore from specified backup file'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify existing migration'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip backup creation (not recommended)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize migration tool
        tool = DataMigrationTool(
            source_db_path=args.source,
            target_db_path=args.target,
            backup_dir=args.backup_dir
        )
        
        # Handle restore operation
        if args.restore:
            logger.info("="*60)
            logger.info("DATABASE RESTORE")
            logger.info("="*60)
            
            success = tool.restore_from_backup(args.restore)
            
            if success:
                logger.info("\n" + "="*60)
                logger.info("RESTORE COMPLETED SUCCESSFULLY")
                logger.info("="*60)
                sys.exit(0)
            else:
                logger.error("\n" + "="*60)
                logger.error("RESTORE FAILED")
                logger.error("="*60)
                sys.exit(1)
        
        # Handle verify-only operation
        if args.verify_only:
            logger.info("="*60)
            logger.info("MIGRATION VERIFICATION")
            logger.info("="*60)
            
            results = tool.verify_migration()
            tool.save_migration_log()
            
            if results['success']:
                logger.info("\n" + "="*60)
                logger.info("VERIFICATION PASSED")
                logger.info("="*60)
                sys.exit(0)
            else:
                logger.error("\n" + "="*60)
                logger.error("VERIFICATION FAILED")
                logger.error("="*60)
                sys.exit(1)
        
        # Full migration process
        logger.info("="*60)
        logger.info("DATABASE MIGRATION")
        logger.info("="*60)
        logger.info(f"Source: {args.source}")
        logger.info(f"Target: {args.target or 'auto-generated'}")
        logger.info("="*60)
        
        # Step 1: Create backup
        if not args.no_backup:
            tool.create_backup()
        else:
            logger.warning("⚠ Skipping backup (--no-backup specified)")
        
        # Step 2: Migrate data (unless backup-only)
        if not args.backup_only:
            success = tool.migrate_data()
            
            if not success:
                logger.error("\n" + "="*60)
                logger.error("MIGRATION FAILED")
                logger.error("="*60)
                tool.save_migration_log()
                sys.exit(1)
            
            # Step 3: Verify migration
            results = tool.verify_migration()
            
            if not results['success']:
                logger.error("\n" + "="*60)
                logger.error("VERIFICATION FAILED - MIGRATION MAY BE INCOMPLETE")
                logger.error("="*60)
                tool.save_migration_log()
                sys.exit(1)
        
        # Save migration log
        tool.save_migration_log()
        
        logger.info("\n" + "="*60)
        logger.info("MIGRATION COMPLETED SUCCESSFULLY")
        logger.info("="*60)
        
        if not args.backup_only:
            logger.info("\nNext steps:")
            logger.info(f"1. Review migration log in: {tool.backup_dir}")
            logger.info(f"2. Test the new database: {tool.target_db_path}")
            logger.info(f"3. If satisfied, replace old database with new one")
            logger.info(f"4. Keep backup for safety: {tool.backup_path}")
        
    except Exception as e:
        logger.error(f"\n✗ Migration tool error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
