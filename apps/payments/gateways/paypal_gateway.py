from decimal import Decimal
from typing import Optional
from django.conf import settings
from apps.payments.gateways.base import PaymentGateway, PaymentResult, RefundResult
import logging
import requests

logger = logging.getLogger(__name__)


class PayPalGateway(PaymentGateway):
    def __init__(self):
        self.client_id = getattr(settings, 'PAYPAL_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'PAYPAL_CLIENT_SECRET', '')
        self.sandbox = getattr(settings, 'PAYPAL_SANDBOX', True)
        self.base_url = 'https://api-m.sandbox.paypal.com' if self.sandbox else 'https://api-m.paypal.com'

    def _get_access_token(self) -> Optional[str]:
        try:
            response = requests.post(
                f'{self.base_url}/v1/oauth2/token',
                auth=(self.client_id, self.client_secret),
                data={'grant_type': 'client_credentials'},
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get('access_token')
        except Exception as e:
            logger.error(f"PayPal auth error: {e}")
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
        token = self._get_access_token()
        if not token:
            return PaymentResult(success=False, reference=reference, error_message="PayPal auth failed")

        try:
            response = requests.post(
                f'{self.base_url}/v2/checkout/orders',
                headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                json={
                    'intent': 'CAPTURE',
                    'purchase_units': [{
                        'reference_id': reference,
                        'description': description,
                        'amount': {
                            'currency_code': currency.upper(),
                            'value': str(amount),
                        },
                    }],
                    'application_context': {
                        'return_url': return_url,
                        'cancel_url': cancel_url,
                    },
                },
                timeout=30
            )
            if response.status_code == 201:
                data = response.json()
                approve_url = next((link['href'] for link in data.get('links', []) if link['rel'] == 'approve'), None)
                return PaymentResult(
                    success=True,
                    reference=reference,
                    external_reference=data['id'],
                    redirect_url=approve_url,
                    requires_redirect=True,
                )
            return PaymentResult(success=False, reference=reference, error_message=response.text)
        except Exception as e:
            return PaymentResult(success=False, reference=reference, error_message=str(e))

    def verify_payment(self, reference: str, external_reference: str) -> PaymentResult:
        token = self._get_access_token()
        if not token:
            return PaymentResult(success=False, reference=reference, error_message="PayPal auth failed")

        try:
            response = requests.post(
                f'{self.base_url}/v2/checkout/orders/{external_reference}/capture',
                headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                timeout=30
            )
            if response.status_code == 201:
                data = response.json()
                if data.get('status') == 'COMPLETED':
                    return PaymentResult(success=True, reference=reference, external_reference=external_reference)
            return PaymentResult(success=False, reference=reference, error_message="Capture failed")
        except Exception as e:
            return PaymentResult(success=False, reference=reference, error_message=str(e))

    def process_refund(self, payment_reference: str, amount: Decimal, reason: str) -> RefundResult:
        token = self._get_access_token()
        if not token:
            return RefundResult(success=False, reference=payment_reference, error_message="PayPal auth failed")

        try:
            response = requests.post(
                f'{self.base_url}/v2/payments/captures/{payment_reference}/refund',
                headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                json={'amount': {'currency_code': 'USD', 'value': str(amount)}, 'note_to_payer': reason},
                timeout=30
            )
            if response.status_code == 201:
                return RefundResult(success=True, reference=response.json()['id'])
            return RefundResult(success=False, reference=payment_reference, error_message=response.text)
        except Exception as e:
            return RefundResult(success=False, reference=payment_reference, error_message=str(e))

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        return True

    def get_supported_currencies(self) -> list[str]:
        return ['USD', 'EUR', 'GBP']
