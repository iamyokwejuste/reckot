import json
import csv
from datetime import datetime
from io import BytesIO
from openpyxl import Workbook
from django.views import View
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string
from weasyprint import HTML

from apps.tickets.models import Ticket, Booking
from apps.tickets.services import generate_ticket_pdf, generate_booking_tickets_pdf
from apps.payments.models import Payment


class TicketListView(LoginRequiredMixin, View):
    def get(self, request):
        export_format = request.GET.get("export")

        tickets = Ticket.objects.filter(
            booking__event__organization__members=request.user
        ).select_related("booking__user", "booking__event", "ticket_type", "booking__guest_session")

        search = request.GET.get("search", "").strip()
        if search:
            tickets = tickets.filter(
                Q(attendee_name__icontains=search)
                | Q(attendee_email__icontains=search)
                | Q(booking__user__email__icontains=search)
                | Q(booking__guest_email__icontains=search)
                | Q(booking__guest_name__icontains=search)
                | Q(code__icontains=search)
            )

        event_id = request.GET.get("event")
        if event_id:
            tickets = tickets.filter(booking__event_id=event_id)

        status = request.GET.get("status")
        if status:
            tickets = tickets.filter(booking__status=status)

        checked_in = request.GET.get("checked_in")
        if checked_in == "yes":
            tickets = tickets.filter(is_checked_in=True)
        elif checked_in == "no":
            tickets = tickets.filter(is_checked_in=False)

        date_from = request.GET.get("date_from")
        if date_from:
            tickets = tickets.filter(booking__created_at__gte=date_from)

        date_to = request.GET.get("date_to")
        if date_to:
            tickets = tickets.filter(booking__created_at__lte=date_to)

        tickets = tickets.order_by("-booking__created_at")

        if export_format:
            return self._export_tickets(tickets, export_format, request.user)

        tickets = tickets[:100]

        stats = {
            "total": Ticket.objects.filter(
                booking__event__organization__members=request.user,
                booking__status=Booking.Status.CONFIRMED,
            ).count(),
            "checked_in": Ticket.objects.filter(
                booking__event__organization__members=request.user, is_checked_in=True
            ).count(),
            "pending": Ticket.objects.filter(
                booking__event__organization__members=request.user,
                booking__status=Booking.Status.PENDING,
            ).count(),
        }

        events = (
            request.user.organizations.first().events.all()
            if request.user.organizations.exists()
            else []
        )

        return render(
            request,
            "tickets/list.html",
            {
                "tickets": tickets,
                "stats": stats,
                "events": events,
            },
        )

    def _export_tickets(self, tickets, format_type, user):
        if format_type == "json":
            data = []
            for ticket in tickets:
                data.append({
                    "code": str(ticket.code),
                    "ticket_type": ticket.ticket_type.name,
                    "event": ticket.booking.event.title,
                    "attendee_name": ticket.attendee_name or "",
                    "attendee_email": ticket.attendee_email or "",
                    "booking_email": ticket.booking.user.email if ticket.booking.user else ticket.booking.guest_email,
                    "booking_name": ticket.booking.user.get_full_name() if ticket.booking.user else ticket.booking.guest_name,
                    "status": ticket.booking.status,
                    "checked_in": ticket.is_checked_in,
                    "booking_date": ticket.booking.created_at.isoformat(),
                })

            response = HttpResponse(
                json.dumps(data, indent=2),
                content_type="application/json"
            )
            response["Content-Disposition"] = f'attachment; filename="rsvp-export-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json"'
            return response

        elif format_type == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = f'attachment; filename="rsvp-export-{datetime.now().strftime("%Y%m%d-%H%M%S")}.csv"'

            writer = csv.writer(response)
            writer.writerow([
                "Ticket Code", "Ticket Type", "Event", "Attendee Name",
                "Attendee Email", "Booking Email", "Booking Name",
                "Status", "Checked In", "Booking Date"
            ])

            for ticket in tickets:
                writer.writerow([
                    str(ticket.code),
                    ticket.ticket_type.name,
                    ticket.booking.event.title,
                    ticket.attendee_name or "",
                    ticket.attendee_email or "",
                    ticket.booking.user.email if ticket.booking.user else ticket.booking.guest_email,
                    ticket.booking.user.get_full_name() if ticket.booking.user else ticket.booking.guest_name,
                    ticket.booking.status,
                    "Yes" if ticket.is_checked_in else "No",
                    ticket.booking.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                ])

            return response

        elif format_type == "excel":
            wb = Workbook()
            ws = wb.active
            ws.title = "RSVP Export"

            headers = [
                "Ticket Code", "Ticket Type", "Event", "Attendee Name",
                "Attendee Email", "Booking Email", "Booking Name",
                "Status", "Checked In", "Booking Date"
            ]
            ws.append(headers)

            for ticket in tickets:
                ws.append([
                    str(ticket.code),
                    ticket.ticket_type.name,
                    ticket.booking.event.title,
                    ticket.attendee_name or "",
                    ticket.attendee_email or "",
                    ticket.booking.user.email if ticket.booking.user else ticket.booking.guest_email,
                    ticket.booking.user.get_full_name() if ticket.booking.user else ticket.booking.guest_name,
                    ticket.booking.status,
                    "Yes" if ticket.is_checked_in else "No",
                    ticket.booking.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                ])

            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)

            response = HttpResponse(
                buffer.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response["Content-Disposition"] = f'attachment; filename="rsvp-export-{datetime.now().strftime("%Y%m%d-%H%M%S")}.xlsx"'
            return response

        elif format_type == "pdf":
            html_content = render_to_string("tickets/pdf/rsvp_export.html", {
                "tickets": tickets,
                "user": user,
                "generated_at": datetime.now(),
            })

            pdf_content = HTML(string=html_content).write_pdf()

            response = HttpResponse(pdf_content, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="rsvp-export-{datetime.now().strftime("%Y%m%d-%H%M%S")}.pdf"'
            return response

        return HttpResponse("Invalid export format", status=400)


class TicketPDFView(LoginRequiredMixin, View):
    def get(self, request, ticket_code):
        ticket = get_object_or_404(
            Ticket.objects.select_related(
                "booking__user", "ticket_type__event__organization"
            ),
            code=ticket_code,
            booking__user=request.user,
        )

        pdf_content = generate_ticket_pdf(ticket)

        response = HttpResponse(pdf_content, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="ticket-{ticket.code}.pdf"'
        return response


class BookingTicketsPDFView(LoginRequiredMixin, View):
    def get(self, request, booking_ref):
        booking = get_object_or_404(
            Booking.objects.select_related("event__organization"),
            reference=booking_ref,
            user=request.user,
        )

        pdf_content = generate_booking_tickets_pdf(booking)

        response = HttpResponse(pdf_content, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="tickets-{booking.reference}.pdf"'
        )
        return response


class MyTicketsView(View):
    def get(self, request):
        if request.user.is_authenticated:
            tickets = (
                Ticket.objects.filter(
                    booking__user=request.user, booking__status=Booking.Status.CONFIRMED
                )
                .select_related("booking__event__organization", "ticket_type")
                .order_by("-booking__created_at")
            )
        else:
            guest_token = request.session.get("guest_token")
            if not guest_token:
                messages.info(request, _("Please login or use ticket lookup to view your tickets."))
                return render(request, "tickets/my_tickets.html", {"tickets": []})

            tickets = (
                Ticket.objects.filter(
                    booking__guest_session__token=guest_token,
                    booking__status=Booking.Status.CONFIRMED
                )
                .select_related("booking__event__organization", "ticket_type", "booking__guest_session")
                .order_by("-booking__created_at")
            )

        return render(
            request,
            "tickets/my_tickets.html",
            {
                "tickets": tickets,
            },
        )


class TicketLookupView(View):
    def get(self, request):
        return render(request, "tickets/lookup.html")

    def post(self, request):
        lookup_value = request.POST.get("lookup_value", "").strip()

        if not lookup_value:
            messages.error(
                request, _("Please enter an email, payment reference, or ticket code.")
            )
            return render(request, "tickets/lookup.html")

        booking = None
        payment = None
        tickets = []

        payment = (
            Payment.objects.filter(
                Q(reference__icontains=lookup_value)
                | Q(external_reference__icontains=lookup_value),
                status=Payment.Status.CONFIRMED,
            )
            .select_related("booking__event__organization")
            .first()
        )

        if payment:
            booking = payment.booking
        else:
            booking = (
                Booking.objects.filter(
                    Q(reference__icontains=lookup_value)
                    | Q(guest_email__iexact=lookup_value),
                    status=Booking.Status.CONFIRMED,
                )
                .select_related("event__organization")
                .first()
            )

        if not booking:
            ticket = (
                Ticket.objects.filter(
                    Q(code__icontains=lookup_value),
                    booking__status=Booking.Status.CONFIRMED,
                )
                .select_related("booking__event__organization", "ticket_type")
                .first()
            )

            if ticket:
                booking = ticket.booking

        if booking:
            tickets = Ticket.objects.filter(booking=booking).select_related(
                "ticket_type"
            )
            return render(
                request,
                "tickets/lookup.html",
                {
                    "booking": booking,
                    "tickets": tickets,
                    "payment": payment
                    or Payment.objects.filter(
                        booking=booking, status=Payment.Status.CONFIRMED
                    ).first(),
                    "lookup_value": lookup_value,
                },
            )

        messages.error(
            request, _("No tickets found. Please check your reference and try again.")
        )
        return render(request, "tickets/lookup.html", {"lookup_value": lookup_value})


class PublicBookingPDFView(View):
    def get(self, request, booking_ref):
        booking = get_object_or_404(
            Booking.objects.select_related("event__organization"),
            reference=booking_ref,
            status=Booking.Status.CONFIRMED,
        )

        pdf_content = generate_booking_tickets_pdf(booking)

        response = HttpResponse(pdf_content, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="tickets-{booking.reference}.pdf"'
        )
        return response
