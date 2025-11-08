# Job Queue Implementation - Celery + Redis

## Overview

This document describes the implementation of the background job queue system using Celery and Redis for the Junmai AutoDev project.

**Requirements Addressed:**
- 4.1: Background job execution
- 4.2: Retry logic with exponential backoff
- 4.4: Priority queue management

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Flask API Server                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Job Queue Manager (job_queue_manager.py)       │ │
│  │  - Submit jobs                                         │ │
│  │  - Track status                                        │ │
│  │  - Manage priorities                                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Redis Message Broker                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ High Priority│  │Medium Priority│  │ Low Priority │      │
│  │   Queue      │  │    Queue      │  │    Queue     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Celery Workers                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Task Execution (celery_tasks.py)          │ │
│  │  - process_photo_task                                  │ │
│  │  - analyze_exif_task                                   │ │
│  │  - evaluate_quality_task                               │ │
│  │  - group_similar_photos_task                           │ │
│  │  - apply_preset_task                                   │ │
│  │  - export_photo_task                                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Celery Configuration (`celery_config.py`)

Configures Celery with:
- Redis as message broker and result backend
- Priority queues (high, medium, low, default)
- Task routing based on task type
- Retry settings with exponential backoff
- Worker concurrency and resource limits
- Periodic tasks (cleanup, metrics)

**Key Configuration:**
```python
# Priority queues with max priority levels
task_queues=(
    Queue('high_priority', routing_key='high', 
          queue_arguments={'x-max-priority': 10}),
    Queue('medium_priority', routing_key='medium',
          queue_arguments={'x-max-priority': 5}),
    Queue('low_priority', routing_key='low',
          queue_arguments={'x-max-priority': 1}),
)

# Retry settings
task_acks_late=True
task_reject_on_worker_lost=True
```

### 2. Celery Tasks (`celery_tasks.py`)

Defines all background tasks:

#### Main Tasks

1. **process_photo_task**: Complete photo processing pipeline
   - EXIF analysis
   - Quality evaluation
   - Context recognition
   - Preset selection

2. **analyze_exif_task**: Extract and analyze EXIF metadata

3. **evaluate_quality_task**: AI-based quality evaluation

4. **group_similar_photos_task**: Group similar photos in session

5. **apply_preset_task**: Apply preset to photo (creates Lightroom job)

6. **export_photo_task**: Export photo with specified preset

#### Periodic Tasks

1. **cleanup_old_results**: Clean up expired task results

2. **update_system_metrics**: Collect system performance metrics

#### Base Task Class

All tasks inherit from `BaseTask` which provides:
- Automatic retry with exponential backoff (max 3 retries)
- Error logging and tracking
- Database status updates
- Retry count tracking

```python
class BaseTask(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600  # Max 10 minutes
    retry_jitter = True
```

### 3. Job Queue Manager (`job_queue_manager.py`)

High-level interface for queue operations:

#### Methods

- `submit_photo_processing()`: Submit single photo with priority
- `submit_batch_processing()`: Submit multiple photos
- `submit_session_processing()`: Submit entire session
- `get_job_status()`: Get task status
- `get_queue_stats()`: Get queue statistics
- `cancel_job()`: Cancel pending/running job
- `pause_queue()`: Pause processing
- `resume_queue()`: Resume processing
- `get_worker_stats()`: Get worker statistics
- `get_failed_jobs()`: Get list of failed jobs
- `retry_failed_job()`: Retry a failed job
- `purge_queue()`: Clear all pending tasks

### 4. Worker Startup Script (`start_worker.py`)

Command-line script to start Celery workers:

```bash
# Start worker with default settings
python start_worker.py

# Start with custom concurrency
python start_worker.py --concurrency 5

# Start with specific queues
python start_worker.py --queues high_priority,medium_priority

# Start with debug logging
python start_worker.py --loglevel DEBUG
```

## Priority System

### Priority Calculation

Priority is calculated based on:

1. **User-requested jobs**: Always HIGH priority (9)
2. **AI score >= 4.5**: HIGH priority (9)
3. **AI score 3.5-4.5**: MEDIUM priority (5)
4. **AI score < 3.5**: LOW priority (1)
5. **No AI score**: MEDIUM priority (5)

```python
def get_priority_for_photo(ai_score: float = None, user_requested: bool = False) -> int:
    if user_requested:
        return PRIORITY_HIGH  # 9
    
    if ai_score is not None:
        if ai_score >= 4.5:
            return PRIORITY_HIGH  # 9
        elif ai_score >= 3.5:
            return PRIORITY_MEDIUM  # 5
        else:
            return PRIORITY_LOW  # 1
    
    return PRIORITY_MEDIUM  # 5
```

### Queue Routing

Tasks are automatically routed to appropriate queues:

- `analyze_exif_task` → high_priority
- `apply_preset_task` → high_priority
- `process_photo_task` → medium_priority
- `evaluate_quality_task` → medium_priority
- `group_similar_photos_task` → low_priority
- `export_photo_task` → low_priority

## Retry Logic

### Automatic Retry

All tasks automatically retry on failure with:
- **Max retries**: 3
- **Backoff**: Exponential with jitter
- **Max backoff**: 600 seconds (10 minutes)

### Retry Flow

```
Task Fails
    ↓
Retry 1 (after ~2 seconds)
    ↓ (if fails)
Retry 2 (after ~4 seconds)
    ↓ (if fails)
Retry 3 (after ~8 seconds)
    ↓ (if fails)
Mark as FAILED
    ↓
Log error
Update database
Notify user
```

### Manual Retry

Failed jobs can be manually retried via API:

```bash
POST /queue/retry/{task_id}
```

## API Endpoints

### Job Submission

```bash
# Submit single photo
POST /queue/submit
{
  "photo_id": 123,
  "user_requested": false,
  "config": {...}
}

# Submit batch
POST /queue/batch
{
  "photo_ids": [123, 124, 125],
  "priority": 5
}

# Submit session
POST /queue/session/456
{
  "auto_select": true
}
```

### Job Status

```bash
# Get job status
GET /queue/status/{task_id}

# Get queue statistics
GET /queue/stats

# Get worker statistics
GET /queue/workers

# Get failed jobs
GET /queue/failed?limit=50
```

### Queue Management

```bash
# Cancel job
POST /queue/cancel/{task_id}

# Pause queue
POST /queue/pause

# Resume queue
POST /queue/resume

# Purge queue
POST /queue/purge
{
  "queue_name": "low_priority"  # optional
}

# Retry failed job
POST /queue/retry/{task_id}
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- celery==5.4.0
- redis==5.2.1
- kombu==5.4.2

### 2. Install and Start Redis

**Windows (using WSL):**
```bash
wsl --install
wsl -d Ubuntu -e sudo apt-get install redis-server
wsl -d Ubuntu -e redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

### 3. Start Celery Worker

```bash
cd local_bridge
python start_worker.py
```

### 4. Start Flask API Server

```bash
python app.py
```

## Configuration

### Environment Variables

```bash
# Redis connection
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=  # optional

# Worker settings (can also be set in config.json)
export CELERY_CONCURRENCY=3
export CELERY_LOGLEVEL=INFO
```

### Config File (`config.json`)

```json
{
  "processing": {
    "max_concurrent_jobs": 3,
    "cpu_limit_percent": 80,
    "gpu_temp_limit_celsius": 75
  }
}
```

## Monitoring

### Queue Statistics

```python
from job_queue_manager import get_job_queue_manager

manager = get_job_queue_manager()
stats = manager.get_queue_stats()

print(f"Active tasks: {stats['active_tasks']}")
print(f"Pending tasks: {stats['total_pending']}")
print(f"Jobs by status: {stats['jobs_by_status']}")
```

### Worker Health

```python
worker_stats = manager.get_worker_stats()
print(f"Workers: {worker_stats['workers']}")
print(f"Active tasks: {worker_stats['active_tasks']}")
```

### Failed Jobs

```python
failed = manager.get_failed_jobs(limit=10)
for job in failed:
    print(f"Job {job['id']}: {job['error_message']}")
```

## Testing

Run the test suite:

```bash
pytest test_job_queue.py -v
```

Tests cover:
- Priority calculation
- Job submission
- Status tracking
- Queue management
- Retry logic
- Worker statistics

## Performance Considerations

### Resource Management

1. **Concurrency**: Default 3 workers (configurable)
2. **Memory**: Workers restart after 100 tasks to prevent leaks
3. **CPU**: Monitoring and throttling based on system load
4. **GPU**: Temperature monitoring and throttling

### Optimization Tips

1. **Batch Processing**: Use batch submission for multiple photos
2. **Priority Tuning**: Adjust priorities based on workflow
3. **Worker Scaling**: Increase concurrency for high loads
4. **Queue Purging**: Clear low-priority queue during peak times

## Troubleshooting

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping
# Should return: PONG

# Check Redis connection
redis-cli -h localhost -p 6379
```

### Worker Not Starting

```bash
# Check Celery configuration
python -c "from celery_config import app; print(app.conf)"

# Start worker with debug logging
python start_worker.py --loglevel DEBUG
```

### Tasks Not Processing

```bash
# Check queue status
curl http://localhost:5100/queue/stats

# Check worker status
curl http://localhost:5100/queue/workers

# Purge stuck tasks
curl -X POST http://localhost:5100/queue/purge
```

### High Memory Usage

```bash
# Reduce concurrency
python start_worker.py --concurrency 2

# Reduce max tasks per child
# Edit celery_config.py:
worker_max_tasks_per_child=50
```

## Future Enhancements

1. **Distributed Workers**: Support multiple worker machines
2. **Task Chaining**: Complex workflows with task dependencies
3. **Result Caching**: Cache expensive computations
4. **Dynamic Scaling**: Auto-scale workers based on load
5. **Advanced Monitoring**: Prometheus/Grafana integration
6. **Task Prioritization**: ML-based priority prediction

## References

- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [Kombu Documentation](https://kombu.readthedocs.io/)

## Support

For issues or questions:
1. Check logs: `local_bridge/logs/`
2. Review queue stats: `GET /queue/stats`
3. Check worker health: `GET /queue/workers`
4. Review failed jobs: `GET /queue/failed`
