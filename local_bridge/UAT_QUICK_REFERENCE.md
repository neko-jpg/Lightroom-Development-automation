# UAT Quick Reference

## Commands

### Run Automated Test
```bash
# Default (100 photos from data/test_photos)
py local_bridge/uat_test_runner.py

# Custom directory
py local_bridge/uat_test_runner.py --photos-dir D:/Photos/TestSet

# Specific number
py local_bridge/uat_test_runner.py --num-photos 50

# Custom database
py local_bridge/uat_test_runner.py --db-path data/my_uat.db
```

### Run Manual Approval
```bash
py local_bridge/uat_manual_approval.py UAT_20251109_143022
```

### Run Unit Tests
```bash
py local_bridge/test_uat_runner.py
```

## Database Queries

### Latest Test Run
```sql
SELECT * FROM uat_test_runs ORDER BY start_time DESC LIMIT 1;
```

### Top Photos by AI Score
```sql
SELECT photo_name, ai_score, detected_context, user_approved
FROM uat_results
WHERE test_run_id = 'UAT_20251109_143022'
ORDER BY ai_score DESC LIMIT 10;
```

### Approval Rate
```sql
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN user_approved = 1 THEN 1 ELSE 0 END) as approved,
    ROUND(AVG(CASE WHEN user_approved = 1 THEN 1.0 ELSE 0.0 END) * 100, 1) as rate
FROM uat_results
WHERE test_run_id = 'UAT_20251109_143022';
```

### Processing Time Stats
```sql
SELECT 
    AVG(total_processing_time) as avg,
    MIN(total_processing_time) as min,
    MAX(total_processing_time) as max
FROM uat_results
WHERE test_run_id = 'UAT_20251109_143022'
AND processing_error IS NULL;
```

### Approval by Score Range
```sql
SELECT 
    CASE 
        WHEN ai_score >= 4.0 THEN '4.0-5.0'
        WHEN ai_score >= 3.5 THEN '3.5-4.0'
        WHEN ai_score >= 3.0 THEN '3.0-3.5'
        ELSE '<3.0'
    END as range,
    COUNT(*) as total,
    SUM(CASE WHEN user_approved = 1 THEN 1 ELSE 0 END) as approved
FROM uat_results
WHERE test_run_id = 'UAT_20251109_143022'
GROUP BY range;
```

## Success Criteria

| Metric | Target | Check |
|--------|--------|-------|
| Approval Rate | > 80% | ✓ / ✗ |
| Time Savings | > 90% | ✓ / ✗ |
| Success Rate | > 95% | ✓ / ✗ |
| Avg Processing | < 5s | ✓ / ✗ |

## Files

- `uat_test_runner.py` - Main test runner
- `uat_manual_approval.py` - Manual approval interface
- `test_uat_runner.py` - Unit tests
- `UAT_IMPLEMENTATION.md` - Full documentation
- `UAT_QUICK_START.md` - Quick start guide
- `TASK_51_COMPLETION_SUMMARY.md` - Completion summary

## Troubleshooting

### No photos found
```bash
ls data/test_photos/*.jpg
ls data/test_photos/*.cr3
```

### Import errors
```bash
py -c "from local_bridge.exif_analyzer import EXIFAnalyzer; print('OK')"
```

### Database locked
```bash
# Close all connections, then:
rm data/uat_test.db
py local_bridge/uat_test_runner.py
```

## Example Output

```
============================================================
  USER ACCEPTANCE TEST RESULTS
============================================================

--- Photo Processing ---
Total Photos: 100
Successfully Processed: 98
Success Rate: 98.0%

--- Processing Performance ---
Average Time per Photo: 4.12s

--- Approval Rate ---
Approved: 82 (83.7%)

--- Time Savings ---
Efficiency Gain: 91.5%

--- Goal Achievement ---
  ✓ Approval Rate > 80%: 83.7%
  ✓ Time Savings > 90%: 91.5%
  ✓ Success Rate > 95%: 98.0%
  ✓ Avg Processing < 5s: 4.12s

✓ UAT PASSED - All goals achieved!
```

## Python API

```python
from uat_test_runner import UATTestRunner

# Create runner
runner = UATTestRunner('data/test_photos', 'data/uat_test.db')

# Run test
summary = runner.run_full_test(num_photos=100)

# Access results
print(f"Approval Rate: {summary['approval_rate']:.1f}%")
print(f"Time Savings: {summary['time_savings_percent']:.1f}%")
```

## Integration

```python
# In your CI/CD pipeline
import sys
from uat_test_runner import UATTestRunner

runner = UATTestRunner('test_photos', 'uat.db')
summary = runner.run_full_test(50)

# Exit with error if goals not met
if summary['approval_rate'] < 80 or summary['time_savings_percent'] < 90:
    sys.exit(1)
```
