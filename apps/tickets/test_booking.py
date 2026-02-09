import pytest
from decimal import Decimal
from apps.tickets.models import Booking, TicketType


@pytest.mark.django_db
class TestBookingCreation:
    def test_create_booking(self, event, user, ticket_type):
        booking = Booking.objects.create(
            event=event,
            user=user,
            total_amount=ticket_type.price,
            status=Booking.Status.PENDING,
        )
        assert booking.total_amount == ticket_type.price
        assert booking.status == Booking.Status.PENDING

    def test_free_event_booking(self, event, user):
        free_tt = TicketType.objects.create(
            event=event,
            name="Free Ticket",
            price=Decimal("0"),
            quantity=50,
        )
        booking = Booking.objects.create(
            event=event,
            user=user,
            total_amount=Decimal("0"),
            status=Booking.Status.PENDING,
        )
        assert booking.total_amount == Decimal("0")
