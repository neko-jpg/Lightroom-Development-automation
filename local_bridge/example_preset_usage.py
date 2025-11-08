"""
Example usage of the Preset Management System.

This script demonstrates:
1. Creating presets with context tags
2. Selecting presets based on context
3. Version management
4. Import/Export operations
5. Usage tracking and statistics
"""

from models.database import init_db, get_session
from preset_manager import PresetManager


def example_create_presets():
    """Example: Creating presets with different contexts."""
    print("=" * 60)
    print("Example 1: Creating Presets")
    print("=" * 60)
    
    # Initialize database
    init_db('sqlite:///data/junmai.db')
    db = get_session()
    
    # Create preset manager
    manager = PresetManager(db, "config/presets")
    
    # Define a backlit portrait preset
    backlit_config = {
        "version": "1.0",
        "pipeline": [
            {
                "stage": "base",
                "settings": {
                    "Exposure2012": -0.15,
                    "Highlights2012": -18,
                    "Shadows2012": 12,
                    "Whites2012": -5,
                    "Blacks2012": -8
                }
            },
            {
                "stage": "HSL",
                "hue": {"orange": -4, "blue": 0},
                "sat": {"orange": -6, "blue": -8},
                "lum": {"orange": 4, "blue": -6}
            },
            {
                "stage": "effects",
                "settings": {
                    "Clarity2012": 8,
                    "Dehaze": -5
                }
            }
        ],
        "safety": {
            "snapshot": True,
            "dryRun": False
        }
    }
    
    # Create backlit portrait preset
    backlit_preset = manager.create_preset(
        name="WhiteLayer_Transparency",
        version="v4",
        config_template=backlit_config,
        context_tags=["backlit_portrait", "outdoor", "golden_hour"],
        blend_amount=60
    )
    
    print(f"✓ Created preset: {backlit_preset.name} v{backlit_preset.version}")
    print(f"  Context tags: {backlit_preset.get_context_tags()}")
    print(f"  Blend amount: {backlit_preset.blend_amount}%")
    
    # Define a low-light indoor preset
    lowlight_config = {
        "version": "1.0",
        "pipeline": [
            {
                "stage": "base",
                "settings": {
                    "Exposure2012": 0.25,
                    "Highlights2012": -10,
                    "Shadows2012": 25,
                    "Contrast2012": -5
                }
            },
            {
                "stage": "detail",
                "sharpen": {
                    "Sharpness": 40,
                    "SharpenRadius": 1.0,
                    "SharpenDetail": 25
                },
                "nr": {
                    "LuminanceSmoothing": 35,
                    "ColorNoiseReduction": 50
                }
            }
        ],
        "safety": {
            "snapshot": True,
            "dryRun": False
        }
    }
    
    lowlight_preset = manager.create_preset(
        name="LowLight_NR",
        version="v2",
        config_template=lowlight_config,
        context_tags=["low_light_indoor", "high_iso"],
        blend_amount=80
    )
    
    print(f"✓ Created preset: {lowlight_preset.name} v{lowlight_preset.version}")
    print(f"  Context tags: {lowlight_preset.get_context_tags()}")
    
    db.close()
    print()


def example_context_selection():
    """Example: Selecting presets based on context."""
    print("=" * 60)
    print("Example 2: Context-Based Preset Selection")
    print("=" * 60)
    
    init_db('sqlite:///data/junmai.db')
    db = get_session()
    manager = PresetManager(db, "config/presets")
    
    # Select preset for backlit portrait
    context = "backlit_portrait"
    preset = manager.select_preset_for_context(context)
    
    if preset:
        print(f"Context: {context}")
        print(f"Selected preset: {preset.name} v{preset.version}")
        print(f"Blend amount: {preset.blend_amount}%")
    else:
        print(f"No preset found for context: {context}")
    
    print()
    
    # Get complete context mapping
    mapping = manager.map_contexts_to_presets()
    print("Complete Context-to-Preset Mapping:")
    for ctx, presets in mapping.items():
        print(f"  {ctx}: {', '.join(presets)}")
    
    db.close()
    print()


def example_version_management():
    """Example: Creating and managing preset versions."""
    print("=" * 60)
    print("Example 3: Version Management")
    print("=" * 60)
    
    init_db('sqlite:///data/junmai.db')
    db = get_session()
    manager = PresetManager(db, "config/presets")
    
    # Get base preset
    base_preset = manager.get_preset_by_name("WhiteLayer_Transparency")
    
    if base_preset:
        print(f"Base preset: {base_preset.name} v{base_preset.version}")
        
        # Create new version with modified exposure
        changes = {
            "pipeline": [
                {
                    "stage": "base",
                    "settings": {
                        "Exposure2012": -0.20  # Increased from -0.15
                    }
                }
            ]
        }
        
        new_version = manager.create_preset_version(
            base_preset.id,
            "v5",
            changes
        )
        
        print(f"✓ Created new version: {new_version.name} v{new_version.version}")
        
        # Get all versions
        versions = manager.get_preset_versions("WhiteLayer_Transparency")
        print(f"\nAll versions of WhiteLayer_Transparency:")
        for v in versions:
            print(f"  - {v.name} v{v.version} (created: {v.created_at})")
        
        # Compare versions
        if len(versions) >= 2:
            comparison = manager.compare_preset_versions(
                versions[0].id,
                versions[1].id
            )
            print(f"\nComparison between v{versions[0].version} and v{versions[1].version}:")
            print(f"  Modified stages: {len(comparison['config_diff']['modified'])}")
    
    db.close()
    print()


def example_import_export():
    """Example: Importing and exporting presets."""
    print("=" * 60)
    print("Example 4: Import/Export Operations")
    print("=" * 60)
    
    init_db('sqlite:///data/junmai.db')
    db = get_session()
    manager = PresetManager(db, "config/presets")
    
    # Export a preset
    preset = manager.get_preset_by_name("WhiteLayer_Transparency")
    if preset:
        file_path = manager.export_preset(preset.id)
        print(f"✓ Exported preset to: {file_path}")
        
        # Export all presets
        files = manager.export_all_presets()
        print(f"✓ Exported {len(files)} presets total")
        
        # Import preset (example - would need actual file)
        # imported = manager.import_preset("config/presets/imported_preset.json")
        # print(f"✓ Imported preset: {imported.name}")
    
    db.close()
    print()


def example_usage_tracking():
    """Example: Tracking preset usage and statistics."""
    print("=" * 60)
    print("Example 5: Usage Tracking and Statistics")
    print("=" * 60)
    
    init_db('sqlite:///data/junmai.db')
    db = get_session()
    manager = PresetManager(db, "config/presets")
    
    # Get preset statistics
    preset = manager.get_preset_by_name("WhiteLayer_Transparency")
    if preset:
        stats = manager.get_preset_statistics(preset.id)
        
        print(f"Preset: {stats['name']} v{stats['version']}")
        print(f"Usage count: {stats['usage_count']}")
        print(f"Avg approval rate: {stats['avg_approval_rate']}")
        print(f"Context tags: {', '.join(stats['context_tags'])}")
        print(f"Learning data:")
        print(f"  - Approved: {stats['learning_data']['approved']}")
        print(f"  - Rejected: {stats['learning_data']['rejected']}")
        print(f"  - Modified: {stats['learning_data']['modified']}")
    
    print()
    
    # Get top presets by usage
    print("Top 5 Presets by Usage:")
    top_usage = manager.get_top_presets(limit=5, metric="usage")
    for i, preset_stats in enumerate(top_usage, 1):
        print(f"  {i}. {preset_stats['name']} - {preset_stats['usage_count']} uses")
    
    print()
    
    # Get top presets by approval rate
    print("Top 5 Presets by Approval Rate:")
    top_approval = manager.get_top_presets(limit=5, metric="approval")
    for i, preset_stats in enumerate(top_approval, 1):
        rate = preset_stats['avg_approval_rate']
        rate_str = f"{rate:.1%}" if rate is not None else "N/A"
        print(f"  {i}. {preset_stats['name']} - {rate_str}")
    
    db.close()
    print()


def example_complete_workflow():
    """Example: Complete workflow from context to preset application."""
    print("=" * 60)
    print("Example 6: Complete Workflow")
    print("=" * 60)
    
    init_db('sqlite:///data/junmai.db')
    db = get_session()
    manager = PresetManager(db, "config/presets")
    
    # Scenario: Photo with backlit portrait context
    context_tag = "backlit_portrait"
    print(f"Photo context detected: {context_tag}")
    
    # Step 1: Select appropriate preset
    preset = manager.select_preset_for_context(context_tag)
    if not preset:
        print("No matching preset found!")
        db.close()
        return
    
    print(f"✓ Selected preset: {preset.name} v{preset.version}")
    
    # Step 2: Get config template
    config = preset.get_config_template()
    print(f"✓ Retrieved config template with {len(config['pipeline'])} stages")
    
    # Step 3: Apply blend amount
    print(f"✓ Blend amount: {preset.blend_amount}%")
    
    # Step 4: Simulate application and approval
    # (In real workflow, this would be done by Lightroom plugin)
    print("✓ Applied preset to photo")
    
    # Step 5: Record usage (simulating approval)
    # manager.record_preset_usage(preset.id, photo_id=123, approved=True)
    print("✓ Recorded usage and approval")
    
    # Step 6: Check updated statistics
    stats = manager.get_preset_statistics(preset.id)
    print(f"\nUpdated Statistics:")
    print(f"  Usage count: {stats['usage_count']}")
    if stats['avg_approval_rate'] is not None:
        print(f"  Approval rate: {stats['avg_approval_rate']:.1%}")
    
    db.close()
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRESET MANAGEMENT SYSTEM - EXAMPLE USAGE")
    print("=" * 60 + "\n")
    
    # Run examples
    example_create_presets()
    example_context_selection()
    example_version_management()
    example_import_export()
    example_usage_tracking()
    example_complete_workflow()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)
