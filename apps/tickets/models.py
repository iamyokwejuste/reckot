import uuid
import random
import string
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.events.models import Event, CheckoutQuestion

class TicketType(models.Model):
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="ticket_types"
    )
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    max_per_order = models.PositiveSmallIntegerField(default=10)
    sales_start = models.DateTimeField(null=True, blank=True)
    sales_end = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["event", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} for {self.event.title}"

    @property
    def available_quantity(self):
        sold = self.tickets.count()
        return max(0, self.quantity - sold)

class GuestSession(models.Model):

    token = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    email = models.EmailField()
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"Guest {self.email} ({self.token})"

    @property
    def is_expired(self):
        from django.utils import timezone

        return timezone.now() > self.expires_at

class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending Payment")
        CONFIRMED = "CONFIRMED", _("Confirmed")
        CANCELLED = "CANCELLED", _("Cancelled")
        REFUNDED = "REFUNDED", _("Refunded")

    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="bookings", null=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
        null=True,
        blank=True,
    )
    guest_session = models.ForeignKey(
        GuestSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    guest_email = models.EmailField(blank=True)
    guest_name = models.CharField(max_length=200, blank=True)
    guest_phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["reference"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["event", "status"]),
            models.Index(fields=["guest_session"]),
            models.Index(fields=["guest_email"]),
        ]

    def __str__(self):
        if self.user:
            return f"Booking {self.reference} for {self.user}"
        return f"Booking {self.reference} for {self.guest_email or 'Guest'}"

    @property
    def is_guest(self):
        return self.user is None

    @property
    def buyer_email(self):
        if self.user:
            return self.user.email
        return self.guest_email

    @property
    def buyer_name(self):
        if self.user:
            return self.user.get_full_name() or self.user.email
        return self.guest_name

class Ticket(models.Model):
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="tickets"
    )
    ticket_type = models.ForeignKey(
        TicketType, on_delete=models.CASCADE, related_name="tickets"
    )
    code = models.CharField(max_length=20, editable=False, unique=True, db_index=True)
    attendee_name = models.CharField(max_length=200, blank=True)
    attendee_email = models.EmailField(blank=True)
    is_checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checked_in_tickets",
    )

    class Meta:
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["booking"]),
            models.Index(fields=["is_checked_in"]),
        ]

    def __str__(self):
        return f"Ticket {self.code} for {self.ticket_type.event.title}"

    @staticmethod
    def generate_code(event):
        prefix = (event.ticket_prefix or "RECK").upper()[:4]
        characters = string.ascii_uppercase + string.digits
        while True:
            suffix = ''.join(random.choices(characters, k=6))
            code = f"{prefix}{suffix}"
            if not Ticket.objects.filter(code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.code:
            event = self.ticket_type.event
            self.code = self.generate_code(event)
        super().save(*args, **kwargs)

class TicketQuestionAnswer(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="answers")
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(CheckoutQuestion, on_delete=models.CASCADE)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["booking", "question"]),
        ]
        unique_together = [["ticket", "question"]]
