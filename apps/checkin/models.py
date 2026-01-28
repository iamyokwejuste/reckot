from django.db import models
from django.conf import settings
from apps.tickets.models import Ticket
from apps.events.models import Event


class SwagItem(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='swag_items'
    )
    name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} - {self.event.title}'

    @property
    def remaining(self):
        collected = self.collections.count()
        return self.quantity - collected


class CheckIn(models.Model):
    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE,
        related_name='checkin_record'
    )
    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='checkins_performed'
    )
    checked_in_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-checked_in_at']
        indexes = [
            models.Index(fields=['checked_in_at']),
        ]


class SwagCollection(models.Model):
    checkin = models.ForeignKey(
        CheckIn,
        on_delete=models.CASCADE,
        related_name='swag_collections'
    )
    item = models.ForeignKey(
        SwagItem,
        on_delete=models.CASCADE,
        related_name='collections'
    )
    collected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('checkin', 'item')

    def __str__(self):
        return f'{self.item.name} collected by {self.checkin.ticket.booking.user}'
