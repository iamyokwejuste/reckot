import logging
from decimal import Decimal
from typing import Optional, List
from django.conf import settings

from apps.payments.gateways.base import PaymentGateway, PaymentResult, PaymentStatus
from apps.payments.gateways.campay import CampayGateway
from apps.payments.gateways.pawapay import PawapayGateway
from apps.payments.gateways.flutterwave import FlutterwaveGateway

logger = logging.getLogger(__name__)


GATEWAY_CLASSES = {
    "CAMPAY": CampayGateway,
    "PAWAPAY": PawapayGateway,
    "FLUTTERWAVE": FlutterwaveGateway,
}


class GatewayManager:
    def __init__(self):
        self.config = getattr(settings, "PAYMENT_GATEWAYS", {})
        self.primary = self.config.get("PRIMARY", "CAMPAY")
        self.fallbacks = self.config.get("FALLBACKS", ["PAWAPAY", "FLUTTERWAVE"])
        self._gateways = {}

    def _get_gateway(self, provider: str) -> Optional[PaymentGateway]:
        if provider in self._gateways:
            return self._gateways[provider]

        gateway_class = GATEWAY_CLASSES.get(provider)
        if not gateway_class:
            logger.warning(f"Unknown payment provider: {provider}")
            return None

        credentials = self.config.get("CREDENTIALS", {}).get(provider, {})
        if not credentials:
            logger.warning(f"No credentials configured for {provider}")
            return None

        try:
            gateway = gateway_class(credentials)
            self._gateways[provider] = gateway
            return gateway
        except Exception as e:
            logger.error(f"Failed to initialize {provider} gateway: {e}")
            return None

    def get_available_gateways(self) -> List[str]:
        available = []
        for provider in [self.primary] + self.fallbacks:
            gateway = self._get_gateway(provider)
            if gateway:
                available.append(provider)
        return available

    def initiate_payment(
        self,
        amount: Decimal,
        currency: str,
        phone_number: str,
        reference: str,
        description: str = "",
        callback_url: str = "",
        preferred_provider: Optional[str] = None,
        **kwargs,
    ) -> tuple[PaymentResult, str]:
        providers = [preferred_provider] if preferred_provider else []
        providers.extend([self.primary] + self.fallbacks)
        providers = list(dict.fromkeys(p for p in providers if p))

        last_result = None
        used_provider = None

        for provider in providers:
            gateway = self._get_gateway(provider)
            if not gateway:
                continue

            if currency not in gateway.supported_currencies:
                logger.info(f"{provider} does not support {currency}")
                continue

            logger.info(f"Attempting payment with {provider}")

            result = gateway.initiate_payment(
                amount=amount,
                currency=currency,
                phone_number=phone_number,
                reference=reference,
                description=description,
                callback_url=callback_url,
                **kwargs,
            )

            if result.success:
                logger.info(f"Payment initiated successfully with {provider}")
                return result, provider

            last_result = result
            used_provider = provider
            logger.warning(f"{provider} payment failed: {result.message}")

        if last_result:
            return last_result, used_provider or self.primary

        return PaymentResult(
            success=False,
            status=PaymentStatus.FAILED,
            message="No payment gateway available",
        ), ""

    def verify_payment(self, reference: str, provider: str) -> PaymentResult:
        gateway = self._get_gateway(provider)
        if not gateway:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message=f"Gateway {provider} not available",
            )

        return gateway.verify_payment(reference)

    def check_status(self, external_reference: str, provider: str) -> PaymentResult:
        gateway = self._get_gateway(provider)
        if not gateway:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message=f"Gateway {provider} not available",
            )

        return gateway.check_status(external_reference)

    def process_refund(
        self, external_reference: str, amount: Decimal, provider: str
    ) -> PaymentResult:
        gateway = self._get_gateway(provider)
        if not gateway:
            return PaymentResult(
                success=False, message=f"Gateway {provider} not available"
            )

        return gateway.refund(external_reference, amount)


gateway_manager = GatewayManager()
