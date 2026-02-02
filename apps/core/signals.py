from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from apps.tickets.models import Booking
from apps.payments.models import Payment, Refund
from apps.core.models import Notification


@receiver(post_save, sender=Booking)
def create_ticket_purchase_notification(sender, instance, created, **kwargs):
    if created and instance.user and instance.status == Booking.Status.CONFIRMED:
        Notification.objects.create(
            user=instance.user,
            notification_type=Notification.Type.TICKET_PURCHASE,
            title=f"Ticket confirmed for {instance.event.title}",
            message=f"Your ticket for {instance.event.title} has been confirmed. Check your email for details.",
            link=f"/tickets/my/",
        )


@receiver(post_save, sender=Payment)
def create_payment_notification(sender, instance, created, **kwargs):
    if not created and instance.status == Payment.Status.CONFIRMED and instance.booking.user:
        Notification.objects.create(
            user=instance.booking.user,
            notification_type=Notification.Type.PAYMENT_CONFIRMED,
            title=f"Payment confirmed",
            message=f"Your payment of {instance.amount} {instance.currency} for {instance.booking.event.title} has been confirmed.",
            link=f"/tickets/my/",
        )


@receiver(post_save, sender=Refund)
def create_refund_notification(sender, instance, created, **kwargs):
    if instance.payment.booking.user:
        if created and instance.status == Refund.Status.APPROVED:
            Notification.objects.create(
                user=instance.payment.booking.user,
                notification_type=Notification.Type.REFUND_APPROVED,
                title="Refund approved",
                message=f"Your refund request for {instance.payment.booking.event.title} has been approved.",
                link=f"/tickets/my/",
            )
        elif not created and instance.status == Refund.Status.PROCESSED:
            Notification.objects.create(
                user=instance.payment.booking.user,
                notification_type=Notification.Type.REFUND_PROCESSED,
                title="Refund processed",
                message=f"Your refund of {instance.amount} {instance.payment.currency} has been processed and will arrive soon.",
                link=f"/tickets/my/",
            )
