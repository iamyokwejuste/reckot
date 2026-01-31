from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from apps.ai.models import AIConversation

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_ai_conversations():
    """
    Delete AI conversations older than 10 days.
    Runs periodically via Celery beat.
    """
    cutoff_date = timezone.now() - timedelta(days=10)

    conversations = AIConversation.objects.filter(created_at__lt=cutoff_date)
    count = conversations.count()

    if count > 0:
        conversations.delete()
        logger.info(f"Deleted {count} AI conversations older than 10 days")
    else:
        logger.info("No AI conversations to delete")

    return f"Deleted {count} conversations"
