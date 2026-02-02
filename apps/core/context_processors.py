from django.conf import settings
from django.utils import timezone

from apps.core.models import Notification


def platform_settings(request):
    return {
        "PLATFORM_FEE_PERCENTAGE": int(
            getattr(settings, "RECKOT_PLATFORM_FEE_PERCENTAGE", 7)
        ),
    }


def unread_notifications(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).exclude(expires_at__lt=timezone.now()).count()
        return {"unread_notifications_count": count}
    return {"unread_notifications_count": 0}
