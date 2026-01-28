from django.db import transaction
from apps.tickets.models import TicketType, Booking, Ticket

def create_booking(user, ticket_type: TicketType, quantity: int):
    with transaction.atomic():
        if ticket_type.quantity < quantity:
            return None, "Not enough tickets available."

        booking = Booking.objects.create(user=user)
        for _ in range(quantity):
            Ticket.objects.create(booking=booking, ticket_type=ticket_type)

        ticket_type.quantity -= quantity
        ticket_type.save()
    return booking, None
