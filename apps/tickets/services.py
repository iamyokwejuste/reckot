import logging
import qrcode
import base64
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from decimal import Decimal
from io import BytesIO
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from apps.tickets.models import TicketType, Booking, Ticket, TicketQuestionAnswer
from apps.events.models import CouponUsage, CheckoutQuestion


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


def create_multi_ticket_booking(
    user=None,
    event=None,
    ticket_selections: dict = None,
    question_answers: dict = None,
    coupon=None,
    guest_session=None,
    guest_email: str = None,
    guest_name: str = None,
    guest_phone: str = None,
    attendee_info: dict = None,
):
    if not user and not guest_email:
        return None, "Either user or guest email is required."

    with transaction.atomic():
        total_tickets = sum(ticket_selections.values())
        if total_tickets == 0:
            return None, "Please select at least one ticket."

        total_amount = Decimal("0.00")
        tickets_to_create = []
        now = timezone.localtime(timezone.now())
        now_naive = now.replace(tzinfo=None)

        for ticket_type_id, quantity in ticket_selections.items():
            if quantity <= 0:
                continue

            try:
                ticket_type = TicketType.objects.select_for_update().get(
                    id=ticket_type_id, event=event, is_active=True
                )
            except TicketType.DoesNotExist:
                return None, "Invalid ticket type selected."

            sales_start = (
                ticket_type.sales_start.replace(tzinfo=None)
                if ticket_type.sales_start
                else None
            )
            sales_end = (
                ticket_type.sales_end.replace(tzinfo=None)
                if ticket_type.sales_end
                else None
            )

            if sales_start and now_naive < sales_start:
                return (
                    None,
                    f"{ticket_type.name} tickets are not yet available for purchase.",
                )

            if sales_end and now_naive > sales_end:
                return (
                    None,
                    f"{ticket_type.name} tickets are no longer available for purchase.",
                )

            if ticket_type.available_quantity < quantity:
                return (
                    None,
                    f"Not enough {ticket_type.name} tickets available. Only {ticket_type.available_quantity} left.",
                )

            if quantity > ticket_type.max_per_order:
                return (
                    None,
                    f"Maximum {ticket_type.max_per_order} {ticket_type.name} tickets per order.",
                )

            for i in range(quantity):
                tickets_to_create.append((ticket_type, ticket_type_id, i))

            total_amount += ticket_type.price * quantity

        discount_amount = Decimal("0.00")
        if coupon and coupon.is_valid:
            if coupon.discount_type == "PERCENTAGE":
                discount_amount = total_amount * (
                    coupon.discount_value / Decimal("100")
                )
            else:
                discount_amount = min(coupon.discount_value, total_amount)
            total_amount = max(Decimal("0.00"), total_amount - discount_amount)

        booking = Booking.objects.create(
            user=user,
            event=event,
            total_amount=total_amount,
            guest_session=guest_session,
            guest_email=guest_email or "",
            guest_name=guest_name or "",
            guest_phone=guest_phone or "",
        )

        if coupon and discount_amount > 0:
            CouponUsage.objects.create(
                coupon=coupon,
                booking=booking,
                used_by=user,
                discount_amount=discount_amount,
            )
            coupon.use()

        if total_amount == Decimal("0.00"):
            booking.status = Booking.Status.CONFIRMED
            booking.save(update_fields=["status"])

        created_tickets = []
        for ticket_data in tickets_to_create:
            ticket_type, ticket_type_id, index = ticket_data

            attendee_name = ""
            attendee_email = ""

            if attendee_info:
                name_key = f"attendee_name_{ticket_type_id}_{index}"
                email_key = f"attendee_email_{ticket_type_id}_{index}"
                attendee_name = attendee_info.get(name_key, "")
                attendee_email = attendee_info.get(email_key, "")

            ticket = Ticket.objects.create(
                booking=booking,
                ticket_type=ticket_type,
                attendee_name=attendee_name,
                attendee_email=attendee_email,
            )
            created_tickets.append(ticket)

        if question_answers:
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
                            answer=answer,
                        )
                        break
                except CheckoutQuestion.DoesNotExist:
                    continue

        return booking, None


def get_organization_logo_base64(organization):
    if not organization.logo:
        return None
    try:
        with organization.logo.open("rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except Exception:
        return None


def generate_ticket_qr_code(ticket):
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
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()


def generate_ticket_pdf(ticket):
    logging.getLogger('fontTools').setLevel(logging.WARNING)
    logging.getLogger('weasyprint').setLevel(logging.WARNING)

    qr_code_data = generate_ticket_qr_code(ticket)
    event = ticket.ticket_type.event
    org = event.organization
    org_logo_base64 = get_organization_logo_base64(org)

    try:
        customization = event.customization
        primary_color = customization.primary_color or "#1a1a1a"
        secondary_color = customization.secondary_color or "#2d2d2d"
        text_color = customization.text_color or "#ffffff"
    except Exception:
        customization = None
        primary_color = "#1a1a1a"
        secondary_color = "#2d2d2d"
        text_color = "#ffffff"

    context = {
        "ticket": ticket,
        "event": event,
        "organization": org,
        "qr_code_data": qr_code_data,
        "org_logo_base64": org_logo_base64,
        "customization": customization,
    }

    html_content = render_to_string("tickets/pdf/ticket.html", context)

    font_config = FontConfiguration()
    css_content = f"""
        @page {{
            size: 4in 6in;
            margin: 0;
        }}
        body {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            margin: 0;
            padding: 0;
        }}
        .ticket {{
            width: 4in;
            height: 6in;
            background: linear-gradient(135deg, {primary_color} 0%, {secondary_color} 100%);
            color: {text_color};
            padding: 24px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        .ticket-header {{
            text-align: center;
            padding-bottom: 16px;
            border-bottom: 1px dashed rgba(255,255,255,0.2);
        }}
        .ticket-logo {{
            max-height: 40px;
            max-width: 120px;
            margin-bottom: 8px;
        }}
        .event-title {{
            font-size: 18px;
            font-weight: 700;
            margin: 0;
            line-height: 1.2;
        }}
        .ticket-type {{
            font-size: 11px;
            opacity: 0.7;
            margin-top: 4px;
        }}
        .ticket-details {{
            flex: 1;
            padding: 16px 0;
        }}
        .detail-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }}
        .detail-label {{
            font-size: 9px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            opacity: 0.6;
        }}
        .detail-value {{
            font-size: 12px;
            font-weight: 500;
        }}
        .qr-section {{
            text-align: center;
            padding-top: 12px;
            border-top: 1px dashed rgba(255,255,255,0.2);
        }}
        .qr-code {{
            background: white;
            padding: 10px;
            display: inline-block;
            border-radius: 8px;
        }}
        .qr-code img {{
            width: 90px;
            height: 90px;
        }}
        .ticket-code {{
            font-family: monospace;
            font-size: 9px;
            margin-top: 6px;
            opacity: 0.6;
        }}
    """

    css = CSS(string=css_content, font_config=font_config)

    html = HTML(string=html_content)
    pdf_content = html.write_pdf(stylesheets=[css], font_config=font_config)
    return pdf_content


def generate_booking_tickets_pdf(booking):
    logging.getLogger('fontTools').setLevel(logging.WARNING)
    logging.getLogger('weasyprint').setLevel(logging.WARNING)

    tickets = booking.tickets.select_related(
        "ticket_type", "ticket_type__event", "ticket_type__event__organization"
    )
    event = booking.event
    org = event.organization
    org_logo_base64 = get_organization_logo_base64(org)

    try:
        customization = event.customization
        primary_color = customization.primary_color or "#1a1a1a"
    except Exception:
        customization = None
        primary_color = "#1a1a1a"

    tickets_data = []
    for ticket in tickets:
        qr_code_data = generate_ticket_qr_code(ticket)
        tickets_data.append(
            {
                "ticket": ticket,
                "qr_code_data": qr_code_data,
            }
        )

    context = {
        "booking": booking,
        "event": event,
        "organization": org,
        "tickets_data": tickets_data,
        "org_logo_base64": org_logo_base64,
        "customization": customization,
    }

    html_content = render_to_string("tickets/pdf/booking_tickets.html", context)

    font_config = FontConfiguration()
    css_content = f"""
        @page {{
            size: A4;
            margin: 1cm;
        }}
        body {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            font-size: 12px;
            color: #1a1a1a;
        }}
        .page-break {{
            page-break-before: always;
        }}
        .ticket-card {{
            border: 2px solid #e5e5e5;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            background: #fafafa;
            page-break-inside: avoid;
        }}
        .ticket-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px dashed #e5e5e5;
        }}
        .org-logo {{
            max-height: 50px;
            max-width: 150px;
            margin-bottom: 8px;
        }}
        .event-info h2 {{
            margin: 0 0 4px;
            font-size: 18px;
        }}
        .event-info p {{
            margin: 0;
            color: #666;
            font-size: 12px;
        }}
        .ticket-type-badge {{
            background: {primary_color};
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
        }}
        .ticket-body {{
            display: flex;
            gap: 24px;
        }}
        .ticket-details {{
            flex: 1;
        }}
        .detail-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }}
        .detail-item label {{
            display: block;
            font-size: 10px;
            text-transform: uppercase;
            color: #888;
            margin-bottom: 2px;
        }}
        .detail-item span {{
            font-weight: 500;
        }}
        .qr-section {{
            text-align: center;
        }}
        .qr-code {{
            padding: 8px;
            background: white;
            border: 1px solid #e5e5e5;
            border-radius: 8px;
            display: inline-block;
        }}
        .qr-code img {{
            width: 80px;
            height: 80px;
        }}
        .ticket-code {{
            font-family: monospace;
            font-size: 9px;
            color: #888;
            margin-top: 4px;
        }}
    """

    css = CSS(string=css_content, font_config=font_config)

    html = HTML(string=html_content)
    pdf_content = html.write_pdf(stylesheets=[css], font_config=font_config)
    return pdf_content
