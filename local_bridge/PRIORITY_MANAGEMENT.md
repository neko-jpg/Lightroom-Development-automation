# Priority Management System

## Overview

The Priority Management System provides advanced priority calculation and dynamic adjustment for the Junmai AutoDev job queue. It ensures fair processing, prevents job starvation, and optimizes resource utilization based on multiple factors.

**Requirements**: 4.4

## Features

### 1. Dynamic Priority Calculation

Calculates job priority based on multiple weighted factors:

- **AI Score (40%)**: Higher quality photos get higher priority
- **Age (30%)**: Older jobs get priority boost to prevent starvation
- **User Request (20%)**: Manually requested jobs get immediate high priority
- **Context (10%)**: Important contexts (weddings, events) get priority boost

Priority range: 1 (lowest) to 10 (highest)

### 2. Priority Adjustment

Dynamically adjust priority of existing jobs:

- Manual priority override
- Session-wide priority boost
- Automatic starvation prevention

### 3. Queue Rebalancing

Periodically recalculate priorities for all pending jobs based on:

- Current age
- Updated AI scores
- Queue state

### 4. Starvation Prevention

Automatically detect and boost jobs that have been waiting too long:

- Configurable age threshold (default: 12 hours)
- Automatic priority boost for old jobs
- Monitoring and alerting

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Priority Manager                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Priority Calculation Engine                   │  │
│  │  • AI Score Priority (40%)                           │  │
│  │  • Age Priority (30%)                                │  │
│  │  • User Request Priority (20%)                       │  │
│  │  • Context Priority (10%)                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Dynamic Adjustment                            │  │
│  │  • Manual Priority Override                          │  │
│  │  • Session Priority Boost                            │  │
│  │  • Queue Rebalancing                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Starvation Prevention                         │  │
│  │  • Age Monitoring                                    │  │
│  │  • Automatic Boost                                   │  │
│  │  • Candidate Detection                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### Python API

```python
from priority_manager import get_priority_manager

# Get priority manager instance
priority_mgr = get_priority_manager()

# Calculate priority for a photo
priority = priority_mgr.calculate_priority(
    photo_id=123,
    user_requested=False
)

# Adjust job priority
success = priority_mgr.adjust_job_priority(
    job_id="abc123",
    new_priority=8
)

# Rebalance queue priorities
stats = priority_mgr.rebalance_queue_priorities()

# Boost session priority
stats = priority_mgr.boost_session_priority(
    session_id=5,
    boost_amount=2
)

# Get priority distribution
distribution = priority_mgr.get_priority_distribution()

# Detect starvation candidates
candidates = priority_mgr.get_starvation_candidates(
    age_threshold_hours=12
)

# Auto-boost starving jobs
stats = priority_mgr.auto_boost_starving_jobs(
    age_threshold_hours=12
)
```

### REST API

#### Adjust Job Priority

```http
PUT /queue/priority/{job_id}
Content-Type: application/json

{
  "priority": 8
}
```

Response:
```json
{
  "message": "Job priority adjusted successfully",
  "job_id": "abc123",
  "new_priority": 8
}
```

#### Rebalance Queue Priorities

```http
POST /queue/priority/rebalance
```

Response:
```json
{
  "message": "Queue priorities rebalanced successfully",
  "adjusted_count": 15,
  "total_pending": 50,
  "timestamp": "2025-11-08T10:30:00Z"
}
```

#### Get Priority Distribution

```http
GET /queue/priority/distribution
```

Response:
```json
{
  "by_priority": {
    "1": 5,
    "5": 20,
    "9": 10
  },
  "total_pending": 35,
  "average_priority": 5.7,
  "timestamp": "2025-11-08T10:30:00Z"
}
```

#### Boost Session Priority

```http
POST /queue/priority/session/{session_id}/boost
Content-Type: application/json

{
  "boost_amount": 2
}
```

Response:
```json
{
  "message": "Session priority boosted by 2",
  "session_id": 5,
  "boosted_count": 12,
  "total_jobs": 12,
  "boost_amount": 2
}
```

#### Get Starvation Candidates

```http
GET /queue/priority/starvation?age_threshold_hours=12
```

Response:
```json
{
  "candidates": [
    {
      "job_id": "abc123",
      "photo_id": 456,
      "priority": 5,
      "age_hours": 15.5,
      "created_at": "2025-11-07T19:00:00Z"
    }
  ],
  "count": 1,
  "age_threshold_hours": 12
}
```

#### Auto-Boost Starving Jobs

```http
POST /queue/priority/auto-boost
Content-Type: application/json

{
  "age_threshold_hours": 12
}
```

Response:
```json
{
  "message": "Auto-boosted 3 starving jobs",
  "boosted_count": 3,
  "candidates": 3,
  "threshold_hours": 12
}
```

## Priority Calculation Details

### AI Score Mapping

| AI Score | Priority Contribution |
|----------|----------------------|
| ≥ 4.5    | 10                   |
| ≥ 4.0    | 8                    |
| ≥ 3.5    | 6                    |
| ≥ 3.0    | 5                    |
| ≥ 2.0    | 3                    |
| < 2.0    | 1                    |

### Age-Based Priority Boost

- Linear increase: 0.1 priority per hour
- Maximum boost: 2.4 (at 24 hours)
- Prevents job starvation

### Context Priority Mapping

| Context           | Priority |
|-------------------|----------|
| wedding           | 9        |
| event             | 8        |
| backlit_portrait  | 8        |
| low_light_indoor  | 7        |
| portrait          | 7        |
| landscape_sky     | 6        |
| landscape         | 5        |
| default           | 5        |

### User Request Priority

- User-requested jobs: Priority 9 (HIGH)
- Automatic jobs: Calculated based on other factors

## Configuration

Default configuration:

```python
{
    'ai_score_weight': 0.4,      # 40% weight
    'age_weight': 0.3,            # 30% weight
    'user_request_weight': 0.2,   # 20% weight
    'context_weight': 0.1,        # 10% weight
    'max_age_hours': 24,          # Max age for priority boost
    'age_boost_per_hour': 0.1,    # Priority increase per hour
}
```

Update configuration:

```python
priority_mgr.update_config({
    'ai_score_weight': 0.5,
    'age_weight': 0.25
})
```

## Best Practices

### 1. Regular Rebalancing

Run queue rebalancing periodically (e.g., every hour):

```python
# In a scheduled task
stats = priority_mgr.rebalance_queue_priorities()
```

### 2. Monitor Starvation

Check for starving jobs regularly:

```python
# Check every 30 minutes
candidates = priority_mgr.get_starvation_candidates(age_threshold_hours=12)
if candidates:
    # Alert or auto-boost
    priority_mgr.auto_boost_starving_jobs(age_threshold_hours=12)
```

### 3. Session Priority Management

Boost priority for urgent sessions:

```python
# User marks session as urgent
priority_mgr.boost_session_priority(session_id, boost_amount=3)
```

### 4. Priority Distribution Monitoring

Monitor queue balance:

```python
distribution = priority_mgr.get_priority_distribution()
if distribution['average_priority'] < 3:
    # Queue is mostly low priority, consider rebalancing
    priority_mgr.rebalance_queue_priorities()
```

## Integration with Job Queue

The Priority Manager integrates seamlessly with the Job Queue Manager:

```python
from job_queue_manager import get_job_queue_manager

job_queue = get_job_queue_manager()

# Submit job with calculated priority
task_id = job_queue.submit_photo_processing(
    photo_id=123,
    user_requested=True  # Will get high priority
)

# Adjust priority later
job_queue.adjust_job_priority(task_id, new_priority=8)

# Rebalance all priorities
job_queue.rebalance_priorities()
```

## Performance Considerations

### Priority Calculation

- O(1) for single photo priority calculation
- Database query required to fetch photo data
- Cached results recommended for repeated calculations

### Queue Rebalancing

- O(n) where n = number of pending jobs
- Should be run during low-activity periods
- Recommended frequency: every 1-2 hours

### Starvation Detection

- O(n) where n = number of pending jobs
- Efficient database query with timestamp index
- Recommended frequency: every 30 minutes

## Monitoring and Metrics

### Key Metrics

1. **Average Priority**: Overall queue priority level
2. **Priority Distribution**: Jobs per priority level
3. **Starvation Count**: Jobs waiting beyond threshold
4. **Rebalancing Frequency**: How often priorities are adjusted
5. **Boost Operations**: Manual and automatic priority boosts

### Logging

All priority operations are logged:

```
INFO: Priority calculated (photo_id=123, final_priority=8)
INFO: Job priority adjusted (job_id=abc123, old_priority=5, new_priority=8)
INFO: Queue priority rebalancing completed (adjusted_count=15, total_pending=50)
WARNING: Starvation candidates detected (count=3, threshold_hours=12)
INFO: Auto-boost completed for starving jobs (boosted_count=3)
```

## Troubleshooting

### Jobs Not Processing

1. Check priority distribution
2. Look for starvation candidates
3. Rebalance queue priorities
4. Boost session priority if needed

### Unbalanced Queue

1. Run rebalancing
2. Check configuration weights
3. Adjust age boost parameters

### Priority Not Updating

1. Verify job exists in database
2. Check job status (must be 'pending')
3. Verify priority value is in range 1-10

## Future Enhancements

1. **Machine Learning**: Learn optimal priority weights from historical data
2. **Resource-Based Priority**: Adjust based on system load
3. **Deadline Support**: Priority boost for jobs with deadlines
4. **User Preferences**: Per-user priority customization
5. **Priority Decay**: Gradually reduce priority of repeatedly failed jobs

## References

- Requirements: 4.4 (Priority Management)
- Related: Job Queue Manager, Celery Configuration
- Database: Job and Photo models
