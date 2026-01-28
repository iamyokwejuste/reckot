from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from email.mime.image import MIMEImage
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending emails and SMS notifications."""

    @staticmethod
    def get_site_url() -> str:
        """Get the site URL from settings or default."""
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
        """
        Send an HTML email using a template.

        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Path to the email template (e.g., 'emails/welcome.html')
            context: Template context dictionary
            attachments: List of (filename, content, mimetype) tuples
            inline_images: Dict of {cid: image_bytes} for inline images

        Returns:
            True if email was sent successfully
        """
        try:
            # Add site_url to context
            context['site_url'] = cls.get_site_url()

            # Render HTML template
            html_content = render_to_string(template_name, context)

            # Create plain text version (strip HTML)
            from django.utils.html import strip_tags
            text_content = strip_tags(html_content)

            # Create email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
            )
            msg.attach_alternative(html_content, "text/html")

            # Add inline images (for QR codes, etc.)
            if inline_images:
                msg.mixed_subtype = 'related'
                for cid, image_bytes in inline_images.items():
                    mime_image = MIMEImage(image_bytes)
                    mime_image.add_header('Content-ID', f'<{cid}>')
                    mime_image.add_header('Content-Disposition', 'inline', filename=f'{cid}.png')
                    msg.attach(mime_image)

            # Add attachments
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
        """Send OTP verification email."""
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
        """Send welcome email to new user."""
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
        """Send ticket confirmation email with QR code."""
        # Calculate total
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
        """Send refund status notification email."""
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
        """
        Send an SMS using a template.

        Args:
            phone_number: Recipient phone number
            template_name: Path to the SMS template (e.g., 'sms/otp_verification.txt')
            context: Template context dictionary

        Returns:
            True if SMS was sent successfully
        """
        try:
            # Render template
            message = render_to_string(template_name, context)

            # TODO: Integrate with SMS provider (Twilio, Africa's Talking, etc.)
            # For now, log the message
            logger.info(f"SMS to {phone_number}: {message}")

            # Placeholder for actual SMS sending
            # Example with Africa's Talking:
            # import africastalking
            # africastalking.initialize(username, api_key)
            # sms = africastalking.SMS
            # sms.send(message, [phone_number])

            return True

        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {e}")
            return False

    @classmethod
    def send_otp_sms(cls, phone_number: str, otp_code: str, expiry_minutes: int = 10) -> bool:
        """Send OTP verification SMS."""
        return cls.send_sms(
            phone_number=phone_number,
            template_name="sms/otp_verification.txt",
            context={
                'otp_code': otp_code,
                'expiry_minutes': expiry_minutes,
            }
        )

    @classmethod
    def send_ticket_sms(cls, phone_number: str, booking, tickets: list, event) -> bool:
        """Send ticket confirmation SMS."""
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
        """Send refund notification SMS."""
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
