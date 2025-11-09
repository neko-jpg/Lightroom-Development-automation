"""
Example usage of Data Migration Tool
Demonstrates common migration scenarios.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_migration_tool import DataMigrationTool


def example_full_migration():
    """Example: Full migration with backup and verification."""
    print("="*60)
    print("Example 1: Full Migration with Backup")
    print("="*60)
    
    tool = DataMigrationTool(
        source_db_path='data/junmai.db',
        target_db_path='data/junmai_new.db',
        backup_dir='data/backups'
    )
    
    # Step 1: Create backup
    print("\n1. Creating backup...")
    backup_path = tool.create_backup()
    print(f"   Backup created: {backup_path}")
    
    # Step 2: Migrate data
    print("\n2. Migrating data...")
    success = tool.migrate_data()
    
    if not success:
        print("   Migration failed! Restoring from backup...")
        tool.restore_from_backup(backup_path)
        return False
    
    print("   Migration completed successfully")
    
    # Step 3: Verify migration
    print("\n3. Verifying migration...")
    results = tool.verify_migration()
    
    if not results['success']:
        print("   Verification failed!")
        for error in results['errors']:
            print(f"   - {error}")
        return False
    
    print("   Verification passed")
    
    # Step 4: Save log
    print("\n4. Saving migration log...")
    tool.save_migration_log()
    
    print("\n" + "="*60)
    print("Migration completed successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Test the new database: data/junmai_new.db")
    print("2. If satisfied, replace old database:")
    print("   mv data/junmai.db data/junmai_old.db")
    print("   mv data/junmai_new.db data/junmai.db")
    print(f"3. Keep backup for safety: {backup_path}")
    
    return True


def example_backup_only():
    """Example: Create backup without migration."""
    print("="*60)
    print("Example 2: Backup Only")
    print("="*60)
    
    tool = DataMigrationTool(
        source_db_path='data/junmai.db',
        backup_dir='data/backups'
    )
    
    print("\nCreating backup...")
    backup_path = tool.create_backup()
    
    print("\n" + "="*60)
    print("Backup created successfully!")
    print("="*60)
    print(f"Backup location: {backup_path}")
    
    return backup_path


def example_restore():
    """Example: Restore from backup."""
    print("="*60)
    print("Example 3: Restore from Backup")
    print("="*60)
    
    # First, create a backup
    backup_path = example_backup_only()
    
    # Now restore from it
    print("\nRestoring from backup...")
    tool = DataMigrationTool(
        source_db_path='data/junmai.db',
        backup_dir='data/backups'
    )
    
    success = tool.restore_from_backup(backup_path)
    
    if success:
        print("\n" + "="*60)
        print("Restore completed successfully!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("Restore failed!")
        print("="*60)
    
    return success


def example_verify_only():
    """Example: Verify existing migration."""
    print("="*60)
    print("Example 4: Verify Existing Migration")
    print("="*60)
    
    tool = DataMigrationTool(
        source_db_path='data/junmai.db',
        target_db_path='data/junmai_new.db',
        backup_dir='data/backups'
    )
    
    print("\nVerifying migration...")
    results = tool.verify_migration()
    
    print("\n" + "="*60)
    if results['success']:
        print("Verification PASSED")
    else:
        print("Verification FAILED")
    print("="*60)
    
    print("\nVerification Results:")
    for table, check in results['checks'].items():
        status = "✓" if check['match'] else "✗"
        print(f"  {status} {table}: source={check['source_count']}, target={check['target_count']}")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    return results['success']


def example_programmatic_usage():
    """Example: Programmatic usage with error handling."""
    print("="*60)
    print("Example 5: Programmatic Usage with Error Handling")
    print("="*60)
    
    try:
        tool = DataMigrationTool(
            source_db_path='data/junmai.db',
            target_db_path='data/junmai_new.db',
            backup_dir='data/backups'
        )
        
        # Create backup
        print("\nStep 1: Creating backup...")
        backup_path = tool.create_backup()
        print(f"✓ Backup created: {backup_path}")
        
        # Migrate data
        print("\nStep 2: Migrating data...")
        if not tool.migrate_data():
            raise Exception("Migration failed")
        print("✓ Data migrated successfully")
        
        # Verify migration
        print("\nStep 3: Verifying migration...")
        results = tool.verify_migration()
        if not results['success']:
            raise Exception(f"Verification failed: {results['errors']}")
        print("✓ Verification passed")
        
        # Save log
        print("\nStep 4: Saving log...")
        tool.save_migration_log()
        print("✓ Log saved")
        
        print("\n" + "="*60)
        print("SUCCESS: Migration completed successfully!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        
        # Attempt to restore from backup
        if 'backup_path' in locals():
            print("\nAttempting to restore from backup...")
            try:
                tool.restore_from_backup(backup_path)
                print("✓ Restored from backup successfully")
            except Exception as restore_error:
                print(f"✗ Restore failed: {restore_error}")
        
        print("\n" + "="*60)
        print("FAILED: Migration failed, check logs for details")
        print("="*60)
        
        return False


def example_custom_backup_location():
    """Example: Using custom backup location."""
    print("="*60)
    print("Example 6: Custom Backup Location")
    print("="*60)
    
    custom_backup_dir = Path.home() / 'Documents' / 'JunmaiBackups'
    
    tool = DataMigrationTool(
        source_db_path='data/junmai.db',
        target_db_path='data/junmai_new.db',
        backup_dir=str(custom_backup_dir)
    )
    
    print(f"\nUsing custom backup directory: {custom_backup_dir}")
    print("\nCreating backup...")
    backup_path = tool.create_backup()
    
    print("\n" + "="*60)
    print("Backup created in custom location!")
    print("="*60)
    print(f"Backup location: {backup_path}")
    
    return backup_path


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("DATA MIGRATION TOOL - USAGE EXAMPLES")
    print("="*60)
    
    examples = [
        ("Full Migration", example_full_migration),
        ("Backup Only", example_backup_only),
        ("Restore from Backup", example_restore),
        ("Verify Only", example_verify_only),
        ("Programmatic Usage", example_programmatic_usage),
        ("Custom Backup Location", example_custom_backup_location)
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    
    print("\nNote: These are examples. Modify paths and parameters as needed.")
    print("      Run individual examples by calling their functions directly.")
    
    # Uncomment to run a specific example:
    # example_full_migration()
    # example_backup_only()
    # example_restore()
    # example_verify_only()
    # example_programmatic_usage()
    # example_custom_backup_location()


if __name__ == '__main__':
    main()
