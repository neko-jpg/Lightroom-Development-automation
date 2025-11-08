# Image Quality Evaluator - Quick Start Guide

## Overview

The Image Quality Evaluator automatically assesses photo quality across four dimensions:
- **Focus** (sharpness using Laplacian variance)
- **Exposure** (brightness distribution via histogram analysis)
- **Composition** (Rule of Thirds alignment)
- **Face Detection** (OpenCV DNN or Haar Cascade)

## Installation

```bash
# Install required dependencies
pip install opencv-python numpy

# Or install from requirements.txt
pip install -r requirements.txt
```

## Basic Usage

### 1. Evaluate a Single Image

```python
from image_quality_evaluator import ImageQualityEvaluator

# Initialize evaluator
evaluator = ImageQualityEvaluator()

# Evaluate image
results = evaluator.evaluate('photo.jpg')

# Print results
print(f"Overall Score: {results['overall_score']:.2f} / 5.0")
print(f"Focus: {results['focus_score']:.2f}")
print(f"Exposure: {results['exposure_score']:.2f}")
print(f"Composition: {results['composition_score']:.2f}")
print(f"Faces: {results['faces_detected']}")
```

### 2. Command-Line Usage

```bash
# Evaluate single image
python image_quality_evaluator.py photo.jpg

# Use example script with detailed output
python example_image_quality_usage.py photo.jpg

# Batch evaluation
python example_image_quality_usage.py photo1.jpg photo2.jpg photo3.jpg

# Export results to JSON
python example_image_quality_usage.py *.jpg --output results.json
```

### 3. Integration with AI Selector

```python
from ai_selector import AISelector

# Initialize AI Selector (includes quality evaluator)
selector = AISelector()

# Comprehensive evaluation
result = selector.evaluate('photo.jpg')

print(f"Score: {result['overall_score']:.2f}")
print(f"Recommendation: {result['recommendation']}")
print(f"Tags: {', '.join(result['tags'])}")
```

## Understanding the Scores

### Focus Score (0-5)
- **5.0**: Very sharp, excellent detail
- **4.0**: Sharp, good detail
- **3.0**: Acceptable sharpness
- **2.0**: Slightly blurry
- **1.0**: Very blurry

**Laplacian Variance Thresholds:**
- < 100: Very blurry
- 100-300: Blurry
- 300-500: Acceptable
- 500-1000: Sharp
- > 1000: Very sharp

### Exposure Score (0-5)
- **5.0**: Perfect exposure, no clipping
- **4.0**: Good exposure, minimal clipping
- **3.0**: Acceptable exposure
- **2.0**: Under/overexposed
- **1.0**: Severely under/overexposed

**Evaluation Criteria:**
- Mean brightness (ideal: 100-150)
- Highlight clipping (< 5% ideal)
- Shadow clipping (< 5% ideal)
- Dynamic range (> 150 ideal)

### Composition Score (0-5)
- **5.0**: Excellent composition
- **4.0**: Good composition
- **3.0**: Acceptable composition
- **2.0**: Poor composition
- **1.0**: Very poor composition

**Evaluation Method:**
- Edge density at Rule of Thirds intersections
- Edge density along Rule of Thirds lines
- Visual balance (left/right, top/bottom)

### Overall Score (0-5)
Weighted average of all scores:
- Focus: 35%
- Exposure: 35%
- Composition: 30%
- Bonus: +0.1 per face detected (max +0.3)

## Common Use Cases

### 1. Auto-Select Best Photos

```python
from ai_selector import AISelector

selector = AISelector()

# Filter high-quality photos
image_paths = ['photo1.jpg', 'photo2.jpg', 'photo3.jpg']
best_photos = selector.filter_by_quality(image_paths, min_score=4.0)

print(f"Selected {len(best_photos)} high-quality photos")
```

### 2. Batch Processing with Progress

```python
from image_quality_evaluator import ImageQualityEvaluator
from pathlib import Path

evaluator = ImageQualityEvaluator()
results = []

photo_dir = Path('photos')
photo_files = list(photo_dir.glob('*.jpg'))

for i, photo_path in enumerate(photo_files, 1):
    print(f"[{i}/{len(photo_files)}] {photo_path.name}")
    
    result = evaluator.evaluate(str(photo_path))
    results.append({
        'filename': photo_path.name,
        'score': result['overall_score'],
        'focus': result['focus_score'],
        'exposure': result['exposure_score']
    })

# Sort by score
results.sort(key=lambda x: x['score'], reverse=True)

# Print top 10
print("\nTop 10 Photos:")
for i, r in enumerate(results[:10], 1):
    print(f"{i}. {r['filename']}: {r['score']:.2f}")
```

### 3. Quality Report Generation

```python
from ai_selector import AISelector
import json

selector = AISelector()

# Evaluate all photos
image_paths = ['photo1.jpg', 'photo2.jpg', 'photo3.jpg']
results = selector.batch_evaluate(image_paths)

# Generate report
report = {
    'total_images': len(results),
    'average_score': sum(r['overall_score'] for r in results) / len(results),
    'approved': sum(1 for r in results if r['recommendation'] == 'approve'),
    'review': sum(1 for r in results if r['recommendation'] == 'review'),
    'rejected': sum(1 for r in results if r['recommendation'] == 'reject'),
    'details': results
}

# Save report
with open('quality_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"Report saved: {report['approved']} approved, {report['rejected']} rejected")
```

### 4. Find Similar Quality Photos

```python
from image_quality_evaluator import ImageQualityEvaluator
from pathlib import Path

evaluator = ImageQualityEvaluator()

# Evaluate reference photo
reference = evaluator.evaluate('reference.jpg')
ref_score = reference['overall_score']

# Find similar quality photos
similar = []
for photo in Path('photos').glob('*.jpg'):
    result = evaluator.evaluate(str(photo))
    
    # Within 0.5 score difference
    if abs(result['overall_score'] - ref_score) < 0.5:
        similar.append({
            'path': str(photo),
            'score': result['overall_score']
        })

print(f"Found {len(similar)} photos with similar quality")
```

## Performance Tips

### 1. Reuse Evaluator Instance
```python
# Good - reuse instance
evaluator = ImageQualityEvaluator()
for image in images:
    result = evaluator.evaluate(image)

# Bad - create new instance each time
for image in images:
    evaluator = ImageQualityEvaluator()  # Slow!
    result = evaluator.evaluate(image)
```

### 2. Parallel Processing
```python
from multiprocessing import Pool
from functools import partial

def evaluate_image(image_path):
    evaluator = ImageQualityEvaluator()
    return evaluator.evaluate(image_path)

# Process in parallel
with Pool(processes=4) as pool:
    results = pool.map(evaluate_image, image_paths)
```

### 3. Skip Face Detection if Not Needed
```python
# Face detection adds ~50-100ms per image
# If you don't need it, the evaluator will still work
evaluator = ImageQualityEvaluator()
# Face detection will be disabled if no model is found
```

## Troubleshooting

### Issue: "Could not load image"
**Solution:** Check file path and format. Supported formats: JPG, PNG, TIFF, RAW (if OpenCV supports)

```python
import os
if not os.path.exists(image_path):
    print(f"File not found: {image_path}")
```

### Issue: Low focus scores on sharp images
**Possible causes:**
- JPEG compression artifacts
- Image downscaling
- Low contrast subjects

**Solution:** Use RAW or high-quality JPEG files

### Issue: Face detection not working
**Check:**
```python
evaluator = ImageQualityEvaluator()
print(f"Face detection enabled: {evaluator.face_detection_enabled}")
```

**Solution:** Install face detection models (see IMAGE_QUALITY_IMPLEMENTATION.md)

### Issue: Slow processing
**Optimization:**
1. Resize large images before evaluation
2. Use parallel processing for batches
3. Disable face detection if not needed

```python
import cv2

# Resize large images
img = cv2.imread(image_path)
if img.shape[0] > 1920 or img.shape[1] > 1920:
    scale = 1920 / max(img.shape[:2])
    img = cv2.resize(img, None, fx=scale, fy=scale)
    cv2.imwrite('resized.jpg', img)
    result = evaluator.evaluate('resized.jpg')
```

## Integration Examples

### With Hot Folder Watcher

```python
from hot_folder_watcher import HotFolderWatcher
from image_quality_evaluator import ImageQualityEvaluator

evaluator = ImageQualityEvaluator()

def on_new_photo(file_path):
    result = evaluator.evaluate(file_path)
    
    if result['overall_score'] >= 4.0:
        print(f"✓ High quality: {file_path}")
        # Process further
    else:
        print(f"✗ Low quality: {file_path}")
        # Skip or flag for review

watcher = HotFolderWatcher(['D:/Photos/Inbox'], on_new_photo)
watcher.start()
```

### With EXIF Analyzer

```python
from image_quality_evaluator import ImageQualityEvaluator
from exif_analyzer import EXIFAnalyzer

quality_eval = ImageQualityEvaluator()
exif_analyzer = EXIFAnalyzer()

# Combined analysis
quality = quality_eval.evaluate(image_path)
exif = exif_analyzer.analyze(image_path)

print(f"Quality: {quality['overall_score']:.2f}")
print(f"Camera: {exif['camera']['make']} {exif['camera']['model']}")
print(f"ISO: {exif['settings']['iso']}")
```

### With Database Storage

```python
from image_quality_evaluator import ImageQualityEvaluator
from models.database import Session, Photo

evaluator = ImageQualityEvaluator()
session = Session()

# Evaluate and store
result = evaluator.evaluate(image_path)

photo = Photo(
    file_path=image_path,
    ai_score=result['overall_score'],
    focus_score=result['focus_score'],
    exposure_score=result['exposure_score'],
    composition_score=result['composition_score'],
    detected_faces=result['faces_detected']
)

session.add(photo)
session.commit()
```

## Next Steps

1. **Read Full Documentation:** See `IMAGE_QUALITY_IMPLEMENTATION.md`
2. **Run Tests:** `python test_image_quality_evaluator.py`
3. **Try Examples:** `python example_image_quality_usage.py`
4. **Integrate with AI Selector:** See `ai_selector.py`

## Support

For issues or questions:
1. Check `IMAGE_QUALITY_IMPLEMENTATION.md` for detailed documentation
2. Review test cases in `test_image_quality_evaluator.py`
3. See example usage in `example_image_quality_usage.py`
