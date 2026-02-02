import csv
import json
from datetime import datetime
from io import BytesIO, StringIO

from django.contrib.staticfiles import finders
from django.db.models import Count, Sum
from django.template.loader import render_to_string
from openpyxl import Workbook
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

from apps.payments.models import Payment
from apps.reports.queries import (
    get_checkin_data,
    get_payment_data,
    get_rsvp_data,
    get_swag_data,
)
from apps.tickets.models import Booking, Ticket

DATA_FETCHERS = {
    "RSVP": get_rsvp_data,
    "PAYMENTS": get_payment_data,
    "CHECKINS": get_checkin_data,
    "SWAG": get_swag_data,
}


def get_financial_summary(event):
    payments = Payment.objects.filter(
        booking__event=event, status=Payment.Status.CONFIRMED
    )

    return {
        "event": event,
        "total_revenue": payments.aggregate(total=Sum("amount"))["total"] or 0,
        "total_transactions": payments.count(),
        "tickets_sold": Ticket.objects.filter(
            booking__event=event, booking__status=Booking.Status.CONFIRMED
        ).count(),
        "ticket_breakdown": Ticket.objects.filter(
            booking__event=event, booking__status=Booking.Status.CONFIRMED
        )
        .values("ticket_type__name", "ticket_type__price")
        .annotate(count=Count("id"), revenue=Sum("ticket_type__price"))
        .order_by("-count"),
        "payment_methods": payments.values("provider")
        .annotate(count=Count("id"), total=Sum("amount"))
        .order_by("-total"),
        "generated_at": datetime.now(),
    }


def get_ticket_sales_data(event):
    tickets = Ticket.objects.filter(
        booking__event=event, booking__status=Booking.Status.CONFIRMED
    ).select_related("booking__user", "ticket_type", "booking__payment")

    return {
        "event": event,
        "tickets": tickets,
        "total_sold": tickets.count(),
        "by_type": tickets.values("ticket_type__name")
        .annotate(count=Count("id"))
        .order_by("-count"),
        "generated_at": datetime.now(),
    }


def generate_csv_content(data: list) -> str:
    if not data:
        return ""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()


def generate_csv_export(event, report_type: str, user, mask_emails: bool = True):
    fetcher = DATA_FETCHERS.get(report_type)
    if not fetcher:
        raise ValueError(f"Unknown report type: {report_type}")
    data = fetcher(event.id, mask_emails)
    content = generate_csv_content(data)
    filename = f"{report_type.lower()}_{event.slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return content.encode("utf-8"), filename, "text/csv"


def generate_excel_export(event, report_type: str, user, mask_emails: bool = True):
    fetcher = DATA_FETCHERS.get(report_type)
    if not fetcher:
        raise ValueError(f"Unknown report type: {report_type}")
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
    filename = f"{report_type.lower()}_{event.slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return (
        output.getvalue(),
        filename,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def generate_json_export(event, report_type: str, user, mask_emails: bool = True):
    if report_type == "FINANCIAL":
        data = get_financial_summary(event)
        json_data = {
            "event": {
                "id": event.id,
                "title": event.title,
                "slug": event.slug,
            },
            "total_revenue": float(data["total_revenue"]),
            "total_transactions": data["total_transactions"],
            "tickets_sold": data["tickets_sold"],
            "ticket_breakdown": list(data["ticket_breakdown"]),
            "payment_methods": list(data["payment_methods"]),
            "generated_at": data["generated_at"].isoformat(),
        }
    elif report_type == "TICKET_SALES":
        data = get_ticket_sales_data(event)
        json_data = {
            "event": {
                "id": event.id,
                "title": event.title,
                "slug": event.slug,
            },
            "total_sold": data["total_sold"],
            "by_type": list(data["by_type"]),
            "tickets": [
                {
                    "ticket_code": t.ticket_code,
                    "ticket_type": t.ticket_type.name,
                    "price": float(t.ticket_type.price),
                    "buyer_email": t.booking.user.email
                    if not mask_emails
                    else t.booking.user.email[:3] + "***",
                    "is_checked_in": t.is_checked_in,
                }
                for t in data["tickets"]
            ],
            "generated_at": data["generated_at"].isoformat(),
        }
    else:
        fetcher = DATA_FETCHERS.get(report_type)
        if fetcher:
            json_data = {
                "event": {
                    "id": event.id,
                    "title": event.title,
                    "slug": event.slug,
                },
                "data": fetcher(event.id, mask_emails),
                "generated_at": datetime.now().isoformat(),
            }
        else:
            json_data = {"error": "Unknown report type"}

    content = json.dumps(json_data, indent=2, default=str)
    filename = f"{report_type.lower()}_{event.slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return content.encode("utf-8"), filename, "application/json"


def generate_pdf_export(event, report_type: str, user, mask_emails: bool = True):
    template_map = {
        "RSVP": "reports/pdf/attendees.html",
        "PAYMENTS": "reports/pdf/payments.html",
        "FINANCIAL": "reports/pdf/financial.html",
        "TICKET_SALES": "reports/pdf/ticket_sales.html",
        "CHECKINS": "reports/pdf/checkins.html",
    }

    template = template_map.get(report_type, "reports/pdf/generic.html")

    if report_type == "FINANCIAL":
        context = get_financial_summary(event)
    elif report_type == "TICKET_SALES":
        context = get_ticket_sales_data(event)
    else:
        fetcher = DATA_FETCHERS.get(report_type)
        if fetcher:
            context = {
                "event": event,
                "data": fetcher(event.id, mask_emails),
                "generated_at": datetime.now(),
            }
        else:
            context = {"event": event, "data": [], "generated_at": datetime.now()}

    context["organization"] = event.organization
    context["report_type"] = report_type
    report_titles = {
        "RSVP": "Registered Attendees",
        "PAYMENTS": "Payment Records",
        "CHECKINS": "Check-in Report",
        "SWAG": "Swag Collection",
        "FINANCIAL": "Financial Summary",
        "TICKET_SALES": "Ticket Sales",
    }
    context["report_title"] = report_titles.get(report_type, report_type)

    html_content = render_to_string(template, context)

    font_config = FontConfiguration()
    css_path = finders.find("css/report_pdf.css")
    css = CSS(filename=css_path, font_config=font_config)

    html = HTML(string=html_content)
    pdf_content = html.write_pdf(stylesheets=[css], font_config=font_config)

    filename = f"{report_type.lower()}_{event.slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return pdf_content, filename, "application/pdf"
