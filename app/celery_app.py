"""
Celery application configuration.

Uses Redis as message broker and result backend.
Configured for async sentiment processing tasks.
"""

from celery import Celery

from app.config import settings

# ═══════════════════════════════════════════════════════
# Celery App
# ═══════════════════════════════════════════════════════

celery_app = Celery(
    "stockintel",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="Asia/Kolkata",
    enable_utc=True,

    # Task routing
    task_routes={
        "app.tasks.sentiment_tasks.*": {"queue": "sentiment"},
    },

    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time (GPU-bound)
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (memory leak safety)
    task_acks_late=True,

    # Task settings
    task_soft_time_limit=600,   # 10 min soft limit
    task_time_limit=900,        # 15 min hard limit

    # Result expiry
    result_expires=3600,  # 1 hour
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
