from decimal import Decimal
from typing import Optional
from apps.payments.gateways.base import PaymentGateway, PaymentResult, RefundResult
import uuid


class OfflineGateway(PaymentGateway):
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
        return PaymentResult(
            success=True,
            reference=reference,
            external_reference=f"OFFLINE-{uuid.uuid4().hex[:8].upper()}",
            requires_verification=True,
        )

    def verify_payment(self, reference: str, external_reference: str) -> PaymentResult:
        return PaymentResult(
            success=False, reference=reference, requires_verification=True
        )

    def process_refund(
        self, payment_reference: str, amount: Decimal, reason: str
    ) -> RefundResult:
        return RefundResult(
            success=True, reference=f"REFUND-{uuid.uuid4().hex[:8].upper()}"
        )

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        return True

    def get_supported_currencies(self) -> list[str]:
        return ["XAF", "USD", "EUR", "GBP", "NGN"]
