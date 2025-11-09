# Export Preset Management - Quick Start Guide

## Overview

The Export Preset Management system provides comprehensive management of export presets for the Junmai AutoDev system. It allows you to configure multiple export destinations with different parameters for various use cases (SNS, Print, Archive, etc.).

**Requirements**: 6.1, 6.2

## Features

- ✅ Multiple export preset configuration
- ✅ Preset-specific parameters (format, quality, resolution, color space)
- ✅ Export destination folder management
- ✅ Preset validation and CRUD operations
- ✅ Preset enable/disable functionality
- ✅ Preset duplication
- ✅ Import/Export presets to JSON files
- ✅ RESTful API endpoints

## Quick Start

### 1. Basic Usage

```python
from export_preset_manager import ExportPresetManager, ExportPreset

# Initialize manager
manager = ExportPresetManager()

# List all presets
presets = manager.list_presets()
for preset in presets:
    print(f"{preset.name}: {preset.format} {preset.max_dimension}px @ {preset.quality}%")

# Get specific preset
sns_preset = manager.get_preset("SNS")
print(f"SNS Preset: {sns_preset.destination}")
```

### 2. Create Custom Preset

```python
# Create a new export preset
custom_preset = ExportPreset(
    name="Instagram_Square",
    enabled=True,
    format="JPEG",
    quality=90,
    max_dimension=1080,
    color_space="sRGB",
    destination="D:/Export/Instagram",
    resize_mode="fit",
    sharpen_for_screen=True,
    sharpen_amount=50,
    filename_template="{date}_IG_{sequence}"
)

# Add to manager
manager.add_preset(custom_preset)
manager.save()
```

### 3. Update Existing Preset

```python
# Update preset parameters
manager.update_preset("SNS", {
    "quality": 90,
    "max_dimension": 2560,
    "sharpen_amount": 60
})
manager.save()
```

### 4. Enable/Disable Presets

```python
# Disable preset
manager.disable_preset("Print")

# Enable preset
manager.enable_preset("Archive")

# Get only enabled presets
enabled_presets = manager.get_enabled_presets()
print(f"Enabled presets: {[p.name for p in enabled_presets]}")

manager.save()
```

### 5. Duplicate Preset

```python
# Duplicate existing preset
manager.duplicate_preset("SNS", "SNS_High_Quality")

# Update the duplicated preset
manager.update_preset("SNS_High_Quality", {
    "quality": 95,
    "max_dimension": 3840
})

manager.save()
```

## API Endpoints

### Get All Presets

```bash
GET /export/presets
GET /export/presets?enabled_only=true
```

**Response:**
```json
{
  "success": true,
  "presets": [
    {
      "name": "SNS",
      "enabled": true,
      "format": "JPEG",
      "quality": 85,
      "max_dimension": 2048,
      "color_space": "sRGB",
      "destination": "D:/Export/SNS",
      "resize_mode": "long_edge",
      "sharpen_for_screen": true,
      "sharpen_amount": 50,
      "filename_template": "{date}_{sequence}",
      "created_at": "2025-11-08T10:00:00",
      "updated_at": "2025-11-08T10:00:00"
    }
  ],
  "count": 5
}
```

### Get Specific Preset

```bash
GET /export/presets/SNS
```

**Response:**
```json
{
  "success": true,
  "preset": {
    "name": "SNS",
    "enabled": true,
    "format": "JPEG",
    "quality": 85,
    "max_dimension": 2048,
    "color_space": "sRGB",
    "destination": "D:/Export/SNS"
  }
}
```

### Create New Preset

```bash
POST /export/presets
Content-Type: application/json

{
  "name": "Custom_4K",
  "enabled": true,
  "format": "JPEG",
  "quality": 88,
  "max_dimension": 3840,
  "color_space": "sRGB",
  "destination": "D:/Export/Custom"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Preset 'Custom_4K' created successfully",
  "preset": { ... }
}
```

### Update Preset

```bash
PUT /export/presets/SNS
Content-Type: application/json

{
  "quality": 90,
  "max_dimension": 2560
}
```

**Response:**
```json
{
  "success": true,
  "message": "Preset 'SNS' updated successfully",
  "preset": { ... }
}
```

### Delete Preset

```bash
DELETE /export/presets/Custom_4K
```

**Response:**
```json
{
  "success": true,
  "message": "Preset 'Custom_4K' deleted successfully"
}
```

### Enable/Disable Preset

```bash
POST /export/presets/Print/enable
POST /export/presets/Archive/disable
```

**Response:**
```json
{
  "success": true,
  "message": "Preset 'Print' enabled successfully"
}
```

### Duplicate Preset

```bash
POST /export/presets/SNS/duplicate
Content-Type: application/json

{
  "new_name": "SNS_Copy"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Preset 'SNS' duplicated to 'SNS_Copy' successfully",
  "preset": { ... }
}
```

### Validate Preset

```bash
POST /export/presets/validate
Content-Type: application/json

{
  "name": "Test",
  "enabled": true,
  "format": "JPEG",
  "quality": 85,
  "max_dimension": 2048,
  "color_space": "sRGB",
  "destination": "D:/Export/Test"
}
```

**Response:**
```json
{
  "success": true,
  "valid": true,
  "message": "Preset is valid"
}
```

### Get Preset Statistics

```bash
GET /export/presets/stats
```

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_presets": 5,
    "enabled_presets": 3,
    "disabled_presets": 2,
    "format_distribution": {
      "JPEG": 4,
      "TIFF": 1
    },
    "color_space_distribution": {
      "sRGB": 3,
      "AdobeRGB": 1,
      "ProPhotoRGB": 1
    }
  }
}
```

### Export Presets to File

```bash
GET /export/presets/export
GET /export/presets/export?path=D:/Backup/presets.json
```

**Response:**
```json
{
  "success": true,
  "message": "Presets exported successfully",
  "export_path": "D:/Backup/presets.json"
}
```

### Import Presets from File

```bash
POST /export/presets/import
Content-Type: application/json

{
  "path": "D:/Backup/presets.json",
  "merge": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Imported 5 presets successfully",
  "imported_count": 5
}
```

## Default Presets

The system comes with 5 default presets:

### 1. SNS (Social Media)
- **Format**: JPEG
- **Quality**: 85%
- **Max Dimension**: 2048px
- **Color Space**: sRGB
- **Features**: Screen sharpening enabled, metadata removed for privacy

### 2. Print (High Quality Printing)
- **Format**: JPEG
- **Quality**: 95%
- **Max Dimension**: 4096px
- **Color Space**: AdobeRGB
- **Features**: No sharpening, full metadata

### 3. Archive (Maximum Quality)
- **Format**: TIFF
- **Quality**: 100%
- **Max Dimension**: 8192px
- **Color Space**: ProPhotoRGB
- **Features**: Lossless, full metadata

### 4. Web_Portfolio
- **Format**: JPEG
- **Quality**: 90%
- **Max Dimension**: 3000px
- **Color Space**: sRGB
- **Features**: Watermark support, copyright metadata

### 5. Client_Delivery
- **Format**: JPEG
- **Quality**: 92%
- **Max Dimension**: 3840px
- **Color Space**: sRGB
- **Features**: Moderate sharpening, full metadata

## Preset Parameters

### Required Parameters

- `name`: Preset name (string)
- `enabled`: Whether preset is enabled (boolean)
- `format`: Export format - JPEG, PNG, TIFF, DNG (string)
- `quality`: Quality 1-100 (integer)
- `max_dimension`: Maximum dimension in pixels 512-8192 (integer)
- `color_space`: Color space - sRGB, AdobeRGB, ProPhotoRGB (string)
- `destination`: Export destination folder path (string)

### Optional Parameters

- `resize_mode`: Resize mode - long_edge, short_edge, width, height, fit (default: long_edge)
- `sharpen_for_screen`: Enable screen sharpening (boolean, default: false)
- `sharpen_amount`: Sharpening amount 0-100 (integer, default: 0)
- `watermark_enabled`: Enable watermark (boolean, default: false)
- `watermark_text`: Watermark text (string, default: "")
- `metadata_include`: Include metadata (boolean, default: true)
- `metadata_copyright`: Copyright metadata (string, default: "")
- `filename_template`: Filename template (string, default: "{date}_{sequence}")
- `sequence_start`: Starting sequence number (integer, default: 1)

### Filename Template Variables

- `{date}`: Date in YYYYMMDD format
- `{time}`: Time in HHMMSS format
- `{sequence}`: Sequential number
- `{original}`: Original filename (without extension)
- `{year}`: Current year

Example: `"{date}_IG_{sequence}"` → `20251108_IG_001.jpg`

## Best Practices

### 1. Organize by Use Case

Create presets for specific use cases:
- Social media platforms (Instagram, Twitter, Facebook)
- Client deliverables
- Print sizes (4x6, 8x10, 11x14)
- Web galleries
- Archive/backup

### 2. Use Descriptive Names

Use clear, descriptive names:
- ✅ `Instagram_Square_1080`
- ✅ `Client_Web_Gallery`
- ✅ `Print_8x10_AdobeRGB`
- ❌ `Preset1`
- ❌ `Test`

### 3. Disable Unused Presets

Disable presets you don't use regularly to keep the list manageable:

```python
manager.disable_preset("Archive")
manager.disable_preset("Print")
```

### 4. Backup Presets Regularly

Export your presets regularly for backup:

```python
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = f"D:/Backup/export_presets_{timestamp}.json"
manager.export_presets(pathlib.Path(backup_path))
```

### 5. Validate Before Saving

Always validate presets before adding them:

```python
is_valid, error = manager.validate_preset(new_preset)
if is_valid:
    manager.add_preset(new_preset)
    manager.save()
else:
    print(f"Validation failed: {error}")
```

## Common Use Cases

### Instagram Export

```python
instagram_preset = ExportPreset(
    name="Instagram_Feed",
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
manager.add_preset(instagram_preset)
```

### Client Delivery with Watermark

```python
client_preset = ExportPreset(
    name="Client_Watermarked",
    enabled=True,
    format="JPEG",
    quality=92,
    max_dimension=3840,
    color_space="sRGB",
    destination="D:/Export/Client",
    watermark_enabled=True,
    watermark_text="© {year} Your Studio Name",
    metadata_include=True,
    metadata_copyright="© {year} Your Studio Name. All rights reserved.",
    filename_template="{date}_{original}"
)
manager.add_preset(client_preset)
```

### Print-Ready Export

```python
print_preset = ExportPreset(
    name="Print_11x14",
    enabled=True,
    format="TIFF",
    quality=100,
    max_dimension=4200,
    color_space="AdobeRGB",
    destination="D:/Export/Print",
    sharpen_for_screen=False,
    metadata_include=True,
    filename_template="PRINT_{date}_{sequence}"
)
manager.add_preset(print_preset)
```

## Troubleshooting

### Preset Not Saving

**Problem**: Changes to presets are not persisted.

**Solution**: Always call `manager.save()` after making changes:

```python
manager.update_preset("SNS", {"quality": 90})
manager.save()  # Don't forget this!
```

### Invalid Destination Path

**Problem**: Preset validation fails due to invalid destination.

**Solution**: Use absolute paths and ensure parent directory exists:

```python
destination = "D:/Export/Custom"
is_valid, error = manager.validate_destination(destination)
if not is_valid:
    print(f"Invalid destination: {error}")
```

### Preset Not Found

**Problem**: `get_preset()` returns None.

**Solution**: Check preset name (case-sensitive):

```python
# List all preset names
presets = manager.list_presets()
print([p.name for p in presets])

# Get preset with correct name
preset = manager.get_preset("SNS")  # Case-sensitive!
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest test_export_preset_manager.py -v

# Run specific test class
pytest test_export_preset_manager.py::TestExportPreset -v

# Run specific test
pytest test_export_preset_manager.py::TestExportPresetManager::test_add_preset -v
```

## Next Steps

1. ✅ **Task 20 Complete**: Export preset management implemented
2. ⏭️ **Task 21**: Implement auto-export functionality
3. ⏭️ **Task 22**: Implement cloud sync functionality

## Related Documentation

- `EXPORT_PRESET_IMPLEMENTATION.md` - Detailed implementation guide
- `CONFIG_IMPLEMENTATION.md` - Configuration system documentation
- Design Document - Section: "Auto Export Pipeline"
- Requirements Document - Requirement 6: "自動書き出しとクラウド配信"

## Support

For issues or questions:
1. Check the test suite for usage examples
2. Review the API endpoint documentation
3. Consult the design document for architecture details
