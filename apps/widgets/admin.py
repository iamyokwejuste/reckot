from django.contrib import admin
from apps.widgets.models import EmbedWidget


@admin.register(EmbedWidget)
class EmbedWidgetAdmin(admin.ModelAdmin):
    list_display = ['event', 'widget_id', 'is_active', 'theme', 'created_at']
    list_filter = ['is_active', 'theme']
    search_fields = ['event__title']
    readonly_fields = ['widget_id']
