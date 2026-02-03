from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import DailyMetrics, EventMetrics, PaymentMetrics, OrganizationMetrics


@admin.register(DailyMetrics)
class DailyMetricsAdmin(ModelAdmin):
    list_display = ['date', 'total_revenue', 'platform_fees', 'net_revenue', 'tickets_sold', 'orders_count']
    list_filter = ['date']
    search_fields = ['date']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-date']


@admin.register(EventMetrics)
class EventMetricsAdmin(ModelAdmin):
    list_display = ['event', 'total_revenue', 'tickets_sold', 'orders_count', 'conversion_rate']
    list_filter = ['last_updated']
    search_fields = ['event__title']
    readonly_fields = ['last_updated']
    ordering = ['-last_updated']


@admin.register(PaymentMetrics)
class PaymentMetricsAdmin(ModelAdmin):
    list_display = ['payment', 'platform_fee', 'gateway_fee', 'net_amount_to_organizer', 'created_at']
    list_filter = ['created_at']
    search_fields = ['payment__reference']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(OrganizationMetrics)
class OrganizationMetricsAdmin(ModelAdmin):
    list_display = ['organization', 'total_revenue', 'total_events', 'total_tickets_sold', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['organization__name']
    readonly_fields = ['last_updated']
    ordering = ['-last_updated']
