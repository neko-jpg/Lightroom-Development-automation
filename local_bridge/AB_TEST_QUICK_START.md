# A/B Testing Quick Start Guide

## Overview

The A/B Testing System allows you to scientifically compare two preset versions to determine which performs better based on user approval rates and processing times.

## Quick Start (5 Minutes)

### 1. Setup Database

```bash
cd local_bridge
alembic upgrade head
```

### 2. Create Your First A/B Test

```python
from models.database import init_db, get_session
from ab_test_manager import ABTestManager
from preset_manager import PresetManager

# Initialize
init_db('sqlite:///data/junmai.db')
db = get_session()

# Create managers
ab_manager = ABTestManager(db)
preset_manager = PresetManager(db)

# Get your presets (or create them)
preset_v4 = preset_manager.get_preset_by_name('WhiteLayer_v4')
preset_v5 = preset_manager.get_preset_by_name('WhiteLayer_v5')

# Create A/B test
test = ab_manager.create_ab_test(
    name='WhiteLayer v4 vs v5 Comparison',
    description='Testing improved backlit handling in v5',
    preset_a_id=preset_v4.id,  # Control (current version)
    preset_b_id=preset_v5.id,  # Treatment (new version)
    context_tag='backlit_portrait',  # Optional: target specific context
    target_sample_size=100,
    duration_days=30
)

print(f"✓ Created test: {test.name} (ID: {test.id})")
```

### 3. Assign Photos During Processing

```python
# In your photo processing workflow
for photo in photos_to_process:
    # Assign photo to a variant (A or B)
    assignment = ab_manager.assign_photo_to_variant(
        test_id=test.id,
        photo_id=photo.id
    )
    
    # Use the assigned preset
    preset_id = assignment.preset_id
    
    # ... process photo with preset ...
    
    # Record the result
    ab_manager.record_result(
        test_id=test.id,
        photo_id=photo.id,
        approved=user_approved,  # True/False
        processing_time=elapsed_time  # seconds
    )
```

### 4. Check Progress

```python
progress = ab_manager.get_test_progress(test.id)

print(f"Progress: {progress['progress_percent']:.1f}%")
print(f"Completed: {progress['completed_assignments']}/{progress['target_sample_size']}")
print(f"Ready for analysis: {progress['ready_for_analysis']}")
```

### 5. Analyze Results

```python
# Once you have enough data (30+ samples per variant)
if progress['ready_for_analysis']:
    # Measure effectiveness
    effectiveness = ab_manager.measure_effectiveness(test.id)
    
    print(f"Variant A approval rate: {effectiveness['variant_a']['approval_rate']:.1%}")
    print(f"Variant B approval rate: {effectiveness['variant_b']['approval_rate']:.1%}")
    print(f"Improvement: {effectiveness['improvements']['approval_rate']:+.1f}%")
    
    # Test statistical significance
    significance = ab_manager.test_statistical_significance(test.id)
    
    print(f"Statistically significant: {significance['approval_rate_test']['significant']}")
    print(f"Winner: {significance['winner']}")
    print(f"Recommendation: {significance['recommendation']}")
```

### 6. Generate Report

```python
# Generate comprehensive report
report = ab_manager.generate_report(
    test_id=test.id,
    output_path='reports/ab_test_report.json'
)

print(f"✓ Report saved to: reports/ab_test_report.json")
print(f"Conclusion: {report['summary']['conclusion']}")
print(f"Action: {report['summary']['action']}")
```

## Common Workflows

### Workflow 1: Testing a New Preset Version

```python
# 1. Create new preset version
new_preset = preset_manager.create_preset_version(
    base_preset_id=old_preset.id,
    new_version='v5',
    config_changes={'exposure': 0.1, 'contrast': 5}
)

# 2. Start A/B test
test = ab_manager.create_ab_test(
    name=f'{old_preset.name} v4 vs v5',
    preset_a_id=old_preset.id,
    preset_b_id=new_preset.id
)

# 3. Process photos (automatic assignment)
# 4. Analyze results
# 5. Deploy winner if significant improvement
```

### Workflow 2: Context-Specific Optimization

```python
# Test preset specifically for backlit portraits
test = ab_manager.create_ab_test(
    name='Backlit Portrait Optimization',
    preset_a_id=current_preset.id,
    preset_b_id=optimized_preset.id,
    context_tag='backlit_portrait'  # Only test on this context
)

# Only photos with context_tag='backlit_portrait' will be assigned
```

### Workflow 3: Monitoring Multiple Tests

```python
# List all active tests
active_tests = ab_manager.list_ab_tests(status='active')

for test in active_tests:
    progress = ab_manager.get_test_progress(test.id)
    print(f"{test.name}: {progress['progress_percent']:.0f}% complete")
    
    if progress['ready_for_analysis']:
        significance = ab_manager.test_statistical_significance(test.id)
        if significance['winner']:
            print(f"  → Winner: Variant {significance['winner']}")
```

## Understanding Results

### Approval Rate Improvement

- **< 5%**: Small improvement, may not be practically significant
- **5-10%**: Moderate improvement, worth considering
- **10-20%**: Strong improvement, recommended to deploy
- **> 20%**: Very strong improvement, deploy immediately

### Statistical Significance

- **p < 0.05**: Statistically significant (95% confidence)
- **p ≥ 0.05**: Not significant (continue testing or use current preset)

### Sample Size Guidelines

- **Minimum**: 30 samples per variant (60 total)
- **Recommended**: 50-100 samples per variant
- **Large effects**: Smaller samples may suffice
- **Small effects**: Larger samples needed

## Best Practices

### 1. Always Set Context Tags

```python
# Good: Specific context
test = ab_manager.create_ab_test(
    ...,
    context_tag='backlit_portrait'
)

# Bad: Mixed contexts (unfair comparison)
test = ab_manager.create_ab_test(
    ...,
    context_tag=None  # Will test on all contexts
)
```

### 2. Wait for Sufficient Data

```python
# Check before analyzing
progress = ab_manager.get_test_progress(test.id)

if not progress['ready_for_analysis']:
    print(f"Need {progress['target_sample_size'] - progress['completed_assignments']} more samples")
    return

# Now safe to analyze
significance = ab_manager.test_statistical_significance(test.id)
```

### 3. Consider Practical Significance

```python
significance = ab_manager.test_statistical_significance(test.id)

if significance['winner'] == 'B':
    improvement = effectiveness['improvements']['approval_rate']
    
    if improvement > 10:
        print("Strong improvement - deploy immediately")
    elif improvement > 5:
        print("Moderate improvement - consider deploying")
    else:
        print("Small improvement - evaluate practical value")
```

### 4. Pause Tests When Needed

```python
# Pause test temporarily
ab_manager.pause_ab_test(test.id)

# Resume later
ab_manager.resume_ab_test(test.id)

# Complete when done
ab_manager.complete_ab_test(test.id)
```

## Troubleshooting

### "Insufficient data" Error

**Problem**: Not enough samples for analysis

**Solution**:
```python
progress = ab_manager.get_test_progress(test.id)
print(f"Need {60 - progress['completed_assignments']} more samples")
```

### No Significant Difference

**Problem**: p-value ≥ 0.05

**Possible causes**:
1. Sample size too small → Collect more data
2. Actual difference is small → Consider practical significance
3. High variance → Check for confounding variables

### Unbalanced Assignment

**Problem**: One variant has many more samples

**Solution**: Use automatic assignment (don't specify variant)
```python
# Good: Automatic balancing
assignment = ab_manager.assign_photo_to_variant(test.id, photo.id)

# Bad: Manual assignment (can cause imbalance)
assignment = ab_manager.assign_photo_to_variant(test.id, photo.id, variant='A')
```

## Example Output

```
✓ Created test: WhiteLayer v4 vs v5 Comparison (ID: 1)
Progress: 100.0%
Completed: 100/100
Ready for analysis: True

Variant A approval rate: 72.0%
Variant B approval rate: 86.0%
Improvement: +19.4%

Statistically significant: True
Winner: B
Recommendation: Strong recommendation: Switch to Preset B. 
                Approval rate improved by 19.4% with statistical significance.

✓ Report saved to: reports/ab_test_report.json
Conclusion: Preset B outperforms Preset A with 19.4% improvement in approval rate
Action: Deploy winner
```

## Next Steps

1. **Run Example**: `python example_ab_test_usage.py`
2. **Read Full Docs**: See `AB_TEST_IMPLEMENTATION.md`
3. **Integrate**: Add to your photo processing workflow
4. **Monitor**: Check test progress regularly
5. **Deploy Winners**: Update presets based on results

## Support

- **Documentation**: `AB_TEST_IMPLEMENTATION.md`
- **Tests**: `test_ab_test_manager.py`
- **Example**: `example_ab_test_usage.py`
- **Requirements**: Requirements 10.4, 10.5 in `requirements.md`
