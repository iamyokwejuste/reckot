import csv
from io import StringIO, BytesIO
from django.core.files.base import ContentFile
from openpyxl import Workbook
from .models import ReportExport
from .queries import get_rsvp_data, get_payment_data, get_checkin_data, get_swag_data


DATA_FETCHERS = {
    'RSVP': get_rsvp_data,
    'PAYMENTS': get_payment_data,
    'CHECKINS': get_checkin_data,
    'SWAG': get_swag_data,
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
