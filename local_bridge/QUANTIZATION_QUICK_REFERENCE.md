# Model Quantization Quick Reference

## Quick Commands

### Enable Quantization
```python
from ollama_client import OllamaClient

# 8-bit quantization (50% memory reduction)
client = OllamaClient(enable_quantization=True, quantization_bits=8)

# 4-bit quantization (75% memory reduction)
client = OllamaClient(enable_quantization=True, quantization_bits=4)
```

### Switch Quantization
```python
# Enable 8-bit
client.set_quantization(True, 8)

# Enable 4-bit
client.set_quantization(True, 4)

# Disable
client.set_quantization(False)
```

### Check Settings
```python
settings = client.get_quantization_settings()
print(f"Enabled: {settings['enabled']}")
print(f"Bits: {settings['bits']}")
print(f"Memory Reduction: {settings['memory_reduction']}")
```

### AI Selector Integration
```python
from ai_selector import AISelector

# Create with quantization
selector = AISelector(
    enable_quantization=True,
    quantization_bits=8
)

# Change settings
selector.set_quantization(True, 4)
```

## Model Name Transformations

| Original | 8-bit | 4-bit |
|----------|-------|-------|
| `llama3.1:8b-instruct` | `llama3.1:q8_8b-instruct` | `llama3.1:q4_8b-instruct` |
| `mixtral:8x7b` | `mixtral:q8_8x7b` | `mixtral:q4_8x7b` |
| `llama3.1` | `llama3.1:q8` | `llama3.1:q4` |

## Memory Usage (8B Model)

| Mode | Memory | Reduction |
|------|--------|-----------|
| Full | 8 GB | - |
| 8-bit | 4 GB | 50% |
| 4-bit | 2 GB | 75% |

## GPU Recommendations

| GPU | VRAM | Setting |
|-----|------|---------|
| RTX 4060 | 8 GB | 4-bit |
| RTX 4070 | 12 GB | 8-bit |
| RTX 4080+ | 16+ GB | Full |

## Performance Tracking

```python
# Get stats
stats = client.get_performance_stats("llama3.1:8b")

# Compare quantization
results = client.compare_quantization_performance(
    model="llama3.1:8b-instruct",
    prompt="Test prompt",
    test_iterations=3
)
```

## Configuration

```json
{
  "ai": {
    "enable_quantization": true,
    "quantization_bits": 8
  }
}
```

## Testing

```bash
# Run tests
py local_bridge/test_quantization_standalone.py

# Run examples
py local_bridge/example_quantization_usage.py

# Compare performance
py local_bridge/ollama_client.py --compare
```

## Common Issues

### Model Not Found
```bash
ollama pull llama3.1:q4_8b-instruct
```

### Out of Memory
```python
client.set_quantization(True, 4)  # Switch to 4-bit
```

### Slow Performance
```python
# Check GPU temperature
# May be thermal throttling
```

## Files

- `ollama_client.py` - Core implementation
- `ai_selector.py` - Integration
- `test_quantization_standalone.py` - Tests
- `example_quantization_usage.py` - Examples
- `QUANTIZATION_QUICK_START.md` - Full guide
- `TASK_40_COMPLETION_SUMMARY.md` - Implementation details
