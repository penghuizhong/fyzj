"""Celery application configuration.

Architecture:
  - Three queues: default / agent / dead_letter
  - Dead Letter Exchange (DLX) on RabbitMQ for failed/expired messages
  - IdempotentTask base class uses sync Redis NX lock to prevent duplicate runs
  - Signals provide structured logging for failures and retries
"""

import logging

from celery import Celery, Task
from celery.exceptions import SoftTimeLimitExceeded
from celery.signals import task_failure, task_retry, worker_ready
from celery.utils.log import get_task_logger
from kombu import Exchange, Queue

from core.config import settings
from core.redis import get_sync_redis

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exchange & Queue definitions
# ---------------------------------------------------------------------------

_dlx = Exchange("dlx", type="direct", durable=True)
_default_ex = Exchange("default", type="direct", durable=True)
_agent_ex = Exchange("agent", type="direct", durable=True)

_DLQ_ARGS = {
    "x-dead-letter-exchange": "dlx",
    "x-dead-letter-routing-key": "dead_letter",
}

QUEUES = (
    Queue(
        "default",
        _default_ex,
        routing_key="default",
        durable=True,
        queue_arguments={**_DLQ_ARGS, "x-message-ttl": 3_600_000},  # 1 h TTL
    ),
    Queue(
        "agent",
        _agent_ex,
        routing_key="agent",
        durable=True,
        queue_arguments=_DLQ_ARGS,
    ),
    Queue(
        "dead_letter",
        _dlx,
        routing_key="dead_letter",
        durable=True,
    ),
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Celery("ai_server")

app.conf.update(
    # ── Broker / backend ────────────────────────────────────────────────────
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,

    # ── Serialization ────────────────────────────────────────────────────────
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # ── Time ─────────────────────────────────────────────────────────────────
    timezone="UTC",
    enable_utc=True,

    # ── Task behaviour ───────────────────────────────────────────────────────
    task_track_started=True,
    task_time_limit=3_600,           # hard kill after 1 h
    task_soft_time_limit=3_540,      # SoftTimeLimitExceeded raised 60 s before hard kill
    task_acks_late=True,             # ack only after completion → survives worker crash
    task_reject_on_worker_lost=True, # re-queue instead of silently dropping

    # ── Worker ───────────────────────────────────────────────────────────────
    worker_prefetch_multiplier=1,
    worker_concurrency=getattr(settings, "CELERY_WORKER_CONCURRENCY", 4),

    # ── Results ──────────────────────────────────────────────────────────────
    result_expires=7_200,            # 2 h — longer than task_time_limit to avoid race

    # ── Queues & routing ─────────────────────────────────────────────────────
    task_queues=QUEUES,
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    task_routes={
        "tasks.agent_tasks.*": {"queue": "agent", "routing_key": "agent"},
    },

    # ── Imports ──────────────────────────────────────────────────────────────
    imports=["tasks.agent_tasks"],

    task_always_eager=False,
)

# ---------------------------------------------------------------------------
# Idempotent base task
# ---------------------------------------------------------------------------

_LOCK_EXPIRE = 60 * 10  # 10 minutes


class IdempotentTask(Task):
    """Base task that uses a Redis NX lock to skip duplicate submissions.

    Subclasses can override ``lock_key`` to customise the deduplication scope.

    Example::

        @app.task(base=IdempotentTask, bind=True)
        def process(self, directory: str):
            ...
    """

    abstract = True

    def lock_key(self, *args, **kwargs) -> str:
        """Return the Redis key used to deduplicate this task invocation."""
        return f"celery:lock:{self.name}:{args}:{sorted(kwargs.items())}"

    def __call__(self, *args, **kwargs):
        task_logger = get_task_logger(self.name)
        key = self.lock_key(*args, **kwargs)
        redis = get_sync_redis()

        acquired = redis.set(key, "1", nx=True, ex=_LOCK_EXPIRE)
        if not acquired:
            task_logger.warning("Duplicate task skipped [lock=%s]", key)
            return {"status": "skipped", "reason": "duplicate"}

        try:
            return super().__call__(*args, **kwargs)
        except SoftTimeLimitExceeded:
            task_logger.warning("Soft time limit reached [lock=%s] — cleaning up", key)
            raise
        finally:
            redis.delete(key)


# ---------------------------------------------------------------------------
# Signals — structured observability
# ---------------------------------------------------------------------------

@worker_ready.connect
def on_worker_ready(**kwargs):
    logger.info("Celery worker ready — queues: %s", [q.name for q in QUEUES])


@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, einfo=None, **kwargs):
    logger.error(
        "Task failed",
        extra={
            "task_name": getattr(sender, "name", "unknown"),
            "task_id": task_id,
            "exception": str(exception),
            "traceback": str(einfo),
        },
    )


@task_retry.connect
def on_task_retry(sender=None, reason=None, **kwargs):
    logger.warning(
        "Task retrying",
        extra={
            "task_name": getattr(sender, "name", "unknown"),
            "reason": str(reason),
        },
    )