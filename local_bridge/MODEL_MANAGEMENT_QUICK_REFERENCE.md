# Multi-Model Management - Quick Reference

## Python API

### Initialization
```python
from model_manager import ModelManager
manager = ModelManager()
```

### List Models
```python
# All models
models = manager.list_available_models()

# Installed only
installed = manager.list_available_models(installed_only=True)

# By purpose
speed_models = manager.list_available_models(purpose=ModelPurpose.SPEED)

# By VRAM
vram_models = manager.list_available_models(max_vram_gb=8.0)
```

### Model Information
```python
# Get info
info = manager.get_model_info("llama3.1:8b-instruct")

# Current model
current = manager.get_current_model()

# Check compatibility
compatible, msg = manager.check_model_compatibility("model-name", 8.0)
```

### Model Operations
```python
# Switch model
success = manager.switch_model("llama3.1:8b-instruct")

# Download model
success, msg = manager.download_model("llama3.2:3b-instruct")

# Delete model
success, msg = manager.delete_model("model-name")

# Get recommendation
recommended = manager.recommend_model(8.0, "balanced")
```

### Statistics
```python
# Record usage
manager.record_usage("model-name", 2.5, success=True)

# Get stats
stats = manager.get_model_statistics("model-name")

# All stats
all_stats = manager.get_all_statistics()
```

### Metadata
```python
# Export
manager.export_metadata("backup.json")

# Import
manager.import_metadata("backup.json")

# Sync with Ollama
manager._sync_with_ollama()
```

## REST API

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/model/list` | List models |
| GET | `/api/model/installed` | List installed models |
| GET | `/api/model/current` | Get current model |
| GET | `/api/model/info/<name>` | Get model info |
| POST | `/api/model/switch` | Switch model |
| POST | `/api/model/download` | Download model |
| DELETE | `/api/model/delete` | Delete model |
| POST | `/api/model/recommend` | Get recommendation |
| POST | `/api/model/check_compatibility` | Check compatibility |
| GET | `/api/model/statistics` | Get statistics |
| POST | `/api/model/sync` | Sync with Ollama |
| POST | `/api/model/export` | Export metadata |
| POST | `/api/model/import` | Import metadata |

### Request Examples

#### List Models
```bash
GET /api/model/list?purpose=balanced&max_vram=8.0&installed_only=true
```

#### Switch Model
```bash
POST /api/model/switch
{
  "model": "llama3.1:8b-instruct"
}
```

#### Download Model
```bash
POST /api/model/download
{
  "model": "llama3.2:3b-instruct"
}
```

#### Get Recommendation
```bash
POST /api/model/recommend
{
  "available_vram_gb": 8.0,
  "priority": "balanced"
}
```

#### Check Compatibility
```bash
POST /api/model/check_compatibility
{
  "model": "llama3.1:8b-instruct",
  "available_vram_gb": 8.0
}
```

## Model Catalog

| Model | Size | Purpose | Min VRAM | Download Size |
|-------|------|---------|----------|---------------|
| llama3.2:1b-instruct | 1B | Speed | 1GB | 1.3GB |
| llama3.2:3b-instruct | 3B | Speed | 2GB | 2.0GB |
| llama3.1:8b-instruct | 8B | Balanced | 6GB | 4.7GB |
| llama3.1:13b-instruct | 13B | Quality | 8GB | 7.4GB |
| mixtral:8x7b-instruct | 8x7B | Quality | 24GB | 26GB |
| llama3.1:70b-instruct | 70B | Quality | 40GB | 40GB |

## Model Purposes

| Purpose | Description | Use Case |
|---------|-------------|----------|
| Speed | Fast inference | Batch processing, quick tagging |
| Balanced | Speed + Quality | General photo evaluation |
| Quality | High quality | Detailed analysis, critique |
| Specialized | Specific tasks | Custom workflows |

## Priority Options

| Priority | Selects | Best For |
|----------|---------|----------|
| speed | Fastest models | Batch processing |
| balanced | Balanced models | General use |
| quality | Highest quality | Professional work |

## Statistics Fields

```python
{
  'name': str,
  'usage_count': int,
  'last_used': str (ISO timestamp),
  'avg_inference_time': float (seconds),
  'success_rate': float (0.0-1.0),
  'installed': bool
}
```

## Model Metadata Fields

```python
{
  'name': str,
  'size': str,
  'purpose': str,
  'description': str,
  'recommended_use': str,
  'min_vram_gb': float,
  'quantization_support': List[str],
  'download_size_mb': int,
  'installed': bool,
  'last_used': str,
  'usage_count': int,
  'avg_inference_time': float,
  'success_rate': float
}
```

## Common Patterns

### Pattern 1: Auto-Select Best Model
```python
# Get GPU VRAM
from gpu_manager import GPUManager
gpu = GPUManager()
available_vram = gpu.get_available_memory_gb()

# Get recommendation
model = manager.recommend_model(available_vram, "balanced")
manager.switch_model(model)
```

### Pattern 2: Track All Usage
```python
import time

def process_with_tracking(model_name, func, *args):
    start = time.time()
    try:
        result = func(*args)
        elapsed = time.time() - start
        manager.record_usage(model_name, elapsed, success=True)
        return result
    except Exception as e:
        elapsed = time.time() - start
        manager.record_usage(model_name, elapsed, success=False)
        raise
```

### Pattern 3: Fallback Strategy
```python
def get_best_available_model(vram_gb):
    # Try quality first
    model = manager.recommend_model(vram_gb, "quality")
    if model:
        return model
    
    # Fallback to balanced
    model = manager.recommend_model(vram_gb, "balanced")
    if model:
        return model
    
    # Last resort: speed
    return manager.recommend_model(vram_gb, "speed")
```

### Pattern 4: Performance Monitoring
```python
def get_performance_report():
    stats = manager.get_all_statistics()
    
    # Sort by success rate
    sorted_models = sorted(
        stats.items(),
        key=lambda x: x[1].get('success_rate', 0),
        reverse=True
    )
    
    for model, stat in sorted_models:
        if stat['usage_count'] > 0:
            print(f"{model}:")
            print(f"  Success: {stat['success_rate']*100:.1f}%")
            print(f"  Avg Time: {stat['avg_inference_time']:.2f}s")
```

## Error Codes

| Error | Cause | Solution |
|-------|-------|----------|
| Model not found | Invalid model name | Check catalog |
| Model not installed | Not downloaded | Download first |
| Insufficient VRAM | Model too large | Use smaller model |
| Download failed | Network/Ollama error | Retry or check Ollama |
| Cannot delete current | Deleting active model | Switch first |

## Command Line

```bash
# List models
python model_manager.py list

# Current model
python model_manager.py current

# Recommend
python model_manager.py recommend <vram> <priority>

# Statistics
python model_manager.py stats
```

## Testing

```bash
# Run all tests
py -m pytest test_model_manager.py -v

# Run specific test
py -m pytest test_model_manager.py::TestModelManager::test_switch_model -v

# With coverage
py -m pytest test_model_manager.py --cov=model_manager
```

## Files

| File | Purpose |
|------|---------|
| `model_manager.py` | Core implementation |
| `api_model_management.py` | REST API endpoints |
| `example_model_management_usage.py` | Usage examples |
| `test_model_manager.py` | Unit tests |
| `data/model_metadata.json` | Metadata storage |

## Requirements

- **18.1**: Model list management
- **18.2**: Model switching
- **18.3**: Model download
- **18.4**: Model metadata management

## See Also

- [MODEL_MANAGEMENT_IMPLEMENTATION.md](MODEL_MANAGEMENT_IMPLEMENTATION.md) - Full documentation
- [MODEL_MANAGEMENT_QUICK_START.md](MODEL_MANAGEMENT_QUICK_START.md) - Getting started guide
- [example_model_management_usage.py](example_model_management_usage.py) - Code examples
