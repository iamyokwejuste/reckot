import requests
import logging
from decimal import Decimal
from apps.payments.gateways.base import PaymentGateway, PaymentResult, PaymentStatus

logger = logging.getLogger(__name__)


class FlutterwaveGateway(PaymentGateway):
    name = "flutterwave"
    display_name = "Flutterwave"
    supported_currencies = ["XAF", "XOF", "NGN", "GHS", "USD", "EUR", "GBP", "UGX"]

    BASE_URL = "https://api.flutterwave.com/v3"

    def __init__(self, credentials: dict):
        super().__init__(credentials)
        self.secret_key = credentials.get("secret_key", "")
        self.public_key = credentials.get("public_key", "")
        self.encryption_key = credentials.get("encryption_key", "")

    def validate_credentials(self):
        if not self.credentials.get("secret_key"):
            raise ValueError("Flutterwave requires a secret key")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    def _get_payment_options(self, payment_method: str) -> str:
        payment_options_map = {
            "mobile_money": "mobilemoneycameroon,mobilemoneyghana,mobilemoneyuganda",
            "card": "card",
            "all": "card,mobilemoneycameroon,mobilemoneyghana,mobilemoneyuganda",
        }
        return payment_options_map.get(payment_method, "mobilemoneycameroon,mobilemoneyghana,mobilemoneyuganda")

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
        try:
            phone = self.format_phone(phone_number)
            email = kwargs.get("email", f"{phone}@reckot.com")
            redirect_url = kwargs.get("redirect_url", callback_url)

            payment_method = kwargs.get("payment_method", "mobile_money")
            payment_options = self._get_payment_options(payment_method)

            payload = {
                "tx_ref": reference,
                "amount": str(int(amount)),
                "currency": currency,
                "redirect_url": redirect_url,
                "payment_options": payment_options,
                "customer": {
                    "email": email,
                    "phone_number": phone,
                    "name": kwargs.get("customer_name", "Customer"),
                },
                "customizations": {
                    "title": "Reckot Payment",
                    "description": description or f"Payment for {reference}",
                    "logo": kwargs.get("logo_url", ""),
                },
                "meta": {
                    "consumer_id": kwargs.get("user_id", ""),
                    "consumer_mac": kwargs.get("device_id", ""),
                },
            }

            response = requests.post(
                f"{self.BASE_URL}/payments",
                json=payload,
                headers=self._headers(),
                timeout=60,
            )

            data = response.json()
            logger.info(f"Flutterwave payment response: {data}")

            if data.get("status") == "success":
                return PaymentResult(
                    success=True,
                    transaction_id=reference,
                    external_reference=reference,
                    redirect_url=data.get("data", {}).get("link"),
                    status=PaymentStatus.PENDING,
                    message="Redirect to complete payment",
                    raw_response=data,
                )

            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message=data.get("message", "Payment initiation failed"),
                raw_response=data,
            )

        except requests.Timeout:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message="Request timed out. Please try again.",
            )
        except Exception as e:
            logger.error(f"Flutterwave payment error: {e}")
            return PaymentResult(
                success=False, status=PaymentStatus.FAILED, message=str(e)
            )

    def initiate_mobile_money(
        self,
        amount: Decimal,
        currency: str,
        phone_number: str,
        reference: str,
        network: str = "MTN",
        **kwargs,
    ) -> PaymentResult:
        try:
            phone = self.format_phone(phone_number)
            email = kwargs.get("email", f"{phone}@reckot.com")

            payload = {
                "tx_ref": reference,
                "amount": str(int(amount)),
                "currency": currency,
                "phone_number": phone,
                "network": network,
                "email": email,
                "fullname": kwargs.get("customer_name", "Customer"),
            }

            response = requests.post(
                f"{self.BASE_URL}/charges?type=mobile_money_franco",
                json=payload,
                headers=self._headers(),
                timeout=60,
            )

            data = response.json()
            logger.info(f"Flutterwave MoMo response: {data}")

            if data.get("status") == "success":
                charge_data = data.get("data", {})
                return PaymentResult(
                    success=True,
                    transaction_id=str(charge_data.get("id", "")),
                    external_reference=reference,
                    status=PaymentStatus.PENDING,
                    message=charge_data.get(
                        "processor_response", "Confirm payment on your phone"
                    ),
                    raw_response=data,
                )

            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message=data.get("message", "Payment failed"),
                raw_response=data,
            )

        except Exception as e:
            logger.error(f"Flutterwave MoMo error: {e}")
            return PaymentResult(
                success=False, status=PaymentStatus.FAILED, message=str(e)
            )

    def verify_payment(self, reference: str) -> PaymentResult:
        try:
            response = requests.get(
                f"{self.BASE_URL}/transactions/verify_by_reference?tx_ref={reference}",
                headers=self._headers(),
                timeout=30,
            )

            data = response.json()
            logger.info(f"Flutterwave verify response: {data}")

            if data.get("status") == "success":
                tx_data = data.get("data", {})
                tx_status = tx_data.get("status", "").lower()

                status_map = {
                    "successful": PaymentStatus.SUCCESS,
                    "pending": PaymentStatus.PENDING,
                    "failed": PaymentStatus.FAILED,
                }

                status = status_map.get(tx_status, PaymentStatus.PENDING)

                return PaymentResult(
                    success=status == PaymentStatus.SUCCESS,
                    transaction_id=str(tx_data.get("id", "")),
                    external_reference=reference,
                    status=status,
                    message=tx_data.get("processor_response", ""),
                    raw_response=data,
                )

            return PaymentResult(
                success=False,
                status=PaymentStatus.PENDING,
                message=data.get("message", "Verification failed"),
                raw_response=data,
            )

        except Exception as e:
            logger.error(f"Flutterwave verify error: {e}")
            return PaymentResult(
                success=False, status=PaymentStatus.PENDING, message=str(e)
            )

    def check_status(self, external_reference: str) -> PaymentResult:
        return self.verify_payment(external_reference)

    def refund(self, external_reference: str, amount: Decimal) -> PaymentResult:
        try:
            verify_result = self.verify_payment(external_reference)
            if not verify_result.transaction_id:
                return PaymentResult(success=False, message="Transaction not found")

            payload = {"amount": str(int(amount))}

            response = requests.post(
                f"{self.BASE_URL}/transactions/{verify_result.transaction_id}/refund",
                json=payload,
                headers=self._headers(),
                timeout=30,
            )

            data = response.json()
            logger.info(f"Flutterwave refund response: {data}")

            if data.get("status") == "success":
                return PaymentResult(
                    success=True,
                    transaction_id=str(data.get("data", {}).get("id", "")),
                    status=PaymentStatus.SUCCESS,
                    message="Refund processed successfully",
                    raw_response=data,
                )

            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message=data.get("message", "Refund failed"),
                raw_response=data,
            )

        except Exception as e:
            logger.error(f"Flutterwave refund error: {e}")
            return PaymentResult(success=False, message=str(e))
