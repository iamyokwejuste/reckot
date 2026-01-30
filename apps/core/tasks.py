import logging
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from celery import shared_task

from apps.core.models import OTPVerification
from apps.core.services.notifications import NotificationService

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def send_email_task(
    to_email: str,
    subject: str,
    template_name: str,
    context: dict,
    attachments: list = None,
    inline_images: dict = None,
):
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


@shared_task
def send_sms_task(phone_number: str, template_name: str, context: dict):
    try:
        NotificationService.send_sms(
            phone_number=phone_number,
            template_name=template_name,
            context=context or {},
        )
        logger.info(f"SMS sent to {phone_number}")
    except Exception as e:
        logger.error(f"Failed to send SMS to {phone_number}: {e}")


@shared_task
def send_otp_sms_task(
    phone_number: str, otp_code: str = None, expiry_minutes: int = 10
):
    try:
        NotificationService.send_otp_sms(
            phone_number=phone_number,
            otp_code=otp_code,
            expiry_minutes=expiry_minutes,
        )
        logger.info(f"OTP SMS sent to {phone_number}")
    except Exception as e:
        logger.error(f"Failed to send OTP SMS to {phone_number}: {e}")


@shared_task
def send_otp_verification_task(user_id: int, otp_id: int):
    try:
        user = User.objects.get(id=user_id)
        otp = OTPVerification.objects.get(id=otp_id)

        if otp.is_expired or otp.is_used:
            logger.warning(f"OTP {otp_id} is expired or already used")
            return

        expiry_minutes = max(
            1, int((otp.expires_at - timezone.now()).total_seconds() / 60)
        )

        if user.email:
            NotificationService.send_otp_email(
                to_email=user.email, otp_code=otp.code, expiry_minutes=expiry_minutes
            )

        if user.phone_number:
            NotificationService.send_otp_sms(
                phone_number=user.phone_number,
                otp_code=otp.code,
                expiry_minutes=expiry_minutes,
            )

        logger.info(f"OTP verification sent to user {user_id}")

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
    except OTPVerification.DoesNotExist:
        logger.error(f"OTP {otp_id} not found")
    except Exception as e:
        logger.error(f"Failed to send OTP verification: {e}")


@shared_task
def send_welcome_email_task(user_id: int):
    try:
        user = User.objects.get(id=user_id)
        if user.email:
            NotificationService.send_welcome_email(user)
            logger.info(f"Welcome email sent to user {user_id}")

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")


@shared_task
def resend_otp_task(user_id: int, otp_type: str = "EMAIL"):
    try:
        user = User.objects.get(id=user_id)
        otp = OTPVerification.create_for_user(
            user=user, otp_type=otp_type, expiry_minutes=10
        )
        send_otp_verification_task.enqueue(user_id, otp.id)
        logger.info(f"New OTP created and sent to user {user_id}")
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
    except Exception as e:
        logger.error(f"Failed to resend OTP: {e}")


@shared_task
def cleanup_expired_otps_task():
    try:
        now = timezone.now()
        expired_cutoff = now - timedelta(hours=24)
        used_cutoff = now - timedelta(hours=1)

        deleted, details = OTPVerification.objects.filter(
            Q(expires_at__lt=expired_cutoff) |
            Q(is_used=True, created_at__lt=used_cutoff)
        ).delete()

        if deleted:
            logger.info(f"Cleaned up {deleted} OTP tokens (expired and used)")
            logger.debug(f"Deletion details: {details}")
    except Exception as e:
        logger.error(f"Failed to cleanup OTPs: {e}")
