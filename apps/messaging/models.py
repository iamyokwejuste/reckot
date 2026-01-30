from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.orgs.models import Organization
from apps.events.models import Event
from apps.tickets.models import Ticket
import uuid


class MessageTemplate(models.Model):
    class Type(models.TextChoices):
        EMAIL = "EMAIL", _("Email")
        SMS = "SMS", _("SMS")

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="message_templates"
    )
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=10, choices=Type.choices)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "template_type"]),
        ]


class MessageCampaign(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Draft")
        SCHEDULED = "SCHEDULED", _("Scheduled")
        SENDING = "SENDING", _("Sending")
        COMPLETED = "COMPLETED", _("Completed")
        FAILED = "FAILED", _("Failed")

    class RecipientFilter(models.TextChoices):
        ALL_ATTENDEES = "ALL", _("All Attendees")
        TICKET_TYPE = "TICKET_TYPE", _("By Ticket Type")
        CHECKED_IN = "CHECKED_IN", _("Checked In Only")
        NOT_CHECKED_IN = "NOT_CHECKED_IN", _("Not Checked In")

    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="message_campaigns"
    )
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="message_campaigns"
    )
    name = models.CharField(max_length=100)
    message_type = models.CharField(max_length=10, choices=MessageTemplate.Type.choices)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    recipient_filter = models.CharField(
        max_length=20,
        choices=RecipientFilter.choices,
        default=RecipientFilter.ALL_ATTENDEES,
    )
    ticket_types = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["event", "status"]),
            models.Index(fields=["scheduled_at"]),
        ]


class MessageDelivery(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        SENT = "SENT", _("Sent")
        DELIVERED = "DELIVERED", _("Delivered")
        OPENED = "OPENED", _("Opened")
        CLICKED = "CLICKED", _("Clicked")
        BOUNCED = "BOUNCED", _("Bounced")
        FAILED = "FAILED", _("Failed")

    campaign = models.ForeignKey(
        MessageCampaign, on_delete=models.CASCADE, related_name="deliveries"
    )
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="message_deliveries"
    )
    recipient_email = models.EmailField(blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    tracking_id = models.UUIDField(default=uuid.uuid4, editable=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["campaign", "status"]),
            models.Index(fields=["tracking_id"]),
        ]
