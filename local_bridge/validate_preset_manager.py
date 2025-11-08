"""
Simple validation script for Preset Management System.
Tests core functionality without requiring pytest.
"""

import sys
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.database import Base, Preset
from preset_manager import PresetManager


def test_basic_operations():
    """Test basic CRUD operations."""
    print("Testing basic CRUD operations...")
    
    # Create in-memory database
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        manager = PresetManager(db, temp_dir)
        
        # Test 1: Create preset
        config = {
            "version": "1.0",
            "pipeline": [
                {
                    "stage": "base",
                    "settings": {
                        "Exposure2012": -0.15,
                        "Highlights2012": -18
                    }
                }
            ],
            "safety": {"snapshot": True, "dryRun": False}
        }
        
        preset = manager.create_preset(
            name="TestPreset",
            version="v1",
            config_template=config,
            context_tags=["test_context"],
            blend_amount=60
        )
        
        assert preset.id is not None, "Preset ID should be set"
        assert preset.name == "TestPreset", "Preset name mismatch"
        assert preset.version == "v1", "Preset version mismatch"
        print("  ✓ Create preset")
        
        # Test 2: Get preset
        retrieved = manager.get_preset(preset.id)
        assert retrieved is not None, "Should retrieve preset"
        assert retrieved.name == "TestPreset", "Retrieved preset name mismatch"
        print("  ✓ Get preset")
        
        # Test 3: List presets
        presets = manager.list_presets()
        assert len(presets) == 1, "Should have 1 preset"
        print("  ✓ List presets")
        
        # Test 4: Update preset
        updated = manager.update_preset(preset.id, blend_amount=75)
        assert updated.blend_amount == 75, "Blend amount should be updated"
        print("  ✓ Update preset")
        
        # Test 5: Context selection
        selected = manager.select_preset_for_context("test_context")
        assert selected is not None, "Should select preset for context"
        assert selected.name == "TestPreset", "Selected preset mismatch"
        print("  ✓ Context selection")
        
        # Test 6: Export preset
        file_path = manager.export_preset(preset.id)
        assert Path(file_path).exists(), "Export file should exist"
        print("  ✓ Export preset")
        
        # Test 7: Delete preset
        result = manager.delete_preset(preset.id)
        assert result is True, "Delete should succeed"
        
        retrieved = manager.get_preset(preset.id)
        assert retrieved is None, "Preset should be deleted"
        print("  ✓ Delete preset")
        
        print("✅ All basic operations passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
        shutil.rmtree(temp_dir)


def test_version_management():
    """Test version management."""
    print("Testing version management...")
    
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        manager = PresetManager(db, temp_dir)
        
        config = {
            "version": "1.0",
            "pipeline": [
                {
                    "stage": "base",
                    "settings": {"Exposure2012": -0.15}
                }
            ],
            "safety": {"snapshot": True, "dryRun": False}
        }
        
        # Create base preset
        base = manager.create_preset("BasePreset", "v1", config)
        print("  ✓ Created base preset")
        
        # Create new version
        changes = {
            "pipeline": [
                {
                    "stage": "base",
                    "settings": {"Exposure2012": -0.20}
                }
            ]
        }
        
        new_version = manager.create_preset_version(base.id, "v2", changes)
        assert new_version.name == "BasePreset_v2", "Version name mismatch"
        assert new_version.version == "v2", "Version string mismatch"
        print("  ✓ Created new version")
        
        # Get all versions
        versions = manager.get_preset_versions("BasePreset")
        assert len(versions) == 2, "Should have 2 versions"
        print("  ✓ Retrieved all versions")
        
        # Compare versions
        comparison = manager.compare_preset_versions(base.id, new_version.id)
        assert "config_diff" in comparison, "Should have config diff"
        print("  ✓ Compared versions")
        
        print("✅ Version management tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
        shutil.rmtree(temp_dir)


def test_import_export():
    """Test import/export functionality."""
    print("Testing import/export...")
    
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        manager = PresetManager(db, temp_dir)
        
        config = {
            "version": "1.0",
            "pipeline": [
                {
                    "stage": "base",
                    "settings": {"Exposure2012": -0.15}
                }
            ],
            "safety": {"snapshot": True, "dryRun": False}
        }
        
        # Create and export preset
        preset = manager.create_preset("ExportTest", "v1", config)
        file_path = manager.export_preset(preset.id)
        assert Path(file_path).exists(), "Export file should exist"
        print("  ✓ Exported preset")
        
        # Delete preset
        manager.delete_preset(preset.id)
        
        # Import preset
        imported = manager.import_preset(file_path)
        assert imported.name == "ExportTest", "Imported preset name mismatch"
        assert imported.version == "v1", "Imported preset version mismatch"
        print("  ✓ Imported preset")
        
        # Export all presets
        files = manager.export_all_presets()
        assert len(files) >= 1, "Should export at least 1 file"
        print("  ✓ Exported all presets")
        
        print("✅ Import/export tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
        shutil.rmtree(temp_dir)


def test_usage_tracking():
    """Test usage tracking and statistics."""
    print("Testing usage tracking...")
    
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        manager = PresetManager(db, temp_dir)
        
        config = {
            "version": "1.0",
            "pipeline": [
                {
                    "stage": "base",
                    "settings": {"Exposure2012": -0.15}
                }
            ],
            "safety": {"snapshot": True, "dryRun": False}
        }
        
        # Create preset
        preset = manager.create_preset("StatsTest", "v1", config)
        
        # Record usage
        manager.record_preset_usage(preset.id, photo_id=1, approved=True)
        db.refresh(preset)
        
        assert preset.usage_count == 1, "Usage count should be 1"
        assert preset.avg_approval_rate == 1.0, "Approval rate should be 1.0"
        print("  ✓ Recorded usage (approved)")
        
        # Record rejection
        manager.record_preset_usage(preset.id, photo_id=2, approved=False)
        db.refresh(preset)
        
        assert preset.usage_count == 2, "Usage count should be 2"
        assert 0 < preset.avg_approval_rate < 1.0, "Approval rate should be between 0 and 1"
        print("  ✓ Recorded usage (rejected)")
        
        # Get statistics
        stats = manager.get_preset_statistics(preset.id)
        assert stats["usage_count"] == 2, "Stats usage count mismatch"
        assert stats["name"] == "StatsTest", "Stats name mismatch"
        print("  ✓ Retrieved statistics")
        
        # Get top presets
        top = manager.get_top_presets(limit=5, metric="usage")
        assert len(top) >= 1, "Should have at least 1 top preset"
        print("  ✓ Retrieved top presets")
        
        print("✅ Usage tracking tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
        shutil.rmtree(temp_dir)


def test_validation():
    """Test configuration validation."""
    print("Testing validation...")
    
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        manager = PresetManager(db, temp_dir)
        
        # Test invalid config (missing version)
        invalid_config = {
            "pipeline": []
        }
        
        try:
            manager.create_preset("Invalid", "v1", invalid_config)
            print("  ❌ Should have raised ValueError for missing version")
            return False
        except ValueError as e:
            if "version" in str(e):
                print("  ✓ Caught missing version error")
            else:
                raise
        
        # Test invalid config (missing pipeline)
        invalid_config = {
            "version": "1.0"
        }
        
        try:
            manager.create_preset("Invalid", "v1", invalid_config)
            print("  ❌ Should have raised ValueError for missing pipeline")
            return False
        except ValueError as e:
            if "pipeline" in str(e):
                print("  ✓ Caught missing pipeline error")
            else:
                raise
        
        # Test invalid stage
        invalid_config = {
            "version": "1.0",
            "pipeline": [
                {"stage": "invalid_stage"}
            ]
        }
        
        try:
            manager.create_preset("Invalid", "v1", invalid_config)
            print("  ❌ Should have raised ValueError for invalid stage")
            return False
        except ValueError as e:
            if "Invalid stage" in str(e):
                print("  ✓ Caught invalid stage error")
            else:
                raise
        
        print("✅ Validation tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
        shutil.rmtree(temp_dir)


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("PRESET MANAGEMENT SYSTEM - VALIDATION")
    print("=" * 60)
    print()
    
    results = []
    
    results.append(("Basic Operations", test_basic_operations()))
    results.append(("Version Management", test_version_management()))
    results.append(("Import/Export", test_import_export()))
    results.append(("Usage Tracking", test_usage_tracking()))
    results.append(("Validation", test_validation()))
    
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
    
    print()
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("🎉 All validation tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
