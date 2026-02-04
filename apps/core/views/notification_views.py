from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from apps.core.models import Notification


class NotificationListView(LoginRequiredMixin, View):
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).exclude(
            expires_at__lt=timezone.now()
        )[:20]

        data = []
        for n in notifications:
            time_diff = timezone.now() - n.created_at
            if time_diff.days > 0:
                time_ago = f"{time_diff.days}d ago"
            elif time_diff.seconds // 3600 > 0:
                time_ago = f"{time_diff.seconds // 3600}h ago"
            elif time_diff.seconds // 60 > 0:
                time_ago = f"{time_diff.seconds // 60}m ago"
            else:
                time_ago = "just now"

            data.append(
                {
                    "id": n.id,
                    "title": n.title,
                    "message": n.message,
                    "link": n.link or "#",
                    "is_read": n.is_read,
                    "time_ago": time_ago,
                    "notification_type": n.notification_type,
                }
            )

        unread_count = (
            Notification.objects.filter(user=request.user, is_read=False)
            .exclude(expires_at__lt=timezone.now())
            .count()
        )

        return JsonResponse(
            {
                "notifications": data,
                "unread_count": unread_count,
            }
        )


class NotificationMarkReadView(LoginRequiredMixin, View):
    def post(self, request, notification_id):
        try:
            notif = Notification.objects.get(id=notification_id, user=request.user)
            notif.is_read = True
            notif.save(update_fields=["is_read"])
            return JsonResponse({"success": True})
        except Notification.DoesNotExist:
            return JsonResponse({"success": False}, status=404)


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True
        )
        return JsonResponse({"success": True})
