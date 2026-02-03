from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from apps.orgs.models import Organization, Membership


@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    list_display = ["name", "slug", "owner", "currency", "created_at"]
    list_filter = ["currency", "created_at"]
    search_fields = ["name", "slug", "owner__email"]
    readonly_fields = ["created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Membership)
class MembershipAdmin(ModelAdmin):
    list_display = ["user", "organization", "role", "invited_by", "created_at"]
    list_filter = ["role", "created_at"]
    search_fields = ["user__email", "organization__name"]
    readonly_fields = ["created_at", "updated_at"]
