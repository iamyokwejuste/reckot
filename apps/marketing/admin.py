from django.contrib import admin
from apps.marketing.models import AffiliateLink, AffiliateConversion, SocialShare


@admin.register(AffiliateLink)
class AffiliateLinkAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "code",
        "organization",
        "event",
        "commission_type",
        "commission_value",
        "clicks",
        "is_active",
    ]
    list_filter = ["is_active", "commission_type", "organization"]
    search_fields = ["name", "code"]
    readonly_fields = ["clicks"]


@admin.register(AffiliateConversion)
class AffiliateConversionAdmin(admin.ModelAdmin):
    list_display = [
        "affiliate_link",
        "booking",
        "order_amount",
        "commission_amount",
        "status",
        "created_at",
    ]
    list_filter = ["status", "affiliate_link"]


@admin.register(SocialShare)
class SocialShareAdmin(admin.ModelAdmin):
    list_display = ["event", "platform", "user", "created_at"]
    list_filter = ["platform", "event"]
