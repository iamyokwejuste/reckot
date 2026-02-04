from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from apps.tickets.models import GuestSession, Booking, Ticket, TicketQuestionAnswer


class TicketInline(TabularInline):
    model = Ticket
    extra = 0
    fields = ["ticket_type", "attendee_name", "attendee_email"]


@admin.register(GuestSession)
class GuestSessionAdmin(ModelAdmin):
    list_display = ["email", "name", "token", "created_at", "expires_at"]
    list_filter = ["created_at", "expires_at"]
    search_fields = ["email", "name"]
    readonly_fields = ["token", "created_at"]
    date_hierarchy = "created_at"


@admin.register(Booking)
class BookingAdmin(ModelAdmin):
    list_display = [
        "reference",
        "event",
        "customer_info",
        "status_badge",
        "total_amount",
        "created_at",
    ]
    list_filter = ["status", "delivery_method", "created_at"]
    search_fields = ["reference", "guest_email", "guest_name"]
    readonly_fields = ["reference", "created_at", "updated_at"]
    date_hierarchy = "created_at"
    inlines = [TicketInline]

    @display(description="Customer")
    def customer_info(self, obj):
        if obj.user:
            return obj.user.email
        return obj.guest_email

    @display(description="Status", label=True)
    def status_badge(self, obj):
        colors = {
            "PENDING": "warning",
            "CONFIRMED": "success",
            "CANCELLED": "danger",
            "REFUNDED": "info",
        }
        return obj.status, colors.get(obj.status, "secondary")


@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    list_display = [
        "id",
        "booking",
        "ticket_type",
        "attendee_name",
        "checked_in_status",
    ]
    list_filter = ["ticket_type__event__organization"]
    search_fields = ["attendee_name", "attendee_email", "booking__reference"]

    @display(description="Checked In", boolean=True)
    def checked_in_status(self, obj):
        return obj.check_in_time is not None


@admin.register(TicketQuestionAnswer)
class TicketQuestionAnswerAdmin(ModelAdmin):
    list_display = ["ticket", "question", "answer_preview"]
    search_fields = ["answer"]

    @display(description="Answer")
    def answer_preview(self, obj):
        return obj.answer[:50] + "..." if len(obj.answer) > 50 else obj.answer
