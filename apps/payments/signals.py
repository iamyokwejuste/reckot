from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.payments.models import Payment, Refund, RefundAuditLog
from apps.payments.services import process_refund_payment
from apps.payments.tasks import send_refund_notification_task
from apps.tickets.models import Booking
from apps.tickets.tasks import send_ticket_confirmation_task, send_admin_sale_notifications_task


@receiver(post_save, sender=Payment)
def handle_payment_status_change(sender, instance, created, **kwargs):
    if not created and instance.status == Payment.Status.CONFIRMED:
        booking = instance.booking
        if booking.status != Booking.Status.CONFIRMED:
            booking.status = Booking.Status.CONFIRMED
            booking.save(update_fields=["status"])
        send_ticket_confirmation_task.delay(booking.id)
        send_admin_sale_notifications_task.delay(booking.id)


@receiver(pre_save, sender=Refund)
def track_refund_status_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Refund.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Refund.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Refund)
def handle_refund_status_change(sender, instance, created, **kwargs):
    old_status = getattr(instance, "_old_status", None)

    if created:
        RefundAuditLog.objects.create(
            refund=instance,
            action="CREATED",
            old_status="",
            new_status=instance.status,
            performed_by=instance.requested_by,
            notes=f"Refund requested. Reason: {instance.reason}",
        )
        send_refund_notification_task.delay(instance.id)

    elif old_status and old_status != instance.status:
        action_map = {
            Refund.Status.APPROVED: "APPROVED",
            Refund.Status.PROCESSED: "PROCESSED",
            Refund.Status.REJECTED: "REJECTED",
        }
        action = action_map.get(instance.status, "STATUS_CHANGED")

        notes = ""
        if instance.status == Refund.Status.REJECTED:
            notes = f"Rejection reason: {instance.rejection_reason}"

        RefundAuditLog.objects.create(
            refund=instance,
            action=action,
            old_status=old_status,
            new_status=instance.status,
            performed_by=instance.processed_by,
            notes=notes,
        )

        send_refund_notification_task.delay(instance.id)
