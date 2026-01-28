from django.db import models
from django.conf import settings
from apps.orgs.models import Organization
from apps.events.models import Event
from apps.tickets.models import Ticket
import uuid


class MessageTemplate(models.Model):
    class Type(models.TextChoices):
        EMAIL = 'EMAIL', 'Email'
        SMS = 'SMS', 'SMS'

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='message_templates'
    )
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=10, choices=Type.choices)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'template_type']),
        ]


class MessageCampaign(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        SENDING = 'SENDING', 'Sending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    class RecipientFilter(models.TextChoices):
        ALL_ATTENDEES = 'ALL', 'All Attendees'
        TICKET_TYPE = 'TICKET_TYPE', 'By Ticket Type'
        CHECKED_IN = 'CHECKED_IN', 'Checked In Only'
        NOT_CHECKED_IN = 'NOT_CHECKED_IN', 'Not Checked In'

    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='message_campaigns'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='message_campaigns'
    )
    name = models.CharField(max_length=100)
    message_type = models.CharField(
        max_length=10,
        choices=MessageTemplate.Type.choices
    )
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    recipient_filter = models.CharField(
        max_length=20,
        choices=RecipientFilter.choices,
        default=RecipientFilter.ALL_ATTENDEES
    )
    ticket_types = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['event', 'status']),
            models.Index(fields=['scheduled_at']),
        ]


class MessageDelivery(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        DELIVERED = 'DELIVERED', 'Delivered'
        OPENED = 'OPENED', 'Opened'
        CLICKED = 'CLICKED', 'Clicked'
        BOUNCED = 'BOUNCED', 'Bounced'
        FAILED = 'FAILED', 'Failed'

    campaign = models.ForeignKey(
        MessageCampaign,
        on_delete=models.CASCADE,
        related_name='deliveries'
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='message_deliveries'
    )
    recipient_email = models.EmailField(blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    tracking_id = models.UUIDField(default=uuid.uuid4, editable=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['tracking_id']),
        ]
