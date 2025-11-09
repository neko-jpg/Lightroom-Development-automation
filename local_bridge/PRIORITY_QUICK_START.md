# Priority Management Quick Start Guide

## Overview

The Priority Management System ensures fair and efficient job processing by dynamically calculating and adjusting job priorities based on multiple factors.

## Quick Start

### 1. Basic Usage (Python)

```python
from priority_manager import get_priority_manager
from job_queue_manager import get_job_queue_manager

# Get manager instances
priority_mgr = get_priority_manager()
job_queue = get_job_queue_manager()

# Submit a job (priority calculated automatically)
task_id = job_queue.submit_photo_processing(
    photo_id=123,
    user_requested=True  # High priority
)

# Check priority distribution
distribution = job_queue.get_priority_distribution()
print(f"Average priority: {distribution['average_priority']}")
```

### 2. Basic Usage (REST API)

```bash
# Submit a job
curl -X POST http://localhost:5100/queue/submit \
  -H "Content-Type: application/json" \
  -d '{"photo_id": 123, "user_requested": true}'

# Check priority distribution
curl http://localhost:5100/queue/priority/distribution

# Adjust job priority
curl -X PUT http://localhost:5100/queue/priority/abc123 \
  -H "Content-Type: application/json" \
  -d '{"priority": 8}'
```

## Common Operations

### Adjust Job Priority

```python
# Increase priority for urgent job
job_queue.adjust_job_priority("job_id_123", new_priority=9)
```

```bash
curl -X PUT http://localhost:5100/queue/priority/job_id_123 \
  -H "Content-Type: application/json" \
  -d '{"priority": 9}'
```

### Boost Session Priority

```python
# Boost all jobs in a session
job_queue.boost_session_priority(session_id=5, boost_amount=2)
```

```bash
curl -X POST http://localhost:5100/queue/priority/session/5/boost \
  -H "Content-Type: application/json" \
  -d '{"boost_amount": 2}'
```

### Rebalance Queue

```python
# Rebalance all pending jobs
stats = job_queue.rebalance_priorities()
print(f"Adjusted {stats['adjusted_count']} jobs")
```

```bash
curl -X POST http://localhost:5100/queue/priority/rebalance
```

### Check for Starving Jobs

```python
# Find jobs waiting too long
candidates = job_queue.get_starvation_candidates(age_threshold_hours=12)
print(f"Found {len(candidates)} starving jobs")

# Auto-boost them
stats = job_queue.auto_boost_starving_jobs(age_threshold_hours=12)
print(f"Boosted {stats['boosted_count']} jobs")
```

```bash
# Check starvation
curl http://localhost:5100/queue/priority/starvation?age_threshold_hours=12

# Auto-boost
curl -X POST http://localhost:5100/queue/priority/auto-boost \
  -H "Content-Type: application/json" \
  -d '{"age_threshold_hours": 12}'
```

## Priority Levels

| Priority | Description | Use Case |
|----------|-------------|----------|
| 9-10 | High | User-requested, high-quality photos, urgent sessions |
| 5-8 | Medium | Good quality photos, normal processing |
| 1-4 | Low | Low quality photos, background processing |

## Priority Factors

Jobs are prioritized based on:

1. **AI Score (40%)**: Photo quality evaluation
2. **Age (30%)**: How long the job has been waiting
3. **User Request (20%)**: Manually requested jobs
4. **Context (10%)**: Photo context (wedding, portrait, etc.)

## Automatic Features

### Age-Based Boost
- Jobs automatically get +0.1 priority per hour
- Maximum boost: +2.4 (after 24 hours)
- Prevents job starvation

### Starvation Prevention
- Jobs waiting >12 hours are automatically detected
- Can be auto-boosted with one command
- Configurable threshold

## Monitoring

### Check Queue Health

```python
# Get priority distribution
distribution = job_queue.get_priority_distribution()
print(f"Total pending: {distribution['total_pending']}")
print(f"Average priority: {distribution['average_priority']:.2f}")
print(f"Distribution: {distribution['by_priority']}")
```

### Monitor Starvation

```python
# Regular check (e.g., every 30 minutes)
candidates = job_queue.get_starvation_candidates(age_threshold_hours=12)
if candidates:
    print(f"WARNING: {len(candidates)} jobs are starving!")
    # Auto-boost or alert
    job_queue.auto_boost_starving_jobs(age_threshold_hours=12)
```

## Best Practices

### 1. Regular Rebalancing
Run every 1-2 hours to keep priorities current:
```python
# In a scheduled task
job_queue.rebalance_priorities()
```

### 2. Monitor Starvation
Check every 30 minutes:
```python
candidates = job_queue.get_starvation_candidates(age_threshold_hours=12)
if len(candidates) > 5:
    job_queue.auto_boost_starving_jobs(age_threshold_hours=12)
```

### 3. Boost Urgent Sessions
When user marks a session as urgent:
```python
job_queue.boost_session_priority(session_id, boost_amount=3)
```

### 4. Monitor Queue Balance
Check distribution regularly:
```python
distribution = job_queue.get_priority_distribution()
if distribution['average_priority'] < 3:
    # Queue is mostly low priority, consider rebalancing
    job_queue.rebalance_priorities()
```

## Configuration

Customize priority calculation weights:

```python
priority_mgr.update_config({
    'ai_score_weight': 0.5,      # Increase AI score importance
    'age_weight': 0.25,           # Decrease age importance
    'age_boost_per_hour': 0.15,  # Faster age boost
    'max_age_hours': 48           # Longer max age
})
```

## Troubleshooting

### Jobs Not Processing
1. Check priority distribution
2. Look for starvation candidates
3. Rebalance queue
4. Boost session if needed

### Unbalanced Queue
1. Run rebalancing
2. Check configuration weights
3. Adjust age boost parameters

### Priority Not Updating
1. Verify job exists and is 'pending'
2. Check priority value is 1-10
3. Check logs for errors

## Integration Example

Complete workflow:

```python
from job_queue_manager import get_job_queue_manager

job_queue = get_job_queue_manager()

# 1. Submit photos for processing
task_ids = job_queue.submit_batch_processing(
    photo_ids=[1, 2, 3, 4, 5],
    priority=5  # Medium priority
)

# 2. User marks one as urgent
job_queue.adjust_job_priority(task_ids[0], new_priority=9)

# 3. Check queue health
distribution = job_queue.get_priority_distribution()
print(f"Queue status: {distribution}")

# 4. Rebalance if needed
if distribution['average_priority'] < 4:
    job_queue.rebalance_priorities()

# 5. Check for starvation
candidates = job_queue.get_starvation_candidates(age_threshold_hours=12)
if candidates:
    job_queue.auto_boost_starving_jobs(age_threshold_hours=12)
```

## API Reference

### Python API
- `calculate_priority(photo_id, user_requested, override_priority)`
- `adjust_job_priority(job_id, new_priority)`
- `rebalance_priorities()`
- `boost_session_priority(session_id, boost_amount)`
- `get_priority_distribution()`
- `get_starvation_candidates(age_threshold_hours)`
- `auto_boost_starving_jobs(age_threshold_hours)`

### REST API
- `PUT /queue/priority/{job_id}` - Adjust priority
- `POST /queue/priority/rebalance` - Rebalance queue
- `GET /queue/priority/distribution` - Get distribution
- `POST /queue/priority/session/{session_id}/boost` - Boost session
- `GET /queue/priority/starvation` - Get starvation candidates
- `POST /queue/priority/auto-boost` - Auto-boost starving jobs

## More Information

For detailed documentation, see:
- `PRIORITY_MANAGEMENT.md` - Complete system documentation
- `TASK_15_COMPLETION_SUMMARY.md` - Implementation details
- `priority_manager.py` - Source code with inline documentation

## Support

For issues or questions:
1. Check logs in `logs/main.log`
2. Review `PRIORITY_MANAGEMENT.md` troubleshooting section
3. Verify configuration with `get_priority_distribution()`
