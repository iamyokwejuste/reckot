from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.tickets.models import Ticket


@receiver(post_save, sender=Ticket)
def handle_ticket_created(sender, instance, created, **kwargs):
    pass
