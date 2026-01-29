from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.tickets.models import Ticket, Booking
from apps.tickets.services import generate_ticket_pdf, generate_booking_tickets_pdf
from apps.payments.models import Payment


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


class TicketLookupView(View):
    def get(self, request):
        return render(request, 'tickets/lookup.html')

    def post(self, request):
        lookup_value = request.POST.get('lookup_value', '').strip()

        if not lookup_value:
            messages.error(request, _('Please enter an email, payment reference, or ticket code.'))
            return render(request, 'tickets/lookup.html')

        booking = None
        payment = None
        tickets = []

        payment = Payment.objects.filter(
            Q(reference__icontains=lookup_value) |
            Q(external_reference__icontains=lookup_value),
            status=Payment.Status.CONFIRMED
        ).select_related('booking__event__organization').first()

        if payment:
            booking = payment.booking
        else:
            booking = Booking.objects.filter(
                Q(reference__icontains=lookup_value) |
                Q(guest_email__iexact=lookup_value),
                status=Booking.Status.CONFIRMED
            ).select_related('event__organization').first()

        if not booking:
            ticket = Ticket.objects.filter(
                Q(code__icontains=lookup_value),
                booking__status=Booking.Status.CONFIRMED
            ).select_related('booking__event__organization', 'ticket_type').first()

            if ticket:
                booking = ticket.booking

        if booking:
            tickets = Ticket.objects.filter(booking=booking).select_related('ticket_type')
            return render(request, 'tickets/lookup.html', {
                'booking': booking,
                'tickets': tickets,
                'payment': payment or Payment.objects.filter(booking=booking, status=Payment.Status.CONFIRMED).first(),
                'lookup_value': lookup_value,
            })

        messages.error(request, _('No tickets found. Please check your reference and try again.'))
        return render(request, 'tickets/lookup.html', {'lookup_value': lookup_value})


class PublicBookingPDFView(View):
    def get(self, request, booking_ref):
        booking = get_object_or_404(
            Booking.objects.select_related('event__organization'),
            reference=booking_ref,
            status=Booking.Status.CONFIRMED
        )

        pdf_content = generate_booking_tickets_pdf(booking)

        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="tickets-{booking.reference}.pdf"'
        return response
