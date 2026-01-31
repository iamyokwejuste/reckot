from django.contrib import admin
from apps.core.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "notification_type", "is_read", "created_at", "expires_at"]
    list_filter = ["notification_type", "is_read", "created_at"]
    search_fields = ["title", "message", "user__email"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {"fields": ("user", "notification_type", "title", "message", "link")}),
        ("Status", {"fields": ("is_read", "expires_at")}),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    actions = ["mark_as_read", "mark_as_unread"]

    @admin.action(description="Mark selected notifications as read")
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} notification(s) marked as read.")

    @admin.action(description="Mark selected notifications as unread")
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} notification(s) marked as unread.")
