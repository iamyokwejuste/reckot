from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from enum import Enum


class PaymentStatus(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class PaymentResult:
    success: bool
    transaction_id: Optional[str] = None
    external_reference: Optional[str] = None
    redirect_url: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    message: str = ""
    raw_response: Optional[dict] = None
    reference: Optional[str] = None
    error_message: str = ""
    requires_verification: bool = False
    requires_redirect: bool = False


@dataclass
class RefundResult:
    success: bool
    refund_id: Optional[str] = None
    amount: Optional[Decimal] = None
    message: str = ""
    raw_response: Optional[dict] = None


class PaymentGateway(ABC):
    name: str = "base"
    display_name: str = "Base Gateway"
    supported_currencies: list = ["XAF"]

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
        description: str = "",
        callback_url: str = "",
        **kwargs,
    ) -> PaymentResult:
        pass

    @abstractmethod
    def verify_payment(self, reference: str) -> PaymentResult:
        pass

    @abstractmethod
    def check_status(self, reference: str) -> PaymentResult:
        pass

    def refund(
        self, external_reference: str, amount: Decimal, phone_number: str = None
    ) -> PaymentResult:
        return PaymentResult(
            success=False, message="Refunds not supported by this gateway"
        )

    def format_phone(self, phone: str, country_code: str = "237") -> str:
        phone = "".join(filter(str.isdigit, phone))
        if phone.startswith("00"):
            phone = phone[2:]
        if phone.startswith("+"):
            phone = phone[1:]
        if not phone.startswith(country_code):
            phone = country_code + phone
        return phone

    @staticmethod
    def detect_carrier(phone: str) -> str:
        phone = "".join(filter(str.isdigit, phone))
        if phone.startswith("237"):
            phone = phone[3:]

        if len(phone) < 2:
            return "UNKNOWN"

        mtn_prefixes = [
            "67",
            "650",
            "651",
            "652",
            "653",
            "654",
            "680",
            "681",
            "682",
            "683",
        ]
        orange_prefixes = [
            "640",
            "655",
            "656",
            "657",
            "658",
            "659",
            "686",
            "687",
            "688",
            "689",
            "69",
        ]

        for p in mtn_prefixes:
            if phone.startswith(p):
                return "MTN"

        for p in orange_prefixes:
            if phone.startswith(p):
                return "ORANGE"

        return "UNKNOWN"

    @staticmethod
    def validate_cameroon_phone(phone: str) -> tuple[bool, str]:
        import re

        phone = "".join(filter(str.isdigit, phone))

        if phone.startswith("237"):
            phone = phone[3:]

        pattern = r"^6[4-9]\d{7}$"
        if re.match(pattern, phone):
            carrier = PaymentGateway.detect_carrier(phone)
            return True, carrier

        return False, "INVALID"
