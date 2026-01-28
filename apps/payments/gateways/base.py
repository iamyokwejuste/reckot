from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class PaymentResult:
    success: bool
    reference: str
    external_reference: Optional[str] = None
    redirect_url: Optional[str] = None
    error_message: Optional[str] = None
    requires_redirect: bool = False
    requires_verification: bool = False


@dataclass
class RefundResult:
    success: bool
    reference: str
    error_message: Optional[str] = None


class PaymentGateway(ABC):
    @abstractmethod
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
        pass

    @abstractmethod
    def verify_payment(self, reference: str, external_reference: str) -> PaymentResult:
        pass

    @abstractmethod
    def process_refund(
        self,
        payment_reference: str,
        amount: Decimal,
        reason: str,
    ) -> RefundResult:
        pass

    @abstractmethod
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        pass

    def get_supported_currencies(self) -> list[str]:
        return ['XAF', 'USD', 'EUR']
