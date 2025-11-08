# EXIF Analyzer - Quick Start Guide

## Installation

```bash
cd local_bridge
pip install exifread piexif
```

## Basic Usage

```python
from exif_analyzer import EXIFAnalyzer

# Create analyzer instance
analyzer = EXIFAnalyzer()

# Analyze a photo
result = analyzer.analyze('path/to/photo.jpg')

# Access extracted data
print(f"Camera: {result['camera']['make']} {result['camera']['model']}")
print(f"ISO: {result['settings']['iso']}")
print(f"Time of Day: {result['datetime']['time_of_day']}")
print(f"Context: {result['context_hints']}")
```

## Database Integration

```python
from exif_analyzer import EXIFAnalyzer
from models.database import init_db, get_session, Photo

# Initialize database
init_db('sqlite:///data/junmai.db')

# Extract EXIF for database
analyzer = EXIFAnalyzer()
exif_data = analyzer.extract_for_database('photo.jpg')

# Create photo record
session = get_session()
photo = Photo(
    file_path='photo.jpg',
    file_name='photo.jpg',
    **exif_data
)
session.add(photo)
session.commit()
```

## Context-Based Preset Selection

```python
from exif_analyzer import EXIFAnalyzer

analyzer = EXIFAnalyzer()
result = analyzer.analyze('photo.jpg')
hints = result['context_hints']

# Select preset based on context
if hints.get('backlight_risk'):
    preset = 'WhiteLayer_Transparency_v4'
elif hints.get('likely_indoor') and hints['lighting'] == 'low_light':
    preset = 'LowLight_NR_v2'
elif hints.get('subject_type') == 'portrait':
    preset = 'Portrait_Soft_v3'
else:
    preset = 'Default_v1'

print(f"Recommended preset: {preset}")
```

## Testing

```bash
# Run all tests
python -m unittest test_exif_analyzer -v

# Run specific test
python -m unittest test_exif_analyzer.TestEXIFAnalyzer.test_time_of_day_detection
```

## Examples

```bash
# Run example demonstrations
python example_exif_usage.py
```

## Key Features

✅ Camera info extraction (make, model, lens)  
✅ Settings extraction (ISO, aperture, shutter, focal length)  
✅ GPS location parsing with indoor/outdoor detection  
✅ Time of day detection (9 periods)  
✅ Context inference for preset selection  
✅ Database integration ready  

## Documentation

- Full documentation: `EXIF_ANALYZER_IMPLEMENTATION.md`
- Code examples: `example_exif_usage.py`
- Unit tests: `test_exif_analyzer.py`

## Next Steps

This EXIF analyzer integrates with:
- Task 7: Context Engine
- Task 8: AI Selection Engine
- Task 11: Preset Engine
