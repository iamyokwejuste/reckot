from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Ticket


@receiver(post_save, sender=Ticket)
def handle_ticket_created(sender, instance, created, **kwargs):
    """
    Handle ticket creation.
    Note: Ticket confirmation emails are sent when payment is confirmed,
    not when tickets are created (since tickets may be created before payment).
    """
    pass  # Confirmation handled by payment signal
