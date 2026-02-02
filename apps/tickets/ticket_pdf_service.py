import base64

from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration


def generate_ticket_pdf(booking, tickets, qr_code_bytes=None):
    if not isinstance(tickets, list):
        tickets = [tickets]

    event = booking.event
    organization = event.organization

    qr_code_data_uri = None
    if qr_code_bytes:
        qr_code_base64 = base64.b64encode(qr_code_bytes).decode("utf-8")
        qr_code_data_uri = f"data:image/png;base64,{qr_code_base64}"

    ticket_data = []
    for ticket in tickets:
        ticket_data.append(
            {
                "code": ticket.code,
                "type_name": ticket.ticket_type.name,
                "type_price": ticket.ticket_type.price,
                "attendee_name": ticket.attendee_name or booking.buyer_name,
                "attendee_email": ticket.attendee_email or booking.buyer_email,
            }
        )

    context = {
        "booking": booking,
        "event": event,
        "organization": organization,
        "tickets": ticket_data,
        "ticket_count": len(ticket_data),
        "qr_code": qr_code_data_uri,
        "organization_logo": organization.logo.url if organization.logo else None,
        "event_image": event.cover_image.url if event.cover_image else None,
    }

    html_content = render_to_string("tickets/ticket_pdf.html", context)
    font_config = FontConfiguration()

    css_path = finders.find("css/ticket_pdf.css")
    css = CSS(filename=css_path, font_config=font_config)

    html = HTML(string=html_content)
    pdf_bytes = html.write_pdf(stylesheets=[css], font_config=font_config)

    return pdf_bytes


def generate_single_ticket_pdf(ticket, booking, qr_code_bytes=None):
    return generate_ticket_pdf(booking, [ticket], qr_code_bytes)


def generate_multi_ticket_pdf(tickets, booking, qr_code_bytes=None):
    return generate_ticket_pdf(booking, tickets, qr_code_bytes)
