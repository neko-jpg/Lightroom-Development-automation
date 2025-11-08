"""
Celery Worker Startup Script

This script starts the Celery worker with appropriate configuration
for the Junmai AutoDev background processing system.

Usage:
    python start_worker.py [options]

Options:
    --concurrency N    Number of concurrent workers (default: 3)
    --loglevel LEVEL   Log level (default: INFO)
    --queues QUEUES    Comma-separated list of queues to consume
    
Requirements: 4.1, 4.2
"""

import sys
import argparse
from celery_config import app
from logging_system import get_logging_system

logging_system = get_logging_system()


def start_worker(concurrency=3, loglevel='INFO', queues=None):
    """
    Start Celery worker
    
    Args:
        concurrency: Number of concurrent worker processes
        loglevel: Logging level
        queues: List of queues to consume from
    """
    logging_system.log("INFO", "Starting Celery worker",
                      concurrency=concurrency,
                      loglevel=loglevel,
                      queues=queues)
    
    # Build worker arguments
    argv = [
        'worker',
        f'--concurrency={concurrency}',
        f'--loglevel={loglevel}',
        '--pool=prefork',
        '--max-tasks-per-child=100',
        '--time-limit=600',
        '--soft-time-limit=300',
    ]
    
    # Add queues if specified
    if queues:
        if isinstance(queues, list):
            queues_str = ','.join(queues)
        else:
            queues_str = queues
        argv.append(f'--queues={queues_str}')
    else:
        # Default: consume from all queues
        argv.append('--queues=high_priority,medium_priority,low_priority,default')
    
    # Start worker
    try:
        app.worker_main(argv)
    except KeyboardInterrupt:
        logging_system.log("INFO", "Worker stopped by user")
    except Exception as e:
        logging_system.log_error("Worker crashed", exception=e)
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Start Celery worker for Junmai AutoDev'
    )
    
    parser.add_argument(
        '--concurrency',
        type=int,
        default=3,
        help='Number of concurrent worker processes (default: 3)'
    )
    
    parser.add_argument(
        '--loglevel',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Log level (default: INFO)'
    )
    
    parser.add_argument(
        '--queues',
        type=str,
        default=None,
        help='Comma-separated list of queues to consume (default: all)'
    )
    
    args = parser.parse_args()
    
    # Start worker
    start_worker(
        concurrency=args.concurrency,
        loglevel=args.loglevel,
        queues=args.queues
    )


if __name__ == '__main__':
    main()
