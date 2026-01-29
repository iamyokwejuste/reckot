import requests
import logging
import time
from decimal import Decimal
from django.conf import settings
from .base import PaymentGateway, PaymentResult, PaymentStatus

logger = logging.getLogger(__name__)


class CampayGateway(PaymentGateway):
    name = 'campay'
    display_name = 'Campay'
    supported_currencies = ['XAF']

    BASE_URL = 'https://demo.campay.net'
    PROD_URL = 'https://www.campay.net'

    def __init__(self, credentials: dict):
        super().__init__(credentials)
        self.app_username = credentials.get('app_username', '')
        self.app_password = credentials.get('app_password', '')
        self.permanent_token = credentials.get('permanent_token', '')
        self.webhook_key = credentials.get('webhook_key', '')
        self.is_production = credentials.get('is_production', False)
        self.host = self.PROD_URL if self.is_production else self.BASE_URL

    def validate_credentials(self):
        has_username_password = self.credentials.get('app_username') and self.credentials.get('app_password')
        has_permanent_token = self.credentials.get('permanent_token')
        if not has_username_password and not has_permanent_token:
            raise ValueError('Campay requires either app_username/app_password or permanent_token')

    def _get_token(self) -> str:
        if self.permanent_token:
            return self.permanent_token

        headers = {
            'Content-Type': 'application/json'
        }

        data = {
            'username': self.app_username,
            'password': self.app_password
        }

        try:
            response = requests.post(
                f'{self.host}/api/token/',
                json=data,
                headers=headers,
                timeout=30
            )

            if response.ok:
                result = response.json()
                logger.info('Campay token obtained successfully')
                return result.get('token')
            else:
                logger.error(f'Campay token error: {response.json()}')
                return None
        except Exception as e:
            logger.error(f'Campay token exception: {e}')
            return None

    def _headers(self, token: str) -> dict:
        return {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }

    def calculate_withdrawal_fee(self, amount: Decimal) -> Decimal:
        if amount <= 1000:
            return Decimal('50')
        return (amount * Decimal('0.04')).quantize(Decimal('1'))

    def calculate_platform_fee(self, amount: Decimal) -> Decimal:
        percentage = getattr(settings, 'RECKOT_PLATFORM_FEE_PERCENTAGE', Decimal('7'))
        return (amount * percentage / Decimal('100')).quantize(Decimal('1'))

    def get_total_with_fees(self, amount: Decimal) -> Decimal:
        withdrawal_fee = self.calculate_withdrawal_fee(amount)
        return amount + withdrawal_fee

    def get_payment_link(
        self,
        amount: Decimal,
        currency: str,
        description: str,
        external_reference: str,
        redirect_url: str = '',
        failure_redirect_url: str = '',
        phone_number: str = '',
        first_name: str = '',
        last_name: str = '',
        email: str = '',
        payment_options: str = 'MOMO'
    ) -> PaymentResult:
        logger.info('Campay getting payment link...')

        token = self._get_token()
        if not token:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message='Token error. Please check your App Username and Password.'
            )

        total_amount = self.get_total_with_fees(amount)

        collect_data = {
            'amount': str(int(total_amount)),
            'currency': currency,
            'description': description,
            'external_reference': external_reference,
            'redirect_url': redirect_url,
            'from': self.format_phone(phone_number) if phone_number else '',
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'failure_redirect_url': failure_redirect_url,
            'payment_options': payment_options
        }

        try:
            response = requests.post(
                f'{self.host}/api/get_payment_link/',
                json=collect_data,
                headers=self._headers(token),
                timeout=60
            )

            if response.ok:
                data = response.json()
                logger.info(f'Campay payment link response: {data}')
                return PaymentResult(
                    success=True,
                    status=PaymentStatus.PENDING,
                    message='Payment link generated',
                    raw_response={
                        **data,
                        'base_amount': str(amount),
                        'total_amount': str(total_amount),
                    }
                )
            else:
                data = response.json()
                message = data.get('message', 'Payment link error')
                logger.error(f'Campay payment link error: {message}')
                return PaymentResult(
                    success=False,
                    status=PaymentStatus.FAILED,
                    message=message,
                    raw_response=data
                )
        except Exception as e:
            logger.error(f'Campay payment link exception: {e}')
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message=str(e)
            )

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
        logger.info('Campay initiating collect payment...')

        token = self._get_token()
        if not token:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message='Token error. Please check your App Username and Password.'
            )

        phone = self.format_phone(phone_number)
        total_amount = self.get_total_with_fees(amount)

        payload = {
            'amount': str(int(total_amount)),
            'currency': currency,
            'from': phone,
            'description': description or f'Payment {reference}',
            'external_reference': reference,
        }

        if callback_url:
            payload['callback_url'] = callback_url

        try:
            response = requests.post(
                f'{self.host}/api/collect/',
                json=payload,
                headers=self._headers(token),
                timeout=60
            )

            data = response.json()
            withdrawal_fee = self.calculate_withdrawal_fee(amount)
            logger.info(f'Campay collect response: {data} (base: {amount}, withdrawal_fee: {withdrawal_fee}, total: {total_amount})')

            if response.ok and data.get('reference'):
                return PaymentResult(
                    success=True,
                    transaction_id=data.get('reference'),
                    external_reference=data.get('reference'),
                    status=PaymentStatus.PENDING,
                    message='Payment initiated. Please confirm on your phone.',
                    raw_response={
                        **data,
                        'base_amount': str(amount),
                        'withdrawal_fee': str(withdrawal_fee),
                        'total_amount': str(total_amount),
                    }
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

    def check_status(self, reference: str) -> PaymentResult:
        logger.info(f'Campay getting transaction status for {reference}...')

        if not reference:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message='Transaction reference is required'
            )

        token = self._get_token()
        if not token:
            return PaymentResult(
                success=False,
                status=PaymentStatus.PENDING,
                message='Token error. Please check your credentials.'
            )

        try:
            response = requests.get(
                f'{self.host}/api/transaction/{reference}/',
                headers=self._headers(token),
                timeout=30
            )

            if response.ok:
                data = response.json()
                logger.info(f'Campay transaction status response: {data}')

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
                    external_reference=reference,
                    status=status,
                    message=data.get('reason', ''),
                    raw_response=data
                )
            else:
                logger.error(f'Campay transaction status error: {response.text}')
                return PaymentResult(
                    success=False,
                    status=PaymentStatus.PENDING,
                    message='Request error'
                )

        except Exception as e:
            logger.error(f'Campay status check error: {e}')
            return PaymentResult(
                success=False,
                status=PaymentStatus.PENDING,
                message=str(e)
            )

    def disburse(
        self,
        amount: Decimal,
        currency: str,
        phone_number: str,
        description: str,
        external_reference: str,
        wait_for_completion: bool = False
    ) -> PaymentResult:
        logger.info('Campay disbursing...')

        token = self._get_token()
        if not token:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message='Token error. Please check your credentials.'
            )

        withdraw_data = {
            'amount': str(int(amount)),
            'currency': currency,
            'to': self.format_phone(phone_number),
            'description': description,
            'external_reference': external_reference
        }

        try:
            response = requests.post(
                f'{self.host}/api/withdraw/',
                json=withdraw_data,
                headers=self._headers(token),
                timeout=60
            )

            if response.ok:
                data = response.json()
                logger.info(f'Campay disburse response: {data}')

                reference = data.get('reference')

                if wait_for_completion and reference:
                    status = 'PENDING'
                    max_attempts = 12
                    attempts = 0

                    while status == 'PENDING' and attempts < max_attempts:
                        time.sleep(5)
                        attempts += 1

                        status_response = self.check_status(reference)
                        if status_response.status != PaymentStatus.PENDING:
                            return status_response

                return PaymentResult(
                    success=True,
                    transaction_id=reference,
                    external_reference=external_reference,
                    status=PaymentStatus.PENDING,
                    message='Disbursement initiated',
                    raw_response=data
                )
            else:
                data = response.json()
                message = data.get('message', 'Disburse error')
                logger.error(f'Campay disburse error: {message}')
                return PaymentResult(
                    success=False,
                    status=PaymentStatus.FAILED,
                    message=message,
                    raw_response=data
                )

        except Exception as e:
            logger.error(f'Campay disburse exception: {e}')
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message=str(e)
            )
