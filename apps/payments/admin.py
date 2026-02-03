from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from apps.payments.models import (
    PaymentGatewayConfig,
    Payment,
    OfflinePayment,
    Refund,
    RefundAuditLog,
    Invoice,
    Withdrawal
)


@admin.register(PaymentGatewayConfig)
class PaymentGatewayConfigAdmin(ModelAdmin):
    list_display = ["provider", "is_active", "is_default", "created_at"]
    list_filter = ["provider", "is_active", "is_default"]
    search_fields = ["provider", "merchant_name"]


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ["reference", "booking_info", "amount", "currency", "provider", "status_badge", "created_at"]
    list_filter = ["status", "provider", "currency", "created_at"]
    search_fields = ["reference", "booking__reference"]
    readonly_fields = ["reference", "created_at", "expires_at"]
    date_hierarchy = "created_at"

    @display(description="Booking")
    def booking_info(self, obj):
        if obj.booking:
            return f"{obj.booking.reference}"
        return "-"

    @display(description="Status", label=True)
    def status_badge(self, obj):
        colors = {
            "PENDING": "warning",
            "COMPLETED": "success",
            "CONFIRMED": "success",
            "FAILED": "danger",
            "EXPIRED": "secondary",
            "REFUNDED": "info",
        }
        return obj.status, colors.get(obj.status, "secondary")


@admin.register(OfflinePayment)
class OfflinePaymentAdmin(ModelAdmin):
    list_display = ["id", "payment", "method_description", "verification_status", "verified_by"]
    list_filter = ["verification_status"]
    search_fields = ["payment__reference"]


@admin.register(Refund)
class RefundAdmin(ModelAdmin):
    list_display = ["payment", "amount", "status", "reason_display", "created_at"]
    list_filter = ["status", "reason"]
    search_fields = ["payment__reference"]
    date_hierarchy = "created_at"

    @display(description="Reason")
    def reason_display(self, obj):
        return obj.get_reason_display()


@admin.register(RefundAuditLog)
class RefundAuditLogAdmin(ModelAdmin):
    list_display = ["refund", "action", "performed_by", "created_at"]
    list_filter = ["action"]
    search_fields = ["refund__payment__reference"]


@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ["invoice_number", "order", "total_amount", "issued_at"]
    list_filter = ["issued_at"]
    search_fields = ["invoice_number"]
    readonly_fields = ["invoice_number", "issued_at"]
    date_hierarchy = "issued_at"

    @display(description="Order")
    def order(self, obj):
        return getattr(obj, 'booking', '-') or getattr(obj, 'order', '-')


@admin.register(Withdrawal)
class WithdrawalAdmin(ModelAdmin):
    list_display = ["reference", "organization", "amount", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["reference", "organization__name"]
    readonly_fields = ["reference"]
    date_hierarchy = "created_at"
