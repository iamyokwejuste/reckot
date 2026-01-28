from django.contrib import admin
from apps.messaging.models import MessageTemplate, MessageCampaign, MessageDelivery


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'template_type', 'created_at']
    list_filter = ['template_type', 'organization']
    search_fields = ['name', 'subject', 'body']


@admin.register(MessageCampaign)
class MessageCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'message_type', 'status', 'total_recipients', 'sent_count', 'created_at']
    list_filter = ['status', 'message_type', 'organization']
    search_fields = ['name', 'subject']


@admin.register(MessageDelivery)
class MessageDeliveryAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'recipient_email', 'status', 'sent_at', 'opened_at']
    list_filter = ['status', 'campaign']
    search_fields = ['recipient_email', 'recipient_phone']
