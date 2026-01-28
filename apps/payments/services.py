from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Payment
from apps.tickets.models import Booking


def calculate_booking_amount(booking: Booking) -> Decimal:
    return sum(
        t.ticket_type.price for t in booking.tickets.select_related('ticket_type')
    )


def initiate_payment(booking: Booking, method: str, phone: str) -> Payment:
    with transaction.atomic():
        amount = calculate_booking_amount(booking)
        payment = Payment.objects.create(
            booking=booking,
            amount=amount,
            method=method,
            phone_number=phone,
            expires_at=timezone.now() + timedelta(minutes=30)
        )
        return payment


def confirm_payment(payment: Payment, external_ref: str = '') -> Payment:
    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        if payment.status != Payment.Status.PENDING:
            return payment
        payment.status = Payment.Status.CONFIRMED
        payment.external_reference = external_ref
        payment.confirmed_at = timezone.now()
        payment.save()
        return payment


def fail_payment(payment: Payment, reason: str = '') -> Payment:
    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        if payment.status != Payment.Status.PENDING:
            return payment
        payment.status = Payment.Status.FAILED
        payment.external_reference = reason
        payment.save()
        return payment


def expire_stale_payments() -> int:
    return Payment.objects.filter(
        status=Payment.Status.PENDING,
        expires_at__lt=timezone.now()
    ).update(status=Payment.Status.EXPIRED)


def retry_payment(payment: Payment, method: str, phone: str) -> Payment:
    with transaction.atomic():
        if payment.status not in [Payment.Status.FAILED, Payment.Status.EXPIRED]:
            return payment
        payment.method = method
        payment.phone_number = phone
        payment.status = Payment.Status.PENDING
        payment.expires_at = timezone.now() + timedelta(minutes=30)
        payment.external_reference = ''
        payment.save()
        return payment
