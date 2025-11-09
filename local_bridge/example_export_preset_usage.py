"""
Example usage of Export Preset Manager

This script demonstrates how to use the export preset management system
for the Junmai AutoDev project.

Requirements: 6.1, 6.2
"""

import pathlib
from export_preset_manager import ExportPresetManager, ExportPreset


def main():
    """Main example function"""
    
    print("=" * 60)
    print("Export Preset Manager - Example Usage")
    print("=" * 60)
    
    # Initialize manager
    print("\n1. Initializing Export Preset Manager...")
    manager = ExportPresetManager()
    print(f"   ✓ Loaded {manager.get_preset_count()} presets")
    
    # List all presets
    print("\n2. Listing all presets:")
    presets = manager.list_presets()
    for preset in presets:
        status = "✓ Enabled" if preset.enabled else "✗ Disabled"
        print(f"   {status} {preset.name:20s} | {preset.format:4s} | "
              f"{preset.max_dimension:4d}px | Q:{preset.quality:3d}% | "
              f"{preset.color_space:12s}")
    
    # Get specific preset
    print("\n3. Getting SNS preset details:")
    sns_preset = manager.get_preset("SNS")
    if sns_preset:
        print(f"   Name: {sns_preset.name}")
        print(f"   Format: {sns_preset.format}")
        print(f"   Quality: {sns_preset.quality}%")
        print(f"   Max Dimension: {sns_preset.max_dimension}px")
        print(f"   Color Space: {sns_preset.color_space}")
        print(f"   Destination: {sns_preset.destination}")
        print(f"   Sharpen for Screen: {sns_preset.sharpen_for_screen}")
        print(f"   Sharpen Amount: {sns_preset.sharpen_amount}")
    
    # Create custom preset for Instagram
    print("\n4. Creating custom Instagram preset:")
    instagram_preset = ExportPreset(
        name="Instagram_Square",
        enabled=True,
        format="JPEG",
        quality=90,
        max_dimension=1080,
        color_space="sRGB",
        destination="D:/Export/Instagram",
        resize_mode="fit",
        sharpen_for_screen=True,
        sharpen_amount=60,
        metadata_include=False,
        filename_template="IG_{date}_{sequence}"
    )
    
    success = manager.add_preset(instagram_preset)
    if success:
        print(f"   ✓ Created preset: {instagram_preset.name}")
    else:
        print(f"   ✗ Preset already exists: {instagram_preset.name}")
    
    # Update existing preset
    print("\n5. Updating SNS preset:")
    success = manager.update_preset("SNS", {
        "quality": 88,
        "max_dimension": 2560,
        "sharpen_amount": 55
    })
    if success:
        updated_preset = manager.get_preset("SNS")
        print(f"   ✓ Updated SNS preset")
        print(f"   New Quality: {updated_preset.quality}%")
        print(f"   New Max Dimension: {updated_preset.max_dimension}px")
    
    # Duplicate preset
    print("\n6. Duplicating Print preset:")
    success = manager.duplicate_preset("Print", "Print_High_Quality")
    if success:
        print(f"   ✓ Duplicated Print preset to Print_High_Quality")
        
        # Update the duplicated preset
        manager.update_preset("Print_High_Quality", {
            "quality": 98,
            "max_dimension": 5120
        })
        print(f"   ✓ Updated Print_High_Quality preset")
    
    # Enable/Disable presets
    print("\n7. Managing preset status:")
    manager.disable_preset("Archive")
    print(f"   ✓ Disabled Archive preset")
    
    manager.enable_preset("Web_Portfolio")
    print(f"   ✓ Enabled Web_Portfolio preset")
    
    # Get enabled presets
    print("\n8. Listing enabled presets:")
    enabled_presets = manager.get_enabled_presets()
    print(f"   Enabled: {len(enabled_presets)}/{manager.get_preset_count()}")
    for preset in enabled_presets:
        print(f"   - {preset.name}")
    
    # Validate preset
    print("\n9. Validating custom preset:")
    test_preset = ExportPreset(
        name="Test_Validation",
        enabled=True,
        format="JPEG",
        quality=85,
        max_dimension=2048,
        color_space="sRGB",
        destination="D:/Export/Test"
    )
    is_valid, error = manager.validate_preset(test_preset)
    if is_valid:
        print(f"   ✓ Preset is valid")
    else:
        print(f"   ✗ Preset validation failed: {error}")
    
    # Get statistics
    print("\n10. Getting preset statistics:")
    total = manager.get_preset_count()
    enabled = manager.get_enabled_preset_count()
    disabled = total - enabled
    print(f"   Total Presets: {total}")
    print(f"   Enabled: {enabled}")
    print(f"   Disabled: {disabled}")
    
    # Export presets to backup file
    print("\n11. Exporting presets to backup file:")
    backup_path = pathlib.Path("export_presets_backup.json")
    manager.export_presets(backup_path)
    print(f"   ✓ Exported to: {backup_path}")
    
    # Save all changes
    print("\n12. Saving all changes:")
    manager.save()
    print(f"   ✓ Saved to: {manager.presets_file}")
    
    # Cleanup example preset
    print("\n13. Cleaning up example presets:")
    if manager.get_preset("Instagram_Square"):
        manager.delete_preset("Instagram_Square")
        print(f"   ✓ Deleted Instagram_Square preset")
    
    if manager.get_preset("Print_High_Quality"):
        manager.delete_preset("Print_High_Quality")
        print(f"   ✓ Deleted Print_High_Quality preset")
    
    # Restore original SNS preset
    manager.update_preset("SNS", {
        "quality": 85,
        "max_dimension": 2048,
        "sharpen_amount": 50
    })
    
    # Re-enable Archive
    manager.enable_preset("Archive")
    
    # Save final state
    manager.save()
    print(f"   ✓ Restored original state")
    
    # Cleanup backup file
    if backup_path.exists():
        backup_path.unlink()
        print(f"   ✓ Deleted backup file")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()
