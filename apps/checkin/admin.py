from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from apps.checkin.models import SwagItem, CheckIn, SwagCollection


@admin.register(SwagItem)
class SwagItemAdmin(ModelAdmin):
    list_display = ["name", "event", "quantity", "distributed_count", "remaining_count"]
    list_filter = ["event"]
    search_fields = ["name", "event__title", "description"]

    @display(description="Distributed")
    def distributed_count(self, obj):
        return obj.collections.count()

    @display(description="Remaining")
    def remaining_count(self, obj):
        return obj.quantity - obj.collections.count()


@admin.register(CheckIn)
class CheckInAdmin(ModelAdmin):
    list_display = ["ticket", "event_name", "attendee_name", "checked_in_at", "checked_in_by"]
    list_filter = ["checked_in_at"]
    search_fields = ["ticket__attendee_name", "ticket__attendee_email"]
    readonly_fields = ["checked_in_at"]
    date_hierarchy = "checked_in_at"

    @display(description="Event")
    def event_name(self, obj):
        if obj.ticket and obj.ticket.booking:
            return obj.ticket.booking.event.title
        return "-"

    @display(description="Attendee")
    def attendee_name(self, obj):
        return obj.ticket.attendee_name or obj.ticket.booking.guest_name


@admin.register(SwagCollection)
class SwagCollectionAdmin(ModelAdmin):
    list_display = ["id", "item_name", "ticket_ref", "attendee_name", "collected_at"]
    list_filter = ["collected_at"]
    search_fields = ["ticket__attendee_name"]
    readonly_fields = ["collected_at"]
    date_hierarchy = "collected_at"

    @display(description="Item")
    def item_name(self, obj):
        return getattr(obj, 'swag_item', '-')

    @display(description="Ticket")
    def ticket_ref(self, obj):
        return getattr(obj, 'ticket', '-')

    @display(description="Attendee")
    def attendee_name(self, obj):
        ticket = getattr(obj, 'ticket', None)
        if ticket:
            return ticket.attendee_name or ticket.booking.guest_name
        return "-"
