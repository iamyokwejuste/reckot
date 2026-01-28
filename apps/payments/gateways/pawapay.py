import requests
import logging
import uuid
from decimal import Decimal
from .base import PaymentGateway, PaymentResult, PaymentStatus

logger = logging.getLogger(__name__)


class PawapayGateway(PaymentGateway):
    name = 'pawapay'
    display_name = 'PawaPay'
    supported_currencies = ['XAF', 'XOF', 'GHS', 'UGX', 'NGN']

    SANDBOX_URL = 'https://api.sandbox.pawapay.io'
    PROD_URL = 'https://api.pawapay.io'

    CORRESPONDENT_MAP = {
        'CM': {
            'MTN': 'MTN_MOMO_CMR',
            'ORANGE': 'ORANGE_CMR',
        },
        'GH': {
            'MTN': 'MTN_MOMO_GHA',
            'VODAFONE': 'VODAFONE_GHA',
        },
    }

    def __init__(self, credentials: dict):
        super().__init__(credentials)
        self.api_token = credentials.get('api_token', '')
        self.is_production = credentials.get('is_production', False)
        self.base_url = self.PROD_URL if self.is_production else self.SANDBOX_URL

    def validate_credentials(self):
        if not self.credentials.get('api_token'):
            raise ValueError('PawaPay requires an API token')

    def _headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

    def _detect_correspondent(self, phone: str, country: str = 'CM') -> str:
        phone_clean = ''.join(filter(str.isdigit, phone))

        if country == 'CM':
            if phone_clean.startswith('237'):
                phone_clean = phone_clean[3:]

            if phone_clean.startswith(('67', '68', '69', '65')):
                return self.CORRESPONDENT_MAP['CM']['MTN']
            elif phone_clean.startswith(('69', '65', '66')):
                return self.CORRESPONDENT_MAP['CM']['ORANGE']

        return self.CORRESPONDENT_MAP.get(country, {}).get('MTN', 'MTN_MOMO_CMR')

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
            correspondent = kwargs.get('correspondent') or self._detect_correspondent(phone)
            deposit_id = str(uuid.uuid4())

            payload = {
                'depositId': deposit_id,
                'amount': str(int(amount)),
                'currency': currency,
                'correspondent': correspondent,
                'payer': {
                    'type': 'MSISDN',
                    'address': {'value': phone}
                },
                'customerTimestamp': kwargs.get('timestamp', ''),
                'statementDescription': description[:22] if description else f'Pay {reference[:10]}'
            }

            response = requests.post(
                f'{self.base_url}/deposits',
                json=payload,
                headers=self._headers(),
                timeout=60
            )

            data = response.json()
            logger.info(f'PawaPay deposit response: {data}')

            if response.status_code in [200, 201]:
                status = data.get('status', '').upper()
                if status in ['ACCEPTED', 'SUBMITTED']:
                    return PaymentResult(
                        success=True,
                        transaction_id=deposit_id,
                        external_reference=deposit_id,
                        status=PaymentStatus.PENDING,
                        message='Payment request submitted. Please approve on your phone.',
                        raw_response=data
                    )

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
            logger.error(f'PawaPay payment error: {e}')
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
                f'{self.base_url}/deposits/{external_reference}',
                headers=self._headers(),
                timeout=30
            )

            data = response.json()
            logger.info(f'PawaPay status response: {data}')

            status_map = {
                'COMPLETED': PaymentStatus.SUCCESS,
                'ACCEPTED': PaymentStatus.PENDING,
                'SUBMITTED': PaymentStatus.PENDING,
                'FAILED': PaymentStatus.FAILED,
                'CANCELLED': PaymentStatus.CANCELLED,
            }

            pawapay_status = data.get('status', '').upper()
            status = status_map.get(pawapay_status, PaymentStatus.PENDING)

            return PaymentResult(
                success=status == PaymentStatus.SUCCESS,
                transaction_id=data.get('depositId'),
                external_reference=external_reference,
                status=status,
                message=data.get('failureReason', {}).get('failureMessage', ''),
                raw_response=data
            )

        except Exception as e:
            logger.error(f'PawaPay status check error: {e}')
            return PaymentResult(
                success=False,
                status=PaymentStatus.PENDING,
                message=str(e)
            )
