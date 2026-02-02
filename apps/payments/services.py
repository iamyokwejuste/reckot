import logging
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.events.models import FlyerBilling
from apps.payments.gateways import GatewayManager
from apps.payments.gateways.base import PaymentStatus
from apps.payments.gateways.campay import CampayGateway
from apps.payments.gateways.flutterwave import FlutterwaveGateway
from apps.payments.gateways.pawapay import PawapayGateway
from apps.payments.invoice_service import create_invoice
from apps.payments.models import Payment, PaymentGatewayConfig, Refund, Withdrawal
from apps.tickets.models import Booking

logger = logging.getLogger(__name__)
gateway_manager = GatewayManager()

GATEWAY_CLASSES = {
    "CAMPAY": CampayGateway,
    "PAWAPAY": PawapayGateway,
    "FLUTTERWAVE": FlutterwaveGateway,
}


def calculate_booking_amount(booking: Booking) -> Decimal:
    tickets_qs = booking.ticket_set.select_related("ticket_type")
    total = sum(Decimal(t.ticket_type.price) for t in tickets_qs)
    return Decimal(total)


def calculate_organization_balance(organization):
    confirmed_payments = Payment.objects.filter(
        booking__event__organization=organization, status=Payment.Status.CONFIRMED
    ).aggregate(total_revenue=Sum("amount"), total_service_fees=Sum("service_fee"))

    total_revenue = confirmed_payments["total_revenue"] or Decimal("0")
    total_service_fees = confirmed_payments["total_service_fees"] or Decimal("0")

    total_withdrawals = Withdrawal.objects.filter(
        organization=organization,
        status__in=[Withdrawal.Status.COMPLETED, Withdrawal.Status.PROCESSING],
    ).aggregate(total=Sum("amount"))

    total_withdrawn = total_withdrawals["total"] or Decimal("0")

    total_refunds = Refund.objects.filter(
        payment__booking__event__organization=organization,
        status=Refund.Status.PROCESSED,
    ).aggregate(total=Sum("amount"))

    total_refunded = total_refunds["total"] or Decimal("0")

    pending_flyer_bills = FlyerBilling.objects.filter(
        event__organization=organization, status__in=["PENDING", "INVOICED"]
    ).aggregate(total=Sum("total_amount"))

    total_flyer_bills = pending_flyer_bills["total"] or Decimal("0")

    available_balance = (
        total_revenue
        - total_service_fees
        - total_withdrawn
        - total_refunded
        - total_flyer_bills
    )

    return {
        "total_revenue": total_revenue,
        "service_fees": total_service_fees,
        "total_withdrawn": total_withdrawn,
        "total_refunded": total_refunded,
        "pending_flyer_bills": total_flyer_bills,
        "available_balance": available_balance,
    }


def initiate_payment(
    booking: Booking, provider: str, phone: str, **kwargs
) -> tuple[Payment, dict]:
    with transaction.atomic():
        amount = calculate_booking_amount(booking)
        currency = kwargs.get(
            "currency", settings.PAYMENT_GATEWAYS.get("DEFAULT_CURRENCY", "XAF")
        )

        if booking.user:
            default_email = booking.user.email
        else:
            default_email = booking.guest_email or ""

        organization = booking.event.organization
        gateway_config = None
        try:
            gateway_config = PaymentGatewayConfig.objects.filter(
                organization=organization, provider=provider, is_active=True
            ).first()

            if not gateway_config:
                global_credentials = settings.PAYMENT_GATEWAYS.get(
                    "CREDENTIALS", {}
                ).get(provider, {})
                if global_credentials:
                    gateway_config = PaymentGatewayConfig.objects.create(
                        organization=organization,
                        provider=provider,
                        is_active=True,
                        is_default=True,
                        credentials=global_credentials,
                        supported_currencies=[
                            "XAF",
                            "XOF",
                            "USD",
                            "EUR",
                            "GBP",
                            "NGN",
                            "GHS",
                            "UGX",
                        ],
                        service_fee_type=PaymentGatewayConfig.ServiceFeeType.PERCENTAGE,
                        service_fee_percentage=0,
                    )
                    logger.info(
                        f"Created default gateway config for {organization.name} with provider {provider}"
                    )
        except Exception as e:
            logger.warning(f"Failed to get/create gateway config: {e}")

        existing_payment = Payment.objects.filter(
            booking=booking, status=Payment.Status.PENDING
        ).first()

        if existing_payment:
            existing_payment.phone_number = phone
            existing_payment.provider = provider
            existing_payment.gateway_config = gateway_config
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
                customer_email=kwargs.get("email", default_email),
                gateway_config=gateway_config,
                expires_at=timezone.now() + timedelta(minutes=30),
            )

        callback_base = settings.PAYMENT_GATEWAYS.get("CALLBACK_BASE_URL", "")
        if provider == "CAMPAY":
            callback_url = f"{callback_base}/payments/webhook/campay/"
        elif provider == "FLUTTERWAVE":
            callback_url = f"{callback_base}/payments/webhook/flutterwave/"
        else:
            callback_url = f"{callback_base}/payments/webhook/"

        result, used_provider = gateway_manager.initiate_payment(
            amount=amount,
            currency=currency,
            phone_number=phone,
            reference=str(payment.reference),
            description=f"Tickets for {booking.event.title}",
            callback_url=callback_url,
            preferred_provider=provider,
            email=payment.customer_email,
            **kwargs,
        )

        if result.success:
            payment.external_reference = result.external_reference or ""
            payment.redirect_url = result.redirect_url or ""
            payment.provider = used_provider
            payment.metadata = {
                "gateway_response": result.raw_response,
                "transaction_id": result.transaction_id,
                "payment_method": kwargs.get("payment_method", ""),
            }
            payment.save()

            return payment, {
                "success": True,
                "redirect_url": result.redirect_url,
                "message": result.message,
                "provider": used_provider,
            }
        else:
            payment.status = Payment.Status.FAILED
            payment.metadata = {"error": result.message, "raw": result.raw_response}
            payment.save()

            return payment, {
                "success": False,
                "message": result.message,
                "provider": used_provider,
            }


def verify_and_confirm_payment(payment: Payment) -> dict:
    if payment.status == Payment.Status.CONFIRMED:
        return {"success": True, "message": "Payment already confirmed"}

    if payment.status == Payment.Status.EXPIRED:
        return {"success": False, "message": "Payment expired"}

    campay_reference = (
        payment.metadata.get("transaction_id", "") if payment.metadata else ""
    )
    if not campay_reference:
        campay_reference = payment.external_reference

    if not campay_reference:
        return {
            "success": False,
            "message": "No transaction reference available",
            "status": "PENDING",
        }

    result = gateway_manager.verify_payment(campay_reference, payment.provider)

    if result.status == PaymentStatus.SUCCESS:
        confirm_payment(payment, result.external_reference or result.transaction_id)
        return {"success": True, "message": "Payment confirmed"}

    elif result.status == PaymentStatus.FAILED:
        fail_payment(payment, result.message)
        return {"success": False, "message": result.message}

    return {"success": False, "message": "Payment still pending", "status": "PENDING"}


def confirm_payment(payment: Payment, external_ref: str = "") -> Payment:
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


def fail_payment(payment: Payment, reason: str = "") -> Payment:
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
        status=Payment.Status.PENDING, expires_at__lt=timezone.now()
    ).update(status=Payment.Status.EXPIRED)


def retry_payment(payment: Payment, method: str, phone: str) -> Payment:
    with transaction.atomic():
        if payment.status not in [Payment.Status.FAILED, Payment.Status.EXPIRED]:
            return payment
        payment.provider = method
        payment.phone_number = phone
        payment.status = Payment.Status.PENDING
        payment.expires_at = timezone.now() + timedelta(minutes=30)
        payment.external_reference = ""
        payment.save()
        return payment


def process_refund_payment(refund):
    logger.info(f"Starting refund process for refund ID: {refund.id}")

    payment = refund.payment
    logger.info(
        f"Payment reference: {payment.reference}, Status: {payment.status}, Provider: {payment.provider}"
    )

    if not payment.external_reference:
        logger.error(
            f"Payment {payment.reference} has no external reference for refund"
        )
        return False

    organization = payment.booking.event.organization
    balance_data = calculate_organization_balance(organization)
    available_balance = balance_data["available_balance"]

    if available_balance < refund.amount:
        logger.error(
            f"Insufficient balance for refund. Available: {available_balance} {payment.currency}, Required: {refund.amount} {payment.currency}"
        )
        return False

    logger.info(f"External reference: {payment.external_reference}")

    gateway_config = payment.gateway_config

    if not gateway_config:
        logger.warning(
            f"Payment {payment.reference} has no gateway config, trying to get from organization"
        )

        try:
            organization = payment.booking.event.organization
            gateway_config = PaymentGatewayConfig.objects.filter(
                organization=organization, provider=payment.provider, is_active=True
            ).first()

            if gateway_config:
                logger.info(
                    f"Using organization gateway config: {gateway_config.provider}"
                )
                payment.gateway_config = gateway_config
                payment.save(update_fields=["gateway_config"])
            else:
                if payment.provider == "CAMPAY":
                    logger.warning(
                        f"No organization config for {payment.provider}, attempting to use global credentials"
                    )
                    global_credentials = settings.PAYMENT_GATEWAYS.get(
                        "CREDENTIALS", {}
                    ).get("CAMPAY", {})

                    if global_credentials:
                        gateway_config = PaymentGatewayConfig.objects.create(
                            organization=organization,
                            provider="CAMPAY",
                            is_active=True,
                            is_default=True,
                            credentials=global_credentials,
                            supported_currencies=[
                                "XAF",
                                "XOF",
                                "USD",
                                "EUR",
                                "GBP",
                                "NGN",
                                "GHS",
                                "UGX",
                            ],
                            service_fee_type=PaymentGatewayConfig.ServiceFeeType.PERCENTAGE,
                            service_fee_percentage=0,
                        )
                        logger.info(
                            f"Created default CAMPAY gateway config for {organization.name}"
                        )
                        payment.gateway_config = gateway_config
                        payment.save(update_fields=["gateway_config"])
                    else:
                        logger.error("No global CAMPAY credentials found in settings")
                        return False
                else:
                    logger.error(
                        f"No active gateway config found for organization {organization.name} with provider {payment.provider}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Failed to get gateway config from organization: {e}")
            return False

    logger.info(f"Gateway config found: {gateway_config.provider}")

    try:
        gateway_class = GATEWAY_CLASSES.get(payment.provider)
        if not gateway_class:
            logger.error(f"Unknown payment provider: {payment.provider}")
            return False

        gateway = gateway_class(gateway_config.credentials)

        logger.info(f"Calling gateway refund with amount: {refund.amount}, phone: {payment.phone_number}")

        result = gateway.refund(
            external_reference=payment.external_reference,
            amount=refund.amount,
            phone_number=payment.phone_number
        )

        logger.info(
            f"Gateway refund result - Success: {result.success}, Message: {result.message}"
        )

        if result.success:
            with transaction.atomic():
                booking = payment.booking
                if booking and refund.refund_type == refund.Type.FULL:
                    logger.info(
                        f"Updating booking {booking.reference} status to REFUNDED"
                    )
                    booking.status = Booking.Status.REFUNDED
                    booking.save(update_fields=["status"])

            logger.info(
                f"Refund processed successfully for payment {payment.reference}"
            )
            return True
        else:
            logger.error(
                f"Refund failed for payment {payment.reference}: {result.message}"
            )
            return False

    except Exception as e:
        logger.error(
            f"Failed to process refund for payment {payment.reference}: {e}",
            exc_info=True,
        )
        return False
