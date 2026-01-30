from django.utils import timezone
from apps.core.tasks import send_email_task, send_sms_task
from apps.messaging.models import MessageCampaign, MessageDelivery, MessageTemplate
from apps.tickets.models import Ticket


def get_campaign_recipients(campaign):
    tickets = Ticket.objects.filter(
        booking__event=campaign.event, booking__payment__status="CONFIRMED"
    ).select_related("booking", "booking__customer")

    if campaign.recipient_filter == MessageCampaign.RecipientFilter.TICKET_TYPE:
        tickets = tickets.filter(ticket_type_id__in=campaign.ticket_types)
    elif campaign.recipient_filter == MessageCampaign.RecipientFilter.CHECKED_IN:
        tickets = tickets.filter(is_checked_in=True)
    elif campaign.recipient_filter == MessageCampaign.RecipientFilter.NOT_CHECKED_IN:
        tickets = tickets.filter(is_checked_in=False)

    return tickets


def prepare_campaign(campaign):
    tickets = get_campaign_recipients(campaign)
    deliveries = []

    for ticket in tickets:
        user = ticket.booking.user
        delivery = MessageDelivery(
            campaign=campaign,
            ticket=ticket,
            recipient_email=user.email
            if campaign.message_type == MessageTemplate.Type.EMAIL
            else "",
            recipient_phone=user.phone_number
            if campaign.message_type == MessageTemplate.Type.SMS
            else "",
        )
        deliveries.append(delivery)

    MessageDelivery.objects.bulk_create(deliveries)
    campaign.total_recipients = len(deliveries)
    campaign.save(update_fields=["total_recipients"])

    return len(deliveries)


def personalize_message(template, ticket):
    user = ticket.booking.user
    event = ticket.booking.event

    replacements = {
        "{{first_name}}": user.first_name or "",
        "{{last_name}}": user.last_name or "",
        "{{full_name}}": user.get_full_name() or user.email,
        "{{email}}": user.email,
        "{{event_name}}": event.title,
        "{{event_date}}": event.start_at.strftime("%B %d, %Y")
        if event.start_at
        else "",
        "{{ticket_code}}": ticket.code,
        "{{ticket_type}}": ticket.ticket_type.name,
    }

    result = template
    for key, value in replacements.items():
        result = result.replace(key, str(value))

    return result


def send_campaign_message(delivery):
    campaign = delivery.campaign
    ticket = delivery.ticket

    try:
        body = personalize_message(campaign.body, ticket)

        if campaign.message_type == MessageTemplate.Type.EMAIL:
            subject = personalize_message(campaign.subject, ticket)
            send_email_task.enqueue(
                to_email=delivery.recipient_email,
                subject=subject,
                template_name="emails/campaign_message.html",
                context={"body": body, "tracking_id": str(delivery.tracking_id)},
            )
        else:
            send_sms_task.enqueue(
                phone_number=delivery.recipient_phone,
                template_name="sms/campaign_message.txt",
                context={"body": body},
            )

        delivery.status = MessageDelivery.Status.SENT
        delivery.sent_at = timezone.now()
    except Exception as e:
        delivery.status = MessageDelivery.Status.FAILED
        delivery.error_message = str(e)

    delivery.save(update_fields=["status", "sent_at", "error_message"])
    return delivery.status == MessageDelivery.Status.SENT


def execute_campaign(campaign):
    campaign.status = MessageCampaign.Status.SENDING
    campaign.save(update_fields=["status"])

    deliveries = campaign.deliveries.filter(status=MessageDelivery.Status.PENDING)
    sent_count = 0
    failed_count = 0

    for delivery in deliveries.iterator():
        if send_campaign_message(delivery):
            sent_count += 1
        else:
            failed_count += 1

    campaign.sent_count = sent_count
    campaign.failed_count = failed_count
    campaign.sent_at = timezone.now()
    campaign.status = MessageCampaign.Status.COMPLETED
    campaign.save(update_fields=["sent_count", "failed_count", "sent_at", "status"])

    return sent_count, failed_count


def track_open(tracking_id):
    try:
        delivery = MessageDelivery.objects.get(tracking_id=tracking_id)
        if not delivery.opened_at:
            delivery.status = MessageDelivery.Status.OPENED
            delivery.opened_at = timezone.now()
            delivery.save(update_fields=["status", "opened_at"])
        return True
    except MessageDelivery.DoesNotExist:
        return False


def track_click(tracking_id):
    try:
        delivery = MessageDelivery.objects.get(tracking_id=tracking_id)
        if not delivery.clicked_at:
            delivery.status = MessageDelivery.Status.CLICKED
            delivery.clicked_at = timezone.now()
            delivery.save(update_fields=["status", "clicked_at"])
        return True
    except MessageDelivery.DoesNotExist:
        return False
