from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.orgs.models import Organization
from apps.events.models import Event
from apps.tickets.models import Booking
import uuid


class AffiliateLink(models.Model):
    class CommissionType(models.TextChoices):
        FIXED = "FIXED", _("Fixed Amount")
        PERCENTAGE = "PERCENTAGE", _("Percentage")

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="affiliate_links"
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="affiliate_links",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    affiliate_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="affiliate_links",
    )
    commission_type = models.CharField(
        max_length=20, choices=CommissionType.choices, default=CommissionType.PERCENTAGE
    )
    commission_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    clicks = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["organization", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)

    def calculate_commission(self, amount):
        if self.commission_type == self.CommissionType.FIXED:
            return self.commission_value
        return amount * (self.commission_value / 100)


class AffiliateConversion(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        APPROVED = "APPROVED", _("Approved")
        PAID = "PAID", _("Paid")
        REJECTED = "REJECTED", _("Rejected")

    affiliate_link = models.ForeignKey(
        AffiliateLink, on_delete=models.CASCADE, related_name="conversions"
    )
    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name="affiliate_conversion"
    )
    order_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["affiliate_link", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]


class SocialShare(models.Model):
    class Platform(models.TextChoices):
        FACEBOOK = "FACEBOOK", _("Facebook")
        TWITTER = "TWITTER", _("Twitter/X")
        LINKEDIN = "LINKEDIN", _("LinkedIn")
        WHATSAPP = "WHATSAPP", _("WhatsApp")
        TELEGRAM = "TELEGRAM", _("Telegram")
        EMAIL = "EMAIL", _("Email")
        COPY_LINK = "COPY_LINK", _("Copy Link")

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="shares")
    platform = models.CharField(max_length=20, choices=Platform.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["event", "platform"]),
        ]
