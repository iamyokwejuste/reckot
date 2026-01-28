from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
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
