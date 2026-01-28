from decimal import Decimal
from typing import Optional
from django.conf import settings
from .base import PaymentGateway, PaymentResult, RefundResult
import logging

logger = logging.getLogger(__name__)


class StripeGateway(PaymentGateway):
    def __init__(self):
        self.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        self.webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')

    def _get_stripe(self):
        try:
            import stripe
            stripe.api_key = self.api_key
            return stripe
        except ImportError:
            logger.error("Stripe library not installed")
            return None

    def initiate_payment(
        self,
        amount: Decimal,
        currency: str,
        reference: str,
        description: str,
        return_url: str,
        cancel_url: str,
        customer_email: str,
        customer_phone: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> PaymentResult:
        stripe = self._get_stripe()
        if not stripe:
            return PaymentResult(
                success=False,
                reference=reference,
                error_message="Stripe not configured"
            )

        try:
            amount_cents = int(amount * 100)
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': currency.lower(),
                        'product_data': {'name': description},
                        'unit_amount': amount_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=return_url,
                cancel_url=cancel_url,
                customer_email=customer_email,
                client_reference_id=reference,
                metadata=metadata or {},
            )
            return PaymentResult(
                success=True,
                reference=reference,
                external_reference=session.id,
                redirect_url=session.url,
                requires_redirect=True,
            )
        except Exception as e:
            logger.error(f"Stripe payment error: {e}")
            return PaymentResult(
                success=False,
                reference=reference,
                error_message=str(e)
            )

    def verify_payment(self, reference: str, external_reference: str) -> PaymentResult:
        stripe = self._get_stripe()
        if not stripe:
            return PaymentResult(success=False, reference=reference, error_message="Stripe not configured")

        try:
            session = stripe.checkout.Session.retrieve(external_reference)
            if session.payment_status == 'paid':
                return PaymentResult(success=True, reference=reference, external_reference=external_reference)
            return PaymentResult(success=False, reference=reference, error_message="Payment not completed")
        except Exception as e:
            return PaymentResult(success=False, reference=reference, error_message=str(e))

    def process_refund(self, payment_reference: str, amount: Decimal, reason: str) -> RefundResult:
        stripe = self._get_stripe()
        if not stripe:
            return RefundResult(success=False, reference=payment_reference, error_message="Stripe not configured")

        try:
            refund = stripe.Refund.create(
                payment_intent=payment_reference,
                amount=int(amount * 100),
                reason='requested_by_customer',
            )
            return RefundResult(success=True, reference=refund.id)
        except Exception as e:
            return RefundResult(success=False, reference=payment_reference, error_message=str(e))

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        stripe = self._get_stripe()
        if not stripe:
            return False
        try:
            stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
            return True
        except Exception:
            return False

    def get_supported_currencies(self) -> list[str]:
        return ['USD', 'EUR', 'GBP', 'XAF', 'NGN']
