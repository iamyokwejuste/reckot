from django.db import models
from django.conf import settings
from apps.events.models import Event
import uuid


class ReportExport(models.Model):
    class Type(models.TextChoices):
        RSVP = 'RSVP', 'Registered Attendees'
        PAYMENTS = 'PAYMENTS', 'Payment Records'
        CHECKINS = 'CHECKINS', 'Check-in Report'
        SWAG = 'SWAG', 'Swag Collection'
        FINANCIAL = 'FINANCIAL', 'Financial Summary'
        TICKET_SALES = 'TICKET_SALES', 'Ticket Sales'

    class Format(models.TextChoices):
        CSV = 'CSV', 'CSV'
        EXCEL = 'EXCEL', 'Excel'
        PDF = 'PDF', 'PDF'
        JSON = 'JSON', 'JSON'

    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='exports'
    )
    report_type = models.CharField(max_length=20, choices=Type.choices)
    format = models.CharField(max_length=10, choices=Format.choices)
    file = models.FileField(upload_to='exports/', blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    mask_emails = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event', 'report_type']),
        ]

    def __str__(self):
        return f'{self.get_report_type_display()} - {self.event.title}'
