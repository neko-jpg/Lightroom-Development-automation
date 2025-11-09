# Model Performance Statistics - Quick Reference

## Overview

The Model Performance Statistics system tracks and analyzes performance metrics for individual LLM models, enabling data-driven model selection and optimization.

**Requirements:** 18.5

## Key Features

- ✅ Model-specific processing time recording
- ✅ Model-specific quality score tracking
- ✅ Recommended model selection logic
- ✅ Comparative analysis between models
- ✅ Performance trend analysis
- ✅ Integration with AI Selector and Model Manager

## Quick Start

### 1. Basic Performance Recording

```python
from model_performance_stats import get_model_performance_stats

collector = get_model_performance_stats()

# Record model performance
collector.record_model_performance(
    model_name="llama3.1:8b-instruct",
    operation="photo_evaluation",
    processing_time_ms=1234.56,
    quality_score=4.2,
    success=True,
    memory_used_mb=512.0,
    tokens_generated=150,
    photo_id=123,
    job_id="job_abc123"
)
```

### 2. Get Model Statistics

```python
# Get statistics for a specific model
stats = collector.get_model_statistics("llama3.1:8b-instruct")

print(f"Total Operations: {stats.total_operations}")
print(f"Success Rate: {stats.success_rate:.1f}%")
print(f"Avg Processing Time: {stats.avg_processing_time_ms:.2f}ms")
print(f"Avg Quality Score: {stats.avg_quality_score:.2f}/5.0")

# Get statistics for all models
all_stats = collector.get_all_model_statistics()
```

### 3. Compare Models

```python
# Compare multiple models
comparison = collector.compare_models([
    "llama3.1:8b-instruct",
    "llama3.1:13b-instruct",
    "llama3.2:3b-instruct"
])

# Check rankings
print(f"Fastest: {comparison['rankings']['fastest']['model']}")
print(f"Highest Quality: {comparison['rankings']['highest_quality']['model']}")
print(f"Most Reliable: {comparison['rankings']['most_reliable']['model']}")
print(f"Best Overall: {comparison['rankings']['best_overall']['model']}")
```

### 4. Get Model Recommendation

```python
# Recommend model based on priority
recommended = collector.recommend_model(
    priority="balanced",  # "speed", "quality", "balanced", "reliable"
    available_models=["llama3.1:8b-instruct", "llama3.2:3b-instruct"],
    duration_hours=24,
    min_operations=10
)

print(f"Recommended model: {recommended}")
```

### 5. Integration with AI Selector

```python
from model_performance_integration import get_model_performance_integration
from model_manager import ModelManager

# Initialize integration
model_manager = ModelManager()
integration = get_model_performance_integration(model_manager)

# Automatic performance tracking
with integration.track_model_performance(
    model_name="llama3.1:8b-instruct",
    operation="photo_evaluation",
    photo_id=456
):
    # Your model operation here
    result = ai_selector.evaluate(photo_path)

# Performance is automatically recorded
```

### 6. Get Performance Insights

```python
# Get comprehensive insights
insights = integration.get_performance_insights(duration_hours=24)

print(f"Models Analyzed: {insights['models_analyzed']}")
print(f"Total Operations: {insights['total_operations']}")
print(f"Overall Success Rate: {insights['overall_success_rate']:.1f}%")

# Recommendations for different priorities
for priority, model in insights['recommendations'].items():
    print(f"{priority}: {model}")

# Warnings
for warning in insights['warnings']:
    print(f"⚠ {warning}")
```

## API Endpoints

### Record Performance

```bash
POST /api/model-performance/record
Content-Type: application/json

{
  "model_name": "llama3.1:8b-instruct",
  "operation": "photo_evaluation",
  "processing_time_ms": 1234.56,
  "quality_score": 4.2,
  "success": true,
  "memory_used_mb": 512.0,
  "tokens_generated": 150,
  "photo_id": 123,
  "job_id": "job_abc123"
}
```

### Get Statistics

```bash
# Specific model
GET /api/model-performance/statistics/llama3.1:8b-instruct?duration_hours=24

# All models
GET /api/model-performance/statistics?duration_hours=24&operation=photo_evaluation
```

### Compare Models

```bash
POST /api/model-performance/compare
Content-Type: application/json

{
  "models": ["llama3.1:8b-instruct", "llama3.1:13b-instruct"],
  "duration_hours": 24,
  "operation": "photo_evaluation"
}
```

### Get Recommendation

```bash
GET /api/model-performance/recommend?priority=balanced&duration_hours=24&min_operations=10
```

### Get Performance Trend

```bash
GET /api/model-performance/trend/llama3.1:8b-instruct?metric=processing_time&hours=24&bucket_size_minutes=60
```

### Export Statistics

```bash
GET /api/model-performance/export
```

## Performance Metrics Tracked

| Metric | Description | Unit |
|--------|-------------|------|
| Processing Time | Time taken for operation | milliseconds |
| Quality Score | Quality rating | 1-5 scale |
| Success Rate | Percentage of successful operations | percentage |
| Memory Usage | Memory consumed | MB |
| Token Throughput | Tokens generated per second | tokens/sec |

## Recommendation Priorities

### Speed Priority
- Selects fastest model based on average processing time
- Best for: High-volume batch processing

### Quality Priority
- Selects model with highest average quality score
- Best for: Critical evaluations, final selections

### Balanced Priority
- Composite score: 30% speed + 40% quality + 30% reliability
- Best for: General use, default recommendation

### Reliable Priority
- Selects model with highest success rate
- Best for: Production environments, automated workflows

## Statistics Filtering

### By Duration
```python
# Last 24 hours
stats = collector.get_model_statistics("model_name", duration_hours=24)

# Last week
stats = collector.get_model_statistics("model_name", duration_hours=168)
```

### By Operation
```python
# Specific operation
stats = collector.get_model_statistics(
    "model_name",
    operation="photo_evaluation"
)
```

## Performance Trends

```python
# Get trend data
trend = collector.get_model_performance_trend(
    model_name="llama3.1:8b-instruct",
    metric="processing_time",  # or "quality_score", "success_rate"
    hours=24,
    bucket_size_minutes=60
)

# Analyze buckets
for bucket in trend['buckets']:
    print(f"{bucket['timestamp']}: {bucket['value']:.2f} ({bucket['count']} ops)")
```

## Data Management

### Clear Model Data
```python
# Clear specific model
collector.clear_model_data("llama3.1:8b-instruct")

# Clear old data (older than 30 days)
collector.clear_old_data(days=30)
```

### Export/Import
```python
# Export statistics
collector.export_statistics("model_stats_export.json")

# Data is automatically persisted to storage file
```

## Integration Points

### With AI Selector
- Automatic performance recording during photo evaluation
- Quality score tracking from evaluation results
- Token generation tracking

### With Model Manager
- Model compatibility checking
- Model metadata integration
- Usage statistics synchronization

### With Performance Metrics
- Unified metrics collection
- Processing time recording
- Memory usage tracking

## Best Practices

1. **Minimum Operations**: Require at least 10 operations before making recommendations
2. **Time Windows**: Use 24-hour windows for recent performance, longer for trends
3. **Priority Selection**: Use "balanced" for general use, specific priorities for special cases
4. **Data Cleanup**: Regularly clear old data (30+ days) to maintain performance
5. **Monitoring**: Check performance insights regularly for warnings and issues

## Common Use Cases

### 1. Automatic Model Selection
```python
# Select best model for current conditions
integration = get_model_performance_integration(model_manager)
recommended = integration.select_best_model(
    priority="balanced",
    available_vram_gb=8.0
)
```

### 2. Performance Monitoring
```python
# Monitor model performance over time
insights = integration.get_performance_insights(duration_hours=24)
if insights['warnings']:
    # Alert on performance issues
    send_alert(insights['warnings'])
```

### 3. A/B Testing
```python
# Compare two model versions
comparison = collector.compare_models([
    "llama3.1:8b-instruct",
    "llama3.1:8b-instruct-q4"  # Quantized version
])
```

### 4. Resource Optimization
```python
# Find fastest model that meets quality threshold
all_stats = collector.get_all_model_statistics()
candidates = [
    (name, stats) for name, stats in all_stats.items()
    if stats.avg_quality_score and stats.avg_quality_score >= 4.0
]
fastest = min(candidates, key=lambda x: x[1].avg_processing_time_ms)
```

## Troubleshooting

### No Recommendations Available
- Ensure models have at least `min_operations` recorded
- Check that models are installed and available
- Verify performance data exists for the time window

### Inaccurate Statistics
- Clear old data that may skew results
- Use appropriate time windows (recent data for current performance)
- Ensure sufficient sample size (10+ operations)

### Performance Degradation
- Check warnings in performance insights
- Compare current vs historical performance
- Monitor memory usage and GPU temperature

## Files

- `model_performance_stats.py` - Core statistics collector
- `api_model_performance.py` - REST API endpoints
- `model_performance_integration.py` - Integration layer
- `test_model_performance_stats.py` - Test suite
- `example_model_performance_usage.py` - Usage examples

## Related Documentation

- [Model Management Implementation](MODEL_MANAGEMENT_IMPLEMENTATION.md)
- [Performance Metrics Implementation](PERFORMANCE_METRICS_IMPLEMENTATION.md)
- [GPU Management](GPU_MANAGEMENT_IMPLEMENTATION.md)

## Support

For issues or questions:
1. Check example usage file
2. Review test cases
3. Check logs in `logs/` directory
4. Verify data in `data/model_performance_stats.json`
