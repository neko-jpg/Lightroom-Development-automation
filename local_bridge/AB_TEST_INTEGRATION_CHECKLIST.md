# A/B Testing Integration Checklist

## Pre-Integration

- [ ] Database migration completed (`alembic upgrade head`)
- [ ] Dependencies installed (`scipy` for statistical tests)
- [ ] Existing preset system is working
- [ ] Photo processing pipeline is functional

## Database Setup

- [ ] Run migration: `alembic upgrade head`
- [ ] Verify tables created:
  - [ ] `ab_tests` table exists
  - [ ] `ab_test_assignments` table exists
- [ ] Verify indexes created:
  - [ ] `idx_ab_tests_status`
  - [ ] `idx_ab_test_assignments_test`
  - [ ] `idx_ab_test_assignments_photo`
  - [ ] `idx_ab_test_assignments_variant`

## Code Integration

### 1. Import Module

```python
from ab_test_manager import ABTestManager
```

- [ ] Import successful
- [ ] No import errors

### 2. Initialize Manager

```python
from models.database import get_session

db = get_session()
ab_manager = ABTestManager(db)
```

- [ ] Manager initializes without errors
- [ ] Database connection works

### 3. Create Test A/B Test

```python
test = ab_manager.create_ab_test(
    name='Test Integration',
    description='Testing integration',
    preset_a_id=1,
    preset_b_id=2,
    target_sample_size=10
)
```

- [ ] Test created successfully
- [ ] Test ID returned
- [ ] Test appears in database

### 4. Assign Photos

```python
assignment = ab_manager.assign_photo_to_variant(
    test_id=test.id,
    photo_id=1
)
```

- [ ] Assignment created
- [ ] Variant assigned (A or B)
- [ ] Preset ID set correctly

### 5. Record Results

```python
ab_manager.record_result(
    test_id=test.id,
    photo_id=1,
    approved=True,
    processing_time=5.0
)
```

- [ ] Result recorded
- [ ] Timestamp set
- [ ] Data persisted to database

## Integration Points

### With Preset Manager

- [ ] Can retrieve presets for A/B tests
- [ ] Preset IDs are valid
- [ ] Can create new preset versions for testing

```python
from preset_manager import PresetManager

preset_mgr = PresetManager(db)
preset_a = preset_mgr.get_preset(1)
preset_b = preset_mgr.get_preset(2)

test = ab_manager.create_ab_test(
    name='Preset Comparison',
    preset_a_id=preset_a.id,
    preset_b_id=preset_b.id
)
```

- [ ] Integration works
- [ ] No errors

### With Photo Processing Pipeline

- [ ] Photos can be assigned during processing
- [ ] Assigned preset is used for processing
- [ ] Results are recorded after approval

```python
# In your processing loop
for photo in photos:
    assignment = ab_manager.assign_photo_to_variant(test.id, photo.id)
    
    # Use assignment.preset_id for processing
    preset = preset_mgr.get_preset(assignment.preset_id)
    
    # ... process photo ...
    
    # Record result
    ab_manager.record_result(
        test_id=test.id,
        photo_id=photo.id,
        approved=user_approved,
        processing_time=elapsed_time
    )
```

- [ ] Integration works
- [ ] Photos are processed with correct preset
- [ ] Results are recorded

### With Learning System

- [ ] A/B test results can feed into learning data
- [ ] Approved variants contribute to pattern analysis

```python
from learning_system import LearningSystem

learning = LearningSystem(db)

# After A/B test completes
significance = ab_manager.test_statistical_significance(test.id)

if significance['winner'] == 'B':
    # Record as learning data
    learning.record_approval(
        photo_id=photo.id,
        original_preset=preset_a.name,
        final_preset=preset_b.name
    )
```

- [ ] Integration works
- [ ] Learning data is recorded

## Testing

### Unit Tests

- [ ] Run test suite: `pytest test_ab_test_manager.py -v`
- [ ] All tests pass (10/10)
- [ ] No errors or failures

### Integration Tests

- [ ] Create test with real presets
- [ ] Assign real photos
- [ ] Record real results
- [ ] Analyze results
- [ ] Generate report

```python
# Integration test script
def test_integration():
    # Setup
    db = get_session()
    ab_manager = ABTestManager(db)
    preset_mgr = PresetManager(db)
    
    # Get presets
    presets = preset_mgr.list_presets()
    assert len(presets) >= 2, "Need at least 2 presets"
    
    # Create test
    test = ab_manager.create_ab_test(
        name='Integration Test',
        preset_a_id=presets[0].id,
        preset_b_id=presets[1].id,
        target_sample_size=10
    )
    assert test.id is not None
    
    # Assign and record
    for i in range(10):
        assignment = ab_manager.assign_photo_to_variant(test.id, i+1)
        ab_manager.record_result(test.id, i+1, True, 5.0)
    
    # Analyze
    progress = ab_manager.get_test_progress(test.id)
    assert progress['completed_assignments'] == 10
    
    print("✓ Integration test passed")

test_integration()
```

- [ ] Integration test passes
- [ ] No errors

## Functionality Verification

### Test Management

- [ ] Can create A/B tests
- [ ] Can list tests
- [ ] Can filter by status
- [ ] Can filter by context tag
- [ ] Can pause tests
- [ ] Can resume tests
- [ ] Can complete tests

### Photo Assignment

- [ ] Photos are assigned to variants
- [ ] Assignment is balanced (50/50 split)
- [ ] Can assign to specific variant
- [ ] Duplicate assignments are prevented

### Result Recording

- [ ] Can record approval
- [ ] Can record rejection
- [ ] Can record processing time
- [ ] Timestamps are set correctly

### Analysis

- [ ] Can measure effectiveness
- [ ] Approval rates calculated correctly
- [ ] Processing times calculated correctly
- [ ] Improvements calculated correctly
- [ ] Handles insufficient data gracefully

### Statistical Testing

- [ ] Chi-squared test works
- [ ] T-test works
- [ ] P-values calculated correctly
- [ ] Winner determined correctly
- [ ] Recommendations generated

### Reporting

- [ ] Can generate reports
- [ ] Reports contain all required fields
- [ ] JSON export works
- [ ] Reports are valid JSON
- [ ] Comparison reports work

## Performance Verification

### Database Performance

- [ ] Queries are fast (< 100ms for typical operations)
- [ ] Indexes are being used
- [ ] No N+1 query problems

```python
import time

# Test query performance
start = time.time()
tests = ab_manager.list_ab_tests()
elapsed = time.time() - start
assert elapsed < 0.1, f"Query too slow: {elapsed}s"
```

- [ ] Performance acceptable

### Memory Usage

- [ ] No memory leaks
- [ ] Large result sets handled efficiently

```python
# Test with large dataset
for i in range(1000):
    assignment = ab_manager.assign_photo_to_variant(test.id, i)
    ab_manager.record_result(test.id, i, True, 5.0)

# Check memory usage is reasonable
```

- [ ] Memory usage acceptable

## Documentation

- [ ] README updated with A/B testing info
- [ ] API documentation complete
- [ ] Usage examples provided
- [ ] Integration guide available
- [ ] Troubleshooting guide available

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Integration verified
- [ ] Performance acceptable
- [ ] Documentation complete

### Deployment

- [ ] Database migration applied to production
- [ ] Code deployed
- [ ] Configuration updated
- [ ] Monitoring enabled

### Post-Deployment

- [ ] Create first production A/B test
- [ ] Monitor for errors
- [ ] Verify data is being recorded
- [ ] Check report generation

## Monitoring

### Metrics to Track

- [ ] Number of active tests
- [ ] Total assignments per day
- [ ] Results recorded per day
- [ ] Average test duration
- [ ] Winner determination rate

### Alerts

- [ ] Alert on test creation failures
- [ ] Alert on assignment failures
- [ ] Alert on result recording failures
- [ ] Alert on analysis errors

## Rollback Plan

If issues occur:

1. [ ] Pause all active tests
2. [ ] Stop assigning new photos
3. [ ] Investigate errors
4. [ ] Fix issues
5. [ ] Resume tests

Emergency rollback:
```python
# Pause all active tests
active_tests = ab_manager.list_ab_tests(status='active')
for test in active_tests:
    ab_manager.pause_ab_test(test.id)
```

## Success Criteria

- [ ] Can create and manage A/B tests
- [ ] Photos are assigned and processed correctly
- [ ] Results are recorded accurately
- [ ] Statistical analysis works correctly
- [ ] Reports are generated successfully
- [ ] Integration with existing systems works
- [ ] Performance is acceptable
- [ ] No critical bugs
- [ ] Documentation is complete

## Sign-Off

- [ ] Developer: Implementation complete
- [ ] QA: Testing complete
- [ ] Product: Requirements met
- [ ] DevOps: Deployment ready

## Notes

_Add any integration-specific notes or issues here_

---

**Integration Date**: ___________  
**Completed By**: ___________  
**Verified By**: ___________
