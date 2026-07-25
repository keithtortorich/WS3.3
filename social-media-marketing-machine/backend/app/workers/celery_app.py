"""Celery application instance wired to Redis broker/backend.

Configuration is pulled from Settings (which mirrors .env.example exactly)
rather than hardcoded, so the same code works in docker-compose (broker at
``redis://redis:...``) and local dev (``redis://localhost:...``, if the
developer overrides REDIS_HOST in their .env).
"""
from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "smm",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks.publish_tasks"],
)

celery_app.conf.update(
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "enqueue-due-schedules-every-minute": {
            "task": "publish.enqueue_due_schedules",
            "schedule": 60.0,
        }
    },
)
