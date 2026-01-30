from django.contrib import admin
from django.utils import timezone
from apps.events.models import Event, EventFlyerConfig, CheckoutQuestion
from apps.tickets.models import TicketType


class TicketTypeInline(admin.TabularInline):
    model = TicketType
    extra = 0
    fields = ["name", "price", "quantity", "available_quantity", "is_active"]
    readonly_fields = ["available_quantity"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "organization",
        "state",
        "is_public",
        "is_featured",
        "feature_status",
        "start_at",
    ]
    list_filter = ["state", "is_public", "is_featured", "event_type", "created_at"]
    search_fields = ["title", "organization__name", "description"]
    readonly_fields = ["slug", "created_at", "updated_at", "feature_requested_at"]
    inlines = [TicketTypeInline]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "organization",
                    "title",
                    "slug",
                    "description",
                    "short_description",
                    "cover_image",
                )
            },
        ),
        (
            "Event Details",
            {"fields": ("event_type", "start_at", "end_at", "timezone", "capacity")},
        ),
        (
            "Location",
            {
                "fields": (
                    "location",
                    "venue_name",
                    "address_line_2",
                    "city",
                    "country",
                    "online_url",
                )
            },
        ),
        ("Contact", {"fields": ("contact_email", "contact_phone", "website")}),
        ("Status", {"fields": ("state", "is_public", "is_free")}),
        (
            "Featured",
            {
                "fields": (
                    "is_featured",
                    "feature_requested_at",
                    "feature_approved_at",
                    "feature_expires_at",
                    "feature_order",
                    "feature_rejection_reason",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = ["approve_feature", "reject_feature", "remove_feature"]

    def feature_status(self, obj):
        if obj.is_featured:
            return "Featured"
        elif obj.feature_requested_at and not obj.feature_rejection_reason:
            return "Pending Review"
        elif obj.feature_rejection_reason:
            return "Rejected"
        return "-"

    feature_status.short_description = "Feature Status"

    @admin.action(description="Approve selected events for featuring")
    def approve_feature(self, request, queryset):
        now = timezone.now()
        updated = queryset.filter(
            feature_requested_at__isnull=False, is_featured=False
        ).update(
            is_featured=True,
            feature_approved_at=now,
            feature_expires_at=now + timezone.timedelta(days=30),
            feature_rejection_reason="",
        )
        self.message_user(request, f"{updated} event(s) approved for featuring.")

    @admin.action(description="Reject feature request for selected events")
    def reject_feature(self, request, queryset):
        updated = queryset.filter(
            feature_requested_at__isnull=False, is_featured=False
        ).update(
            feature_rejection_reason="Your event does not meet our featuring criteria at this time. Please ensure your event has a complete description, cover image, and is scheduled at least 7 days in advance."
        )
        self.message_user(request, f"{updated} event(s) feature request rejected.")

    @admin.action(description="Remove featured status from selected events")
    def remove_feature(self, request, queryset):
        updated = queryset.filter(is_featured=True).update(
            is_featured=False, feature_approved_at=None, feature_expires_at=None
        )
        self.message_user(request, f"{updated} event(s) removed from featured.")


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "event",
        "price",
        "quantity",
        "available_quantity",
        "is_active",
    ]
    list_filter = ["is_active", "event__organization"]
    search_fields = ["name", "event__title"]


@admin.register(EventFlyerConfig)
class EventFlyerConfigAdmin(admin.ModelAdmin):
    list_display = [
        "event",
        "is_enabled",
        "pay_per_use_accepted",
        "template_change_count",
    ]
    list_filter = ["is_enabled", "pay_per_use_accepted"]
    search_fields = ["event__title"]


@admin.register(CheckoutQuestion)
class CheckoutQuestionAdmin(admin.ModelAdmin):
    list_display = ["question", "event", "field_type", "is_required", "order"]
    list_filter = ["field_type", "is_required"]
    search_fields = ["question", "event__title"]
