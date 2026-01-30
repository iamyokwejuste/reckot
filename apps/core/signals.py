import logging
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import social_account_added

from apps.core.models import OTPVerification
from apps.core.tasks import send_otp_verification_task, send_welcome_email_task

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(user_signed_up)
def handle_user_signup(sender, request, user, **kwargs):
    sociallogin = kwargs.get("sociallogin")

    try:
        if sociallogin:
            user.email_verified = True
            user.save(update_fields=["email_verified"])
            send_welcome_email_task.enqueue(user.id)
        else:
            otp = OTPVerification.create_for_user(
                user=user, otp_type=OTPVerification.Type.EMAIL, expiry_minutes=10
            )
            send_otp_verification_task.enqueue(user.id, otp.id)
    except Exception as e:
        logger.error(f"Failed to enqueue signup tasks for user {user.id}: {e}")


@receiver(social_account_added)
def handle_social_account_added(sender, request, sociallogin, **kwargs):
    user = sociallogin.user
    if not user.email_verified and sociallogin.account.provider == "google":
        user.email_verified = True
        user.save(update_fields=["email_verified"])
