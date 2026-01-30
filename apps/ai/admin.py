from django.contrib import admin
from apps.ai.models import SupportTicket, AIConversation, AIMessage


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "subject",
        "category",
        "priority",
        "status",
        "user",
        "created_at",
    ]
    list_filter = ["status", "priority", "category", "created_at"]
    search_fields = ["reference", "subject", "description", "user__email"]
    readonly_fields = ["reference", "created_at", "updated_at"]
    raw_id_fields = ["user", "assigned_to", "event", "organization"]


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ["session_id", "user", "created_at", "updated_at"]
    list_filter = ["created_at"]
    search_fields = ["session_id", "user__email"]
    readonly_fields = ["session_id", "created_at", "updated_at"]


@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = ["conversation", "role", "created_at"]
    list_filter = ["role", "created_at"]
    search_fields = ["content"]
    raw_id_fields = ["conversation"]
