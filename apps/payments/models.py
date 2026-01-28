from django.db import models
from django.conf import settings
from apps.tickets.models import Booking
import uuid
from datetime import timedelta
from django.utils import timezone


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        FAILED = 'FAILED', 'Failed'
        EXPIRED = 'EXPIRED', 'Expired'

    class Method(models.TextChoices):
        MTN_MOMO = 'MTN_MOMO', 'MTN Mobile Money'
        ORANGE_MONEY = 'ORANGE_MONEY', 'Orange Money'

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    reference = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices)
    phone_number = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    external_reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['booking']),
        ]
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at and self.status == self.Status.PENDING


class Refund(models.Model):
    """Model for tracking refund requests and their status."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved'
        PROCESSED = 'PROCESSED', 'Processed'
        REJECTED = 'REJECTED', 'Rejected'

    class Type(models.TextChoices):
        FULL = 'FULL', 'Full Refund'
        PARTIAL = 'PARTIAL', 'Partial Refund'

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds'
    )
    reference = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    refund_type = models.CharField(
        max_length=10,
        choices=Type.choices,
        default=Type.FULL
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    reason = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='refund_requests'
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_refunds'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['status']),
            models.Index(fields=['payment']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund {self.reference} - {self.status}"

    def approve(self, processed_by=None):
        """Approve the refund request."""
        self.status = self.Status.APPROVED
        self.processed_by = processed_by
        self.save(update_fields=['status', 'processed_by', 'updated_at'])

    def process(self, processed_by=None):
        """Mark refund as processed (money sent)."""
        self.status = self.Status.PROCESSED
        self.processed_by = processed_by
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_by', 'processed_at', 'updated_at'])

    def reject(self, reason: str, processed_by=None):
        """Reject the refund request."""
        self.status = self.Status.REJECTED
        self.rejection_reason = reason
        self.processed_by = processed_by
        self.save(update_fields=['status', 'rejection_reason', 'processed_by', 'updated_at'])


class RefundAuditLog(models.Model):
    """Audit log for refund status changes."""

    refund = models.ForeignKey(
        Refund,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=50)
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.refund.reference} - {self.action}"
