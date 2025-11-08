"""
Tests for Preset Management System.

Tests cover:
- Preset CRUD operations
- Context-to-preset mapping
- Version management
- Import/Export functionality
- Usage tracking and statistics
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.database import Base, Preset, Photo, Session as DBSession, LearningData
from preset_manager import PresetManager


@pytest.fixture
def db_session():
    """Create a temporary in-memory database for testing."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def temp_presets_dir():
    """Create a temporary directory for preset files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def preset_manager(db_session, temp_presets_dir):
    """Create a PresetManager instance for testing."""
    return PresetManager(db_session, temp_presets_dir)


@pytest.fixture
def sample_config():
    """Sample LrDevConfig template."""
    return {
        "version": "1.0",
        "pipeline": [
            {
                "stage": "base",
                "settings": {
                    "Exposure2012": -0.15,
                    "Highlights2012": -18,
                    "Shadows2012": 12
                }
            },
            {
                "stage": "HSL",
                "hue": {"orange": -4},
                "sat": {"orange": -6},
                "lum": {"orange": 4}
            }
        ],
        "safety": {
            "snapshot": True,
            "dryRun": False
        }
    }


class TestPresetCRUD:
    """Test preset CRUD operations."""
    
    def test_create_preset(self, preset_manager, sample_config):
        """Test creating a new preset."""
        preset = preset_manager.create_preset(
            name="WhiteLayer_Transparency",
            version="v4",
            config_template=sample_config,
            context_tags=["backlit_portrait", "outdoor"],
            blend_amount=60
        )
        
        assert preset.id is not None
        assert preset.name == "WhiteLayer_Transparency"
        assert preset.version == "v4"
        assert preset.blend_amount == 60
        assert preset.usage_count == 0
        assert preset.avg_approval_rate is None
        
        # Check context tags
        tags = preset.get_context_tags()
        assert "backlit_portrait" in tags
        assert "outdoor" in tags
        
        # Check config template
        config = preset.get_config_template()
        assert config["version"] == "1.0"
        assert len(config["pipeline"]) == 2
    
    def test_create_duplicate_preset(self, preset_manager, sample_config):
        """Test that creating duplicate preset raises error."""
        preset_manager.create_preset(
            name="TestPreset",
            version="v1",
            config_template=sample_config
        )
        
        with pytest.raises(ValueError, match="already exists"):
            preset_manager.create_preset(
                name="TestPreset",
                version="v2",
                config_template=sample_config
            )
    
    def test_get_preset(self, preset_manager, sample_config):
        """Test retrieving a preset by ID."""
        created = preset_manager.create_preset(
            name="TestPreset",
            version="v1",
            config_template=sample_config
        )
        
        retrieved = preset_manager.get_preset(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "TestPreset"
    
    def test_get_preset_by_name(self, preset_manager, sample_config):
        """Test retrieving a preset by name."""
        preset_manager.create_preset(
            name="TestPreset",
            version="v1",
            config_template=sample_config
        )
        
        retrieved = preset_manager.get_preset_by_name("TestPreset")
        assert retrieved is not None
        assert retrieved.name == "TestPreset"
    
    def test_list_presets(self, preset_manager, sample_config):
        """Test listing all presets."""
        # Create multiple presets
        preset_manager.create_preset("Preset1", "v1", sample_config)
        preset_manager.create_preset("Preset2", "v1", sample_config)
        preset_manager.create_preset("Preset3", "v1", sample_config)
        
        presets = preset_manager.list_presets()
        assert len(presets) == 3
        
        # Check ordering by name
        names = [p.name for p in presets]
        assert names == sorted(names)
    
    def test_list_presets_by_context(self, preset_manager, sample_config):
        """Test filtering presets by context tag."""
        preset_manager.create_preset(
            "Preset1", "v1", sample_config,
            context_tags=["backlit_portrait"]
        )
        preset_manager.create_preset(
            "Preset2", "v1", sample_config,
            context_tags=["low_light_indoor"]
        )
        preset_manager.create_preset(
            "Preset3", "v1", sample_config,
            context_tags=["backlit_portrait", "outdoor"]
        )
        
        # Filter by backlit_portrait
        filtered = preset_manager.list_presets(context_tag="backlit_portrait")
        assert len(filtered) == 2
        
        names = [p.name for p in filtered]
        assert "Preset1" in names
        assert "Preset3" in names
    
    def test_update_preset(self, preset_manager, sample_config):
        """Test updating a preset."""
        preset = preset_manager.create_preset(
            "TestPreset", "v1", sample_config,
            blend_amount=50
        )
        
        # Update blend amount and version
        updated = preset_manager.update_preset(
            preset.id,
            blend_amount=75,
            version="v2"
        )
        
        assert updated.blend_amount == 75
        assert updated.version == "v2"
    
    def test_delete_preset(self, preset_manager, sample_config):
        """Test deleting a preset."""
        preset = preset_manager.create_preset(
            "TestPreset", "v1", sample_config
        )
        
        # Delete preset
        result = preset_manager.delete_preset(preset.id)
        assert result is True
        
        # Verify it's gone
        retrieved = preset_manager.get_preset(preset.id)
        assert retrieved is None


class TestContextMapping:
    """Test context-to-preset mapping functionality."""
    
    def test_select_preset_for_context(self, preset_manager, sample_config):
        """Test selecting preset based on context."""
        # Create presets with different contexts
        preset_manager.create_preset(
            "BacklitPreset", "v1", sample_config,
            context_tags=["backlit_portrait"]
        )
        preset_manager.create_preset(
            "LowLightPreset", "v1", sample_config,
            context_tags=["low_light_indoor"]
        )
        
        # Select for backlit context
        selected = preset_manager.select_preset_for_context("backlit_portrait")
        assert selected is not None
        assert selected.name == "BacklitPreset"
    
    def test_select_preset_multiple_matches(self, preset_manager, sample_config):
        """Test selecting best preset when multiple match."""
        # Create two presets for same context with different stats
        preset1 = preset_manager.create_preset(
            "Preset1", "v1", sample_config,
            context_tags=["backlit_portrait"]
        )
        preset1.usage_count = 10
        preset1.avg_approval_rate = 0.7
        
        preset2 = preset_manager.create_preset(
            "Preset2", "v1", sample_config,
            context_tags=["backlit_portrait"]
        )
        preset2.usage_count = 20
        preset2.avg_approval_rate = 0.9
        
        preset_manager.db.commit()
        
        # Should select preset with higher approval rate
        selected = preset_manager.select_preset_for_context("backlit_portrait")
        assert selected.name == "Preset2"
    
    def test_map_contexts_to_presets(self, preset_manager, sample_config):
        """Test getting complete context-to-preset mapping."""
        preset_manager.create_preset(
            "Preset1", "v1", sample_config,
            context_tags=["backlit_portrait", "outdoor"]
        )
        preset_manager.create_preset(
            "Preset2", "v1", sample_config,
            context_tags=["low_light_indoor"]
        )
        
        mapping = preset_manager.map_contexts_to_presets()
        
        assert "backlit_portrait" in mapping
        assert "outdoor" in mapping
        assert "low_light_indoor" in mapping
        assert "Preset1" in mapping["backlit_portrait"]
        assert "Preset2" in mapping["low_light_indoor"]


class TestVersionManagement:
    """Test preset version management."""
    
    def test_create_preset_version(self, preset_manager, sample_config):
        """Test creating a new version of a preset."""
        # Create base preset
        base = preset_manager.create_preset(
            "WhiteLayer", "v1", sample_config,
            context_tags=["backlit_portrait"]
        )
        
        # Create new version with changes
        changes = {
            "pipeline": [
                {
                    "stage": "base",
                    "settings": {
                        "Exposure2012": -0.20  # Changed from -0.15
                    }
                }
            ]
        }
        
        new_version = preset_manager.create_preset_version(
            base.id, "v2", changes
        )
        
        assert new_version.name == "WhiteLayer_v2"
        assert new_version.version == "v2"
        
        # Check that config was updated
        config = new_version.get_config_template()
        exposure = config["pipeline"][0]["settings"]["Exposure2012"]
        assert exposure == -0.20
    
    def test_get_preset_versions(self, preset_manager, sample_config):
        """Test retrieving all versions of a preset."""
        # Create base and versions
        base = preset_manager.create_preset(
            "WhiteLayer", "v1", sample_config
        )
        preset_manager.create_preset_version(base.id, "v2")
        preset_manager.create_preset_version(base.id, "v3")
        
        versions = preset_manager.get_preset_versions("WhiteLayer")
        assert len(versions) == 3
        
        # Check version ordering
        version_strings = [p.version for p in versions]
        assert version_strings == ["v1", "v2", "v3"]
    
    def test_compare_preset_versions(self, preset_manager, sample_config):
        """Test comparing two preset versions."""
        # Create two versions
        preset1 = preset_manager.create_preset(
            "Preset_v1", "v1", sample_config
        )
        
        modified_config = sample_config.copy()
        modified_config["pipeline"][0]["settings"]["Exposure2012"] = -0.25
        
        preset2 = preset_manager.create_preset(
            "Preset_v2", "v2", modified_config
        )
        
        comparison = preset_manager.compare_preset_versions(
            preset1.id, preset2.id
        )
        
        assert comparison["preset1"]["version"] == "v1"
        assert comparison["preset2"]["version"] == "v2"
        assert "config_diff" in comparison


class TestImportExport:
    """Test preset import/export functionality."""
    
    def test_export_preset(self, preset_manager, sample_config, temp_presets_dir):
        """Test exporting a preset to JSON file."""
        preset = preset_manager.create_preset(
            "TestPreset", "v1", sample_config,
            context_tags=["test_context"]
        )
        
        file_path = preset_manager.export_preset(preset.id)
        
        # Check file exists
        assert Path(file_path).exists()
        
        # Check file content
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        assert data["name"] == "TestPreset"
        assert data["version"] == "v1"
        assert "test_context" in data["context_tags"]
        assert "config_template" in data
        assert "metadata" in data
    
    def test_import_preset(self, preset_manager, sample_config, temp_presets_dir):
        """Test importing a preset from JSON file."""
        # Create export file
        export_data = {
            "name": "ImportedPreset",
            "version": "v1",
            "context_tags": ["imported"],
            "config_template": sample_config,
            "blend_amount": 80
        }
        
        file_path = Path(temp_presets_dir) / "imported.json"
        with open(file_path, 'w') as f:
            json.dump(export_data, f)
        
        # Import preset
        preset = preset_manager.import_preset(str(file_path))
        
        assert preset.name == "ImportedPreset"
        assert preset.version == "v1"
        assert preset.blend_amount == 80
        assert "imported" in preset.get_context_tags()
    
    def test_import_preset_overwrite(self, preset_manager, sample_config, temp_presets_dir):
        """Test importing with overwrite option."""
        # Create existing preset
        preset_manager.create_preset(
            "ExistingPreset", "v1", sample_config
        )
        
        # Create import file with same name
        export_data = {
            "name": "ExistingPreset",
            "version": "v2",
            "config_template": sample_config
        }
        
        file_path = Path(temp_presets_dir) / "existing.json"
        with open(file_path, 'w') as f:
            json.dump(export_data, f)
        
        # Import without overwrite should fail
        with pytest.raises(ValueError, match="already exists"):
            preset_manager.import_preset(str(file_path), overwrite=False)
        
        # Import with overwrite should succeed
        preset = preset_manager.import_preset(str(file_path), overwrite=True)
        assert preset.version == "v2"
    
    def test_export_all_presets(self, preset_manager, sample_config, temp_presets_dir):
        """Test exporting all presets."""
        # Create multiple presets
        preset_manager.create_preset("Preset1", "v1", sample_config)
        preset_manager.create_preset("Preset2", "v1", sample_config)
        preset_manager.create_preset("Preset3", "v1", sample_config)
        
        files = preset_manager.export_all_presets()
        
        assert len(files) == 3
        for file_path in files:
            assert Path(file_path).exists()
    
    def test_import_presets_from_directory(self, preset_manager, sample_config, temp_presets_dir):
        """Test importing all presets from a directory."""
        # Create multiple preset files
        for i in range(3):
            export_data = {
                "name": f"Preset{i}",
                "version": "v1",
                "config_template": sample_config
            }
            file_path = Path(temp_presets_dir) / f"preset{i}.json"
            with open(file_path, 'w') as f:
                json.dump(export_data, f)
        
        # Import all
        presets = preset_manager.import_presets_from_directory(temp_presets_dir)
        
        assert len(presets) == 3


class TestUsageTracking:
    """Test usage tracking and statistics."""
    
    def test_record_preset_usage(self, preset_manager, sample_config):
        """Test recording preset usage."""
        preset = preset_manager.create_preset(
            "TestPreset", "v1", sample_config
        )
        
        # Create a photo
        photo = Photo(
            file_path="/test/photo.jpg",
            file_name="photo.jpg",
            status="completed"
        )
        preset_manager.db.add(photo)
        preset_manager.db.commit()
        
        # Record usage (approved)
        preset_manager.record_preset_usage(preset.id, photo.id, approved=True)
        
        # Check updated stats
        preset_manager.db.refresh(preset)
        assert preset.usage_count == 1
        assert preset.avg_approval_rate == 1.0
        
        # Record another usage (rejected)
        preset_manager.record_preset_usage(preset.id, photo.id, approved=False)
        
        preset_manager.db.refresh(preset)
        assert preset.usage_count == 2
        assert 0 < preset.avg_approval_rate < 1.0
    
    def test_get_preset_statistics(self, preset_manager, sample_config, db_session):
        """Test getting detailed preset statistics."""
        preset = preset_manager.create_preset(
            "TestPreset", "v1", sample_config,
            context_tags=["test"]
        )
        preset.usage_count = 10
        preset.avg_approval_rate = 0.85
        db_session.commit()
        
        # Create photo and learning data
        photo = Photo(
            file_path="/test/photo.jpg",
            file_name="photo.jpg",
            selected_preset="TestPreset",
            status="completed"
        )
        db_session.add(photo)
        db_session.commit()
        
        learning = LearningData(
            photo_id=photo.id,
            action="approved",
            original_preset="TestPreset"
        )
        db_session.add(learning)
        db_session.commit()
        
        # Get statistics
        stats = preset_manager.get_preset_statistics(preset.id)
        
        assert stats["name"] == "TestPreset"
        assert stats["usage_count"] == 10
        assert stats["avg_approval_rate"] == 0.85
        assert "test" in stats["context_tags"]
        assert stats["learning_data"]["approved"] == 1
    
    def test_get_top_presets(self, preset_manager, sample_config):
        """Test getting top presets by usage or approval."""
        # Create presets with different stats
        preset1 = preset_manager.create_preset("Preset1", "v1", sample_config)
        preset1.usage_count = 100
        preset1.avg_approval_rate = 0.7
        
        preset2 = preset_manager.create_preset("Preset2", "v1", sample_config)
        preset2.usage_count = 50
        preset2.avg_approval_rate = 0.9
        
        preset3 = preset_manager.create_preset("Preset3", "v1", sample_config)
        preset3.usage_count = 75
        preset3.avg_approval_rate = 0.8
        
        preset_manager.db.commit()
        
        # Get top by usage
        top_usage = preset_manager.get_top_presets(limit=2, metric="usage")
        assert len(top_usage) == 2
        assert top_usage[0]["name"] == "Preset1"
        
        # Get top by approval
        top_approval = preset_manager.get_top_presets(limit=2, metric="approval")
        assert len(top_approval) == 2
        assert top_approval[0]["name"] == "Preset2"


class TestValidation:
    """Test configuration validation."""
    
    def test_validate_config_missing_version(self, preset_manager):
        """Test validation fails for missing version."""
        invalid_config = {
            "pipeline": []
        }
        
        with pytest.raises(ValueError, match="version"):
            preset_manager.create_preset(
                "Invalid", "v1", invalid_config
            )
    
    def test_validate_config_missing_pipeline(self, preset_manager):
        """Test validation fails for missing pipeline."""
        invalid_config = {
            "version": "1.0"
        }
        
        with pytest.raises(ValueError, match="pipeline"):
            preset_manager.create_preset(
                "Invalid", "v1", invalid_config
            )
    
    def test_validate_config_invalid_stage(self, preset_manager):
        """Test validation fails for invalid stage."""
        invalid_config = {
            "version": "1.0",
            "pipeline": [
                {"stage": "invalid_stage"}
            ]
        }
        
        with pytest.raises(ValueError, match="Invalid stage"):
            preset_manager.create_preset(
                "Invalid", "v1", invalid_config
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
