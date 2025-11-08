"""
Celery Configuration for Junmai AutoDev Background Job Queue

This module configures Celery with Redis as the message broker and result backend.
It provides task definitions for background photo processing operations.

Requirements: 4.1, 4.2, 4.4
"""

from celery import Celery
from kombu import Queue, Exchange
import os

# Redis connection configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Construct Redis URL
if REDIS_PASSWORD:
    REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
else:
    REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

# Initialize Celery app
app = Celery(
    'junmai_autodev',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['celery_tasks']
)

# Celery configuration
app.conf.update(
    # Task execution settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Tokyo',
    enable_utc=True,
    
    # Task result settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    },
    
    # Task routing and priority
    task_default_queue='default',
    task_default_exchange='tasks',
    task_default_exchange_type='direct',
    task_default_routing_key='default',
    
    # Priority queue configuration (Requirement 4.4)
    task_queues=(
        Queue('high_priority', Exchange('tasks'), routing_key='high',
              queue_arguments={'x-max-priority': 10}),
        Queue('medium_priority', Exchange('tasks'), routing_key='medium',
              queue_arguments={'x-max-priority': 5}),
        Queue('low_priority', Exchange('tasks'), routing_key='low',
              queue_arguments={'x-max-priority': 1}),
        Queue('default', Exchange('tasks'), routing_key='default',
              queue_arguments={'x-max-priority': 5}),
    ),
    
    # Task routes - map task names to queues
    task_routes={
        'celery_tasks.process_photo_task': {'queue': 'medium_priority'},
        'celery_tasks.analyze_exif_task': {'queue': 'high_priority'},
        'celery_tasks.evaluate_quality_task': {'queue': 'medium_priority'},
        'celery_tasks.group_similar_photos_task': {'queue': 'low_priority'},
        'celery_tasks.apply_preset_task': {'queue': 'high_priority'},
        'celery_tasks.export_photo_task': {'queue': 'low_priority'},
    },
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Fetch one task at a time for better priority handling
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks to prevent memory leaks
    worker_disable_rate_limits=False,
    
    # Retry settings (Requirement 4.2)
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,  # Requeue task if worker crashes
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Concurrency settings
    worker_concurrency=3,  # Max concurrent jobs (from config)
    worker_pool='prefork',  # Use process pool for CPU-intensive tasks
    
    # Time limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit
    
    # Beat scheduler (for periodic tasks)
    beat_schedule={
        'cleanup-old-results': {
            'task': 'celery_tasks.cleanup_old_results',
            'schedule': 3600.0,  # Run every hour
        },
        'update-system-metrics': {
            'task': 'celery_tasks.update_system_metrics',
            'schedule': 60.0,  # Run every minute
        },
    },
)

# Task priority levels
PRIORITY_HIGH = 9
PRIORITY_MEDIUM = 5
PRIORITY_LOW = 1

def get_priority_for_photo(ai_score: float = None, user_requested: bool = False) -> int:
    """
    Calculate task priority based on photo characteristics
    
    Args:
        ai_score: AI evaluation score (1-5)
        user_requested: Whether task was manually requested by user
        
    Returns:
        Priority value (1-10)
    """
    if user_requested:
        return PRIORITY_HIGH
    
    if ai_score is not None:
        if ai_score >= 4.5:
            return PRIORITY_HIGH
        elif ai_score >= 3.5:
            return PRIORITY_MEDIUM
        else:
            return PRIORITY_LOW
    
    return PRIORITY_MEDIUM


if __name__ == '__main__':
    app.start()
