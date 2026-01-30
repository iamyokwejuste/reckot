from django.utils import timezone
from celery import shared_task
from apps.messaging.models import MessageCampaign
from apps.messaging.services import prepare_campaign, execute_campaign


@shared_task
def process_scheduled_campaigns():
    campaigns = MessageCampaign.objects.filter(
        status=MessageCampaign.Status.SCHEDULED, scheduled_at__lte=timezone.now()
    )

    for campaign in campaigns:
        prepare_campaign(campaign)
        execute_campaign(campaign)


@shared_task
def send_campaign_task(campaign_id: int):
    try:
        campaign = MessageCampaign.objects.get(id=campaign_id)
        if campaign.status == MessageCampaign.Status.DRAFT:
            prepare_campaign(campaign)
        execute_campaign(campaign)
    except MessageCampaign.DoesNotExist:
        pass
