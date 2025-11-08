# Preset Management System - Quick Start Guide

## Installation

The Preset Management System is already integrated into the Junmai AutoDev system. No additional installation is required.

## Basic Usage

### 1. Initialize the System

```python
from models.database import init_db, get_session
from preset_manager import PresetManager

# Initialize database
init_db('sqlite:///data/junmai.db')
db = get_session()

# Create preset manager
manager = PresetManager(db, "config/presets")
```

### 2. Create a Preset

```python
# Define your Lightroom development configuration
config = {
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

# Create the preset
preset = manager.create_preset(
    name="WhiteLayer_Transparency",
    version="v4",
    config_template=config,
    context_tags=["backlit_portrait", "outdoor"],
    blend_amount=60
)

print(f"Created preset: {preset.name} v{preset.version}")
```

### 3. Select Preset by Context

```python
# Automatically select the best preset for a context
context = "backlit_portrait"
preset = manager.select_preset_for_context(context)

if preset:
    print(f"Selected: {preset.name} v{preset.version}")
    config = preset.get_config_template()
    # Apply config to photo...
```

### 4. Track Usage

```python
# After applying preset to a photo
manager.record_preset_usage(
    preset_id=preset.id,
    photo_id=123,
    approved=True  # or False if rejected
)
```

### 5. Export/Import Presets

```python
# Export a preset
file_path = manager.export_preset(preset.id)
print(f"Exported to: {file_path}")

# Import a preset
imported = manager.import_preset("preset.json")
print(f"Imported: {imported.name}")
```

## Common Workflows

### Workflow 1: Create Multiple Presets for Different Contexts

```python
# Backlit portrait preset
backlit_config = {...}
manager.create_preset(
    "BacklitPortrait", "v1", backlit_config,
    context_tags=["backlit_portrait", "golden_hour"]
)

# Low-light indoor preset
lowlight_config = {...}
manager.create_preset(
    "LowLightIndoor", "v1", lowlight_config,
    context_tags=["low_light_indoor", "high_iso"]
)

# Landscape preset
landscape_config = {...}
manager.create_preset(
    "Landscape", "v1", landscape_config,
    context_tags=["landscape", "outdoor"]
)
```

### Workflow 2: Version Management

```python
# Get base preset
base = manager.get_preset_by_name("WhiteLayer_Transparency")

# Create improved version
changes = {
    "pipeline": [
        {
            "stage": "base",
            "settings": {"Exposure2012": -0.20}  # Adjusted
        }
    ]
}

new_version = manager.create_preset_version(
    base.id, "v5", changes
)

# Compare versions
comparison = manager.compare_preset_versions(base.id, new_version.id)
print(comparison['config_diff'])
```

### Workflow 3: Backup and Restore

```python
# Backup all presets
files = manager.export_all_presets("backups/2025-11-08/")
print(f"Backed up {len(files)} presets")

# Restore from backup
presets = manager.import_presets_from_directory(
    "backups/2025-11-08/",
    overwrite=False
)
print(f"Restored {len(presets)} presets")
```

### Workflow 4: Analytics

```python
# Get preset statistics
stats = manager.get_preset_statistics(preset.id)
print(f"Usage: {stats['usage_count']}")
print(f"Approval rate: {stats['avg_approval_rate']:.1%}")

# Get top performing presets
top_presets = manager.get_top_presets(limit=5, metric="approval")
for p in top_presets:
    print(f"{p['name']}: {p['avg_approval_rate']:.1%}")
```

## Configuration Template Structure

### Minimal Template

```python
{
    "version": "1.0",
    "pipeline": [
        {
            "stage": "base",
            "settings": {
                "Exposure2012": 0.0
            }
        }
    ],
    "safety": {
        "snapshot": True,
        "dryRun": False
    }
}
```

### Complete Template

```python
{
    "version": "1.0",
    "pipeline": [
        {
            "stage": "base",
            "settings": {
                "Exposure2012": -0.15,
                "Contrast2012": 5,
                "Highlights2012": -18,
                "Shadows2012": 12,
                "Whites2012": -5,
                "Blacks2012": -8,
                "Clarity2012": 8,
                "Vibrance": 10,
                "Saturation": 0
            }
        },
        {
            "stage": "toneCurve",
            "rgb": [[0, 0], [28, 22], [64, 60], [190, 192], [255, 255]]
        },
        {
            "stage": "HSL",
            "hue": {"red": 0, "orange": -4, "yellow": 0, "green": 0, "aqua": 0, "blue": 0, "purple": 0, "magenta": 0},
            "sat": {"red": 0, "orange": -6, "yellow": 0, "green": 0, "aqua": 0, "blue": -8, "purple": 0, "magenta": 0},
            "lum": {"red": 0, "orange": 4, "yellow": 0, "green": 0, "aqua": 0, "blue": -6, "purple": 0, "magenta": 0}
        },
        {
            "stage": "detail",
            "sharpen": {
                "Sharpness": 40,
                "SharpenRadius": 1.0,
                "SharpenDetail": 25,
                "SharpenEdgeMasking": 0
            },
            "nr": {
                "LuminanceSmoothing": 0,
                "LuminanceDetail": 50,
                "ColorNoiseReduction": 25,
                "ColorDetail": 50
            }
        },
        {
            "stage": "effects",
            "settings": {
                "Dehaze": -5
            },
            "vignette": {
                "PostCropVignetteAmount": -10,
                "PostCropVignetteMidpoint": 50,
                "PostCropVignetteFeather": 50,
                "PostCropVignetteRoundness": 0
            },
            "grain": {
                "GrainAmount": 0,
                "GrainSize": 25,
                "GrainFrequency": 50
            }
        }
    ],
    "safety": {
        "snapshot": True,
        "dryRun": False
    }
}
```

## Valid Pipeline Stages

- `base`: Basic adjustments (exposure, contrast, highlights, shadows, etc.)
- `toneCurve`: Tone curve adjustments
- `HSL`: Hue, Saturation, Luminance adjustments
- `detail`: Sharpening and noise reduction
- `effects`: Clarity, dehaze, vignette, grain
- `calibration`: Camera calibration
- `local`: Local adjustments (brushes, gradients)
- `preset`: Apply existing Lightroom preset

## Context Tags

Common context tags used in the system:

- `backlit_portrait` - Backlit portrait photography
- `low_light_indoor` - Indoor low-light situations
- `high_iso` - High ISO photography
- `landscape` - Landscape photography
- `outdoor` - Outdoor photography
- `golden_hour` - Golden hour lighting
- `blue_hour` - Blue hour lighting
- `night` - Night photography
- `studio` - Studio photography
- `street` - Street photography

You can create custom context tags as needed.

## Tips and Best Practices

### 1. Naming Conventions

- Use descriptive names: `WhiteLayer_Transparency`, `LowLight_NR`
- Include version in name for major changes: `WhiteLayer_v4`, `WhiteLayer_v5`
- Use consistent naming across related presets

### 2. Context Tags

- Be specific: `backlit_portrait` is better than just `portrait`
- Use multiple tags: `["backlit_portrait", "outdoor", "golden_hour"]`
- Keep tags consistent across presets

### 3. Version Management

- Create new versions for significant changes
- Use semantic versioning: v1, v2, v2.1, etc.
- Document changes in version comparison

### 4. Blend Amount

- Start with 100% for full effect
- Reduce to 60-80% for subtle adjustments
- Test different blend amounts for best results

### 5. Usage Tracking

- Always record usage after applying presets
- Track both approvals and rejections
- Use statistics to improve preset selection

### 6. Backup

- Export presets regularly
- Keep versioned backups
- Store backups in multiple locations

## Troubleshooting

### Problem: "Preset with name 'X' already exists"

**Solution**: Use a different name or delete the existing preset first.

```python
# Delete existing preset
existing = manager.get_preset_by_name("PresetName")
if existing:
    manager.delete_preset(existing.id)

# Now create new preset
preset = manager.create_preset("PresetName", ...)
```

### Problem: "Config template must have 'version' field"

**Solution**: Ensure your config has the required `version` field.

```python
config = {
    "version": "1.0",  # Required!
    "pipeline": [...]
}
```

### Problem: "Invalid stage 'X'"

**Solution**: Use only valid pipeline stages (see list above).

```python
# Valid stages
valid_stages = ["base", "toneCurve", "HSL", "detail", "effects", "calibration", "local", "preset"]
```

### Problem: No preset found for context

**Solution**: Create a preset with that context tag, or create a "default" preset.

```python
# Create default preset
default_config = {...}
manager.create_preset(
    "default", "v1", default_config,
    context_tags=["default"]
)
```

## Next Steps

1. **Create your first preset**: Start with a simple base adjustment
2. **Test context selection**: Verify presets are selected correctly
3. **Track usage**: Monitor approval rates and adjust presets
4. **Create versions**: Iterate and improve your presets
5. **Backup regularly**: Export presets to prevent data loss

## Additional Resources

- Full documentation: `PRESET_MANAGEMENT_IMPLEMENTATION.md`
- Example code: `example_preset_usage.py`
- Test suite: `test_preset_manager.py`
- Validation script: `validate_preset_manager.py`

## Support

For issues or questions:
1. Check the full documentation
2. Review example code
3. Run validation script to verify setup
4. Check database connection and initialization
