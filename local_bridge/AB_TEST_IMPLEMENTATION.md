# A/B Testing System Implementation

## Overview

The A/B Testing System enables systematic comparison of preset versions to determine which performs better based on user approval rates and processing times. This implementation fulfills Requirements 10.4 and 10.5.

## Features

### 1. Preset Comparison Experiments (Requirement 10.4)

- **Test Creation**: Create A/B tests comparing two preset versions
- **Photo Assignment**: Automatically assign photos to variants (A or B) with balanced distribution
- **Context Filtering**: Target specific contexts (e.g., "backlit_portrait", "low_light_indoor")
- **Sample Size Management**: Set target sample sizes and track progress
- **Test Lifecycle**: Pause, resume, and complete tests as needed

### 2. Effectiveness Measurement (Requirement 10.5)

- **Approval Rate Analysis**: Calculate and compare approval rates between variants
- **Processing Time Comparison**: Measure and compare processing times
- **Improvement Metrics**: Calculate relative improvements (percentage change)
- **Sample Size Validation**: Ensure sufficient data before analysis

### 3. Statistical Significance Testing (Requirement 10.5)

- **Chi-Squared Test**: Test for significant differences in approval rates
- **T-Test**: Test for significant differences in processing times
- **Significance Level**: Configurable α level (default: 0.05)
- **Winner Determination**: Automatically identify the better-performing variant
- **Recommendations**: Generate actionable recommendations based on results

### 4. Report Generation (Requirement 10.5)

- **Comprehensive Reports**: Include test info, effectiveness metrics, and statistical tests
- **JSON Export**: Export reports to JSON files for archival and sharing
- **Comparison Reports**: Compare multiple A/B tests side-by-side
- **Summary Generation**: Automatic generation of conclusions and recommendations

## Database Schema

### ABTest Table

```sql
CREATE TABLE ab_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    preset_a_id INTEGER NOT NULL,  -- Control variant
    preset_b_id INTEGER NOT NULL,  -- Treatment variant
    context_tag VARCHAR(100),
    target_sample_size INTEGER DEFAULT 100,
    duration_days INTEGER DEFAULT 30,
    status VARCHAR(50) CHECK(status IN ('active', 'paused', 'completed')),
    start_date DATETIME,
    end_date DATETIME,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (preset_a_id) REFERENCES presets(id),
    FOREIGN KEY (preset_b_id) REFERENCES presets(id)
);
```

### ABTestAssignment Table

```sql
CREATE TABLE ab_test_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id INTEGER NOT NULL,
    photo_id INTEGER NOT NULL,
    variant VARCHAR(1) CHECK(variant IN ('A', 'B')),
    preset_id INTEGER NOT NULL,
    assigned_at DATETIME NOT NULL,
    approved BOOLEAN,
    processing_time FLOAT,
    result_recorded_at DATETIME,
    FOREIGN KEY (test_id) REFERENCES ab_tests(id),
    FOREIGN KEY (photo_id) REFERENCES photos(id),
    FOREIGN KEY (preset_id) REFERENCES presets(id)
);
```

## API Reference

### ABTestManager Class

#### Test Management

```python
# Create a new A/B test
ab_test = manager.create_ab_test(
    name='WhiteLayer v4 vs v5',
    description='Testing new version',
    preset_a_id=1,
    preset_b_id=2,
    context_tag='backlit_portrait',
    target_sample_size=100,
    duration_days=30
)

# Get test by ID
ab_test = manager.get_ab_test(test_id=1)

# List tests with filters
tests = manager.list_ab_tests(status='active', context_tag='backlit_portrait')

# Pause/Resume/Complete test
manager.pause_ab_test(test_id=1)
manager.resume_ab_test(test_id=1)
manager.complete_ab_test(test_id=1)
```

#### Photo Assignment

```python
# Assign photo to variant (automatic balancing)
assignment = manager.assign_photo_to_variant(
    test_id=1,
    photo_id=123
)

# Assign to specific variant
assignment = manager.assign_photo_to_variant(
    test_id=1,
    photo_id=124,
    variant='B'
)

# Record result
manager.record_result(
    test_id=1,
    photo_id=123,
    approved=True,
    processing_time=5.2
)
```

#### Analysis

```python
# Measure effectiveness
effectiveness = manager.measure_effectiveness(test_id=1)
# Returns: approval rates, processing times, improvements

# Test statistical significance
significance = manager.test_statistical_significance(test_id=1)
# Returns: chi-squared test, t-test, winner, recommendation

# Get test progress
progress = manager.get_test_progress(test_id=1)
# Returns: assignments, completion rate, readiness for analysis
```

#### Reporting

```python
# Generate single test report
report = manager.generate_report(
    test_id=1,
    output_path='reports/ab_test_1.json'
)

# Generate comparison report
comparison = manager.generate_comparison_report(
    test_ids=[1, 2, 3],
    output_path='reports/comparison.json'
)
```

## Usage Examples

### Example 1: Basic A/B Test

```python
from models.database import init_db, get_session
from ab_test_manager import ABTestManager

# Initialize
init_db()
db = get_session()
manager = ABTestManager(db)

# Create test
test = manager.create_ab_test(
    name='Preset Comparison',
    description='Testing v4 vs v5',
    preset_a_id=1,
    preset_b_id=2,
    target_sample_size=100
)

# Assign photos and record results
for photo_id in photo_ids:
    assignment = manager.assign_photo_to_variant(test.id, photo_id)
    # ... process photo ...
    manager.record_result(test.id, photo_id, approved=True, processing_time=5.0)

# Analyze results
effectiveness = manager.measure_effectiveness(test.id)
significance = manager.test_statistical_significance(test.id)

# Generate report
report = manager.generate_report(test.id, 'report.json')
```

### Example 2: Context-Specific Testing

```python
# Test preset for specific context
test = manager.create_ab_test(
    name='Backlit Portrait Optimization',
    description='Testing improved backlit handling',
    preset_a_id=1,
    preset_b_id=2,
    context_tag='backlit_portrait',  # Only test on backlit portraits
    target_sample_size=50
)

# Only photos with matching context will be assigned
```

### Example 3: Monitoring Test Progress

```python
# Check if test is ready for analysis
progress = manager.get_test_progress(test_id=1)

if progress['ready_for_analysis']:
    significance = manager.test_statistical_significance(test_id=1)
    
    if significance['winner']:
        print(f"Winner: Variant {significance['winner']}")
        print(f"Recommendation: {significance['recommendation']}")
    else:
        print("No significant difference found")
else:
    print(f"Need {progress['target_sample_size'] - progress['completed_assignments']} more samples")
```

## Statistical Methods

### Chi-Squared Test (Approval Rates)

Tests whether the difference in approval rates between variants is statistically significant.

- **Null Hypothesis**: No difference in approval rates
- **Alternative Hypothesis**: Significant difference exists
- **Test Statistic**: Chi-squared (χ²)
- **Significance Level**: α = 0.05 (default)

### Independent T-Test (Processing Times)

Tests whether the difference in processing times between variants is statistically significant.

- **Null Hypothesis**: No difference in mean processing times
- **Alternative Hypothesis**: Significant difference exists
- **Test Statistic**: t-statistic
- **Significance Level**: α = 0.05 (default)

## Best Practices

### 1. Sample Size

- **Minimum**: 30 samples per variant (60 total)
- **Recommended**: 50-100 samples per variant for reliable results
- **Large Effects**: Smaller samples may suffice for large differences
- **Small Effects**: Larger samples needed to detect subtle differences

### 2. Test Duration

- **Short Tests**: 7-14 days for quick feedback
- **Standard Tests**: 30 days for balanced results
- **Long Tests**: 60+ days for seasonal variations

### 3. Context Targeting

- Always specify `context_tag` when testing context-specific presets
- Ensures fair comparison within the same shooting conditions
- Reduces confounding variables

### 4. Interpretation

- **p < 0.05**: Statistically significant difference
- **p ≥ 0.05**: No significant difference (continue with current preset)
- **Practical Significance**: Consider both statistical and practical importance
  - 5% improvement: Moderate
  - 10% improvement: Strong
  - 20%+ improvement: Very strong

### 5. Multiple Testing

- When running multiple A/B tests simultaneously, consider Bonferroni correction
- Adjust significance level: α_adjusted = α / number_of_tests

## Integration with Existing Systems

### Preset Manager Integration

```python
from preset_manager import PresetManager
from ab_test_manager import ABTestManager

preset_mgr = PresetManager(db)
ab_mgr = ABTestManager(db)

# Create new preset version
new_preset = preset_mgr.create_preset_version(
    base_preset_id=1,
    new_version='v5',
    config_changes={'exposure': 0.1}
)

# Immediately start A/B test
test = ab_mgr.create_ab_test(
    name=f'{base_preset.name} v4 vs v5',
    preset_a_id=base_preset.id,
    preset_b_id=new_preset.id
)
```

### Learning System Integration

```python
from learning_system import LearningSystem
from ab_test_manager import ABTestManager

learning = LearningSystem(db)
ab_mgr = ABTestManager(db)

# After A/B test completes, use winner for learning
significance = ab_mgr.test_statistical_significance(test_id)

if significance['winner'] == 'B':
    # Update preset usage tracking
    preset_mgr.record_preset_usage(
        preset_id=test.preset_b_id,
        photo_id=photo_id,
        approved=True
    )
```

## Migration

Run the database migration to create A/B testing tables:

```bash
cd local_bridge
alembic upgrade head
```

This will execute migration `003_add_ab_testing.py` and create:
- `ab_tests` table
- `ab_test_assignments` table
- Associated indexes

## Testing

Run the test suite:

```bash
pytest test_ab_test_manager.py -v
```

Tests cover:
- Test creation and management
- Photo assignment and balancing
- Result recording
- Effectiveness measurement
- Statistical significance testing
- Report generation
- Test lifecycle (pause/resume/complete)

## Performance Considerations

### Database Indexes

The following indexes are created for optimal performance:
- `idx_ab_tests_status`: Fast filtering by test status
- `idx_ab_test_assignments_test`: Fast lookup of assignments by test
- `idx_ab_test_assignments_photo`: Fast lookup of assignments by photo
- `idx_ab_test_assignments_variant`: Fast filtering by variant

### Query Optimization

- Batch assignment operations when possible
- Use `ready_for_analysis` flag to avoid premature analysis
- Cache effectiveness results for completed tests

## Troubleshooting

### Insufficient Data Error

**Problem**: `measure_effectiveness()` returns `insufficient_data`

**Solution**: 
- Ensure at least 30 samples per variant (60 total)
- Check `get_test_progress()` to see current sample count
- Continue assigning photos until target is reached

### No Significant Difference

**Problem**: Statistical tests show no significant difference

**Possible Causes**:
1. Sample size too small
2. Actual difference is small
3. High variance in results

**Solutions**:
- Increase sample size
- Extend test duration
- Check for confounding variables (different contexts mixed)

### Unbalanced Assignment

**Problem**: One variant has many more assignments than the other

**Solution**:
- Use automatic assignment (don't specify variant)
- The system automatically balances assignments
- Check for bugs in custom assignment logic

## Future Enhancements

1. **Multi-Armed Bandit**: Dynamic allocation based on performance
2. **Bayesian A/B Testing**: Continuous probability of superiority
3. **Sequential Testing**: Early stopping when significance is reached
4. **Segmentation**: Analyze results by photo characteristics
5. **Visualization**: Charts and graphs for effectiveness metrics

## References

- Requirements: 10.4, 10.5 in requirements.md
- Design: Section on Preset Library and Version Management in design.md
- Database: models/database.py
- Tests: test_ab_test_manager.py
- Example: example_ab_test_usage.py
