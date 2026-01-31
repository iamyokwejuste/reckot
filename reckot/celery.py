import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reckot.settings")

app = Celery("reckot")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "expire-stale-payments-every-5-minutes": {
        "task": "apps.payments.tasks.process_expired_payments_task",
        "schedule": 300.0,
    },
    "cleanup-otps-every-hour": {
        "task": "apps.core.tasks.cleanup_expired_otps_task",
        "schedule": crontab(minute=0),
    },
    "process-scheduled-campaigns-every-minute": {
        "task": "apps.messaging.tasks.process_scheduled_campaigns",
        "schedule": 60.0,
    },
    "cleanup-old-ai-conversations-daily": {
        "task": "apps.ai.tasks.cleanup_old_ai_conversations",
        "schedule": crontab(hour=2, minute=0),
    },
}
