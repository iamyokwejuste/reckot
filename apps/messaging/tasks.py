from django.utils import timezone
from django_tasks import task
from apps.messaging.models import MessageCampaign
from apps.messaging.services import prepare_campaign, execute_campaign


@task
def process_scheduled_campaigns():
    campaigns = MessageCampaign.objects.filter(
        status=MessageCampaign.Status.SCHEDULED, scheduled_at__lte=timezone.now()
    )

    for campaign in campaigns:
        prepare_campaign(campaign)
        execute_campaign(campaign)


@task
def send_campaign_task(campaign_id: int):
    try:
        campaign = MessageCampaign.objects.get(id=campaign_id)
        if campaign.status == MessageCampaign.Status.DRAFT:
            prepare_campaign(campaign)
        execute_campaign(campaign)
    except MessageCampaign.DoesNotExist:
        pass
