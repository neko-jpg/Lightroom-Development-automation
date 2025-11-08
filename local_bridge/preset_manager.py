"""
Preset Management System for Junmai AutoDev.

This module provides comprehensive preset management functionality including:
- Context-to-preset mapping
- Preset versioning
- Import/Export capabilities
- Usage tracking and approval rate statistics

Requirements: 3.3, 10.1, 10.2
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from models.database import Preset, LearningData, Photo


class PresetManager:
    """
    Manages presets for the Junmai AutoDev system.
    
    Provides functionality for:
    - Creating and updating presets
    - Context-based preset selection
    - Version management
    - Import/Export operations
    - Usage statistics and approval rate tracking
    """
    
    def __init__(self, db_session: Session, presets_dir: str = "config/presets"):
        """
        Initialize the PresetManager.
        
        Args:
            db_session: SQLAlchemy database session
            presets_dir: Directory for storing preset files
        """
        self.db = db_session
        self.presets_dir = Path(presets_dir)
        self.presets_dir.mkdir(parents=True, exist_ok=True)
    
    # ========== Preset CRUD Operations ==========
    
    def create_preset(
        self,
        name: str,
        version: str,
        config_template: Dict,
        context_tags: Optional[List[str]] = None,
        blend_amount: int = 100
    ) -> Preset:
        """
        Create a new preset.
        
        Args:
            name: Unique preset name
            version: Version string (e.g., "v1", "v2.1")
            config_template: LrDevConfig JSON template
            context_tags: List of context tags this preset applies to
            blend_amount: Blend amount (0-100)
        
        Returns:
            Created Preset object
        
        Raises:
            ValueError: If preset with same name already exists
        """
        # Check if preset already exists
        existing = self.db.query(Preset).filter_by(name=name).first()
        if existing:
            raise ValueError(f"Preset with name '{name}' already exists")
        
        # Validate config template
        self._validate_config_template(config_template)
        
        # Create preset
        preset = Preset(
            name=name,
            version=version,
            blend_amount=blend_amount,
            usage_count=0,
            avg_approval_rate=None
        )
        preset.set_config_template(config_template)
        preset.set_context_tags(context_tags or [])
        
        self.db.add(preset)
        self.db.commit()
        self.db.refresh(preset)
        
        return preset
    
    def get_preset(self, preset_id: int) -> Optional[Preset]:
        """Get preset by ID."""
        return self.db.query(Preset).filter_by(id=preset_id).first()
    
    def get_preset_by_name(self, name: str) -> Optional[Preset]:
        """Get preset by name."""
        return self.db.query(Preset).filter_by(name=name).first()
    
    def list_presets(
        self,
        context_tag: Optional[str] = None,
        order_by: str = "name"
    ) -> List[Preset]:
        """
        List all presets, optionally filtered by context tag.
        
        Args:
            context_tag: Filter by context tag (optional)
            order_by: Sort field ("name", "usage_count", "avg_approval_rate", "created_at")
        
        Returns:
            List of Preset objects
        """
        query = self.db.query(Preset)
        
        # Filter by context tag if specified
        if context_tag:
            query = query.filter(Preset.context_tags.like(f'%"{context_tag}"%'))
        
        # Apply ordering
        if order_by == "usage_count":
            query = query.order_by(desc(Preset.usage_count))
        elif order_by == "avg_approval_rate":
            query = query.order_by(desc(Preset.avg_approval_rate))
        elif order_by == "created_at":
            query = query.order_by(desc(Preset.created_at))
        else:  # default to name
            query = query.order_by(Preset.name)
        
        return query.all()
    
    def update_preset(
        self,
        preset_id: int,
        config_template: Optional[Dict] = None,
        context_tags: Optional[List[str]] = None,
        blend_amount: Optional[int] = None,
        version: Optional[str] = None
    ) -> Preset:
        """
        Update an existing preset.
        
        Args:
            preset_id: Preset ID to update
            config_template: New config template (optional)
            context_tags: New context tags (optional)
            blend_amount: New blend amount (optional)
            version: New version string (optional)
        
        Returns:
            Updated Preset object
        
        Raises:
            ValueError: If preset not found
        """
        preset = self.get_preset(preset_id)
        if not preset:
            raise ValueError(f"Preset with ID {preset_id} not found")
        
        if config_template is not None:
            self._validate_config_template(config_template)
            preset.set_config_template(config_template)
        
        if context_tags is not None:
            preset.set_context_tags(context_tags)
        
        if blend_amount is not None:
            if not 0 <= blend_amount <= 100:
                raise ValueError("blend_amount must be between 0 and 100")
            preset.blend_amount = blend_amount
        
        if version is not None:
            preset.version = version
        
        preset.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(preset)
        
        return preset
    
    def delete_preset(self, preset_id: int) -> bool:
        """
        Delete a preset.
        
        Args:
            preset_id: Preset ID to delete
        
        Returns:
            True if deleted, False if not found
        """
        preset = self.get_preset(preset_id)
        if not preset:
            return False
        
        self.db.delete(preset)
        self.db.commit()
        
        return True
    
    # ========== Context-to-Preset Mapping ==========
    
    def select_preset_for_context(
        self,
        context_tag: str,
        learning_data: Optional[Dict] = None
    ) -> Optional[Preset]:
        """
        Select the best preset for a given context.
        
        Args:
            context_tag: Context tag (e.g., "backlit_portrait", "low_light_indoor")
            learning_data: Optional learning data for personalization
        
        Returns:
            Best matching Preset object, or None if no match
        """
        # Find presets matching the context tag
        matching_presets = self.db.query(Preset).filter(
            Preset.context_tags.like(f'%"{context_tag}"%')
        ).all()
        
        if not matching_presets:
            # Fall back to default preset
            return self.get_preset_by_name("default")
        
        # If only one match, return it
        if len(matching_presets) == 1:
            return matching_presets[0]
        
        # Multiple matches: select based on approval rate and usage
        # Sort by approval rate (descending), then usage count (descending)
        best_preset = max(
            matching_presets,
            key=lambda p: (
                p.avg_approval_rate if p.avg_approval_rate is not None else 0,
                p.usage_count
            )
        )
        
        return best_preset
    
    def map_contexts_to_presets(self) -> Dict[str, List[str]]:
        """
        Get a mapping of all context tags to preset names.
        
        Returns:
            Dictionary mapping context tags to list of preset names
        """
        presets = self.list_presets()
        mapping = {}
        
        for preset in presets:
            tags = preset.get_context_tags()
            for tag in tags:
                if tag not in mapping:
                    mapping[tag] = []
                mapping[tag].append(preset.name)
        
        return mapping
    
    # ========== Version Management ==========
    
    def create_preset_version(
        self,
        base_preset_id: int,
        new_version: str,
        config_changes: Optional[Dict] = None
    ) -> Preset:
        """
        Create a new version of an existing preset.
        
        Args:
            base_preset_id: ID of the preset to version
            new_version: New version string
            config_changes: Optional changes to apply to config template
        
        Returns:
            New Preset object with updated version
        
        Raises:
            ValueError: If base preset not found
        """
        base_preset = self.get_preset(base_preset_id)
        if not base_preset:
            raise ValueError(f"Base preset with ID {base_preset_id} not found")
        
        # Create new preset name with version
        new_name = f"{base_preset.name}_{new_version}"
        
        # Get base config and apply changes
        config = base_preset.get_config_template()
        if config_changes:
            config = self._merge_config_changes(config, config_changes)
        
        # Create new preset
        new_preset = self.create_preset(
            name=new_name,
            version=new_version,
            config_template=config,
            context_tags=base_preset.get_context_tags(),
            blend_amount=base_preset.blend_amount
        )
        
        return new_preset
    
    def get_preset_versions(self, base_name: str) -> List[Preset]:
        """
        Get all versions of a preset.
        
        Args:
            base_name: Base preset name (without version suffix)
        
        Returns:
            List of Preset objects, ordered by version
        """
        presets = self.db.query(Preset).filter(
            Preset.name.like(f"{base_name}%")
        ).order_by(Preset.version).all()
        
        return presets
    
    def compare_preset_versions(
        self,
        preset_id_1: int,
        preset_id_2: int
    ) -> Dict:
        """
        Compare two preset versions.
        
        Args:
            preset_id_1: First preset ID
            preset_id_2: Second preset ID
        
        Returns:
            Dictionary with comparison results
        """
        preset1 = self.get_preset(preset_id_1)
        preset2 = self.get_preset(preset_id_2)
        
        if not preset1 or not preset2:
            raise ValueError("One or both presets not found")
        
        config1 = preset1.get_config_template()
        config2 = preset2.get_config_template()
        
        return {
            "preset1": {
                "id": preset1.id,
                "name": preset1.name,
                "version": preset1.version,
                "usage_count": preset1.usage_count,
                "avg_approval_rate": preset1.avg_approval_rate
            },
            "preset2": {
                "id": preset2.id,
                "name": preset2.name,
                "version": preset2.version,
                "usage_count": preset2.usage_count,
                "avg_approval_rate": preset2.avg_approval_rate
            },
            "config_diff": self._diff_configs(config1, config2)
        }
    
    # ========== Import/Export ==========
    
    def export_preset(self, preset_id: int, file_path: Optional[str] = None) -> str:
        """
        Export a preset to a JSON file.
        
        Args:
            preset_id: Preset ID to export
            file_path: Optional custom file path (defaults to presets_dir)
        
        Returns:
            Path to exported file
        
        Raises:
            ValueError: If preset not found
        """
        preset = self.get_preset(preset_id)
        if not preset:
            raise ValueError(f"Preset with ID {preset_id} not found")
        
        # Prepare export data
        export_data = {
            "name": preset.name,
            "version": preset.version,
            "context_tags": preset.get_context_tags(),
            "config_template": preset.get_config_template(),
            "blend_amount": preset.blend_amount,
            "exported_at": datetime.utcnow().isoformat(),
            "metadata": {
                "usage_count": preset.usage_count,
                "avg_approval_rate": preset.avg_approval_rate,
                "created_at": preset.created_at.isoformat(),
                "updated_at": preset.updated_at.isoformat()
            }
        }
        
        # Determine file path
        if file_path is None:
            file_path = self.presets_dir / f"{preset.name}_{preset.version}.json"
        else:
            file_path = Path(file_path)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return str(file_path)
    
    def import_preset(
        self,
        file_path: str,
        overwrite: bool = False
    ) -> Preset:
        """
        Import a preset from a JSON file.
        
        Args:
            file_path: Path to preset JSON file
            overwrite: If True, overwrite existing preset with same name
        
        Returns:
            Imported Preset object
        
        Raises:
            ValueError: If file not found or invalid format
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Preset file not found: {file_path}")
        
        # Load preset data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate required fields
        required_fields = ["name", "version", "config_template"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Invalid preset file: missing '{field}' field")
        
        # Check if preset already exists
        existing = self.get_preset_by_name(data["name"])
        if existing:
            if not overwrite:
                raise ValueError(
                    f"Preset '{data['name']}' already exists. "
                    "Use overwrite=True to replace it."
                )
            # Delete existing preset
            self.delete_preset(existing.id)
        
        # Create new preset
        preset = self.create_preset(
            name=data["name"],
            version=data["version"],
            config_template=data["config_template"],
            context_tags=data.get("context_tags", []),
            blend_amount=data.get("blend_amount", 100)
        )
        
        return preset
    
    def export_all_presets(self, output_dir: Optional[str] = None) -> List[str]:
        """
        Export all presets to JSON files.
        
        Args:
            output_dir: Optional output directory (defaults to presets_dir)
        
        Returns:
            List of exported file paths
        """
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = self.presets_dir
        
        presets = self.list_presets()
        exported_files = []
        
        for preset in presets:
            file_path = output_dir / f"{preset.name}_{preset.version}.json"
            self.export_preset(preset.id, str(file_path))
            exported_files.append(str(file_path))
        
        return exported_files
    
    def import_presets_from_directory(
        self,
        directory: str,
        overwrite: bool = False
    ) -> List[Preset]:
        """
        Import all presets from a directory.
        
        Args:
            directory: Directory containing preset JSON files
            overwrite: If True, overwrite existing presets
        
        Returns:
            List of imported Preset objects
        """
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        imported_presets = []
        
        for file_path in directory.glob("*.json"):
            try:
                preset = self.import_preset(str(file_path), overwrite=overwrite)
                imported_presets.append(preset)
            except Exception as e:
                print(f"Warning: Failed to import {file_path}: {e}")
        
        return imported_presets
    
    # ========== Usage Tracking and Statistics ==========
    
    def record_preset_usage(
        self,
        preset_id: int,
        photo_id: int,
        approved: bool
    ) -> None:
        """
        Record preset usage and update statistics.
        
        Args:
            preset_id: Preset ID that was used
            photo_id: Photo ID it was applied to
            approved: Whether the result was approved
        """
        preset = self.get_preset(preset_id)
        if not preset:
            return
        
        # Increment usage count
        preset.usage_count += 1
        
        # Update approval rate (moving average)
        if preset.avg_approval_rate is None:
            preset.avg_approval_rate = 1.0 if approved else 0.0
        else:
            # Weighted moving average (more weight to recent approvals)
            alpha = 0.1
            new_value = 1.0 if approved else 0.0
            preset.avg_approval_rate = (
                alpha * new_value + (1 - alpha) * preset.avg_approval_rate
            )
        
        self.db.commit()
    
    def get_preset_statistics(self, preset_id: int) -> Dict:
        """
        Get detailed statistics for a preset.
        
        Args:
            preset_id: Preset ID
        
        Returns:
            Dictionary with statistics
        """
        preset = self.get_preset(preset_id)
        if not preset:
            raise ValueError(f"Preset with ID {preset_id} not found")
        
        # Get learning data for this preset
        learning_stats = self.db.query(
            LearningData.action,
            func.count(LearningData.id).label('count')
        ).join(Photo).filter(
            Photo.selected_preset == preset.name
        ).group_by(LearningData.action).all()
        
        action_counts = {action: count for action, count in learning_stats}
        
        return {
            "preset_id": preset.id,
            "name": preset.name,
            "version": preset.version,
            "usage_count": preset.usage_count,
            "avg_approval_rate": preset.avg_approval_rate,
            "context_tags": preset.get_context_tags(),
            "blend_amount": preset.blend_amount,
            "created_at": preset.created_at.isoformat(),
            "updated_at": preset.updated_at.isoformat(),
            "learning_data": {
                "approved": action_counts.get('approved', 0),
                "rejected": action_counts.get('rejected', 0),
                "modified": action_counts.get('modified', 0)
            }
        }
    
    def get_top_presets(self, limit: int = 10, metric: str = "usage") -> List[Dict]:
        """
        Get top presets by usage or approval rate.
        
        Args:
            limit: Maximum number of presets to return
            metric: Metric to sort by ("usage" or "approval")
        
        Returns:
            List of preset statistics dictionaries
        """
        if metric == "approval":
            presets = self.list_presets(order_by="avg_approval_rate")
        else:
            presets = self.list_presets(order_by="usage_count")
        
        return [
            self.get_preset_statistics(preset.id)
            for preset in presets[:limit]
        ]
    
    # ========== Helper Methods ==========
    
    def _validate_config_template(self, config: Dict) -> None:
        """
        Validate config template structure.
        
        Args:
            config: Config template dictionary
        
        Raises:
            ValueError: If config is invalid
        """
        # Check required fields
        if "version" not in config:
            raise ValueError("Config template must have 'version' field")
        
        if "pipeline" not in config:
            raise ValueError("Config template must have 'pipeline' field")
        
        if not isinstance(config["pipeline"], list):
            raise ValueError("Config 'pipeline' must be a list")
        
        # Validate pipeline stages
        valid_stages = [
            "base", "toneCurve", "HSL", "detail", 
            "effects", "calibration", "local", "preset"
        ]
        
        for item in config["pipeline"]:
            if "stage" not in item:
                raise ValueError("Pipeline item must have 'stage' field")
            
            if item["stage"] not in valid_stages:
                raise ValueError(
                    f"Invalid stage '{item['stage']}'. "
                    f"Must be one of: {', '.join(valid_stages)}"
                )
    
    def _merge_config_changes(self, base_config: Dict, changes: Dict) -> Dict:
        """
        Merge configuration changes into base config.
        
        Args:
            base_config: Base configuration dictionary
            changes: Changes to apply
        
        Returns:
            Merged configuration dictionary
        """
        import copy
        merged = copy.deepcopy(base_config)
        
        # Simple deep merge
        def deep_merge(target, source):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    deep_merge(target[key], value)
                else:
                    target[key] = value
        
        deep_merge(merged, changes)
        return merged
    
    def _diff_configs(self, config1: Dict, config2: Dict) -> Dict:
        """
        Calculate differences between two configurations.
        
        Args:
            config1: First configuration
            config2: Second configuration
        
        Returns:
            Dictionary describing differences
        """
        differences = {
            "added": [],
            "removed": [],
            "modified": []
        }
        
        # Compare pipeline stages
        stages1 = {item["stage"]: item for item in config1.get("pipeline", [])}
        stages2 = {item["stage"]: item for item in config2.get("pipeline", [])}
        
        # Find added stages
        for stage in stages2:
            if stage not in stages1:
                differences["added"].append(stage)
        
        # Find removed stages
        for stage in stages1:
            if stage not in stages2:
                differences["removed"].append(stage)
        
        # Find modified stages
        for stage in stages1:
            if stage in stages2 and stages1[stage] != stages2[stage]:
                differences["modified"].append({
                    "stage": stage,
                    "old": stages1[stage],
                    "new": stages2[stage]
                })
        
        return differences
