from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.events.models import Event
import uuid


class ReportExport(models.Model):
    class Type(models.TextChoices):
        RSVP = 'RSVP', _('Registered Attendees')
        PAYMENTS = 'PAYMENTS', _('Payment Records')
        CHECKINS = 'CHECKINS', _('Check-in Report')
        SWAG = 'SWAG', _('Swag Collection')
        FINANCIAL = 'FINANCIAL', _('Financial Summary')
        TICKET_SALES = 'TICKET_SALES', _('Ticket Sales')

    class Format(models.TextChoices):
        CSV = 'CSV', _('CSV')
        EXCEL = 'EXCEL', _('Excel')
        PDF = 'PDF', _('PDF')
        JSON = 'JSON', _('JSON')

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
