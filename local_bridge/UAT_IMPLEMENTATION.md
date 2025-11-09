# User Acceptance Testing (UAT) Implementation

## Overview

本ドキュメントは、Junmai AutoDev システムのユーザー受け入れテスト（UAT）の実装と実行方法を説明します。

## 目的

UATは以下の3つの主要な測定を行います：

1. **実環境での100枚テスト**: 実際の写真を使用した処理性能の検証
2. **承認率の測定**: AI選別とプリセット選択の精度評価
3. **時間削減効果の測定**: 従来手法との比較による効率化の定量評価

## Requirements

- Python 3.8+
- SQLite3
- 実際の写真ファイル（RAW/JPEG）100枚以上
- 必要なコンポーネント:
  - `exif_analyzer.py`
  - `ai_selector.py`
  - `context_engine.py`
  - `preset_engine.py`
  - `ollama_client.py`

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   UAT Test Runner                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Photo Collection                                    │
│     └─> Scan test directory for RAW/JPEG files         │
│                                                          │
│  2. Processing Pipeline                                 │
│     ├─> EXIF Analysis                                   │
│     ├─> AI Evaluation                                   │
│     ├─> Context Determination                           │
│     └─> Preset Selection                                │
│                                                          │
│  3. Approval Simulation/Manual                          │
│     └─> User approval based on AI scores                │
│                                                          │
│  4. Metrics Collection                                  │
│     ├─> Processing times                                │
│     ├─> Approval rates                                  │
│     └─> Time savings calculation                        │
│                                                          │
│  5. Report Generation                                   │
│     ├─> Console output                                  │
│     ├─> JSON report                                     │
│     └─> SQLite database                                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Database Schema

### uat_results Table

```sql
CREATE TABLE uat_results (
    id INTEGER PRIMARY KEY,
    test_run_id TEXT NOT NULL,
    photo_path TEXT NOT NULL,
    photo_name TEXT NOT NULL,
    
    -- Timing metrics
    import_time REAL,
    exif_analysis_time REAL,
    ai_evaluation_time REAL,
    context_determination_time REAL,
    preset_selection_time REAL,
    total_processing_time REAL,
    
    -- AI evaluation
    ai_score REAL,
    focus_score REAL,
    exposure_score REAL,
    composition_score REAL,
    
    -- Context and preset
    detected_context TEXT,
    selected_preset TEXT,
    
    -- User approval
    user_approved BOOLEAN,
    user_rating INTEGER,
    user_feedback TEXT,
    approval_timestamp TIMESTAMP,
    
    -- Error tracking
    processing_error TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### uat_test_runs Table

```sql
CREATE TABLE uat_test_runs (
    id TEXT PRIMARY KEY,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_photos INTEGER,
    processed_photos INTEGER,
    failed_photos INTEGER,
    avg_processing_time REAL,
    approval_rate REAL,
    time_savings_percent REAL,
    notes TEXT
);
```

## Usage

### 1. Automated Test Run

```bash
# Run with default settings (100 photos)
py local_bridge/uat_test_runner.py

# Specify custom photo directory
py local_bridge/uat_test_runner.py --photos-dir D:/Photos/TestSet

# Test with specific number of photos
py local_bridge/uat_test_runner.py --num-photos 50

# Custom database path
py local_bridge/uat_test_runner.py --db-path data/my_uat.db
```

### 2. Manual Approval Interface

```bash
# Run manual approval for a test run
py local_bridge/uat_manual_approval.py UAT_20251109_143022

# With custom database
py local_bridge/uat_manual_approval.py UAT_20251109_143022 --db-path data/uat_test.db
```

## Test Workflow

### Phase 1: Preparation

1. **Prepare Test Photos**
   ```bash
   mkdir -p data/test_photos
   # Copy 100+ representative photos to this directory
   ```

2. **Verify Components**
   ```bash
   py -c "from local_bridge.exif_analyzer import EXIFAnalyzer; print('OK')"
   py -c "from local_bridge.ai_selector import AISelector; print('OK')"
   ```

### Phase 2: Execution

1. **Run Automated Test**
   ```bash
   py local_bridge/uat_test_runner.py --photos-dir data/test_photos --num-photos 100
   ```

2. **Monitor Progress**
   - Watch console output for real-time progress
   - Check for any errors or warnings
   - Note processing times per photo

### Phase 3: Analysis

1. **Review Console Report**
   - Success rate
   - Average processing time
   - Approval rate (simulated)
   - Time savings percentage

2. **Check JSON Report**
   ```bash
   cat data/uat_report_UAT_*.json
   ```

3. **Query Database**
   ```sql
   -- Get test run summary
   SELECT * FROM uat_test_runs ORDER BY start_time DESC LIMIT 1;
   
   -- Get detailed results
   SELECT photo_name, ai_score, detected_context, 
          total_processing_time, user_approved
   FROM uat_results
   WHERE test_run_id = 'UAT_20251109_143022'
   ORDER BY ai_score DESC;
   
   -- Calculate approval rate by AI score range
   SELECT 
       CASE 
           WHEN ai_score >= 4.0 THEN '4.0-5.0'
           WHEN ai_score >= 3.5 THEN '3.5-4.0'
           WHEN ai_score >= 3.0 THEN '3.0-3.5'
           ELSE '<3.0'
       END as score_range,
       COUNT(*) as total,
       SUM(CASE WHEN user_approved = 1 THEN 1 ELSE 0 END) as approved,
       ROUND(AVG(CASE WHEN user_approved = 1 THEN 1.0 ELSE 0.0 END) * 100, 1) as approval_rate
   FROM uat_results
   WHERE test_run_id = 'UAT_20251109_143022'
   GROUP BY score_range;
   ```

## Metrics Collected

### 1. Processing Performance

- **Total Processing Time**: End-to-end time per photo
- **Component Breakdown**:
  - EXIF Analysis Time
  - AI Evaluation Time
  - Context Determination Time
  - Preset Selection Time
- **Statistics**: Average, Min, Max, Median

### 2. Approval Rate

- **Overall Approval Rate**: Percentage of photos approved
- **By AI Score Range**: Approval rate segmented by AI score
- **By Context**: Approval rate per detected context
- **By Preset**: Approval rate per selected preset

### 3. Time Savings

- **Traditional Method**: 
  - Manual selection: 2 hours (100 photos)
  - Manual development: 1 hour
  - Total: 3 hours (180 minutes)

- **New System**:
  - Automated processing: ~5 seconds per photo
  - Manual approval: ~5 seconds per photo
  - Total: ~17 minutes for 100 photos

- **Time Savings**: ~163 minutes (90.6% reduction)

## Success Criteria

### Primary Goals

1. ✓ **Approval Rate > 80%**
   - AI-selected photos should be approved by users at least 80% of the time

2. ✓ **Time Savings > 90%**
   - System should reduce total workflow time by at least 90%

3. ✓ **Success Rate > 95%**
   - At least 95% of photos should process without errors

4. ✓ **Average Processing < 5 seconds**
   - Each photo should be processed in under 5 seconds on average

### Secondary Goals

- AI Score Accuracy: Correlation between AI score and user rating > 0.7
- Context Detection Accuracy: > 85% correct context identification
- Preset Selection Accuracy: > 80% appropriate preset selection

## Troubleshooting

### Common Issues

1. **No Photos Found**
   ```
   Solution: Verify test_photos directory exists and contains image files
   ```

2. **Component Import Errors**
   ```
   Solution: Ensure all required modules are in the same directory
   ```

3. **Database Locked**
   ```
   Solution: Close any other connections to the database
   ```

4. **Slow Processing**
   ```
   Solution: Check GPU availability and Ollama service status
   ```

## Example Output

```
============================================================
  Junmai AutoDev - User Acceptance Test
============================================================

Test Run ID: UAT_20251109_143022
Target Photos: 100
Test Photos Directory: data/test_photos

✓ Found 100 photos for testing

------------------------------------------------------------
Processing Photos...
------------------------------------------------------------

[1/100] Processing: IMG_5432.CR3
  ✓ Processed in 4.23s
  AI Score: 4.2★
  Context: backlit_portrait

[2/100] Processing: IMG_5433.CR3
  ✓ Processed in 3.87s
  AI Score: 3.8★
  Context: landscape_sky

...

============================================================
  USER ACCEPTANCE TEST RESULTS
============================================================

Test Run ID: UAT_20251109_143022
Test Duration: 456.3 seconds

--- Photo Processing ---
Total Photos: 100
Successfully Processed: 98
Failed: 2
Success Rate: 98.0%

--- Processing Performance ---
Average Time per Photo: 4.12s
Fastest: 2.34s
Slowest: 7.89s
Average AI Score: 3.78★

--- Approval Rate ---
Approved: 82 (83.7%)
Rejected: 16

--- Time Savings ---
Traditional Method: 180 minutes
New System: 15.3 minutes
Time Saved: 164.7 minutes
Efficiency Gain: 91.5%

--- Goal Achievement ---
  ✓ Approval Rate > 80%: 83.7%
  ✓ Time Savings > 90%: 91.5%
  ✓ Success Rate > 95%: 98.0%
  ✓ Avg Processing < 5s: 4.12s

============================================================

✓ Detailed report saved: data/uat_report_UAT_20251109_143022.json
✓ Database: data/uat_test.db

✓ UAT PASSED - All goals achieved!
```

## Integration with CI/CD

```yaml
# .github/workflows/uat.yml
name: User Acceptance Test

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  uat:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Prepare test photos
      run: |
        # Download or generate test photos
        mkdir -p data/test_photos
    
    - name: Run UAT
      run: |
        py local_bridge/uat_test_runner.py --num-photos 50
    
    - name: Upload results
      uses: actions/upload-artifact@v2
      with:
        name: uat-results
        path: data/uat_report_*.json
```

## Next Steps

After successful UAT:

1. **Document Results**: Create summary report for stakeholders
2. **Identify Improvements**: Analyze failed cases and low approval rates
3. **Optimize Parameters**: Adjust AI thresholds and preset mappings
4. **Production Deployment**: Roll out to production environment
5. **Continuous Monitoring**: Set up ongoing performance tracking

## Related Files

- `uat_test_runner.py`: Main test execution script
- `uat_manual_approval.py`: Manual approval interface
- `UAT_QUICK_START.md`: Quick start guide
- `UAT_RESULTS_TEMPLATE.md`: Results documentation template
