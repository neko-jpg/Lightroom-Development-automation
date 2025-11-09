"""
Test suite for Export Preset Manager

Tests the export preset management functionality including:
- Preset creation, update, deletion
- Preset validation
- Preset enable/disable
- Preset duplication
- Preset import/export
- API endpoint integration

Requirements: 6.1, 6.2
"""

import pytest
import json
import pathlib
import tempfile
import shutil
from datetime import datetime

from export_preset_manager import (
    ExportPreset,
    ExportPresetManager,
    get_export_preset_manager
)


class TestExportPreset:
    """Test ExportPreset data class"""
    
    def test_create_valid_preset(self):
        """Test creating a valid export preset"""
        preset = ExportPreset(
            name="Test_SNS",
            enabled=True,
            format="JPEG",
            quality=85,
            max_dimension=2048,
            color_space="sRGB",
            destination="D:/Export/Test"
        )
        
        assert preset.name == "Test_SNS"
        assert preset.enabled is True
        assert preset.format == "JPEG"
        assert preset.quality == 85
        assert preset.max_dimension == 2048
        assert preset.color_space == "sRGB"
        assert preset.destination == "D:/Export/Test"
        assert preset.created_at is not None
        assert preset.updated_at is not None
    
    def test_invalid_format(self):
        """Test creating preset with invalid format"""
        with pytest.raises(ValueError, match="Invalid format"):
            ExportPreset(
                name="Test",
                enabled=True,
                format="INVALID",
                quality=85,
                max_dimension=2048,
                color_space="sRGB",
                destination="D:/Export/Test"
            )
    
    def test_invalid_quality(self):
        """Test creating preset with invalid quality"""
        with pytest.raises(ValueError, match="Invalid quality"):
            ExportPreset(
                name="Test",
                enabled=True,
                format="JPEG",
                quality=150,
                max_dimension=2048,
                color_space="sRGB",
                destination="D:/Export/Test"
            )
    
    def test_invalid_dimension(self):
        """Test creating preset with invalid dimension"""
        with pytest.raises(ValueError, match="Invalid max_dimension"):
            ExportPreset(
                name="Test",
                enabled=True,
                format="JPEG",
                quality=85,
                max_dimension=100,
                color_space="sRGB",
                destination="D:/Export/Test"
            )
    
    def test_invalid_color_space(self):
        """Test creating preset with invalid color space"""
        with pytest.raises(ValueError, match="Invalid color_space"):
            ExportPreset(
                name="Test",
                enabled=True,
                format="JPEG",
                quality=85,
                max_dimension=2048,
                color_space="INVALID",
                destination="D:/Export/Test"
            )
    
    def test_to_dict(self):
        """Test converting preset to dictionary"""
        preset = ExportPreset(
            name="Test",
            enabled=True,
            format="JPEG",
            quality=85,
            max_dimension=2048,
            color_space="sRGB",
            destination="D:/Export/Test"
        )
        
        preset_dict = preset.to_dict()
        
        assert isinstance(preset_dict, dict)
        assert preset_dict['name'] == "Test"
        assert preset_dict['format'] == "JPEG"
        assert preset_dict['quality'] == 85
    
    def test_from_dict(self):
        """Test creating preset from dictionary"""
        data = {
            "name": "Test",
            "enabled": True,
            "format": "JPEG",
            "quality": 85,
            "max_dimension": 2048,
            "color_space": "sRGB",
            "destination": "D:/Export/Test"
        }
        
        preset = ExportPreset.from_dict(data)
        
        assert preset.name == "Test"
        assert preset.format == "JPEG"
        assert preset.quality == 85


class TestExportPresetManager:
    """Test ExportPresetManager"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield pathlib.Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_dir):
        """Create ExportPresetManager instance for testing"""
        presets_file = temp_dir / "test_presets.json"
        return ExportPresetManager(presets_file)
    
    def test_create_default_presets(self, manager):
        """Test creating default presets"""
        assert manager.get_preset_count() > 0
        
        # Check default presets exist
        sns_preset = manager.get_preset("SNS")
        assert sns_preset is not None
        assert sns_preset.format == "JPEG"
        assert sns_preset.max_dimension == 2048
    
    def test_add_preset(self, manager):
        """Test adding a new preset"""
        initial_count = manager.get_preset_count()
        
        new_preset = ExportPreset(
            name="Custom_Test",
            enabled=True,
            format="PNG",
            quality=90,
            max_dimension=3000,
            color_space="sRGB",
            destination="D:/Export/Custom"
        )
        
        success = manager.add_preset(new_preset)
        
        assert success is True
        assert manager.get_preset_count() == initial_count + 1
        
        retrieved_preset = manager.get_preset("Custom_Test")
        assert retrieved_preset is not None
        assert retrieved_preset.format == "PNG"
    
    def test_add_duplicate_preset(self, manager):
        """Test adding preset with duplicate name"""
        preset1 = ExportPreset(
            name="Duplicate",
            enabled=True,
            format="JPEG",
            quality=85,
            max_dimension=2048,
            color_space="sRGB",
            destination="D:/Export/Test1"
        )
        
        preset2 = ExportPreset(
            name="Duplicate",
            enabled=True,
            format="PNG",
            quality=90,
            max_dimension=3000,
            color_space="sRGB",
            destination="D:/Export/Test2"
        )
        
        success1 = manager.add_preset(preset1)
        success2 = manager.add_preset(preset2)
        
        assert success1 is True
        assert success2 is False
    
    def test_update_preset(self, manager):
        """Test updating an existing preset"""
        preset_name = "SNS"
        
        success = manager.update_preset(preset_name, {
            "quality": 90,
            "max_dimension": 2560
        })
        
        assert success is True
        
        updated_preset = manager.get_preset(preset_name)
        assert updated_preset.quality == 90
        assert updated_preset.max_dimension == 2560
    
    def test_update_nonexistent_preset(self, manager):
        """Test updating a preset that doesn't exist"""
        success = manager.update_preset("Nonexistent", {"quality": 90})
        assert success is False
    
    def test_delete_preset(self, manager):
        """Test deleting a preset"""
        initial_count = manager.get_preset_count()
        
        # Add a preset to delete
        test_preset = ExportPreset(
            name="ToDelete",
            enabled=True,
            format="JPEG",
            quality=85,
            max_dimension=2048,
            color_space="sRGB",
            destination="D:/Export/Test"
        )
        manager.add_preset(test_preset)
        
        # Delete the preset
        success = manager.delete_preset("ToDelete")
        
        assert success is True
        assert manager.get_preset_count() == initial_count
        assert manager.get_preset("ToDelete") is None
    
    def test_delete_nonexistent_preset(self, manager):
        """Test deleting a preset that doesn't exist"""
        success = manager.delete_preset("Nonexistent")
        assert success is False
    
    def test_enable_disable_preset(self, manager):
        """Test enabling and disabling presets"""
        preset_name = "Print"
        
        # Disable preset
        success = manager.disable_preset(preset_name)
        assert success is True
        
        preset = manager.get_preset(preset_name)
        assert preset.enabled is False
        
        # Enable preset
        success = manager.enable_preset(preset_name)
        assert success is True
        
        preset = manager.get_preset(preset_name)
        assert preset.enabled is True
    
    def test_list_presets(self, manager):
        """Test listing all presets"""
        all_presets = manager.list_presets()
        assert len(all_presets) > 0
        assert all(isinstance(p, ExportPreset) for p in all_presets)
    
    def test_list_enabled_presets_only(self, manager):
        """Test listing only enabled presets"""
        # Disable some presets
        manager.disable_preset("Print")
        manager.disable_preset("Archive")
        
        enabled_presets = manager.list_presets(enabled_only=True)
        
        assert all(p.enabled for p in enabled_presets)
        assert len(enabled_presets) < manager.get_preset_count()
    
    def test_get_enabled_presets(self, manager):
        """Test getting enabled presets"""
        enabled_presets = manager.get_enabled_presets()
        assert all(p.enabled for p in enabled_presets)
    
    def test_duplicate_preset(self, manager):
        """Test duplicating a preset"""
        source_name = "SNS"
        new_name = "SNS_Copy"
        
        initial_count = manager.get_preset_count()
        
        success = manager.duplicate_preset(source_name, new_name)
        
        assert success is True
        assert manager.get_preset_count() == initial_count + 1
        
        source_preset = manager.get_preset(source_name)
        duplicated_preset = manager.get_preset(new_name)
        
        assert duplicated_preset is not None
        assert duplicated_preset.format == source_preset.format
        assert duplicated_preset.quality == source_preset.quality
        assert duplicated_preset.name == new_name
    
    def test_duplicate_nonexistent_preset(self, manager):
        """Test duplicating a preset that doesn't exist"""
        success = manager.duplicate_preset("Nonexistent", "Copy")
        assert success is False
    
    def test_save_and_load(self, manager, temp_dir):
        """Test saving and loading presets"""
        # Add a custom preset
        custom_preset = ExportPreset(
            name="Custom_Save_Test",
            enabled=True,
            format="TIFF",
            quality=100,
            max_dimension=4096,
            color_space="ProPhotoRGB",
            destination="D:/Export/Custom"
        )
        manager.add_preset(custom_preset)
        
        # Save presets
        manager.save()
        
        # Create new manager and load
        presets_file = temp_dir / "test_presets.json"
        new_manager = ExportPresetManager(presets_file)
        
        # Verify loaded preset
        loaded_preset = new_manager.get_preset("Custom_Save_Test")
        assert loaded_preset is not None
        assert loaded_preset.format == "TIFF"
        assert loaded_preset.quality == 100
    
    def test_export_import_presets(self, manager, temp_dir):
        """Test exporting and importing presets"""
        export_path = temp_dir / "export_test.json"
        
        # Export presets
        manager.export_presets(export_path)
        assert export_path.exists()
        
        # Create new manager
        new_presets_file = temp_dir / "new_presets.json"
        new_manager = ExportPresetManager(new_presets_file)
        
        # Clear presets
        for preset_name in list(new_manager.presets.keys()):
            new_manager.delete_preset(preset_name)
        
        assert new_manager.get_preset_count() == 0
        
        # Import presets
        imported_count = new_manager.import_presets(export_path, merge=False)
        
        assert imported_count > 0
        assert new_manager.get_preset_count() == imported_count
    
    def test_validate_preset(self, manager):
        """Test preset validation"""
        valid_preset = ExportPreset(
            name="Valid",
            enabled=True,
            format="JPEG",
            quality=85,
            max_dimension=2048,
            color_space="sRGB",
            destination="D:/Export/Valid"
        )
        
        is_valid, error = manager.validate_preset(valid_preset)
        assert is_valid is True
        assert error is None
    
    def test_get_preset_count(self, manager):
        """Test getting preset count"""
        count = manager.get_preset_count()
        assert count > 0
        assert isinstance(count, int)
    
    def test_get_enabled_preset_count(self, manager):
        """Test getting enabled preset count"""
        # Disable some presets
        manager.disable_preset("Print")
        manager.disable_preset("Archive")
        
        enabled_count = manager.get_enabled_preset_count()
        total_count = manager.get_preset_count()
        
        assert enabled_count < total_count
        assert enabled_count > 0


class TestExportPresetManagerIntegration:
    """Integration tests for Export Preset Manager"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield pathlib.Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_full_workflow(self, temp_dir):
        """Test complete workflow: create, update, duplicate, export, import"""
        presets_file = temp_dir / "workflow_test.json"
        manager = ExportPresetManager(presets_file)
        
        # 1. Create custom preset
        custom_preset = ExportPreset(
            name="Workflow_Test",
            enabled=True,
            format="JPEG",
            quality=88,
            max_dimension=2560,
            color_space="sRGB",
            destination="D:/Export/Workflow"
        )
        manager.add_preset(custom_preset)
        
        # 2. Update preset
        manager.update_preset("Workflow_Test", {"quality": 92})
        
        # 3. Duplicate preset
        manager.duplicate_preset("Workflow_Test", "Workflow_Test_Copy")
        
        # 4. Save presets
        manager.save()
        
        # 5. Export presets
        export_path = temp_dir / "workflow_export.json"
        manager.export_presets(export_path)
        
        # 6. Create new manager and import
        new_presets_file = temp_dir / "workflow_import.json"
        new_manager = ExportPresetManager(new_presets_file)
        
        # Clear default presets
        for preset_name in list(new_manager.presets.keys()):
            new_manager.delete_preset(preset_name)
        
        # Import
        imported_count = new_manager.import_presets(export_path, merge=False)
        
        # 7. Verify
        assert imported_count > 0
        
        workflow_preset = new_manager.get_preset("Workflow_Test")
        assert workflow_preset is not None
        assert workflow_preset.quality == 92
        
        workflow_copy = new_manager.get_preset("Workflow_Test_Copy")
        assert workflow_copy is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
