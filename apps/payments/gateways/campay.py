import requests
import logging
from decimal import Decimal
from .base import PaymentGateway, PaymentResult, PaymentStatus

logger = logging.getLogger(__name__)


class CampayGateway(PaymentGateway):
    name = 'campay'
    display_name = 'Campay'
    supported_currencies = ['XAF']

    BASE_URL = 'https://demo.campay.net/api'
    PROD_URL = 'https://campay.net/api'

    def __init__(self, credentials: dict):
        super().__init__(credentials)
        self.username = credentials.get('username', '')
        self.password = credentials.get('password', '')
        self.is_production = credentials.get('is_production', False)
        self.base_url = self.PROD_URL if self.is_production else self.BASE_URL
        self._token = None

    def validate_credentials(self):
        if not self.credentials.get('username') or not self.credentials.get('password'):
            raise ValueError('Campay requires username and password')

    def _get_token(self) -> str:
        if self._token:
            return self._token

        try:
            response = requests.post(
                f'{self.base_url}/token/',
                json={
                    'username': self.username,
                    'password': self.password
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            self._token = data.get('token')
            return self._token
        except Exception as e:
            logger.error(f'Campay token error: {e}')
            raise

    def _headers(self) -> dict:
        return {
            'Authorization': f'Token {self._get_token()}',
            'Content-Type': 'application/json'
        }

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
        try:
            phone = self.format_phone(phone_number)

            payload = {
                'amount': str(int(amount)),
                'currency': currency,
                'from': phone,
                'description': description or f'Payment {reference}',
                'external_reference': reference,
            }

            if callback_url:
                payload['callback_url'] = callback_url

            response = requests.post(
                f'{self.base_url}/collect/',
                json=payload,
                headers=self._headers(),
                timeout=60
            )

            data = response.json()
            logger.info(f'Campay collect response: {data}')

            if response.status_code == 200 and data.get('reference'):
                return PaymentResult(
                    success=True,
                    transaction_id=data.get('reference'),
                    external_reference=data.get('reference'),
                    status=PaymentStatus.PENDING,
                    message='Payment initiated. Please confirm on your phone.',
                    raw_response=data
                )
            else:
                return PaymentResult(
                    success=False,
                    status=PaymentStatus.FAILED,
                    message=data.get('message', 'Payment initiation failed'),
                    raw_response=data
                )

        except requests.Timeout:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message='Request timed out. Please try again.'
            )
        except Exception as e:
            logger.error(f'Campay payment error: {e}')
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message=str(e)
            )

    def verify_payment(self, reference: str) -> PaymentResult:
        return self.check_status(reference)

    def check_status(self, external_reference: str) -> PaymentResult:
        try:
            response = requests.get(
                f'{self.base_url}/transaction/{external_reference}/',
                headers=self._headers(),
                timeout=30
            )

            data = response.json()
            logger.info(f'Campay status response: {data}')

            status_map = {
                'SUCCESSFUL': PaymentStatus.SUCCESS,
                'PENDING': PaymentStatus.PENDING,
                'FAILED': PaymentStatus.FAILED,
            }

            campay_status = data.get('status', '').upper()
            status = status_map.get(campay_status, PaymentStatus.PENDING)

            return PaymentResult(
                success=status == PaymentStatus.SUCCESS,
                transaction_id=data.get('reference'),
                external_reference=external_reference,
                status=status,
                message=data.get('reason', ''),
                raw_response=data
            )

        except Exception as e:
            logger.error(f'Campay status check error: {e}')
            return PaymentResult(
                success=False,
                status=PaymentStatus.PENDING,
                message=str(e)
            )
