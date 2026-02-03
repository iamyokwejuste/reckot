from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from apps.marketing.models import AffiliateLink, AffiliateConversion, SocialShare


@admin.register(AffiliateLink)
class AffiliateLinkAdmin(ModelAdmin):
    list_display = [
        "name",
        "code",
        "organization",
        "event",
        "commission_display",
        "clicks",
        "conversion_count",
        "status_badge",
    ]
    list_filter = ["is_active", "commission_type", "organization"]
    search_fields = ["name", "code", "organization__name"]
    readonly_fields = ["clicks"]

    @display(description="Commission")
    def commission_display(self, obj):
        if obj.commission_type == "PERCENTAGE":
            return f"{obj.commission_value}%"
        return f"{obj.commission_value}"

    @display(description="Conversions")
    def conversion_count(self, obj):
        return obj.conversions.filter(status="PAID").count()

    @display(description="Status", label=True)
    def status_badge(self, obj):
        if obj.is_active:
            return "Active", "success"
        return "Inactive", "secondary"


@admin.register(AffiliateConversion)
class AffiliateConversionAdmin(ModelAdmin):
    list_display = [
        "affiliate_link",
        "booking_ref",
        "order_amount",
        "commission_amount",
        "status_badge",
        "created_at",
    ]
    list_filter = ["status", "affiliate_link", "created_at"]
    search_fields = ["booking__reference", "affiliate_link__code"]
    readonly_fields = ["created_at", "paid_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        ("Conversion Information", {
            "fields": ("affiliate_link", "booking", "order_amount", "commission_amount")
        }),
        ("Status", {
            "fields": ("status", "paid_at")
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    @display(description="Booking")
    def booking_ref(self, obj):
        return obj.booking.reference if obj.booking else "-"

    @display(description="Status", label=True)
    def status_badge(self, obj):
        colors = {
            "PENDING": "warning",
            "PAID": "success",
            "CANCELLED": "danger",
        }
        return obj.status, colors.get(obj.status, "secondary")


@admin.register(SocialShare)
class SocialShareAdmin(ModelAdmin):
    list_display = ["event", "platform_badge", "user_info", "ip_address", "created_at"]
    list_filter = ["platform", "created_at"]
    search_fields = ["event__title", "user__email"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"

    @display(description="Platform", label=True)
    def platform_badge(self, obj):
        colors = {
            "FACEBOOK": "primary",
            "TWITTER": "info",
            "WHATSAPP": "success",
            "LINKEDIN": "primary",
            "COPY_LINK": "secondary",
        }
        return obj.platform, colors.get(obj.platform, "secondary")

    @display(description="User")
    def user_info(self, obj):
        return obj.user.email if obj.user else "Guest"
