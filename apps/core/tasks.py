import logging
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


def send_email_task(
    to_email: str,
    subject: str,
    template_name: str,
    context: dict,
    attachments: list = None,
    inline_images: dict = None,
):
    from .services.notifications import NotificationService
    try:
        NotificationService.send_email(
            to_email=to_email,
            subject=subject,
            template_name=template_name,
            context=context or {},
            attachments=attachments,
            inline_images=inline_images,
        )
        logger.info(f"Email sent to {to_email}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")


def send_sms_task(phone_number: str, template_name: str, context: dict):
    from .services.notifications import NotificationService
    try:
        NotificationService.send_sms(
            phone_number=phone_number,
            template_name=template_name,
            context=context or {},
        )
        logger.info(f"SMS sent to {phone_number}")
    except Exception as e:
        logger.error(f"Failed to send SMS to {phone_number}: {e}")


def send_otp_verification_task(user_id: int, otp_id: int):
    from .models import OTPVerification
    from .services.notifications import NotificationService

    try:
        user = User.objects.get(id=user_id)
        otp = OTPVerification.objects.get(id=otp_id)

        if otp.is_expired or otp.is_used:
            logger.warning(f"OTP {otp_id} is expired or already used")
            return

        from django.utils import timezone
        expiry_minutes = max(1, int((otp.expires_at - timezone.now()).total_seconds() / 60))

        if user.email:
            NotificationService.send_otp_email(
                to_email=user.email,
                otp_code=otp.code,
                expiry_minutes=expiry_minutes
            )

        if user.phone_number:
            NotificationService.send_otp_sms(
                phone_number=user.phone_number,
                otp_code=otp.code,
                expiry_minutes=expiry_minutes
            )

        logger.info(f"OTP verification sent to user {user_id}")

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
    except OTPVerification.DoesNotExist:
        logger.error(f"OTP {otp_id} not found")
    except Exception as e:
        logger.error(f"Failed to send OTP verification: {e}")


def send_welcome_email_task(user_id: int):
    from .services.notifications import NotificationService

    try:
        user = User.objects.get(id=user_id)
        if user.email:
            NotificationService.send_welcome_email(user)
            logger.info(f"Welcome email sent to user {user_id}")

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")


def resend_otp_task(user_id: int, otp_type: str = 'EMAIL'):
    from .models import OTPVerification

    try:
        user = User.objects.get(id=user_id)
        otp = OTPVerification.create_for_user(
            user=user,
            otp_type=otp_type,
            expiry_minutes=10
        )
        send_otp_verification_task(user_id, otp.id)
        logger.info(f"New OTP created and sent to user {user_id}")
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
    except Exception as e:
        logger.error(f"Failed to resend OTP: {e}")


def cleanup_expired_otps_task():
    from django.utils import timezone
    from datetime import timedelta
    from .models import OTPVerification

    try:
        cutoff = timezone.now() - timedelta(hours=24)
        deleted, _ = OTPVerification.objects.filter(
            expires_at__lt=cutoff
        ).delete()
        if deleted:
            logger.info(f"Cleaned up {deleted} expired OTPs")
    except Exception as e:
        logger.error(f"Failed to cleanup OTPs: {e}")


def cleanup_used_otps_task():
    from django.utils import timezone
    from datetime import timedelta
    from .models import OTPVerification

    try:
        cutoff = timezone.now() - timedelta(hours=1)
        deleted, _ = OTPVerification.objects.filter(
            is_used=True,
            created_at__lt=cutoff
        ).delete()
        if deleted:
            logger.info(f"Cleaned up {deleted} used OTPs")
    except Exception as e:
        logger.error(f"Failed to cleanup used OTPs: {e}")
