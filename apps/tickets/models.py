from django.db import models
from django.conf import settings
from apps.events.models import Event, CheckoutQuestion
import uuid


class TicketType(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_types')
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
            models.Index(fields=['event', 'is_active']),
        ]

    def __str__(self):
        return f'{self.name} for {self.event.title}'

    @property
    def available_quantity(self):
        sold = self.tickets.count()
        return max(0, self.quantity - sold)


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Payment'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUNDED = 'REFUNDED', 'Refunded'

    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings', null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['event', 'status']),
        ]

    def __str__(self):
        return f'Booking {self.reference} for {self.user}'


class Ticket(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='tickets')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name='tickets')
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    attendee_name = models.CharField(max_length=200, blank=True)
    attendee_email = models.EmailField(blank=True)
    is_checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_in_tickets'
    )

    class Meta:
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['booking']),
            models.Index(fields=['is_checked_in']),
        ]

    def __str__(self):
        return f'Ticket {self.code} for {self.ticket_type.event.title}'


class TicketQuestionAnswer(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='answers')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(CheckoutQuestion, on_delete=models.CASCADE)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['booking', 'question']),
        ]
        unique_together = [['ticket', 'question']]