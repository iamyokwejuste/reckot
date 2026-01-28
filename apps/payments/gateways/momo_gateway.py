from decimal import Decimal
from typing import Optional
from django.conf import settings
from .base import PaymentGateway, PaymentResult, RefundResult
import logging
import requests
import uuid

logger = logging.getLogger(__name__)


class MoMoGateway(PaymentGateway):
    def __init__(self):
        self.api_key = getattr(settings, 'MOMO_API_KEY', '')
        self.api_secret = getattr(settings, 'MOMO_API_SECRET', '')
        self.base_url = getattr(settings, 'MOMO_API_URL', 'https://sandbox.momodeveloper.mtn.com')
        self.subscription_key = getattr(settings, 'MOMO_SUBSCRIPTION_KEY', '')

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
        if not customer_phone:
            return PaymentResult(success=False, reference=reference, error_message="Phone number required")

        external_id = str(uuid.uuid4())
        try:
            response = requests.post(
                f'{self.base_url}/collection/v1_0/requesttopay',
                headers={
                    'Authorization': f'Bearer {self._get_token()}',
                    'X-Reference-Id': external_id,
                    'X-Target-Environment': 'sandbox',
                    'Ocp-Apim-Subscription-Key': self.subscription_key,
                    'Content-Type': 'application/json',
                },
                json={
                    'amount': str(int(amount)),
                    'currency': currency,
                    'externalId': reference,
                    'payer': {'partyIdType': 'MSISDN', 'partyId': customer_phone.replace('+', '')},
                    'payerMessage': description,
                    'payeeNote': description,
                },
                timeout=30
            )
            if response.status_code == 202:
                return PaymentResult(
                    success=True,
                    reference=reference,
                    external_reference=external_id,
                    requires_verification=True,
                )
            return PaymentResult(success=False, reference=reference, error_message=response.text)
        except Exception as e:
            logger.error(f"MoMo payment error: {e}")
            return PaymentResult(success=False, reference=reference, error_message=str(e))

    def _get_token(self) -> str:
        try:
            response = requests.post(
                f'{self.base_url}/collection/token/',
                auth=(self.api_key, self.api_secret),
                headers={'Ocp-Apim-Subscription-Key': self.subscription_key},
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get('access_token', '')
        except Exception as e:
            logger.error(f"MoMo token error: {e}")
        return ''

    def verify_payment(self, reference: str, external_reference: str) -> PaymentResult:
        try:
            response = requests.get(
                f'{self.base_url}/collection/v1_0/requesttopay/{external_reference}',
                headers={
                    'Authorization': f'Bearer {self._get_token()}',
                    'X-Target-Environment': 'sandbox',
                    'Ocp-Apim-Subscription-Key': self.subscription_key,
                },
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'SUCCESSFUL':
                    return PaymentResult(success=True, reference=reference, external_reference=external_reference)
                elif data.get('status') == 'PENDING':
                    return PaymentResult(success=False, reference=reference, requires_verification=True)
            return PaymentResult(success=False, reference=reference, error_message="Payment failed")
        except Exception as e:
            return PaymentResult(success=False, reference=reference, error_message=str(e))

    def process_refund(self, payment_reference: str, amount: Decimal, reason: str) -> RefundResult:
        return RefundResult(success=False, reference=payment_reference, error_message="MoMo refunds not supported via API")

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        return True

    def get_supported_currencies(self) -> list[str]:
        return ['XAF', 'XOF', 'UGX', 'GHS']
