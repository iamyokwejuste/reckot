import logging
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from decimal import Decimal
from apps.payments.models import Payment
from apps.payments.gateways import GatewayManager
from apps.payments.gateways.base import PaymentStatus
from apps.payments.invoice_service import create_invoice
from apps.tickets.models import Booking

logger = logging.getLogger(__name__)
gateway_manager = GatewayManager()


def calculate_booking_amount(booking: Booking) -> Decimal:
    return sum(
        t.ticket_type.price for t in booking.tickets.select_related('ticket_type')
    )


def initiate_payment(booking: Booking, provider: str, phone: str, **kwargs) -> tuple[Payment, dict]:
    with transaction.atomic():
        amount = calculate_booking_amount(booking)
        currency = kwargs.get('currency', settings.PAYMENT_GATEWAYS.get('DEFAULT_CURRENCY', 'XAF'))

        if booking.user:
            default_email = booking.user.email
        else:
            default_email = booking.guest_email or ''

        existing_payment = Payment.objects.filter(
            booking=booking,
            status=Payment.Status.PENDING
        ).first()

        if existing_payment:
            existing_payment.phone_number = phone
            existing_payment.provider = provider
            existing_payment.expires_at = timezone.now() + timedelta(minutes=30)
            existing_payment.save()
            payment = existing_payment
        else:
            payment = Payment.objects.create(
                booking=booking,
                amount=amount,
                currency=currency,
                provider=provider,
                phone_number=phone,
                customer_email=kwargs.get('email', default_email),
                expires_at=timezone.now() + timedelta(minutes=30)
            )

        callback_base = settings.PAYMENT_GATEWAYS.get('CALLBACK_BASE_URL', '')
        if provider == 'CAMPAY':
            callback_url = f"{callback_base}/payments/webhook/campay/"
        else:
            callback_url = f"{callback_base}/payments/webhook/"

        result, used_provider = gateway_manager.initiate_payment(
            amount=amount,
            currency=currency,
            phone_number=phone,
            reference=str(payment.reference),
            description=f'Tickets for {booking.event.title}',
            callback_url=callback_url,
            preferred_provider=provider,
            email=payment.customer_email,
            **kwargs
        )

        if result.success:
            payment.external_reference = result.external_reference or ''
            payment.redirect_url = result.redirect_url or ''
            payment.provider = used_provider
            payment.metadata = {
                'gateway_response': result.raw_response,
                'transaction_id': result.transaction_id
            }
            payment.save()

            return payment, {
                'success': True,
                'redirect_url': result.redirect_url,
                'message': result.message,
                'provider': used_provider
            }
        else:
            payment.status = Payment.Status.FAILED
            payment.metadata = {'error': result.message, 'raw': result.raw_response}
            payment.save()

            return payment, {
                'success': False,
                'message': result.message,
                'provider': used_provider
            }


def verify_and_confirm_payment(payment: Payment) -> dict:
    if payment.status == Payment.Status.CONFIRMED:
        return {'success': True, 'message': 'Payment already confirmed'}

    if payment.status == Payment.Status.EXPIRED:
        return {'success': False, 'message': 'Payment expired'}

    campay_reference = payment.metadata.get('transaction_id', '') if payment.metadata else ''
    if not campay_reference:
        campay_reference = payment.external_reference

    if not campay_reference:
        return {'success': False, 'message': 'No transaction reference available', 'status': 'PENDING'}

    result = gateway_manager.verify_payment(
        campay_reference,
        payment.provider
    )

    if result.status == PaymentStatus.SUCCESS:
        confirm_payment(payment, result.external_reference or result.transaction_id)
        return {'success': True, 'message': 'Payment confirmed'}

    elif result.status == PaymentStatus.FAILED:
        fail_payment(payment, result.message)
        return {'success': False, 'message': result.message}

    return {'success': False, 'message': 'Payment still pending', 'status': 'PENDING'}


def confirm_payment(payment: Payment, external_ref: str = '') -> Payment:
    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        if payment.status != Payment.Status.PENDING:
            return payment
        payment.status = Payment.Status.CONFIRMED
        payment.external_reference = external_ref
        payment.confirmed_at = timezone.now()
        payment.save()

    try:
        create_invoice(payment)
    except Exception:
        pass

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
        payment.provider = method
        payment.phone_number = phone
        payment.status = Payment.Status.PENDING
        payment.expires_at = timezone.now() + timedelta(minutes=30)
        payment.external_reference = ''
        payment.save()
        return payment
