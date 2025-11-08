# Image Quality Evaluator Implementation

## Overview

The Image Quality Evaluator module provides comprehensive automated image quality assessment for the Junmai AutoDev system. It evaluates photos across four key dimensions: focus, exposure, composition, and face detection.

**Requirements Addressed:** 2.2, 2.3

## Features

### 1. Focus Evaluation (Laplacian Variance)
- **Method**: Calculates Laplacian variance to measure image sharpness
- **Score Range**: 0-5 (higher = sharper)
- **Categories**: very_blurry, blurry, acceptable, sharp, very_sharp
- **Thresholds**:
  - < 100: Very blurry (0-2 score)
  - 100-500: Acceptable (2-4 score)
  - > 500: Sharp (4-5 score)

### 2. Exposure Evaluation (Histogram Analysis)
- **Metrics Analyzed**:
  - Mean brightness (ideal: 100-150)
  - Highlight clipping (< 5% ideal)
  - Shadow clipping (< 5% ideal)
  - Dynamic range (> 150 ideal)
- **Score Range**: 0-5 (higher = better exposure)
- **Categories**: overexposed, underexposed, dark, bright, well_exposed

### 3. Composition Evaluation (Rule of Thirds)
- **Method**: Analyzes edge density at rule of thirds intersections and lines
- **Components**:
  - Power point alignment (4 intersection points)
  - Line alignment (2 vertical + 2 horizontal lines)
  - Visual balance (left/right, top/bottom)
- **Score Range**: 0-5 (higher = better composition)
- **Categories**: excellent, good, acceptable, poor

### 4. Face Detection (OpenCV DNN)
- **Methods Supported**:
  - OpenCV DNN (Caffe model) - Primary
  - Haar Cascade - Fallback
- **Output**: Number of faces + bounding boxes (x, y, width, height)
- **Bonus**: Adds up to 0.3 to overall score for detected faces

## Architecture

```
ImageQualityEvaluator
├── __init__(face_detection_model_path)
├── evaluate(image_path) → Dict
│   ├── _calculate_focus(img) → (score, metrics)
│   ├── _calculate_exposure(img) → (score, metrics)
│   ├── _calculate_composition(img) → (score, metrics)
│   ├── _detect_faces(img) → (count, locations)
│   └── _calculate_overall_score(...) → score
└── Helper Methods
    ├── _categorize_sharpness(variance)
    ├── _categorize_exposure(brightness, clips)
    ├── _categorize_composition(score)
    └── _calculate_balance(img)
```

## Usage

### Basic Usage

```python
from image_quality_evaluator import ImageQualityEvaluator

# Initialize evaluator
evaluator = ImageQualityEvaluator()

# Evaluate single image
results = evaluator.evaluate('photo.jpg')

print(f"Overall Score: {results['overall_score']:.2f} / 5.0")
print(f"Focus: {results['focus_score']:.2f}")
print(f"Exposure: {results['exposure_score']:.2f}")
print(f"Composition: {results['composition_score']:.2f}")
print(f"Faces: {results['faces_detected']}")
```

### With Custom Face Detection Model

```python
evaluator = ImageQualityEvaluator(
    face_detection_model_path='models/res10_300x300_ssd_iter_140000.caffemodel'
)
```

### Batch Processing

```python
import os
from pathlib import Path

evaluator = ImageQualityEvaluator()
results = []

for image_file in Path('photos').glob('*.jpg'):
    result = evaluator.evaluate(str(image_file))
    results.append(result)

# Filter high-quality images (score >= 4.0)
high_quality = [r for r in results if r['overall_score'] >= 4.0]
print(f"High quality images: {len(high_quality)}/{len(results)}")
```

## Output Format

```json
{
  "focus_score": 4.2,
  "exposure_score": 3.8,
  "composition_score": 3.5,
  "faces_detected": 2,
  "face_locations": [[120, 80, 150, 150], [400, 100, 140, 140]],
  "overall_score": 4.1,
  "metrics": {
    "focus": {
      "laplacian_variance": 523.45,
      "sharpness_category": "sharp"
    },
    "exposure": {
      "mean_brightness": 128.5,
      "std_brightness": 45.2,
      "highlight_clip_percent": 2.3,
      "shadow_clip_percent": 1.8,
      "dynamic_range": 180,
      "exposure_category": "well_exposed"
    },
    "composition": {
      "power_point_alignment": 0.0234,
      "line_alignment": 0.0189,
      "balance_score": 4.2,
      "composition_category": "good"
    }
  }
}
```

## Integration with AI Selection Engine

The Image Quality Evaluator is designed to integrate with the AI Selection Engine:

```python
from image_quality_evaluator import ImageQualityEvaluator
from exif_analyzer import EXIFAnalyzer

# Initialize components
quality_evaluator = ImageQualityEvaluator()
exif_analyzer = EXIFAnalyzer()

# Evaluate photo
image_path = 'photo.jpg'
quality_results = quality_evaluator.evaluate(image_path)
exif_data = exif_analyzer.analyze(image_path)

# Combine for AI selection
if quality_results['overall_score'] >= 3.5:
    # High quality - proceed to AI evaluation
    print("✓ Photo passes quality threshold")
    print(f"  Focus: {quality_results['focus_score']:.2f}")
    print(f"  Exposure: {quality_results['exposure_score']:.2f}")
    print(f"  Faces: {quality_results['faces_detected']}")
else:
    # Low quality - skip or flag for review
    print("✗ Photo below quality threshold")
```

## Testing

### Run Tests

```bash
# Run all tests
python test_image_quality_evaluator.py

# Run specific test class
python -m unittest test_image_quality_evaluator.TestImageQualityEvaluator

# Run with verbose output
python test_image_quality_evaluator.py -v
```

### Test Coverage

- ✅ Focus evaluation (sharp and blurry images)
- ✅ Exposure evaluation (well-exposed, over-exposed, under-exposed)
- ✅ Composition evaluation (rule of thirds, balance)
- ✅ Face detection (with and without faces)
- ✅ Overall score calculation
- ✅ Batch processing
- ✅ Different image sizes
- ✅ Error handling

## Example Usage Script

```bash
# Evaluate single image
python example_image_quality_usage.py photo.jpg

# Evaluate multiple images
python example_image_quality_usage.py photo1.jpg photo2.jpg photo3.jpg

# Export results to JSON
python example_image_quality_usage.py *.jpg --output results.json
```

## Performance Considerations

### Processing Time
- **Small images (640x480)**: ~50-100ms per image
- **Medium images (1920x1080)**: ~100-200ms per image
- **Large images (4000x3000)**: ~200-400ms per image

### Memory Usage
- **Per image**: ~10-50MB (depends on image size)
- **Face detection**: Additional ~100MB for model loading

### Optimization Tips
1. **Batch Processing**: Reuse evaluator instance for multiple images
2. **Resize Large Images**: Downscale to 1920x1080 for faster processing
3. **Disable Face Detection**: If not needed, skip model loading
4. **Parallel Processing**: Use multiprocessing for large batches

```python
from multiprocessing import Pool
from functools import partial

def evaluate_image(image_path, evaluator):
    return evaluator.evaluate(image_path)

# Parallel batch processing
evaluator = ImageQualityEvaluator()
image_paths = ['photo1.jpg', 'photo2.jpg', 'photo3.jpg']

with Pool(processes=4) as pool:
    results = pool.map(partial(evaluate_image, evaluator=evaluator), image_paths)
```

## Dependencies

```
opencv-python==4.10.0.84
numpy==1.26.4
```

Install with:
```bash
pip install opencv-python numpy
```

## Face Detection Models

### Option 1: OpenCV DNN (Recommended)
Download pre-trained models:
- **Prototxt**: https://github.com/opencv/opencv/blob/master/samples/dnn/face_detector/deploy.prototxt
- **Caffemodel**: https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel

Place in `models/` directory.

### Option 2: Haar Cascade (Fallback)
Automatically loaded from OpenCV installation. No additional download needed.

## Troubleshooting

### Face Detection Not Working
```python
# Check if face detection is enabled
evaluator = ImageQualityEvaluator()
print(f"Face detection enabled: {evaluator.face_detection_enabled}")

# Manually load model
evaluator._load_face_detector('path/to/model.caffemodel')
```

### Low Focus Scores on Sharp Images
- Check image format (JPEG compression can reduce sharpness)
- Verify image is not downscaled
- Consider adjusting thresholds in `_calculate_focus()`

### Inconsistent Exposure Scores
- Ensure images are in standard color space (sRGB)
- Check for extreme lighting conditions
- Review histogram distribution in metrics

## Future Enhancements

1. **Deep Learning Models**: Integrate CLIP or other vision models for semantic understanding
2. **Custom Thresholds**: Allow user-configurable quality thresholds
3. **GPU Acceleration**: Use CUDA for faster processing
4. **Additional Metrics**: Color harmony, noise level, chromatic aberration
5. **Learning System**: Adapt thresholds based on user approval patterns

## References

- OpenCV Documentation: https://docs.opencv.org/
- Laplacian Variance for Focus: https://www.pyimagesearch.com/2015/09/07/blur-detection-with-opencv/
- Rule of Thirds: https://en.wikipedia.org/wiki/Rule_of_thirds
- Face Detection with DNN: https://www.pyimagesearch.com/2018/02/26/face-detection-with-opencv-and-deep-learning/

## License

Part of Junmai AutoDev System
© 2025 Lightroom×ChatGPT Auto-Develop System
