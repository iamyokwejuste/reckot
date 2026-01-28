import csv
from io import StringIO, BytesIO
from datetime import datetime
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.db.models import Sum, Count
from openpyxl import Workbook
from apps.reports.models import ReportExport
from apps.reports.queries import get_rsvp_data, get_payment_data, get_checkin_data, get_swag_data


DATA_FETCHERS = {
    'RSVP': get_rsvp_data,
    'PAYMENTS': get_payment_data,
    'CHECKINS': get_checkin_data,
    'SWAG': get_swag_data,
}


def get_financial_summary(event):
    from apps.payments.models import Payment
    from apps.tickets.models import Ticket, Booking

    payments = Payment.objects.filter(
        booking__event=event,
        status=Payment.Status.CONFIRMED
    )

    return {
        'event': event,
        'total_revenue': payments.aggregate(total=Sum('amount'))['total'] or 0,
        'total_transactions': payments.count(),
        'tickets_sold': Ticket.objects.filter(
            booking__event=event,
            booking__status=Booking.Status.CONFIRMED
        ).count(),
        'ticket_breakdown': Ticket.objects.filter(
            booking__event=event,
            booking__status=Booking.Status.CONFIRMED
        ).values('ticket_type__name', 'ticket_type__price').annotate(
            count=Count('id'),
            revenue=Sum('ticket_type__price')
        ).order_by('-count'),
        'payment_methods': payments.values('method').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('-total'),
        'generated_at': datetime.now(),
    }


def get_ticket_sales_data(event):
    from apps.tickets.models import Ticket, Booking

    tickets = Ticket.objects.filter(
        booking__event=event,
        booking__status=Booking.Status.CONFIRMED
    ).select_related('booking__user', 'ticket_type', 'booking__payment')

    return {
        'event': event,
        'tickets': tickets,
        'total_sold': tickets.count(),
        'by_type': tickets.values('ticket_type__name').annotate(
            count=Count('id')
        ).order_by('-count'),
        'generated_at': datetime.now(),
    }


def generate_csv_content(data: list) -> str:
    if not data:
        return ''
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()


def generate_csv_export(event, report_type: str, user, mask_emails: bool = True) -> ReportExport:
    fetcher = DATA_FETCHERS.get(report_type)
    if not fetcher:
        raise ValueError(f'Unknown report type: {report_type}')
    data = fetcher(event.id, mask_emails)
    content = generate_csv_content(data)
    export = ReportExport.objects.create(
        event=event,
        report_type=report_type,
        format='CSV',
        created_by=user,
        mask_emails=mask_emails
    )
    filename = f'{report_type.lower()}_{event.id}_{export.id}.csv'
    export.file.save(filename, ContentFile(content.encode('utf-8')))
    return export


def generate_excel_export(event, report_type: str, user, mask_emails: bool = True) -> ReportExport:
    fetcher = DATA_FETCHERS.get(report_type)
    if not fetcher:
        raise ValueError(f'Unknown report type: {report_type}')
    data = fetcher(event.id, mask_emails)
    wb = Workbook()
    ws = wb.active
    ws.title = report_type
    if data:
        headers = list(data[0].keys())
        ws.append(headers)
        for row in data:
            ws.append([row[h] for h in headers])
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    export = ReportExport.objects.create(
        event=event,
        report_type=report_type,
        format='EXCEL',
        created_by=user,
        mask_emails=mask_emails
    )
    filename = f'{report_type.lower()}_{event.id}_{export.id}.xlsx'
    export.file.save(filename, ContentFile(output.getvalue()))
    return export


def get_recent_exports(event_id: int, limit: int = 10):
    return ReportExport.objects.filter(
        event_id=event_id
    ).order_by('-created_at')[:limit]


def generate_json_export(event, report_type: str, user, mask_emails: bool = True) -> ReportExport:
    import json

    if report_type == 'FINANCIAL':
        data = get_financial_summary(event)
        # Convert to JSON-serializable format
        json_data = {
            'event': {
                'id': event.id,
                'title': event.title,
                'slug': event.slug,
            },
            'total_revenue': float(data['total_revenue']),
            'total_transactions': data['total_transactions'],
            'tickets_sold': data['tickets_sold'],
            'ticket_breakdown': list(data['ticket_breakdown']),
            'payment_methods': list(data['payment_methods']),
            'generated_at': data['generated_at'].isoformat(),
        }
    elif report_type == 'TICKET_SALES':
        data = get_ticket_sales_data(event)
        json_data = {
            'event': {
                'id': event.id,
                'title': event.title,
                'slug': event.slug,
            },
            'total_sold': data['total_sold'],
            'by_type': list(data['by_type']),
            'tickets': [
                {
                    'ticket_code': t.ticket_code,
                    'ticket_type': t.ticket_type.name,
                    'price': float(t.ticket_type.price),
                    'buyer_email': t.booking.user.email if not mask_emails else t.booking.user.email[:3] + '***',
                    'is_checked_in': t.is_checked_in,
                }
                for t in data['tickets']
            ],
            'generated_at': data['generated_at'].isoformat(),
        }
    else:
        fetcher = DATA_FETCHERS.get(report_type)
        if fetcher:
            json_data = {
                'event': {
                    'id': event.id,
                    'title': event.title,
                    'slug': event.slug,
                },
                'data': fetcher(event.id, mask_emails),
                'generated_at': datetime.now().isoformat(),
            }
        else:
            json_data = {'error': 'Unknown report type'}

    content = json.dumps(json_data, indent=2, default=str)

    export = ReportExport.objects.create(
        event=event,
        report_type=report_type,
        format='JSON',
        created_by=user,
        mask_emails=mask_emails
    )
    filename = f'{report_type.lower()}_{event.slug}_{export.reference.hex[:8]}.json'
    export.file.save(filename, ContentFile(content.encode('utf-8')))
    return export


def generate_pdf_export(event, report_type: str, user, mask_emails: bool = True) -> ReportExport:
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
    except ImportError:
        raise ImportError('weasyprint is required for PDF export. Install it with: pip install weasyprint')

    template_map = {
        'RSVP': 'reports/pdf/attendees.html',
        'PAYMENTS': 'reports/pdf/payments.html',
        'FINANCIAL': 'reports/pdf/financial.html',
        'TICKET_SALES': 'reports/pdf/ticket_sales.html',
        'CHECKINS': 'reports/pdf/checkins.html',
    }

    template = template_map.get(report_type, 'reports/pdf/generic.html')

    if report_type == 'FINANCIAL':
        context = get_financial_summary(event)
    elif report_type == 'TICKET_SALES':
        context = get_ticket_sales_data(event)
    else:
        fetcher = DATA_FETCHERS.get(report_type)
        if fetcher:
            context = {
                'event': event,
                'data': fetcher(event.id, mask_emails),
                'generated_at': datetime.now(),
            }
        else:
            context = {'event': event, 'data': [], 'generated_at': datetime.now()}

    context['organization'] = event.organization
    context['report_type'] = report_type
    context['report_title'] = dict(ReportExport.Type.choices).get(report_type, report_type)

    html_content = render_to_string(template, context)

    font_config = FontConfiguration()
    css = CSS(string='''
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        @page {
            size: A4;
            margin: 2cm;
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10px;
                color: #666;
            }
        }
        body {
            font-family: 'Inter', system-ui, sans-serif;
            font-size: 12px;
            line-height: 1.5;
            color: #1a1a1a;
        }
        .cover-page {
            page-break-after: always;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            text-align: center;
        }
        .cover-logo {
            max-width: 200px;
            max-height: 100px;
            margin-bottom: 40px;
        }
        .cover-title {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 16px;
        }
        .cover-subtitle {
            font-size: 18px;
            color: #666;
            margin-bottom: 8px;
        }
        .cover-date {
            font-size: 14px;
            color: #999;
            margin-top: 40px;
        }
        h1 { font-size: 24px; font-weight: 700; margin-bottom: 16px; }
        h2 { font-size: 18px; font-weight: 600; margin: 24px 0 12px; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
        }
        th, td {
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid #e5e5e5;
        }
        th {
            background: #f5f5f5;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        tr:nth-child(even) { background: #fafafa; }
        .stat-card {
            display: inline-block;
            padding: 16px 24px;
            background: #f5f5f5;
            border-radius: 8px;
            margin: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: #1a1a1a;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }
        .summary-section { margin: 24px 0; }
        .text-right { text-align: right; }
        .text-muted { color: #666; }
        .font-bold { font-weight: 600; }
    ''', font_config=font_config)

    html = HTML(string=html_content)
    pdf_content = html.write_pdf(stylesheets=[css], font_config=font_config)

    export = ReportExport.objects.create(
        event=event,
        report_type=report_type,
        format='PDF',
        created_by=user,
        mask_emails=mask_emails
    )
    filename = f'{report_type.lower()}_{event.slug}_{export.reference.hex[:8]}.pdf'
    export.file.save(filename, ContentFile(pdf_content))
    return export
