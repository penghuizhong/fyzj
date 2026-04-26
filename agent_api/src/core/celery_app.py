"""Celery application configuration."""

from celery import Celery
from celery.signals import worker_ready

from core.config import settings

app = Celery("ai_server")

app.conf.update(
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    result_expires=3600,
    task_always_eager=False,
)

import tasks


@worker_ready.connect
def on_worker_ready(**kwargs):
    print("Celery worker is ready!")
