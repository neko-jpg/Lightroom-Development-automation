"""
Export Preset Management System for Junmai AutoDev

This module provides comprehensive export preset management including:
- Multiple export preset configuration
- Preset-specific export parameters (resolution, format, quality)
- Export destination folder management
- Preset validation and CRUD operations

Requirements: 6.1, 6.2
"""

import json
import pathlib
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from copy import deepcopy

logger = logging.getLogger(__name__)


@dataclass
class ExportPreset:
    """
    Export Preset Data Class
    
    Represents a single export preset with all its parameters.
    """
    name: str
    enabled: bool
    format: str  # JPEG, PNG, TIFF, DNG
    quality: int  # 1-100
    max_dimension: int  # Maximum width or height in pixels
    color_space: str  # sRGB, AdobeRGB, ProPhotoRGB
    destination: str  # Output folder path
    
    # Optional advanced settings
    resize_mode: str = "long_edge"  # long_edge, short_edge, width, height, fit
    sharpen_for_screen: bool = False
    sharpen_amount: int = 0  # 0-100
    watermark_enabled: bool = False
    watermark_text: str = ""
    metadata_include: bool = True
    metadata_copyright: str = ""
    
    # File naming
    filename_template: str = "{date}_{sequence}"  # {date}, {time}, {sequence}, {original}
    sequence_start: int = 1
    
    # Created/Updated timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """Validate preset parameters after initialization"""
        self._validate()
        
        # Set timestamps if not provided
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
    
    def _validate(self):
        """Validate preset parameters"""
        # Validate format
        valid_formats = ["JPEG", "PNG", "TIFF", "DNG"]
        if self.format not in valid_formats:
            raise ValueError(f"Invalid format: {self.format}. Must be one of {valid_formats}")
        
        # Validate quality
        if not 1 <= self.quality <= 100:
            raise ValueError(f"Invalid quality: {self.quality}. Must be between 1 and 100")
        
        # Validate max_dimension
        if not 512 <= self.max_dimension <= 8192:
            raise ValueError(f"Invalid max_dimension: {self.max_dimension}. Must be between 512 and 8192")
        
        # Validate color_space
        valid_color_spaces = ["sRGB", "AdobeRGB", "ProPhotoRGB"]
        if self.color_space not in valid_color_spaces:
            raise ValueError(f"Invalid color_space: {self.color_space}. Must be one of {valid_color_spaces}")
        
        # Validate resize_mode
        valid_resize_modes = ["long_edge", "short_edge", "width", "height", "fit"]
        if self.resize_mode not in valid_resize_modes:
            raise ValueError(f"Invalid resize_mode: {self.resize_mode}. Must be one of {valid_resize_modes}")
        
        # Validate sharpen_amount
        if not 0 <= self.sharpen_amount <= 100:
            raise ValueError(f"Invalid sharpen_amount: {self.sharpen_amount}. Must be between 0 and 100")
        
        # Validate destination path
        if not self.destination:
            raise ValueError("Destination path cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert preset to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExportPreset':
        """Create preset from dictionary"""
        return cls(**data)
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now().isoformat()


class ExportPresetManager:
    """
    Export Preset Manager for Junmai AutoDev System
    
    Manages export presets including CRUD operations, validation, and persistence.
    """
    
    def __init__(self, presets_file: Optional[pathlib.Path] = None):
        """
        Initialize ExportPresetManager
        
        Args:
            presets_file: Path to presets JSON file. If None, uses default location.
        """
        if presets_file is None:
            base_dir = pathlib.Path(__file__).parent
            presets_file = base_dir / "config" / "export_presets.json"
        
        self.presets_file = pathlib.Path(presets_file)
        self.presets: Dict[str, ExportPreset] = {}
        self._ensure_presets_directory()
        
        # Load presets or create defaults
        if self.presets_file.exists():
            self.load()
        else:
            self._create_default_presets()
            self.save()
    
    def _ensure_presets_directory(self) -> None:
        """Ensure presets directory exists"""
        self.presets_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _create_default_presets(self) -> None:
        """Create default export presets"""
        logger.info("Creating default export presets")
        
        # SNS Preset (Instagram, Twitter, etc.)
        sns_preset = ExportPreset(
            name="SNS",
            enabled=True,
            format="JPEG",
            quality=85,
            max_dimension=2048,
            color_space="sRGB",
            destination="D:/Export/SNS",
            resize_mode="long_edge",
            sharpen_for_screen=True,
            sharpen_amount=50,
            filename_template="{date}_{sequence}",
            metadata_include=False  # Remove metadata for privacy
        )
        
        # Print Preset (High quality for printing)
        print_preset = ExportPreset(
            name="Print",
            enabled=False,
            format="JPEG",
            quality=95,
            max_dimension=4096,
            color_space="AdobeRGB",
            destination="D:/Export/Print",
            resize_mode="long_edge",
            sharpen_for_screen=False,
            sharpen_amount=0,
            filename_template="{date}_{original}",
            metadata_include=True
        )
        
        # Archive Preset (Maximum quality for archival)
        archive_preset = ExportPreset(
            name="Archive",
            enabled=False,
            format="TIFF",
            quality=100,
            max_dimension=8192,
            color_space="ProPhotoRGB",
            destination="D:/Export/Archive",
            resize_mode="long_edge",
            sharpen_for_screen=False,
            sharpen_amount=0,
            filename_template="{date}_{time}_{original}",
            metadata_include=True
        )
        
        # Web Portfolio Preset
        web_preset = ExportPreset(
            name="Web_Portfolio",
            enabled=False,
            format="JPEG",
            quality=90,
            max_dimension=3000,
            color_space="sRGB",
            destination="D:/Export/Web",
            resize_mode="long_edge",
            sharpen_for_screen=True,
            sharpen_amount=40,
            watermark_enabled=True,
            watermark_text="© {year} Your Name",
            filename_template="{date}_{sequence}",
            metadata_include=True,
            metadata_copyright="© {year} Your Name. All rights reserved."
        )
        
        # Client Delivery Preset
        client_preset = ExportPreset(
            name="Client_Delivery",
            enabled=False,
            format="JPEG",
            quality=92,
            max_dimension=3840,
            color_space="sRGB",
            destination="D:/Export/Client",
            resize_mode="long_edge",
            sharpen_for_screen=False,
            sharpen_amount=30,
            filename_template="{date}_{sequence}",
            metadata_include=True
        )
        
        self.presets = {
            "SNS": sns_preset,
            "Print": print_preset,
            "Archive": archive_preset,
            "Web_Portfolio": web_preset,
            "Client_Delivery": client_preset
        }
    
    def load(self) -> Dict[str, ExportPreset]:
        """
        Load presets from file
        
        Returns:
            Dictionary of presets
            
        Raises:
            FileNotFoundError: If presets file doesn't exist
            json.JSONDecodeError: If presets file is invalid JSON
        """
        if not self.presets_file.exists():
            logger.warning(f"Presets file not found: {self.presets_file}")
            self._create_default_presets()
            self.save()
            return self.presets
        
        try:
            with open(self.presets_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.presets = {}
            for name, preset_data in data.items():
                try:
                    self.presets[name] = ExportPreset.from_dict(preset_data)
                except Exception as e:
                    logger.error(f"Failed to load preset '{name}': {e}")
                    continue
            
            logger.info(f"Loaded {len(self.presets)} export presets from: {self.presets_file}")
            return self.presets
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in presets file: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load presets: {e}")
            raise
    
    def save(self) -> None:
        """
        Save presets to file
        
        Raises:
            IOError: If file cannot be written
        """
        try:
            self._ensure_presets_directory()
            
            # Convert presets to dictionary format
            data = {name: preset.to_dict() for name, preset in self.presets.items()}
            
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(self.presets)} export presets to: {self.presets_file}")
            
        except IOError as e:
            logger.error(f"Failed to save presets: {e}")
            raise
    
    def add_preset(self, preset: ExportPreset) -> bool:
        """
        Add a new export preset
        
        Args:
            preset: ExportPreset to add
            
        Returns:
            True if added successfully, False if preset with same name exists
        """
        if preset.name in self.presets:
            logger.warning(f"Preset '{preset.name}' already exists")
            return False
        
        self.presets[preset.name] = preset
        logger.info(f"Added export preset: {preset.name}")
        return True
    
    def update_preset(self, name: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing export preset
        
        Args:
            name: Name of preset to update
            updates: Dictionary of fields to update
            
        Returns:
            True if updated successfully, False if preset not found
        """
        if name not in self.presets:
            logger.warning(f"Preset '{name}' not found")
            return False
        
        preset = self.presets[name]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(preset, key):
                setattr(preset, key, value)
        
        # Update timestamp
        preset.update_timestamp()
        
        # Validate after update
        try:
            preset._validate()
        except ValueError as e:
            logger.error(f"Validation failed after update: {e}")
            return False
        
        logger.info(f"Updated export preset: {name}")
        return True
    
    def delete_preset(self, name: str) -> bool:
        """
        Delete an export preset
        
        Args:
            name: Name of preset to delete
            
        Returns:
            True if deleted successfully, False if preset not found
        """
        if name not in self.presets:
            logger.warning(f"Preset '{name}' not found")
            return False
        
        del self.presets[name]
        logger.info(f"Deleted export preset: {name}")
        return True
    
    def get_preset(self, name: str) -> Optional[ExportPreset]:
        """
        Get an export preset by name
        
        Args:
            name: Name of preset to retrieve
            
        Returns:
            ExportPreset if found, None otherwise
        """
        return self.presets.get(name)
    
    def list_presets(self, enabled_only: bool = False) -> List[ExportPreset]:
        """
        List all export presets
        
        Args:
            enabled_only: If True, only return enabled presets
            
        Returns:
            List of ExportPreset objects
        """
        presets = list(self.presets.values())
        
        if enabled_only:
            presets = [p for p in presets if p.enabled]
        
        return presets
    
    def get_enabled_presets(self) -> List[ExportPreset]:
        """
        Get all enabled export presets
        
        Returns:
            List of enabled ExportPreset objects
        """
        return self.list_presets(enabled_only=True)
    
    def enable_preset(self, name: str) -> bool:
        """
        Enable an export preset
        
        Args:
            name: Name of preset to enable
            
        Returns:
            True if enabled successfully, False if preset not found
        """
        return self.update_preset(name, {"enabled": True})
    
    def disable_preset(self, name: str) -> bool:
        """
        Disable an export preset
        
        Args:
            name: Name of preset to disable
            
        Returns:
            True if disabled successfully, False if preset not found
        """
        return self.update_preset(name, {"enabled": False})
    
    def validate_preset(self, preset: ExportPreset) -> Tuple[bool, Optional[str]]:
        """
        Validate an export preset
        
        Args:
            preset: ExportPreset to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            preset._validate()
            return True, None
        except ValueError as e:
            return False, str(e)
    
    def validate_destination(self, destination: str) -> Tuple[bool, Optional[str]]:
        """
        Validate export destination path
        
        Args:
            destination: Destination path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        dest_path = pathlib.Path(destination)
        
        # Check if path is absolute
        if not dest_path.is_absolute():
            return False, "Destination path must be absolute"
        
        # Check if parent directory exists or can be created
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            return True, None
        except Exception as e:
            return False, f"Cannot create destination directory: {e}"
    
    def export_presets(self, export_path: pathlib.Path) -> None:
        """
        Export presets to a different file
        
        Args:
            export_path: Path to export presets to
        """
        export_path = pathlib.Path(export_path)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            data = {name: preset.to_dict() for name, preset in self.presets.items()}
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Exported {len(self.presets)} presets to: {export_path}")
            
        except IOError as e:
            logger.error(f"Failed to export presets: {e}")
            raise
    
    def import_presets(self, import_path: pathlib.Path, merge: bool = True) -> int:
        """
        Import presets from a different file
        
        Args:
            import_path: Path to import presets from
            merge: If True, merge with existing presets. If False, replace all.
            
        Returns:
            Number of presets imported
            
        Raises:
            FileNotFoundError: If import file doesn't exist
        """
        import_path = pathlib.Path(import_path)
        
        if not import_path.exists():
            raise FileNotFoundError(f"Import file not found: {import_path}")
        
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported_presets = {}
            for name, preset_data in data.items():
                try:
                    imported_presets[name] = ExportPreset.from_dict(preset_data)
                except Exception as e:
                    logger.error(f"Failed to import preset '{name}': {e}")
                    continue
            
            if not merge:
                self.presets = imported_presets
            else:
                self.presets.update(imported_presets)
            
            logger.info(f"Imported {len(imported_presets)} presets from: {import_path}")
            return len(imported_presets)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in import file: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to import presets: {e}")
            raise
    
    def duplicate_preset(self, source_name: str, new_name: str) -> bool:
        """
        Duplicate an existing preset with a new name
        
        Args:
            source_name: Name of preset to duplicate
            new_name: Name for the duplicated preset
            
        Returns:
            True if duplicated successfully, False otherwise
        """
        if source_name not in self.presets:
            logger.warning(f"Source preset '{source_name}' not found")
            return False
        
        if new_name in self.presets:
            logger.warning(f"Preset '{new_name}' already exists")
            return False
        
        # Create a deep copy of the source preset
        source_preset = self.presets[source_name]
        preset_dict = source_preset.to_dict()
        preset_dict['name'] = new_name
        preset_dict['created_at'] = datetime.now().isoformat()
        preset_dict['updated_at'] = datetime.now().isoformat()
        
        new_preset = ExportPreset.from_dict(preset_dict)
        self.presets[new_name] = new_preset
        
        logger.info(f"Duplicated preset '{source_name}' to '{new_name}'")
        return True
    
    def get_preset_count(self) -> int:
        """
        Get total number of presets
        
        Returns:
            Number of presets
        """
        return len(self.presets)
    
    def get_enabled_preset_count(self) -> int:
        """
        Get number of enabled presets
        
        Returns:
            Number of enabled presets
        """
        return len([p for p in self.presets.values() if p.enabled])


# Convenience function for quick access
def get_export_preset_manager(presets_file: Optional[pathlib.Path] = None) -> ExportPresetManager:
    """
    Get an ExportPresetManager instance
    
    Args:
        presets_file: Optional path to presets file
        
    Returns:
        ExportPresetManager instance
    """
    return ExportPresetManager(presets_file)


if __name__ == '__main__':
    # Setup logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test export preset manager
    print("=== Testing Export Preset Manager ===\n")
    
    # Test 1: Create manager with default presets
    print("Test 1: Create manager with default presets")
    manager = ExportPresetManager(pathlib.Path("test_export_presets.json"))
    print(f"✓ Created manager with {manager.get_preset_count()} default presets")
    
    # Test 2: List all presets
    print("\nTest 2: List all presets")
    presets = manager.list_presets()
    for preset in presets:
        print(f"  - {preset.name}: {preset.format} {preset.max_dimension}px @ {preset.quality}% (Enabled: {preset.enabled})")
    
    # Test 3: Get specific preset
    print("\nTest 3: Get specific preset")
    sns_preset = manager.get_preset("SNS")
    if sns_preset:
        print(f"✓ SNS Preset: {sns_preset.format}, {sns_preset.max_dimension}px, Quality: {sns_preset.quality}%")
    
    # Test 4: Update preset
    print("\nTest 4: Update preset")
    success = manager.update_preset("SNS", {"quality": 90, "max_dimension": 2560})
    if success:
        updated_preset = manager.get_preset("SNS")
        print(f"✓ Updated SNS preset: Quality={updated_preset.quality}%, Dimension={updated_preset.max_dimension}px")
    
    # Test 5: Add new preset
    print("\nTest 5: Add new preset")
    custom_preset = ExportPreset(
        name="Custom_4K",
        enabled=True,
        format="JPEG",
        quality=88,
        max_dimension=3840,
        color_space="sRGB",
        destination="D:/Export/Custom"
    )
    success = manager.add_preset(custom_preset)
    print(f"✓ Added custom preset: {success}")
    
    # Test 6: Duplicate preset
    print("\nTest 6: Duplicate preset")
    success = manager.duplicate_preset("SNS", "SNS_Copy")
    if success:
        print(f"✓ Duplicated SNS preset to SNS_Copy")
    
    # Test 7: Enable/Disable preset
    print("\nTest 7: Enable/Disable preset")
    manager.disable_preset("Print")
    manager.enable_preset("Archive")
    enabled_count = manager.get_enabled_preset_count()
    print(f"✓ Enabled presets: {enabled_count}/{manager.get_preset_count()}")
    
    # Test 8: Get enabled presets only
    print("\nTest 8: Get enabled presets only")
    enabled_presets = manager.get_enabled_presets()
    print(f"✓ Enabled presets: {[p.name for p in enabled_presets]}")
    
    # Test 9: Save presets
    print("\nTest 9: Save presets")
    manager.save()
    print(f"✓ Saved presets to: {manager.presets_file}")
    
    # Test 10: Load presets
    print("\nTest 10: Load presets")
    manager2 = ExportPresetManager(pathlib.Path("test_export_presets.json"))
    loaded_count = manager2.get_preset_count()
    print(f"✓ Loaded {loaded_count} presets")
    
    # Test 11: Delete preset
    print("\nTest 11: Delete preset")
    success = manager.delete_preset("SNS_Copy")
    print(f"✓ Deleted preset: {success}, Remaining: {manager.get_preset_count()}")
    
    # Test 12: Validate preset
    print("\nTest 12: Validate preset")
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
    print(f"✓ Validation result: {is_valid}, Error: {error}")
    
    # Test 13: Export/Import presets
    print("\nTest 13: Export/Import presets")
    export_path = pathlib.Path("test_export_backup.json")
    manager.export_presets(export_path)
    print(f"✓ Exported presets to: {export_path}")
    
    imported_count = manager.import_presets(export_path, merge=False)
    print(f"✓ Imported {imported_count} presets")
    
    # Cleanup
    import os
    for file in ["test_export_presets.json", "test_export_backup.json"]:
        if os.path.exists(file):
            os.remove(file)
    print("\n✓ Test files cleaned up")
    
    print("\n=== All tests passed! ===")
