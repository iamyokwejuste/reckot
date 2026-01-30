import logging
from django.utils import timezone
from celery import shared_task

from apps.core.services.notifications import NotificationService
from apps.payments.models import Payment, Refund

logger = logging.getLogger(__name__)


@shared_task
def send_refund_notification_task(refund_id: int):
    try:
        refund = (
            Refund.objects.select_related(
                "payment__booking__user", "payment__booking__event"
            )
            .prefetch_related("payment__booking__tickets__ticket_type__event")
            .get(id=refund_id)
        )

        payment = refund.payment
        booking = payment.booking
        user = booking.user

        ticket = list(booking.tickets.all())[0] if booking.tickets.exists() else None
        if not ticket:
            logger.warning(f"Refund {refund_id} has no associated tickets")
            return

        event = booking.event
        payment_method = payment.get_provider_display()

        if user.email:
            NotificationService.send_refund_notification(
                to_email=user.email,
                refund=refund,
                event=event,
                original_amount=payment.amount,
                payment_method=payment_method,
            )

        if user.phone_number and refund.status in [
            Refund.Status.APPROVED,
            Refund.Status.PROCESSED,
        ]:
            NotificationService.send_refund_sms(
                phone_number=user.phone_number,
                refund=refund,
                event=event,
                payment_method=payment_method,
            )

        logger.info(f"Refund notification sent for refund {refund_id}")

    except Refund.DoesNotExist:
        logger.error(f"Refund {refund_id} not found")
    except Exception as e:
        logger.error(f"Failed to send refund notification: {e}")


@shared_task
def process_expired_payments_task():
    try:
        expired_count = Payment.objects.filter(
            status=Payment.Status.PENDING, expires_at__lt=timezone.now()
        ).update(status=Payment.Status.EXPIRED)

        if expired_count > 0:
            logger.info(f"Marked {expired_count} payments as expired")

    except Exception as e:
        logger.error(f"Failed to process expired payments: {e}")


@shared_task
def send_payment_reminder_task(payment_id: int):
    try:
        payment = (
            Payment.objects.select_related("booking__user", "booking__event")
            .prefetch_related("booking__tickets__ticket_type")
            .get(id=payment_id)
        )

        if payment.status != Payment.Status.PENDING:
            return

        user = payment.booking.user
        ticket = (
            list(payment.booking.tickets.all())[0]
            if payment.booking.tickets.exists()
            else None
        )
        if not ticket:
            return

        event = payment.booking.event
        minutes_remaining = max(
            0, int((payment.expires_at - timezone.now()).total_seconds() / 60)
        )

        if user.phone_number and minutes_remaining > 0:
            NotificationService.send_sms(
                phone_number=user.phone_number,
                template_name="sms/payment_reminder.txt",
                context={
                    "event": event,
                    "booking": payment.booking,
                    "minutes_remaining": minutes_remaining,
                },
            )
            logger.info(f"Payment reminder sent for payment {payment_id}")

    except Payment.DoesNotExist:
        logger.error(f"Payment {payment_id} not found")
    except Exception as e:
        logger.error(f"Failed to send payment reminder: {e}")
