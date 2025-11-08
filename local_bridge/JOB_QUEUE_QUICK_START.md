# Job Queue Quick Start Guide

## Prerequisites

- Python 3.11+
- Redis server
- All dependencies from requirements.txt

## Installation

### 1. Install Redis

**Windows (WSL):**
```bash
wsl --install
wsl -d Ubuntu
sudo apt-get update
sudo apt-get install redis-server
```

**macOS:**
```bash
brew install redis
```

**Linux:**
```bash
sudo apt-get install redis-server
```

### 2. Install Python Dependencies

```bash
cd local_bridge
pip install -r requirements.txt
```

## Starting the System

### 1. Start Redis Server

**Windows (WSL):**
```bash
wsl -d Ubuntu -e redis-server
```

**macOS:**
```bash
brew services start redis
# or
redis-server
```

**Linux:**
```bash
sudo systemctl start redis
# or
redis-server
```

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### 2. Start Celery Worker

Open a new terminal:

```bash
cd local_bridge
python start_worker.py
```

You should see output like:
```
[INFO] Starting Celery worker
[INFO] Consuming from queues: high_priority, medium_priority, low_priority, default
celery@hostname ready.
```

### 3. Start Flask API Server

Open another terminal:

```bash
cd local_bridge
python app.py
```

You should see:
```
[INFO] Starting Junmai AutoDev Bridge Server
 * Running on http://127.0.0.1:5100
```

## Basic Usage

### Submit a Photo for Processing

```bash
curl -X POST http://localhost:5100/queue/submit \
  -H "Content-Type: application/json" \
  -d '{
    "photo_id": 1,
    "user_requested": false
  }'
```

Response:
```json
{
  "message": "Job submitted successfully",
  "task_id": "abc123-def456-...",
  "photo_id": 1
}
```

### Check Job Status

```bash
curl http://localhost:5100/queue/status/abc123-def456-...
```

Response:
```json
{
  "task_id": "abc123-def456-...",
  "state": "SUCCESS",
  "ready": true,
  "successful": true,
  "result": {
    "processing_time": 5.2,
    "ai_score": 4.3,
    "context": "portrait_indoor"
  }
}
```

### Submit Batch Processing

```bash
curl -X POST http://localhost:5100/queue/batch \
  -H "Content-Type: application/json" \
  -d '{
    "photo_ids": [1, 2, 3, 4, 5],
    "priority": 5
  }'
```

### Submit Entire Session

```bash
curl -X POST http://localhost:5100/queue/session/1 \
  -H "Content-Type: application/json" \
  -d '{
    "auto_select": true
  }'
```

### Get Queue Statistics

```bash
curl http://localhost:5100/queue/stats
```

Response:
```json
{
  "active_tasks": 2,
  "scheduled_tasks": 5,
  "reserved_tasks": 1,
  "total_pending": 8,
  "jobs_by_status": {
    "pending": 5,
    "processing": 2,
    "completed": 45,
    "failed": 1
  },
  "jobs_by_priority": {
    "9": 2,
    "5": 4,
    "1": 2
  }
}
```

### Get Worker Statistics

```bash
curl http://localhost:5100/queue/workers
```

### Cancel a Job

```bash
curl -X POST http://localhost:5100/queue/cancel/abc123-def456-...
```

### Pause Queue

```bash
curl -X POST http://localhost:5100/queue/pause
```

### Resume Queue

```bash
curl -X POST http://localhost:5100/queue/resume
```

### Get Failed Jobs

```bash
curl http://localhost:5100/queue/failed?limit=10
```

### Retry Failed Job

```bash
curl -X POST http://localhost:5100/queue/retry/abc123-def456-...
```

## Python Usage

### Submit Job from Python

```python
from job_queue_manager import get_job_queue_manager

manager = get_job_queue_manager()

# Submit single photo
task_id = manager.submit_photo_processing(
    photo_id=1,
    user_requested=True
)
print(f"Task submitted: {task_id}")

# Submit batch
task_ids = manager.submit_batch_processing(
    photo_ids=[1, 2, 3, 4, 5],
    priority=5
)
print(f"Batch submitted: {len(task_ids)} tasks")

# Submit session
result = manager.submit_session_processing(
    session_id=1,
    auto_select=True
)
print(f"Session submitted: {result['photo_count']} photos")
```

### Check Status

```python
# Get job status
status = manager.get_job_status(task_id)
print(f"State: {status['state']}")
print(f"Ready: {status['ready']}")

if status['ready'] and status['successful']:
    print(f"Result: {status['result']}")
```

### Monitor Queue

```python
# Get queue stats
stats = manager.get_queue_stats()
print(f"Active: {stats['active_tasks']}")
print(f"Pending: {stats['total_pending']}")

# Get worker stats
worker_stats = manager.get_worker_stats()
print(f"Workers: {len(worker_stats['workers'])}")
```

### Handle Failed Jobs

```python
# Get failed jobs
failed = manager.get_failed_jobs(limit=10)
for job in failed:
    print(f"Job {job['id']}: {job['error_message']}")
    
    # Retry failed job
    new_task_id = manager.retry_failed_job(job['id'])
    if new_task_id:
        print(f"Retried as: {new_task_id}")
```

## Configuration

### Adjust Worker Concurrency

```bash
# Start with 5 concurrent workers
python start_worker.py --concurrency 5
```

### Consume Specific Queues

```bash
# Only process high priority jobs
python start_worker.py --queues high_priority

# Process high and medium priority
python start_worker.py --queues high_priority,medium_priority
```

### Adjust Log Level

```bash
# Debug logging
python start_worker.py --loglevel DEBUG

# Warning and above only
python start_worker.py --loglevel WARNING
```

### Environment Variables

```bash
# Custom Redis connection
export REDIS_HOST=192.168.1.100
export REDIS_PORT=6380
export REDIS_PASSWORD=mypassword

python start_worker.py
```

## Monitoring

### Real-time Worker Monitoring

```bash
# Watch worker output
python start_worker.py --loglevel INFO
```

### Check Redis Queue Length

```bash
redis-cli
> LLEN high_priority
> LLEN medium_priority
> LLEN low_priority
```

### Monitor System Resources

```bash
# CPU and memory usage
curl http://localhost:5100/queue/stats

# Worker health
curl http://localhost:5100/queue/workers
```

## Troubleshooting

### Redis Not Running

```bash
# Check if Redis is running
redis-cli ping

# If not, start it
redis-server
```

### Worker Not Processing Tasks

```bash
# Check worker is running
ps aux | grep celery

# Restart worker
# Ctrl+C to stop, then:
python start_worker.py
```

### Tasks Stuck in Queue

```bash
# Check queue stats
curl http://localhost:5100/queue/stats

# Purge queue if needed
curl -X POST http://localhost:5100/queue/purge
```

### High Memory Usage

```bash
# Reduce concurrency
python start_worker.py --concurrency 2

# Or restart worker periodically
# Workers auto-restart after 100 tasks by default
```

## Next Steps

1. **Integration**: Integrate with hot folder watcher for automatic processing
2. **Monitoring**: Set up monitoring dashboard
3. **Scaling**: Add more workers for higher throughput
4. **Optimization**: Tune priorities based on your workflow

## Common Workflows

### Automatic Processing on Import

```python
# In hot folder callback
def on_new_file_detected(file_path):
    # Import file
    photo = import_file(file_path)
    
    # Submit for processing
    manager = get_job_queue_manager()
    task_id = manager.submit_photo_processing(photo.id)
    
    print(f"Photo {photo.id} queued for processing: {task_id}")
```

### Batch Process Session

```python
# Process all photos in a session
manager = get_job_queue_manager()
result = manager.submit_session_processing(
    session_id=session_id,
    auto_select=True  # Only process photos with AI score >= 3.5
)

print(f"Processing {result['photo_count']} photos")
```

### Priority Processing

```python
# High priority for user-selected photos
for photo_id in user_selected_photos:
    task_id = manager.submit_photo_processing(
        photo_id=photo_id,
        user_requested=True  # High priority
    )
```

## Support

For more details, see:
- `JOB_QUEUE_IMPLEMENTATION.md` - Complete implementation guide
- `celery_config.py` - Configuration options
- `celery_tasks.py` - Available tasks
- `job_queue_manager.py` - API reference

For issues:
1. Check logs in `local_bridge/logs/`
2. Review queue stats: `GET /queue/stats`
3. Check worker health: `GET /queue/workers`
