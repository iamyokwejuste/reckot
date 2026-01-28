from django.db import transaction
from decimal import Decimal
from apps.tickets.models import TicketType, Booking, Ticket, TicketQuestionAnswer


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


def create_multi_ticket_booking(user, event, ticket_selections: dict, question_answers: dict = None):
    """
    Create a booking with multiple ticket types.

    Args:
        user: The user making the booking
        event: The event being booked
        ticket_selections: Dict of {ticket_type_id: quantity}
        question_answers: Dict of {question_id: answer}

    Returns:
        tuple: (booking, error_message)
    """
    with transaction.atomic():
        total_tickets = sum(ticket_selections.values())
        if total_tickets == 0:
            return None, "Please select at least one ticket."

        total_amount = Decimal('0.00')
        tickets_to_create = []

        for ticket_type_id, quantity in ticket_selections.items():
            if quantity <= 0:
                continue

            try:
                ticket_type = TicketType.objects.select_for_update().get(
                    id=ticket_type_id,
                    event=event,
                    is_active=True
                )
            except TicketType.DoesNotExist:
                return None, f"Invalid ticket type selected."

            if ticket_type.available_quantity < quantity:
                return None, f"Not enough {ticket_type.name} tickets available. Only {ticket_type.available_quantity} left."

            if quantity > ticket_type.max_per_order:
                return None, f"Maximum {ticket_type.max_per_order} {ticket_type.name} tickets per order."

            for _ in range(quantity):
                tickets_to_create.append(ticket_type)

            total_amount += ticket_type.price * quantity

        booking = Booking.objects.create(
            user=user,
            event=event,
            total_amount=total_amount
        )

        created_tickets = []
        for ticket_type in tickets_to_create:
            ticket = Ticket.objects.create(
                booking=booking,
                ticket_type=ticket_type
            )
            created_tickets.append(ticket)

        if question_answers:
            from apps.events.models import CheckoutQuestion
            for question_id, answer in question_answers.items():
                if not answer:
                    continue
                try:
                    question = CheckoutQuestion.objects.get(id=question_id, event=event)
                    for ticket in created_tickets:
                        TicketQuestionAnswer.objects.create(
                            ticket=ticket,
                            booking=booking,
                            question=question,
                            answer=answer
                        )
                        break
                except CheckoutQuestion.DoesNotExist:
                    continue

        return booking, None
