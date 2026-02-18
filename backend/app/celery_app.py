"""
Celery application configuration.
Implements async task processing with Redis as broker.
"""
from celery import Celery
import os

# Celery configuration
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery(
    "pricing_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks.pricing_tasks", "app.tasks.ml_tasks", "app.tasks.notification_tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="Europe/Warsaw",
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    task_soft_time_limit=240,  # 4 minutes soft limit
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    
    # Result expiration
    result_expires=3600,  # 1 hour
    
    # Retry policy
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "recalculate-ml-scores-daily": {
            "task": "app.tasks.ml_tasks.recalculate_all_scores",
            "schedule": 86400.0,  # Every 24 hours
        },
        "cleanup-old-data-weekly": {
            "task": "app.tasks.pricing_tasks.cleanup_old_offers",
            "schedule": 604800.0,  # Every 7 days
        },
        "health-check-every-5-minutes": {
            "task": "app.tasks.pricing_tasks.health_check",
            "schedule": 300.0,  # Every 5 minutes
        },
    },
)
