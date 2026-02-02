import logging
import requests
from email.mime.image import MIMEImage
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

TWILIO_API_BASE = "https://api.twilio.com/2010-04-01"
TWILIO_VERIFY_BASE = "https://verify.twilio.com/v2"


class NotificationService:
    @staticmethod
    def get_site_url() -> str:
        return getattr(settings, "SITE_URL", "http://127.0.0.1:8000")

    @staticmethod
    def _get_twilio_auth():
        return (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict,
        attachments: list | None = None,
        inline_images: dict | None = None,
    ) -> bool:
        try:
            context["site_url"] = cls.get_site_url()

            html_content = render_to_string(template_name, context)

            text_content = strip_tags(html_content)

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
            )
            msg.attach_alternative(html_content, "text/html")

            if inline_images:
                msg.mixed_subtype = "related"
                for cid, image_bytes in inline_images.items():
                    mime_image = MIMEImage(image_bytes)
                    mime_image.add_header("Content-ID", f"<{cid}>")
                    mime_image.add_header(
                        "Content-Disposition", "inline", filename=f"{cid}.png"
                    )
                    msg.attach(mime_image)

            if attachments:
                for filename, content, mimetype in attachments:
                    msg.attach(filename, content, mimetype)

            msg.send(fail_silently=False)
            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    @classmethod
    def send_otp_email(
        cls, to_email: str, otp_code: str, expiry_minutes: int = 10
    ) -> bool:
        return cls.send_email(
            to_email=to_email,
            subject="Verify your email - Reckot",
            template_name="emails/otp_verification.html",
            context={
                "otp_code": otp_code,
                "expiry_minutes": expiry_minutes,
            },
        )

    @classmethod
    def send_welcome_email(cls, user) -> bool:
        return cls.send_email(
            to_email=user.email,
            subject="Welcome to Reckot!",
            template_name="emails/welcome.html",
            context={
                "user": user,
            },
        )

    @classmethod
    def send_ticket_confirmation(
        cls,
        to_email: str,
        booking,
        tickets: list,
        event,
        qr_code_bytes: bytes | None = None,
        pdf_attachment: bytes | None = None,
    ) -> bool:
        total_amount = sum(t.ticket_type.price for t in tickets)

        inline_images = {}
        if qr_code_bytes:
            inline_images["qr_code"] = qr_code_bytes

        attachments = None
        if pdf_attachment:
            filename = f"ticket_{booking.reference}.pdf"
            attachments = [(filename, pdf_attachment, "application/pdf")]

        return cls.send_email(
            to_email=to_email,
            subject=f"Your tickets for {event.title} - Reckot",
            template_name="emails/ticket_confirmation.html",
            context={
                "booking": booking,
                "tickets": tickets,
                "event": event,
                "total_amount": total_amount,
            },
            inline_images=inline_images if inline_images else None,
            attachments=attachments,
        )

    @classmethod
    def send_refund_notification(
        cls,
        to_email: str,
        refund,
        event,
        original_amount,
        payment_method: str | None = None,
    ) -> bool:
        return cls.send_email(
            to_email=to_email,
            subject=f"Refund update for {event.title} - Reckot",
            template_name="emails/refund_notification.html",
            context={
                "refund": refund,
                "event": event,
                "original_amount": original_amount,
                "payment_method": payment_method,
            },
        )

    @classmethod
    def send_admin_sale_notification(
        cls,
        to_email: str,
        booking,
        event,
        tickets: list,
        ticket_summary: dict,
        payment=None,
    ) -> bool:
        return cls.send_email(
            to_email=to_email,
            subject=f"New Sale for {event.title} - Reckot",
            template_name="emails/admin_sale_notification.html",
            context={
                "booking": booking,
                "event": event,
                "tickets": tickets,
                "ticket_summary": ticket_summary,
                "payment": payment,
            },
        )

    @classmethod
    def send_sms(cls, phone_number: str, template_name: str, context: dict) -> bool:
        try:
            message = render_to_string(template_name, context)

            has_messaging_service = bool(
                getattr(settings, "TWILIO_MESSAGING_SERVICE_SID", "")
            )
            has_phone = bool(getattr(settings, "TWILIO_PHONE_NUMBER", ""))

            if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN]):
                logger.warning(
                    f"Twilio not configured, SMS to {phone_number}: {message}"
                )
                return True

            if not has_messaging_service and not has_phone:
                logger.warning(
                    f"No Twilio sender configured, SMS to {phone_number}: {message}"
                )
                return True

            url = f"{TWILIO_API_BASE}/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
            data = {
                "To": phone_number,
                "Body": message,
            }

            if has_messaging_service:
                data["MessagingServiceSid"] = settings.TWILIO_MESSAGING_SERVICE_SID
            else:
                data["From"] = settings.TWILIO_PHONE_NUMBER

            response = requests.post(url, data=data, auth=cls._get_twilio_auth())

            if response.status_code in (200, 201):
                logger.info(f"SMS sent to {phone_number}")
                return True
            else:
                logger.error(
                    f"Twilio SMS failed: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {e}")
            return False

    @classmethod
    def send_otp_sms(
        cls, phone_number: str, otp_code: str | None = None, expiry_minutes: int = 10
    ) -> bool:
        try:
            verify_sid = getattr(settings, "TWILIO_VERIFY_SERVICE_SID", "")
            if (
                verify_sid
                and settings.TWILIO_ACCOUNT_SID
                and settings.TWILIO_AUTH_TOKEN
            ):
                url = f"{TWILIO_VERIFY_BASE}/Services/{verify_sid}/Verifications"
                data = {"To": phone_number, "Channel": "sms"}
                response = requests.post(url, data=data, auth=cls._get_twilio_auth())

                if response.status_code in (200, 201):
                    logger.info(f"Twilio Verify OTP sent to {phone_number}")
                    return True
                else:
                    logger.error(
                        f"Twilio Verify failed: {response.status_code} - {response.text}"
                    )
                    return False

            elif otp_code:
                return cls.send_sms(
                    phone_number=phone_number,
                    template_name="sms/otp_verification.txt",
                    context={
                        "otp_code": otp_code,
                        "expiry_minutes": expiry_minutes,
                    },
                )
            else:
                logger.warning(
                    f"Twilio Verify not configured, no OTP sent to {phone_number}"
                )
                return False
        except Exception as e:
            logger.error(f"Failed to send OTP to {phone_number}: {e}")
            return False

    @classmethod
    def verify_otp_sms(cls, phone_number: str, code: str) -> bool:
        try:
            verify_sid = getattr(settings, "TWILIO_VERIFY_SERVICE_SID", "")
            if (
                verify_sid
                and settings.TWILIO_ACCOUNT_SID
                and settings.TWILIO_AUTH_TOKEN
            ):
                url = f"{TWILIO_VERIFY_BASE}/Services/{verify_sid}/VerificationCheck"
                data = {"To": phone_number, "Code": code}
                response = requests.post(url, data=data, auth=cls._get_twilio_auth())

                if response.status_code in (200, 201):
                    result = response.json()
                    return result.get("status") == "approved"
                else:
                    logger.error(
                        f"Twilio Verify check failed: {response.status_code} - {response.text}"
                    )
                    return False
            return False
        except Exception as e:
            logger.error(f"Failed to verify OTP for {phone_number}: {e}")
            return False

    @classmethod
    def send_ticket_sms(cls, phone_number: str, booking, tickets: list, event) -> bool:
        return cls.send_sms(
            phone_number=phone_number,
            template_name="sms/ticket_confirmation.txt",
            context={
                "booking": booking,
                "tickets": tickets,
                "event": event,
            },
        )

    @classmethod
    def send_refund_sms(
        cls, phone_number: str, refund, event, payment_method: str | None = None
    ) -> bool:
        template = (
            "sms/refund_processed.txt"
            if refund.status == "PROCESSED"
            else "sms/refund_approved.txt"
        )
        return cls.send_sms(
            phone_number=phone_number,
            template_name=template,
            context={
                "refund": refund,
                "event": event,
                "payment_method": payment_method,
            },
        )
