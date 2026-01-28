from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Payment, Refund, RefundAuditLog


@receiver(post_save, sender=Payment)
def handle_payment_status_change(sender, instance, created, **kwargs):
    """
    Handle payment status changes.
    - On confirmation: send ticket confirmation email/SMS
    """
    if not created and instance.status == Payment.Status.CONFIRMED:
        from apps.tickets.tasks import send_ticket_confirmation_task

        booking = instance.booking
        send_ticket_confirmation_task(booking.id)


@receiver(pre_save, sender=Refund)
def track_refund_status_change(sender, instance, **kwargs):
    """Track the old status before save for audit logging."""
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
    """
    Handle refund status changes.
    - Create audit log
    - Send notification emails/SMS
    """
    from apps.payments.tasks import send_refund_notification_task

    old_status = getattr(instance, '_old_status', None)

    # Create audit log for status changes
    if created:
        RefundAuditLog.objects.create(
            refund=instance,
            action='CREATED',
            old_status='',
            new_status=instance.status,
            performed_by=instance.requested_by,
            notes=f'Refund requested. Reason: {instance.reason}'
        )
        # Send pending notification
        send_refund_notification_task(instance.id)

    elif old_status and old_status != instance.status:
        action_map = {
            Refund.Status.APPROVED: 'APPROVED',
            Refund.Status.PROCESSED: 'PROCESSED',
            Refund.Status.REJECTED: 'REJECTED',
        }
        action = action_map.get(instance.status, 'STATUS_CHANGED')

        notes = ''
        if instance.status == Refund.Status.REJECTED:
            notes = f'Rejection reason: {instance.rejection_reason}'

        RefundAuditLog.objects.create(
            refund=instance,
            action=action,
            old_status=old_status,
            new_status=instance.status,
            performed_by=instance.processed_by,
            notes=notes
        )

        # Send notification for status change
        send_refund_notification_task(instance.id)
