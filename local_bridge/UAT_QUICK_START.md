# UAT Quick Start Guide

## 5-Minute Setup

### 1. Prepare Test Photos

```bash
# Create test directory
mkdir -p data/test_photos

# Copy your test photos (100+ recommended)
# RAW files: .cr3, .cr2, .nef, .arw, .dng
# JPEG files: .jpg, .jpeg
```

### 2. Run Automated Test

```bash
# Basic run (uses data/test_photos by default)
py local_bridge/uat_test_runner.py

# Custom directory
py local_bridge/uat_test_runner.py --photos-dir D:/Photos/TestSet

# Specific number of photos
py local_bridge/uat_test_runner.py --num-photos 50
```

### 3. Review Results

The test will output:
- ✓ Console report with all metrics
- ✓ JSON report: `data/uat_report_UAT_*.json`
- ✓ SQLite database: `data/uat_test.db`

## What Gets Measured

### 1. Processing Performance
- Average time per photo (Target: < 5 seconds)
- Component breakdown (EXIF, AI, Context, Preset)

### 2. Approval Rate
- Percentage of AI-selected photos approved (Target: > 80%)
- Simulated based on AI scores

### 3. Time Savings
- Traditional: 180 minutes for 100 photos
- New System: ~15 minutes
- Target: > 90% time reduction

## Success Criteria

| Metric | Target | Pass/Fail |
|--------|--------|-----------|
| Approval Rate | > 80% | ✓ / ✗ |
| Time Savings | > 90% | ✓ / ✗ |
| Success Rate | > 95% | ✓ / ✗ |
| Avg Processing | < 5s | ✓ / ✗ |

## Manual Approval (Optional)

For real user feedback:

```bash
# Get test run ID from automated test output
py local_bridge/uat_manual_approval.py UAT_20251109_143022

# Interactive approval interface
# [a] Approve, [r] Reject, [s] Skip, [q] Quit
```

## Quick Database Queries

```bash
# Open database
sqlite3 data/uat_test.db

# View latest test run
SELECT * FROM uat_test_runs ORDER BY start_time DESC LIMIT 1;

# View top 10 photos by AI score
SELECT photo_name, ai_score, detected_context, user_approved
FROM uat_results
WHERE test_run_id = 'UAT_20251109_143022'
ORDER BY ai_score DESC
LIMIT 10;

# Calculate approval rate
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN user_approved = 1 THEN 1 ELSE 0 END) as approved,
    ROUND(AVG(CASE WHEN user_approved = 1 THEN 1.0 ELSE 0.0 END) * 100, 1) as rate
FROM uat_results
WHERE test_run_id = 'UAT_20251109_143022';
```

## Troubleshooting

### No photos found
```bash
# Check directory
ls data/test_photos

# Verify file extensions
ls data/test_photos/*.cr3
ls data/test_photos/*.jpg
```

### Import errors
```bash
# Verify components
py -c "from local_bridge.exif_analyzer import EXIFAnalyzer; print('OK')"
py -c "from local_bridge.ai_selector import AISelector; print('OK')"
```

### Slow processing
- Check GPU availability
- Verify Ollama is running: `ollama list`
- Reduce number of photos: `--num-photos 10`

## Example Output

```
============================================================
  USER ACCEPTANCE TEST RESULTS
============================================================

Test Run ID: UAT_20251109_143022

--- Photo Processing ---
Total Photos: 100
Successfully Processed: 98
Success Rate: 98.0%

--- Processing Performance ---
Average Time per Photo: 4.12s

--- Approval Rate ---
Approved: 82 (83.7%)

--- Time Savings ---
Time Saved: 164.7 minutes
Efficiency Gain: 91.5%

--- Goal Achievement ---
  ✓ Approval Rate > 80%: 83.7%
  ✓ Time Savings > 90%: 91.5%
  ✓ Success Rate > 95%: 98.0%
  ✓ Avg Processing < 5s: 4.12s

✓ UAT PASSED - All goals achieved!
```

## Next Steps

1. Review detailed JSON report
2. Analyze failed cases (if any)
3. Run manual approval for real user feedback
4. Document results for stakeholders
5. Proceed to production deployment

## Full Documentation

See `UAT_IMPLEMENTATION.md` for complete details.
