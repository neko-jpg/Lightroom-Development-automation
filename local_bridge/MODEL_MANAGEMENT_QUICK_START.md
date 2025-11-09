# Multi-Model Management - Quick Start Guide

## Quick Setup

### 1. Initialize Model Manager

```python
from model_manager import ModelManager

# Create manager instance
manager = ModelManager()

# Manager automatically syncs with Ollama
print(f"Current model: {manager.get_current_model()}")
```

### 2. List Available Models

```python
# List all models
models = manager.list_available_models()
for model in models:
    status = "✓" if model.installed else "✗"
    print(f"{status} {model.name} - {model.purpose.value}")

# List only installed models
installed = manager.list_available_models(installed_only=True)
print(f"Installed: {len(installed)} models")

# List models for 8GB VRAM
vram_models = manager.list_available_models(max_vram_gb=8.0)
```

### 3. Switch Models

```python
# Switch to a different model
success = manager.switch_model("llama3.1:8b-instruct")
if success:
    print("Model switched successfully")
else:
    print("Failed to switch model")
```

### 4. Download Models

```python
# Download a model
def progress_callback(data):
    if 'completed' in data and 'total' in data:
        percent = (data['completed'] / data['total'] * 100)
        print(f"Progress: {percent:.1f}%")

success, message = manager.download_model(
    "llama3.2:3b-instruct",
    progress_callback=progress_callback
)
print(message)
```

### 5. Get Model Recommendations

```python
# Get recommended model for your hardware
recommended = manager.recommend_model(
    available_vram_gb=8.0,
    priority="balanced"  # or "speed" or "quality"
)
print(f"Recommended: {recommended}")
```

### 6. Track Model Usage

```python
# After using a model
manager.record_usage(
    model_name="llama3.1:8b-instruct",
    inference_time=2.5,  # seconds
    success=True
)

# Get statistics
stats = manager.get_model_statistics("llama3.1:8b-instruct")
print(f"Usage: {stats['usage_count']} times")
print(f"Avg time: {stats['avg_inference_time']:.2f}s")
print(f"Success rate: {stats['success_rate']*100:.1f}%")
```

## REST API Quick Start

### List Models
```bash
curl http://localhost:5100/api/model/list
```

### Get Current Model
```bash
curl http://localhost:5100/api/model/current
```

### Switch Model
```bash
curl -X POST http://localhost:5100/api/model/switch \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.1:8b-instruct"}'
```

### Download Model
```bash
curl -X POST http://localhost:5100/api/model/download \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2:3b-instruct"}'
```

### Get Recommendation
```bash
curl -X POST http://localhost:5100/api/model/recommend \
  -H "Content-Type: application/json" \
  -d '{"available_vram_gb": 8.0, "priority": "balanced"}'
```

### Get Statistics
```bash
curl http://localhost:5100/api/model/statistics
```

## Common Use Cases

### Use Case 1: First-Time Setup

```python
from model_manager import ModelManager

# Initialize
manager = ModelManager()

# Check what's installed
installed = manager.list_installed_models()
print(f"Installed models: {installed}")

# If nothing installed, download recommended model
if not installed:
    recommended = manager.recommend_model(8.0, "balanced")
    print(f"Downloading {recommended}...")
    success, msg = manager.download_model(recommended)
    if success:
        manager.switch_model(recommended)
```

### Use Case 2: Optimize for Speed

```python
# Get fastest model for your hardware
speed_model = manager.recommend_model(
    available_vram_gb=8.0,
    priority="speed"
)

# Switch to it
manager.switch_model(speed_model)
print(f"Using speed-optimized model: {speed_model}")
```

### Use Case 3: Optimize for Quality

```python
# Get highest quality model that fits
quality_model = manager.recommend_model(
    available_vram_gb=8.0,
    priority="quality"
)

# Check compatibility first
compatible, msg = manager.check_model_compatibility(
    quality_model,
    8.0
)

if compatible:
    manager.switch_model(quality_model)
    print(f"Using quality-optimized model: {quality_model}")
else:
    print(f"Model not compatible: {msg}")
```

### Use Case 4: Monitor Performance

```python
# Get all statistics
all_stats = manager.get_all_statistics()

# Find best performing model
best_model = None
best_rate = 0

for model_name, stats in all_stats.items():
    if stats['usage_count'] > 10:  # Only consider well-tested models
        rate = stats.get('success_rate', 0)
        if rate > best_rate:
            best_rate = rate
            best_model = model_name

print(f"Best performing model: {best_model} ({best_rate*100:.1f}% success)")
```

### Use Case 5: Batch Processing

```python
# For batch processing, use fastest model
manager.switch_model(
    manager.recommend_model(8.0, "speed")
)

# Process images
for image_path in image_paths:
    start_time = time.time()
    
    # Your processing code here
    result = process_image(image_path)
    
    elapsed = time.time() - start_time
    
    # Track usage
    manager.record_usage(
        manager.get_current_model(),
        elapsed,
        success=result is not None
    )
```

## Model Selection Guide

### For RTX 4060 (8GB VRAM)

**Recommended Models:**
1. **Llama 3.1 8B** - Best balance (6GB VRAM)
2. **Llama 3.2 3B** - Fast processing (2GB VRAM)
3. **Llama 3.2 1B** - Ultra-fast (1GB VRAM)

### For RTX 3060 (12GB VRAM)

**Recommended Models:**
1. **Llama 3.1 13B** - High quality (8GB VRAM)
2. **Llama 3.1 8B** - Balanced (6GB VRAM)

### For RTX 4090 (24GB VRAM)

**Recommended Models:**
1. **Mixtral 8x7B** - Complex analysis (24GB VRAM)
2. **Llama 3.1 13B** - High quality (8GB VRAM)

## Troubleshooting

### Model Not Found
```python
# Check if model exists in catalog
info = manager.get_model_info("model-name")
if not info:
    print("Model not in catalog")
```

### Model Not Installed
```python
# Check installation status
info = manager.get_model_info("model-name")
if not info.installed:
    print("Model not installed, downloading...")
    manager.download_model("model-name")
```

### Insufficient VRAM
```python
# Check compatibility
compatible, msg = manager.check_model_compatibility(
    "llama3.1:70b-instruct",
    8.0
)
if not compatible:
    print(msg)
    # Get alternative
    alt = manager.recommend_model(8.0, "quality")
    print(f"Alternative: {alt}")
```

### Download Failed
```python
# Retry download
max_retries = 3
for i in range(max_retries):
    success, msg = manager.download_model("model-name")
    if success:
        break
    print(f"Retry {i+1}/{max_retries}: {msg}")
```

## Integration Examples

### With OllamaClient

```python
from ollama_client import OllamaClient
from model_manager import ModelManager

manager = ModelManager()
client = OllamaClient()

# Use current model
model = manager.get_current_model()
response = client.generate(model, "Your prompt here")

# Track usage
manager.record_usage(model, 2.5, success=True)
```

### With AI Selector

```python
from ai_selector import AISelector
from model_manager import ModelManager

manager = ModelManager()

# Create selector with current model
selector = AISelector(
    llm_model=manager.get_current_model()
)

# Evaluate photo
result = selector.evaluate("photo.jpg")

# Track usage
manager.record_usage(
    manager.get_current_model(),
    result.get('inference_time', 0),
    success=True
)
```

## Command Line Usage

```bash
# List models
python model_manager.py list

# Show current model
python model_manager.py current

# Get recommendation
python model_manager.py recommend 8.0 balanced

# Show statistics
python model_manager.py stats
```

## Next Steps

1. Review [MODEL_MANAGEMENT_IMPLEMENTATION.md](MODEL_MANAGEMENT_IMPLEMENTATION.md) for detailed documentation
2. Check [example_model_management_usage.py](example_model_management_usage.py) for more examples
3. Run tests: `py -m pytest test_model_manager.py -v`
4. Integrate with your application

## Support

For issues or questions:
1. Check the implementation documentation
2. Review test cases for examples
3. Check Ollama documentation for model-specific issues
