from django.views import View
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.db.models import Count
from apps.tickets.models import Ticket, Booking


class TicketListView(LoginRequiredMixin, View):
    def get(self, request):
        tickets = Ticket.objects.filter(
            booking__event__organization__members=request.user
        ).select_related(
            'booking__user',
            'booking__event',
            'ticket_type'
        ).order_by('-booking__created_at')[:100]

        stats = {
            'total': Ticket.objects.filter(
                booking__event__organization__members=request.user,
                booking__status=Booking.Status.CONFIRMED
            ).count(),
            'checked_in': Ticket.objects.filter(
                booking__event__organization__members=request.user,
                is_checked_in=True
            ).count(),
            'pending': Ticket.objects.filter(
                booking__event__organization__members=request.user,
                booking__status=Booking.Status.PENDING
            ).count(),
        }

        return render(request, 'tickets/list.html', {
            'tickets': tickets,
            'stats': stats,
        })


class TicketPDFView(LoginRequiredMixin, View):
    def get(self, request, ticket_code):
        ticket = get_object_or_404(
            Ticket.objects.select_related('booking__user', 'ticket_type__event__organization'),
            code=ticket_code,
            booking__user=request.user
        )

        from apps.tickets.services import generate_ticket_pdf
        pdf_content = generate_ticket_pdf(ticket)

        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="ticket-{ticket.code}.pdf"'
        return response


class BookingTicketsPDFView(LoginRequiredMixin, View):
    def get(self, request, booking_ref):
        booking = get_object_or_404(
            Booking.objects.select_related('event__organization'),
            reference=booking_ref,
            user=request.user
        )

        from apps.tickets.services import generate_booking_tickets_pdf
        pdf_content = generate_booking_tickets_pdf(booking)

        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="tickets-{booking.reference}.pdf"'
        return response


class MyTicketsView(LoginRequiredMixin, View):
    def get(self, request):
        tickets = Ticket.objects.filter(
            booking__user=request.user,
            booking__status=Booking.Status.CONFIRMED
        ).select_related(
            'booking__event__organization',
            'ticket_type'
        ).order_by('-booking__created_at')

        return render(request, 'tickets/my_tickets.html', {
            'tickets': tickets,
        })
