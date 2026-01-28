from django.db import transaction
from django.template.loader import render_to_string
from decimal import Decimal
from io import BytesIO
import qrcode
import base64
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


def generate_ticket_qr_code(ticket):
    """Generate a QR code for a ticket."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(str(ticket.code))
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()


def generate_ticket_pdf(ticket):
    """Generate a PDF for a single ticket."""
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
    except ImportError:
        raise ImportError('weasyprint is required for PDF tickets. Install with: pip install weasyprint')

    qr_code_data = generate_ticket_qr_code(ticket)
    event = ticket.ticket_type.event
    org = event.organization

    try:
        customization = event.customization
    except Exception:
        customization = None

    context = {
        'ticket': ticket,
        'event': event,
        'organization': org,
        'qr_code_data': qr_code_data,
        'customization': customization,
    }

    html_content = render_to_string('tickets/pdf/ticket.html', context)

    font_config = FontConfiguration()
    css = CSS(string='''
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        @page {
            size: 4in 6in;
            margin: 0;
        }
        body {
            font-family: 'Inter', system-ui, sans-serif;
            margin: 0;
            padding: 0;
        }
        .ticket {
            width: 4in;
            height: 6in;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            color: white;
            padding: 24px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
        }
        .ticket-header {
            text-align: center;
            padding-bottom: 16px;
            border-bottom: 1px dashed rgba(255,255,255,0.2);
        }
        .ticket-logo {
            max-height: 40px;
            max-width: 120px;
            margin-bottom: 8px;
        }
        .event-title {
            font-size: 20px;
            font-weight: 700;
            margin: 0;
            line-height: 1.2;
        }
        .ticket-type {
            font-size: 12px;
            opacity: 0.7;
            margin-top: 4px;
        }
        .ticket-details {
            flex: 1;
            padding: 16px 0;
        }
        .detail-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
        }
        .detail-label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            opacity: 0.6;
        }
        .detail-value {
            font-size: 13px;
            font-weight: 500;
        }
        .qr-section {
            text-align: center;
            padding-top: 16px;
            border-top: 1px dashed rgba(255,255,255,0.2);
        }
        .qr-code {
            background: white;
            padding: 12px;
            display: inline-block;
            border-radius: 8px;
        }
        .qr-code img {
            width: 100px;
            height: 100px;
        }
        .ticket-code {
            font-family: monospace;
            font-size: 10px;
            margin-top: 8px;
            opacity: 0.6;
        }
    ''', font_config=font_config)

    html = HTML(string=html_content)
    pdf_content = html.write_pdf(stylesheets=[css], font_config=font_config)
    return pdf_content


def generate_booking_tickets_pdf(booking):
    """Generate a PDF with all tickets from a booking."""
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
    except ImportError:
        raise ImportError('weasyprint is required for PDF tickets. Install with: pip install weasyprint')

    tickets = booking.tickets.select_related('ticket_type', 'ticket_type__event', 'ticket_type__event__organization')
    event = booking.event
    org = event.organization

    try:
        customization = event.customization
    except Exception:
        customization = None

    tickets_data = []
    for ticket in tickets:
        qr_code_data = generate_ticket_qr_code(ticket)
        tickets_data.append({
            'ticket': ticket,
            'qr_code_data': qr_code_data,
        })

    context = {
        'booking': booking,
        'event': event,
        'organization': org,
        'tickets_data': tickets_data,
        'customization': customization,
    }

    html_content = render_to_string('tickets/pdf/booking_tickets.html', context)

    font_config = FontConfiguration()
    css = CSS(string='''
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        @page {
            size: A4;
            margin: 1cm;
        }
        body {
            font-family: 'Inter', system-ui, sans-serif;
            font-size: 12px;
            color: #1a1a1a;
        }
        .page-break {
            page-break-before: always;
        }
        .ticket-card {
            border: 2px solid #e5e5e5;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            background: #fafafa;
        }
        .ticket-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px dashed #e5e5e5;
        }
        .event-info h2 {
            margin: 0 0 4px;
            font-size: 18px;
        }
        .event-info p {
            margin: 0;
            color: #666;
            font-size: 12px;
        }
        .ticket-type-badge {
            background: #1a1a1a;
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
        }
        .ticket-body {
            display: flex;
            gap: 24px;
        }
        .ticket-details {
            flex: 1;
        }
        .detail-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        .detail-item label {
            display: block;
            font-size: 10px;
            text-transform: uppercase;
            color: #888;
            margin-bottom: 2px;
        }
        .detail-item span {
            font-weight: 500;
        }
        .qr-section {
            text-align: center;
        }
        .qr-code {
            padding: 8px;
            background: white;
            border: 1px solid #e5e5e5;
            border-radius: 8px;
            display: inline-block;
        }
        .qr-code img {
            width: 80px;
            height: 80px;
        }
        .ticket-code {
            font-family: monospace;
            font-size: 9px;
            color: #888;
            margin-top: 4px;
        }
    ''', font_config=font_config)

    html = HTML(string=html_content)
    pdf_content = html.write_pdf(stylesheets=[css], font_config=font_config)
    return pdf_content
