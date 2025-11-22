from celery import Celery
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

celery_app = Celery(
    "brand_reputation_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.workers.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    worker_disable_rate_limits=False,
)

celery_app.conf.beat_schedule = {
    'collect-mentions-every-15-minutes': {
        'task': 'app.workers.tasks.collect_all_mentions',
        'schedule': settings.COLLECTION_INTERVAL_MINUTES * 60.0,
    },
    'detect-spikes-hourly': {
        'task': 'app.workers.tasks.check_for_spikes',
        'schedule': 3600.0,
    },
    'update-topics-daily': {
        'task': 'app.workers.tasks.update_topics',
        'schedule': 86400.0,
    },
}

logger.info("Celery app configured successfully")
