# Multi-Model Management Implementation

## Overview

The Multi-Model Management System provides comprehensive management of LLM models for the Junmai AutoDev system. It supports multiple models from the Llama family and other compatible models, with features for model switching, downloading, performance tracking, and intelligent recommendations.

## Requirements

- **18.1**: Model list management functionality
- **18.2**: Model switching functionality
- **18.3**: Model download functionality
- **18.4**: Model metadata management

## Architecture

### Components

1. **ModelManager** (`model_manager.py`)
   - Core model management logic
   - Model catalog with predefined models
   - Metadata persistence
   - Performance tracking

2. **API Endpoints** (`api_model_management.py`)
   - REST API for model operations
   - Integration with Flask application

3. **Model Metadata**
   - Model information storage
   - Usage statistics
   - Performance metrics

## Features

### 1. Model List Management (Requirement 18.1)

**Supported Models:**
- Llama 3.1 8B Instruct (Balanced)
- Llama 3.1 13B Instruct (Quality)
- Llama 3.1 70B Instruct (Highest Quality)
- Llama 3.2 1B Instruct (Ultra-fast)
- Llama 3.2 3B Instruct (Fast)
- Mixtral 8x7B Instruct (Complex Analysis)

**Model Purposes:**
- **Speed**: Fast inference, lower quality
- **Balanced**: Balance between speed and quality
- **Quality**: High quality, slower inference
- **Specialized**: Specialized tasks

**Filtering Options:**
- By purpose (speed/balanced/quality)
- By VRAM requirement
- Installed only

### 2. Model Switching (Requirement 18.2)

**Features:**
- Switch between installed models
- Validation of model availability
- Automatic timestamp tracking
- Persistence of current model selection

**Safety:**
- Cannot switch to non-installed models
- Validates model existence before switching

### 3. Model Download (Requirement 18.3)

**Features:**
- Download models from Ollama
- Progress tracking via callbacks
- Streaming download support
- Automatic metadata update after download

**Download Information:**
- Model size estimation
- VRAM requirements
- Quantization support

### 4. Model Metadata Management (Requirement 18.4)

**Metadata Fields:**
- Name and size
- Purpose and description
- Recommended use cases
- VRAM requirements
- Quantization support
- Installation status
- Usage statistics
- Performance metrics

**Statistics Tracked:**
- Usage count
- Last used timestamp
- Average inference time
- Success rate

## Usage

### Python API

```python
from model_manager import ModelManager

# Initialize manager
manager = ModelManager()

# List available models
models = manager.list_available_models()
for model in models:
    print(f"{model.name} - {model.purpose.value}")

# Get model information
info = manager.get_model_info("llama3.1:8b-instruct")
print(f"Min VRAM: {info.min_vram_gb}GB")

# Switch model
success = manager.switch_model("llama3.1:8b-instruct")

# Download model
success, message = manager.download_model("llama3.2:3b-instruct")

# Get recommendation
recommended = manager.recommend_model(
    available_vram_gb=8.0,
    priority="balanced"
)

# Track usage
manager.record_usage("llama3.1:8b-instruct", 2.5, success=True)

# Get statistics
stats = manager.get_model_statistics("llama3.1:8b-instruct")
print(f"Usage: {stats['usage_count']} times")
print(f"Avg time: {stats['avg_inference_time']:.2f}s")
```

### REST API

#### List Models
```bash
GET /api/model/list?purpose=balanced&max_vram=8.0&installed_only=true
```

#### Get Current Model
```bash
GET /api/model/current
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

#### Get Statistics
```bash
GET /api/model/statistics?model=llama3.1:8b-instruct
```

## Model Catalog

### Llama 3.1 8B Instruct
- **Purpose**: Balanced
- **Min VRAM**: 6GB
- **Download Size**: ~4.7GB
- **Use Case**: General photo evaluation and tagging
- **Quantization**: 4-bit, 8-bit

### Llama 3.1 13B Instruct
- **Purpose**: Quality
- **Min VRAM**: 8GB
- **Download Size**: ~7.4GB
- **Use Case**: Detailed photo analysis and critique
- **Quantization**: 4-bit, 8-bit

### Llama 3.1 70B Instruct
- **Purpose**: Quality
- **Min VRAM**: 40GB
- **Download Size**: ~40GB
- **Use Case**: Professional photo evaluation
- **Quantization**: 4-bit, 8-bit

### Llama 3.2 3B Instruct
- **Purpose**: Speed
- **Min VRAM**: 2GB
- **Download Size**: ~2GB
- **Use Case**: Quick photo tagging and basic evaluation
- **Quantization**: 4-bit, 8-bit

### Llama 3.2 1B Instruct
- **Purpose**: Speed
- **Min VRAM**: 1GB
- **Download Size**: ~1.3GB
- **Use Case**: Rapid batch processing
- **Quantization**: 4-bit, 8-bit

### Mixtral 8x7B Instruct
- **Purpose**: Quality
- **Min VRAM**: 24GB
- **Download Size**: ~26GB
- **Use Case**: Complex photo analysis
- **Quantization**: 4-bit, 8-bit

## Model Recommendation Logic

The system recommends models based on:

1. **Available VRAM**: Filters models that fit in available memory
2. **Priority**: Matches purpose to priority (speed/balanced/quality)
3. **Performance History**: Prefers models with good success rates
4. **Usage History**: Considers proven models
5. **Model Size**: Larger models for quality priority

## Performance Tracking

### Metrics Collected
- Total usage count
- Successful inference count
- Failed inference count
- Average inference time
- Min/max inference time
- Success rate
- Last used timestamp

### Statistics Usage
- Model comparison
- Performance optimization
- Recommendation improvement
- Usage pattern analysis

## Metadata Persistence

### Storage Format
```json
{
  "current_model": "llama3.1:8b-instruct",
  "models": {
    "llama3.1:8b-instruct": {
      "name": "llama3.1:8b-instruct",
      "size": "8b",
      "purpose": "balanced",
      "description": "...",
      "min_vram_gb": 6.0,
      "installed": true,
      "usage_count": 42,
      "avg_inference_time": 2.5,
      "success_rate": 0.95,
      "last_used": "2025-11-08T14:30:00"
    }
  },
  "last_updated": "2025-11-08T14:30:00"
}
```

### File Location
- Default: `data/model_metadata.json`
- Configurable via constructor parameter

## Integration

### With OllamaClient
```python
from ollama_client import OllamaClient
from model_manager import ModelManager

manager = ModelManager()
client = OllamaClient()

# Get recommended model
model = manager.recommend_model(8.0, "balanced")

# Use with client
response = client.generate(model, prompt)

# Track usage
manager.record_usage(model, inference_time, success=True)
```

### With AI Selector
```python
from ai_selector import AISelector
from model_manager import ModelManager

manager = ModelManager()
selector = AISelector(llm_model=manager.get_current_model())

# Evaluate photo
result = selector.evaluate(image_path)

# Track model usage
manager.record_usage(
    manager.get_current_model(),
    result.get('inference_time', 0),
    success=True
)
```

## Error Handling

### Common Errors
1. **Model Not Found**: Model doesn't exist in catalog
2. **Model Not Installed**: Model not available in Ollama
3. **Insufficient VRAM**: Model requires more VRAM than available
4. **Download Failed**: Network or Ollama error during download
5. **Cannot Delete Current**: Attempting to delete active model

### Error Responses
All errors return appropriate HTTP status codes and descriptive messages.

## Testing

### Unit Tests
```bash
py -m pytest test_model_manager.py -v
```

### Test Coverage
- Model metadata operations
- Model listing and filtering
- Model switching
- Download simulation
- Statistics tracking
- Recommendation logic
- Compatibility checking
- Metadata persistence

## Best Practices

1. **Model Selection**
   - Use recommendation system for optimal model selection
   - Consider VRAM constraints
   - Match priority to use case

2. **Performance Tracking**
   - Always record usage after inference
   - Monitor success rates
   - Review statistics regularly

3. **Resource Management**
   - Check compatibility before switching
   - Monitor VRAM usage
   - Use quantization for memory constraints

4. **Metadata Management**
   - Regular backups via export
   - Sync with Ollama periodically
   - Keep metadata file secure

## Future Enhancements

1. **Async Download**: Background model downloads with WebSocket progress
2. **Auto-Update**: Automatic model updates when new versions available
3. **Custom Models**: Support for user-defined custom models
4. **Model Comparison**: Side-by-side performance comparison
5. **Cloud Sync**: Sync metadata across multiple installations

## References

- Ollama API Documentation
- Llama Model Documentation
- Requirements: 18.1, 18.2, 18.3, 18.4
