from django.conf import settings
from django.utils import timezone

from apps.core.models import Notification
from apps.events.models import Organization


def platform_settings(request):
    return {
        "PLATFORM_FEE_PERCENTAGE": int(
            getattr(settings, "RECKOT_PLATFORM_FEE_PERCENTAGE", 7)
        ),
    }


def unread_notifications(request):
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        count = (
            Notification.objects.filter(user=user, is_read=False)
            .exclude(expires_at__lt=timezone.now())
            .count()
        )
        return {"unread_notifications_count": count}
    return {"unread_notifications_count": 0}


def user_currency(request):
    currency = "XAF"

    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        user_org = Organization.objects.filter(members=user).first()
        if user_org:
            currency = user_org.currency

    return {"currency": currency}
