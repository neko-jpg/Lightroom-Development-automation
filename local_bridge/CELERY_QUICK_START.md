# Celery + Redis Job Queue - Quick Start Guide

## Prerequisites

1. **Python 3.11+** installed
2. **Redis server** (one of the following):
   - WSL with Redis
   - Docker with Redis
   - Memurai (Windows native)

## Installation

### Step 1: Install Python Dependencies

```bash
cd local_bridge
pip install -r requirements.txt
```

This installs:
- `celery==5.4.0` - Task queue framework
- `redis==5.2.1` - Redis client
- `kombu==5.4.2` - Messaging library

### Step 2: Install and Start Redis

#### Option A: Using WSL (Recommended for Windows)

```bash
# Install WSL if not already installed
wsl --install

# Install Redis in WSL
wsl -d Ubuntu -e sudo apt-get update
wsl -d Ubuntu -e sudo apt-get install redis-server -y

# Start Redis server
wsl -d Ubuntu -e redis-server
```

#### Option B: Using Docker

```bash
# Pull Redis image
docker pull redis:latest

# Run Redis container
docker run -d --name redis -p 6379:6379 redis:latest

# Check Redis is running
docker ps | findstr redis
```

#### Option C: Using Memurai (Windows Native)

1. Download from https://www.memurai.com/
2. Install and start as Windows service
3. Memurai runs on port 6379 by default

### Step 3: Verify Redis Connection

```bash
# Test Redis connection
redis-cli ping
# Should return: PONG

# Or using Python
python -c "import redis; r = redis.Redis(); print(r.ping())"
# Should return: True
```

## Running the System

### Terminal 1: Start Celery Worker

```bash
cd local_bridge

# Start worker with default settings
celery -A celery_config worker --loglevel=info

# Or with custom concurrency
celery -A celery_config worker --concurrency=3 --loglevel=info
```

You should see output like:
```
 -------------- celery@HOSTNAME v5.4.0
---- **** -----
--- * ***  * -- Windows-10.0.19045-SP0 2025-11-09 14:30:00
-- * - **** ---
- ** ---------- [config]
- ** ---------- .> app:         junmai_autodev:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 3 (prefork)
-- ******* ---- .> task events: ON
--- ***** -----
 -------------- [queues]
                .> high_priority    exchange=tasks(direct) key=high
                .> medium_priority  exchange=tasks(direct) key=medium
                .> low_priority     exchange=tasks(direct) key=low
                .> default          exchange=tasks(direct) key=default

[tasks]
  . celery_tasks.analyze_exif_task
  . celery_tasks.apply_preset_task
  . celery_tasks.cleanup_old_results
  . celery_tasks.evaluate_quality_task
  . celery_tasks.export_photo_task
  . celery_tasks.group_similar_photos_task
  . celery_tasks.process_photo_task
  . celery_tasks.update_system_metrics

[2025-11-09 14:30:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2025-11-09 14:30:00,000: INFO/MainProcess] mingle: searching for neighbors
[2025-11-09 14:30:01,000: INFO/MainProcess] mingle: all alone
[2025-11-09 14:30:01,000: INFO/MainProcess] celery@HOSTNAME ready.
```

### Terminal 2: Start Celery Beat (Optional - for periodic tasks)

```bash
cd local_bridge

# Start beat scheduler
celery -A celery_config beat --loglevel=info
```

This enables periodic tasks:
- Cleanup old results (every hour)
- Update system metrics (every minute)

## Basic Usage

### Example 1: Submit a Photo for Processing

```python
from job_queue_manager import get_job_queue_manager

# Get manager instance
manager = get_job_queue_manager()

# Submit photo for processing
task_id = manager.submit_photo_processing(
    photo_id=1,
    user_requested=True  # High priority
)

print(f"Task submitted: {task_id}")
```

### Example 2: Check Job Status

```python
# Check status
status = manager.get_job_status(task_id)

print(f"State: {status['state']}")  # PENDING, STARTED, SUCCESS, FAILURE
print(f"Ready: {status['ready']}")  # True if completed

if status['ready']:
    if status['successful']:
        print(f"Result: {status['result']}")
    else:
        print(f"Error: {status['error']}")
```

### Example 3: Process Multiple Photos

```python
# Submit batch
photo_ids = [1, 2, 3, 4, 5]
task_ids = manager.submit_batch_processing(photo_ids)

print(f"Submitted {len(task_ids)} tasks")

# Check queue stats
stats = manager.get_queue_stats()
print(f"Active tasks: {stats['active_tasks']}")
print(f"Pending tasks: {stats['total_pending']}")
```

### Example 4: Process Entire Session

```python
# Process all photos in a session
result = manager.submit_session_processing(
    session_id=1,
    auto_select=True  # Only process photos with AI score >= 3.5
)

print(f"Processing {result['photo_count']} photos")
print(f"Task IDs: {result['task_ids']}")
```

## Monitoring

### Check Queue Statistics

```python
from job_queue_manager import get_job_queue_manager

manager = get_job_queue_manager()
stats = manager.get_queue_stats()

print(f"Active tasks: {stats['active_tasks']}")
print(f"Scheduled tasks: {stats['scheduled_tasks']}")
print(f"Reserved tasks: {stats['reserved_tasks']}")
print(f"Jobs by status: {stats['jobs_by_status']}")
print(f"Jobs by priority: {stats['jobs_by_priority']}")
```

### Using Celery CLI

```bash
# List active tasks
celery -A celery_config inspect active

# List scheduled tasks
celery -A celery_config inspect scheduled

# Get worker stats
celery -A celery_config inspect stats

# Check registered tasks
celery -A celery_config inspect registered
```

### Using Flower (Web UI)

```bash
# Install Flower
pip install flower

# Start Flower
celery -A celery_config flower

# Access at http://localhost:5555
```

## Priority System

The system automatically assigns priorities based on:

1. **User-requested tasks**: Priority 9 (High)
2. **AI score >= 4.5**: Priority 9 (High)
3. **AI score 3.5-4.4**: Priority 5 (Medium)
4. **AI score < 3.5**: Priority 1 (Low)

Example:
```python
# High priority (user requested)
task_id = manager.submit_photo_processing(
    photo_id=1,
    user_requested=True
)

# Priority based on AI score
task_id = manager.submit_photo_processing(
    photo_id=2,
    user_requested=False  # Will use AI score to determine priority
)
```

## Error Handling and Retries

Tasks automatically retry on failure:
- **Max retries**: 3
- **Backoff strategy**: Exponential with jitter
- **Max backoff**: 600 seconds (10 minutes)

Example of retry behavior:
```
Attempt 1: Fails → Wait ~2-4 seconds
Attempt 2: Fails → Wait ~4-8 seconds
Attempt 3: Fails → Wait ~8-16 seconds
Attempt 4: Fails → Mark as failed, log error
```

Check failed jobs:
```python
# Get failed jobs
failed_jobs = manager.get_failed_jobs(limit=10)

for job in failed_jobs:
    print(f"Job {job['id']}: {job['error_message']}")
    print(f"Retry count: {job['retry_count']}")
```

Retry a failed job:
```python
# Retry failed job
new_task_id = manager.retry_failed_job(original_task_id)
if new_task_id:
    print(f"Job retried with new task ID: {new_task_id}")
```

## Pausing and Resuming

```python
# Pause all processing
manager.pause_queue()
print("Queue paused - no new tasks will be processed")

# Resume processing
manager.resume_queue()
print("Queue resumed - processing continues")
```

## Troubleshooting

### Problem: Worker won't start

**Solution**: Check Redis connection
```bash
redis-cli ping
# Should return: PONG
```

### Problem: Tasks not processing

**Solution**: Check worker is running and consuming from queues
```bash
celery -A celery_config inspect active_queues
```

### Problem: High memory usage

**Solution**: Reduce concurrency
```bash
celery -A celery_config worker --concurrency=2
```

### Problem: Tasks timing out

**Solution**: Increase time limits in `celery_config.py`
```python
task_soft_time_limit=600  # 10 minutes
task_time_limit=900       # 15 minutes
```

## Configuration

### Environment Variables

```bash
# Redis connection (optional, defaults shown)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Leave empty if no password
```

### Celery Settings

Edit `celery_config.py` to customize:

```python
# Worker concurrency
worker_concurrency=3  # Number of concurrent workers

# Task time limits
task_soft_time_limit=300  # 5 minutes
task_time_limit=600       # 10 minutes

# Worker settings
worker_prefetch_multiplier=1  # Tasks to prefetch
worker_max_tasks_per_child=100  # Restart after N tasks
```

## Testing

### Run Unit Tests

```bash
cd local_bridge

# Run all tests
python -m unittest test_celery_queue -v

# Run specific test
python -m unittest test_celery_queue.TestCeleryConfiguration -v
```

### Manual Testing

```python
# Test task submission
from celery_tasks import process_photo_task

result = process_photo_task.apply_async(args=[1])
print(f"Task ID: {result.id}")
print(f"State: {result.state}")

# Wait for result (blocking)
try:
    output = result.get(timeout=60)
    print(f"Result: {output}")
except Exception as e:
    print(f"Error: {e}")
```

## Next Steps

1. **Integrate with main application**: Use `JobQueueManager` in your Flask app
2. **Add monitoring**: Set up Flower for real-time monitoring
3. **Configure alerts**: Set up notifications for failed tasks
4. **Optimize performance**: Tune concurrency and time limits
5. **Scale workers**: Add more workers for higher throughput

## Resources

- **Celery Documentation**: https://docs.celeryq.dev/
- **Redis Documentation**: https://redis.io/docs/
- **Flower Documentation**: https://flower.readthedocs.io/

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review `CELERY_QUEUE_IMPLEMENTATION.md` for detailed documentation
3. Check Celery worker output for error messages
4. Use `celery inspect` commands for debugging

---

**Quick Start Version**: 1.0  
**Last Updated**: 2025-11-09  
**Status**: Production Ready ✅
