from django.contrib.staticfiles import finders
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

from apps.payments.models import Invoice, Payment


def create_invoice(payment: Payment) -> Invoice:
    if hasattr(payment, "invoice"):
        return payment.invoice

    booking = payment.booking
    event = booking.event
    organization = event.organization
    user = booking.user
    tickets = booking.tickets.select_related("ticket_type")
    subtotal = sum(t.ticket_type.price for t in tickets)

    if user:
        billing_name = user.get_full_name() or user.email
        billing_email = user.email
    else:
        billing_name = booking.guest_name or booking.guest_email
        billing_email = booking.guest_email

    invoice = Invoice.objects.create(
        payment=payment,
        invoice_number=Invoice.generate_invoice_number(),
        subtotal=subtotal,
        service_fee=payment.service_fee,
        total_amount=payment.amount + payment.service_fee,
        currency=payment.currency,
        billing_name=billing_name,
        billing_email=billing_email,
        organization_name=organization.name,
        organization_email=organization.owner.email if organization.owner else "",
        organization_logo=organization.logo.url if organization.logo else "",
    )

    generate_invoice_pdf(invoice)
    return invoice


def generate_invoice_pdf(invoice: Invoice) -> None:
    payment = invoice.payment
    booking = payment.booking
    tickets = booking.tickets.select_related("ticket_type")

    ticket_items = []
    for ticket in tickets:
        ticket_items.append(
            {
                "description": f"{ticket.ticket_type.name} - {booking.event.title}",
                "quantity": 1,
                "unit_price": ticket.ticket_type.price,
                "total": ticket.ticket_type.price,
            }
        )

    context = {
        "invoice": invoice,
        "payment": payment,
        "booking": booking,
        "event": booking.event,
        "ticket_items": ticket_items,
        "organization": booking.event.organization,
    }

    html_content = render_to_string("payments/invoice_pdf.html", context)
    font_config = FontConfiguration()

    css_path = finders.find("css/invoice_pdf.css")
    css = CSS(filename=css_path, font_config=font_config)

    html = HTML(string=html_content)
    pdf_bytes = html.write_pdf(stylesheets=[css], font_config=font_config)

    filename = f"invoice_{invoice.invoice_number}.pdf"
    invoice.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)


def get_invoice_pdf(invoice: Invoice) -> bytes:
    if invoice.pdf_file:
        invoice.pdf_file.open("rb")
        content = invoice.pdf_file.read()
        invoice.pdf_file.close()
        return content

    generate_invoice_pdf(invoice)
    if invoice.pdf_file:
        invoice.pdf_file.open("rb")
        content = invoice.pdf_file.read()
        invoice.pdf_file.close()
        return content

    return b""
