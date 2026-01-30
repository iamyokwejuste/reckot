import logging
from django_tasks import task

logger = logging.getLogger(__name__)


@task
def send_refund_notification_task(refund_id: int):
    from .models import Refund
    from apps.core.services.notifications import NotificationService

    try:
        refund = Refund.objects.select_related(
            'payment__booking__user',
            'payment__booking'
        ).get(id=refund_id)

        payment = refund.payment
        booking = payment.booking
        user = booking.user

        ticket = booking.tickets.select_related('ticket_type__event').first()
        if not ticket:
            logger.warning(f"Refund {refund_id} has no associated tickets")
            return

        event = ticket.ticket_type.event
        payment_method = payment.get_provider_display()

        if user.email:
            NotificationService.send_refund_notification(
                to_email=user.email,
                refund=refund,
                event=event,
                original_amount=payment.amount,
                payment_method=payment_method
            )

        if user.phone_number and refund.status in [Refund.Status.APPROVED, Refund.Status.PROCESSED]:
            NotificationService.send_refund_sms(
                phone_number=user.phone_number,
                refund=refund,
                event=event,
                payment_method=payment_method
            )

        logger.info(f"Refund notification sent for refund {refund_id}")

    except Refund.DoesNotExist:
        logger.error(f"Refund {refund_id} not found")
    except Exception as e:
        logger.error(f"Failed to send refund notification: {e}")


@task
def process_expired_payments_task():
    from django.utils import timezone
    from .models import Payment

    try:
        expired_count = Payment.objects.filter(
            status=Payment.Status.PENDING,
            expires_at__lt=timezone.now()
        ).update(status=Payment.Status.EXPIRED)

        if expired_count > 0:
            logger.info(f"Marked {expired_count} payments as expired")

    except Exception as e:
        logger.error(f"Failed to process expired payments: {e}")


@task
def send_payment_reminder_task(payment_id: int):
    from django.utils import timezone
    from .models import Payment
    from apps.core.services.notifications import NotificationService

    try:
        payment = Payment.objects.select_related(
            'booking__user'
        ).get(id=payment_id)

        if payment.status != Payment.Status.PENDING:
            return

        user = payment.booking.user
        ticket = payment.booking.tickets.select_related('ticket_type__event').first()
        if not ticket:
            return

        event = ticket.ticket_type.event
        minutes_remaining = max(0, int((payment.expires_at - timezone.now()).total_seconds() / 60))

        if user.phone_number and minutes_remaining > 0:
            NotificationService.send_sms(
                phone_number=user.phone_number,
                template_name='sms/payment_reminder.txt',
                context={
                    'event': event,
                    'booking': payment.booking,
                    'minutes_remaining': minutes_remaining,
                }
            )
            logger.info(f"Payment reminder sent for payment {payment_id}")

    except Payment.DoesNotExist:
        logger.error(f"Payment {payment_id} not found")
    except Exception as e:
        logger.error(f"Failed to send payment reminder: {e}")
