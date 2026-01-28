from io import BytesIO
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.conf import settings
from apps.payments.models import Invoice, Payment


def create_invoice(payment: Payment) -> Invoice:
    if hasattr(payment, 'invoice'):
        return payment.invoice

    booking = payment.booking
    event = booking.event
    organization = event.organization
    user = booking.user

    tickets = booking.tickets.select_related('ticket_type')
    subtotal = sum(t.ticket_type.price for t in tickets)

    invoice = Invoice.objects.create(
        payment=payment,
        invoice_number=Invoice.generate_invoice_number(),
        subtotal=subtotal,
        service_fee=payment.service_fee,
        total_amount=payment.amount + payment.service_fee,
        currency=payment.currency,
        billing_name=user.get_full_name() or user.email,
        billing_email=user.email,
        organization_name=organization.name,
        organization_email=organization.owner.email if organization.owner else '',
        organization_logo=organization.logo.url if organization.logo else '',
    )

    generate_invoice_pdf(invoice)
    return invoice


def generate_invoice_pdf(invoice: Invoice) -> None:
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
    except ImportError:
        return

    payment = invoice.payment
    booking = payment.booking
    tickets = booking.tickets.select_related('ticket_type')

    ticket_items = []
    for ticket in tickets:
        ticket_items.append({
            'description': f"{ticket.ticket_type.name} - {booking.event.title}",
            'quantity': 1,
            'unit_price': ticket.ticket_type.price,
            'total': ticket.ticket_type.price,
        })

    context = {
        'invoice': invoice,
        'payment': payment,
        'booking': booking,
        'event': booking.event,
        'ticket_items': ticket_items,
        'organization': booking.event.organization,
    }

    html_content = render_to_string('payments/invoice_pdf.html', context)
    font_config = FontConfiguration()

    css = CSS(string='''
        @page { size: A4; margin: 1.5cm; }
        body { font-family: sans-serif; font-size: 12px; line-height: 1.5; color: #1a1a1a; }
        .invoice-header { display: flex; justify-content: space-between; margin-bottom: 30px; }
        .invoice-title { font-size: 28px; font-weight: bold; color: #111; }
        .invoice-meta { text-align: right; }
        .invoice-number { font-size: 14px; color: #666; }
        .section { margin-bottom: 25px; }
        .section-title { font-size: 11px; font-weight: 600; color: #666; text-transform: uppercase; margin-bottom: 8px; }
        .billing-info { font-size: 13px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th { background: #f5f5f5; padding: 10px; text-align: left; font-size: 11px; text-transform: uppercase; border-bottom: 2px solid #ddd; }
        td { padding: 12px 10px; border-bottom: 1px solid #eee; }
        .text-right { text-align: right; }
        .totals { margin-top: 20px; }
        .totals-row { display: flex; justify-content: flex-end; padding: 5px 0; }
        .totals-label { width: 150px; text-align: right; padding-right: 20px; }
        .totals-value { width: 100px; text-align: right; font-weight: 500; }
        .total-final { font-size: 16px; font-weight: bold; border-top: 2px solid #111; padding-top: 10px; margin-top: 10px; }
        .status-paid { display: inline-block; background: #22c55e; color: white; padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: 600; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 11px; color: #666; text-align: center; }
    ''', font_config=font_config)

    html = HTML(string=html_content)
    pdf_bytes = html.write_pdf(stylesheets=[css], font_config=font_config)

    filename = f"invoice_{invoice.invoice_number}.pdf"
    invoice.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)


def get_invoice_pdf(invoice: Invoice) -> bytes:
    if invoice.pdf_file:
        invoice.pdf_file.open('rb')
        content = invoice.pdf_file.read()
        invoice.pdf_file.close()
        return content

    generate_invoice_pdf(invoice)
    if invoice.pdf_file:
        invoice.pdf_file.open('rb')
        content = invoice.pdf_file.read()
        invoice.pdf_file.close()
        return content

    return b''
