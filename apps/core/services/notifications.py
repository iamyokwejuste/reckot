from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from email.mime.image import MIMEImage
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    def get_site_url() -> str:
        return getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict,
        attachments: list = None,
        inline_images: dict = None,
    ) -> bool:
        try:
            context['site_url'] = cls.get_site_url()

            html_content = render_to_string(template_name, context)

            from django.utils.html import strip_tags
            text_content = strip_tags(html_content)

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
            )
            msg.attach_alternative(html_content, "text/html")

            if inline_images:
                msg.mixed_subtype = 'related'
                for cid, image_bytes in inline_images.items():
                    mime_image = MIMEImage(image_bytes)
                    mime_image.add_header('Content-ID', f'<{cid}>')
                    mime_image.add_header('Content-Disposition', 'inline', filename=f'{cid}.png')
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
    def send_otp_email(cls, to_email: str, otp_code: str, expiry_minutes: int = 10) -> bool:
        return cls.send_email(
            to_email=to_email,
            subject="Verify your email - Reckot",
            template_name="emails/otp_verification.html",
            context={
                'otp_code': otp_code,
                'expiry_minutes': expiry_minutes,
            }
        )

    @classmethod
    def send_welcome_email(cls, user) -> bool:
        return cls.send_email(
            to_email=user.email,
            subject="Welcome to Reckot!",
            template_name="emails/welcome.html",
            context={
                'user': user,
            }
        )

    @classmethod
    def send_ticket_confirmation(
        cls,
        to_email: str,
        booking,
        tickets: list,
        event,
        qr_code_bytes: bytes = None,
    ) -> bool:
        total_amount = sum(t.ticket_type.price for t in tickets)

        inline_images = {}
        if qr_code_bytes:
            inline_images['qr_code'] = qr_code_bytes

        return cls.send_email(
            to_email=to_email,
            subject=f"Your tickets for {event.title} - Reckot",
            template_name="emails/ticket_confirmation.html",
            context={
                'booking': booking,
                'tickets': tickets,
                'event': event,
                'total_amount': total_amount,
            },
            inline_images=inline_images if inline_images else None,
        )

    @classmethod
    def send_refund_notification(
        cls,
        to_email: str,
        refund,
        event,
        original_amount,
        payment_method: str = None,
    ) -> bool:
        return cls.send_email(
            to_email=to_email,
            subject=f"Refund update for {event.title} - Reckot",
            template_name="emails/refund_notification.html",
            context={
                'refund': refund,
                'event': event,
                'original_amount': original_amount,
                'payment_method': payment_method,
            }
        )

    @classmethod
    def send_sms(cls, phone_number: str, template_name: str, context: dict) -> bool:
        try:
            message = render_to_string(template_name, context)

            has_messaging_service = bool(getattr(settings, 'TWILIO_MESSAGING_SERVICE_SID', ''))
            has_phone = bool(getattr(settings, 'TWILIO_PHONE_NUMBER', ''))

            if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN]):
                logger.warning(f"Twilio not configured, SMS to {phone_number}: {message}")
                return True

            if not has_messaging_service and not has_phone:
                logger.warning(f"No Twilio sender configured, SMS to {phone_number}: {message}")
                return True

            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

            if has_messaging_service:
                client.messages.create(
                    body=message,
                    messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID,
                    to=phone_number
                )
            else:
                client.messages.create(
                    body=message,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone_number
                )
            logger.info(f"SMS sent to {phone_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {e}")
            return False

    @classmethod
    def send_otp_sms(cls, phone_number: str, otp_code: str = None, expiry_minutes: int = 10) -> bool:
        try:
            if settings.TWILIO_VERIFY_SERVICE_SID and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
                from twilio.rest import Client
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
                    to=phone_number,
                    channel='sms'
                )
                logger.info(f"Twilio Verify OTP sent to {phone_number}")
                return True
            elif otp_code:
                return cls.send_sms(
                    phone_number=phone_number,
                    template_name="sms/otp_verification.txt",
                    context={
                        'otp_code': otp_code,
                        'expiry_minutes': expiry_minutes,
                    }
                )
            else:
                logger.warning(f"Twilio Verify not configured, no OTP sent to {phone_number}")
                return False
        except Exception as e:
            logger.error(f"Failed to send OTP to {phone_number}: {e}")
            return False

    @classmethod
    def verify_otp_sms(cls, phone_number: str, code: str) -> bool:
        try:
            if settings.TWILIO_VERIFY_SERVICE_SID and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
                from twilio.rest import Client
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                verification_check = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
                    to=phone_number,
                    code=code
                )
                return verification_check.status == 'approved'
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
                'booking': booking,
                'tickets': tickets,
                'event': event,
            }
        )

    @classmethod
    def send_refund_sms(cls, phone_number: str, refund, event, payment_method: str = None) -> bool:
        template = 'sms/refund_processed.txt' if refund.status == 'PROCESSED' else 'sms/refund_approved.txt'
        return cls.send_sms(
            phone_number=phone_number,
            template_name=template,
            context={
                'refund': refund,
                'event': event,
                'payment_method': payment_method,
            }
        )
