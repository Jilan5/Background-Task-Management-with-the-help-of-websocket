from celery import Celery
import os
import time
import redis
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
BACKEND_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'

celery = Celery('tasks',
                broker=BROKER_URL,
                backend=BACKEND_URL)

# Enhanced Celery configuration for better Flower integration
celery.conf.update(
    result_expires=3600,  # Results will expire after 1 hour
    task_track_started=True,  # Track when tasks are started
    task_time_limit=60 * 5,  # Tasks have 5 minutes to run
    worker_max_tasks_per_child=200,  # Worker processes will be recycled after 200 tasks
    worker_prefetch_multiplier=4,  # Number of tasks to prefetch per worker process
    worker_send_task_events=True,  # Send task-related events for Flower
    task_send_sent_event=True,  # Required for monitoring task execution
    event_queue_expires=60,  # Event queue expiry time in seconds
    worker_pool_restarts=True,  # Enable worker pool restarts
)

# Redis configuration for publishing status updates
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

@celery.task(name="create_task", bind=True)
def create_task(self, task_length):
    """
    Example background task that runs for a specified amount of time and updates
    progress through Redis pub/sub
    """
    logger.info(f"Task {self.request.id} started, running for {task_length} seconds")
    
    total_steps = task_length
    for step in range(total_steps):
        # Update progress
        percentage = int((step + 1) * 100 / total_steps)
        self.update_state(state="PROGRESS", meta={"progress": percentage})
        
        # Publish progress to Redis
        status_data = {
            "task_id": self.request.id,
            "status": "PROGRESS",
            "progress": percentage
        }
        redis_client.publish("task_status", json.dumps(status_data))
        
        # Simulate work with sleep
        time.sleep(1)
    
    # Final update
    result = {"status": "Task completed!", "result": 100}
    
    # Publish completion to Redis
    status_data = {
        "task_id": self.request.id,
        "status": "COMPLETED",
        "progress": 100
    }
    redis_client.publish("task_status", json.dumps(status_data))
    
    return result