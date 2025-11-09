# Model Quantization Quick Start Guide

## Overview

Model quantization reduces memory usage and can improve inference speed by using lower-precision representations (4-bit or 8-bit) instead of full precision (16-bit). This is especially useful for running large language models on GPUs with limited VRAM like the RTX 4060 (8GB).

**Requirements:** 17.4

## Benefits

- **4-bit Quantization**: ~75% memory reduction, faster inference
- **8-bit Quantization**: ~50% memory reduction, balanced quality/speed
- **Full Precision**: Best quality, highest memory usage

## Quick Start

### 1. Basic Usage

```python
from ollama_client import OllamaClient

# Create client with 8-bit quantization
client = OllamaClient(
    enable_quantization=True,
    quantization_bits=8
)

# Check settings
settings = client.get_quantization_settings()
print(f"Enabled: {settings['enabled']}")
print(f"Bits: {settings['bits']}")
print(f"Memory Reduction: {settings['memory_reduction']}")
```

### 2. Switch Quantization Levels

```python
# Switch to 4-bit quantization
client.set_quantization(True, 4)

# Disable quantization
client.set_quantization(False)
```

### 3. AI Selector Integration

```python
from ai_selector import AISelector

# Create AI Selector with quantization
selector = AISelector(
    enable_llm=True,
    enable_quantization=True,
    quantization_bits=8
)

# Evaluate photos with quantized model
result = selector.evaluate('photo.jpg')
```

### 4. Performance Comparison

```python
# Compare performance between quantization levels
results = client.compare_quantization_performance(
    model="llama3.1:8b-instruct",
    prompt="Test prompt",
    test_iterations=3
)

print(f"Non-quantized: {results['non_quantized']['avg_time']:.2f}s")
print(f"8-bit: {results['quantized_8bit']['avg_time']:.2f}s")
print(f"4-bit: {results['quantized_4bit']['avg_time']:.2f}s")
```

## Model Name Transformation

Quantization automatically transforms model names:

| Original | 8-bit Quantized | 4-bit Quantized |
|----------|----------------|----------------|
| `llama3.1:8b-instruct` | `llama3.1:q8_8b-instruct` | `llama3.1:q4_8b-instruct` |
| `mixtral:8x7b` | `mixtral:q8_8x7b` | `mixtral:q4_8x7b` |

## Memory Usage Estimates

For an 8B parameter model:

| Precision | Memory Usage | Reduction |
|-----------|-------------|-----------|
| Full (16-bit) | ~8 GB | - |
| 8-bit | ~4 GB | 50% |
| 4-bit | ~2 GB | 75% |

## Recommendations by GPU

| GPU | VRAM | Recommendation |
|-----|------|---------------|
| RTX 4060 | 8 GB | 4-bit or 8-bit quantization |
| RTX 4070 | 12 GB | 8-bit quantization |
| RTX 4080 | 16 GB | Full precision or 8-bit |
| RTX 4090 | 24 GB | Full precision |

## Performance Tracking

Track performance metrics for each model:

```python
# Get performance statistics
stats = client.get_performance_stats("llama3.1:8b")

print(f"Total Calls: {stats['total_calls']}")
print(f"Avg Time: {stats['avg_time']:.2f}s")
print(f"Success Rate: {stats['successful_calls']/stats['total_calls']*100:.1f}%")
```

## Configuration File

Add to `config.json`:

```json
{
  "ai": {
    "llm_provider": "ollama",
    "llm_model": "llama3.1:8b-instruct",
    "ollama_host": "http://localhost:11434",
    "enable_quantization": true,
    "quantization_bits": 8,
    "gpu_memory_limit_mb": 6144
  }
}
```

## Testing

Run the test suite:

```bash
py -m pytest local_bridge/test_quantization.py -v
```

Run examples:

```bash
py local_bridge/example_quantization_usage.py
```

## Troubleshooting

### Quantized Model Not Found

If you get an error about a quantized model not being available:

1. Check available models:
   ```bash
   ollama list
   ```

2. Pull the quantized model:
   ```bash
   ollama pull llama3.1:q4_8b-instruct
   ```

3. Or disable quantization temporarily:
   ```python
   client.set_quantization(False)
   ```

### Out of Memory Errors

If you still get OOM errors with quantization:

1. Switch to 4-bit quantization:
   ```python
   client.set_quantization(True, 4)
   ```

2. Reduce GPU memory limit in config:
   ```json
   "gpu_memory_limit_mb": 4096
   ```

3. Close other GPU-intensive applications

### Performance Issues

If quantized models are slower:

1. Check GPU temperature (may be throttling)
2. Verify model is actually using GPU (not CPU)
3. Try different quantization levels
4. Run performance comparison to identify bottlenecks

## API Reference

### OllamaClient

#### `__init__(host, enable_quantization, quantization_bits)`
Initialize client with quantization settings.

#### `set_quantization(enable, bits)`
Enable/disable quantization and set bits (4 or 8).

#### `get_quantization_settings()`
Get current quantization settings.

#### `compare_quantization_performance(model, prompt, test_iterations)`
Compare performance across quantization levels.

#### `get_performance_stats(model)`
Get performance statistics for a model.

### AISelector

#### `set_quantization(enable, bits)`
Set quantization on the AI selector.

#### `get_quantization_settings()`
Get current quantization settings.

#### `compare_quantization_performance(test_image_path, test_iterations)`
Compare quantization performance using a test image.

## Best Practices

1. **Start with 8-bit**: Good balance of quality and memory savings
2. **Monitor Performance**: Track metrics to optimize settings
3. **Test Quality**: Verify quantization doesn't degrade results
4. **GPU Temperature**: Watch for thermal throttling
5. **Batch Processing**: Quantization benefits increase with batch size

## Related Documentation

- [GPU Management Implementation](GPU_MANAGEMENT_IMPLEMENTATION.md)
- [AI Selector Documentation](ai_selector.py)
- [Ollama Documentation](https://ollama.ai/docs)

## Support

For issues or questions:
1. Check logs in `logs/main.log`
2. Run diagnostics: `py local_bridge/example_quantization_usage.py`
3. Review GPU stats: `py local_bridge/example_gpu_usage.py`
