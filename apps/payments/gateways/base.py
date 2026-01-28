from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from enum import Enum


class PaymentStatus(Enum):
    PENDING = 'PENDING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'


@dataclass
class PaymentResult:
    success: bool
    transaction_id: Optional[str] = None
    external_reference: Optional[str] = None
    redirect_url: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    message: str = ''
    raw_response: Optional[dict] = None


class PaymentGateway(ABC):
    name: str = 'base'
    display_name: str = 'Base Gateway'
    supported_currencies: list = ['XAF']

    def __init__(self, credentials: dict):
        self.credentials = credentials
        self.validate_credentials()

    def validate_credentials(self):
        pass

    @abstractmethod
    def initiate_payment(
        self,
        amount: Decimal,
        currency: str,
        phone_number: str,
        reference: str,
        description: str = '',
        callback_url: str = '',
        **kwargs
    ) -> PaymentResult:
        pass

    @abstractmethod
    def verify_payment(self, reference: str) -> PaymentResult:
        pass

    @abstractmethod
    def check_status(self, external_reference: str) -> PaymentResult:
        pass

    def refund(self, external_reference: str, amount: Decimal) -> PaymentResult:
        return PaymentResult(
            success=False,
            message='Refunds not supported by this gateway'
        )

    def format_phone(self, phone: str, country_code: str = '237') -> str:
        phone = ''.join(filter(str.isdigit, phone))
        if phone.startswith('00'):
            phone = phone[2:]
        if phone.startswith('+'):
            phone = phone[1:]
        if not phone.startswith(country_code):
            phone = country_code + phone
        return phone
