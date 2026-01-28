from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import EventForm, TicketTypeForm
from .services import create_event
from .queries import get_user_events
from .models import Event
from apps.tickets.forms import BookingForm
from apps.tickets.services import create_booking

class EventListView(LoginRequiredMixin, View):
    def get(self, request):
        events = get_user_events(request.user)
        return render(request, 'events/list_events.html', {'events': events})

class EventCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = EventForm()
        return render(request, 'events/create_event.html', {'form': form})

    def post(self, request):
        try:
            organization = request.user.owned_organizations.first()
            if not organization:
                organization = request.user.organizations.first()
            if not organization:
                return render(request, 'events/no_org.html')
        except AttributeError:
             return render(request, 'events/no_org.html')

        event, errors = create_event(request.user, organization, request.POST)
        if event:
            return redirect('events:list')
        else:
            form = EventForm(request.POST)
            return render(request, 'events/create_event.html', {'form': form, 'errors': errors})

class TicketTypeManageView(LoginRequiredMixin, View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        ticket_types = event.ticket_types.all()
        form = TicketTypeForm()
        return render(request, 'events/manage_ticket_types.html', {'event': event, 'ticket_types': ticket_types, 'form': form})

    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        form = TicketTypeForm(request.POST)
        if form.is_valid():
            ticket_type = form.save(commit=False)
            ticket_type.event = event
            ticket_type.save()
            return redirect('events:manage_ticket_types', event_id=event.pk)
        ticket_types = event.ticket_types.all()
        return render(request, 'events/manage_ticket_types.html', {'event': event, 'ticket_types': ticket_types, 'form': form})

class EventDetailView(LoginRequiredMixin, View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        booking_form = BookingForm(initial={'ticket_type': event.ticket_types.first()})
        return render(request, 'events/event_detail.html', {'event': event, 'booking_form': booking_form})

    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        booking_form = BookingForm(request.POST)
        if booking_form.is_valid():
            ticket_type = booking_form.cleaned_data['ticket_type']
            quantity = booking_form.cleaned_data['quantity']
            booking, error = create_booking(request.user, ticket_type, quantity)
            if booking:
                return redirect('events:list') # Redirect to some booking confirmation page later
            else:
                return render(request, 'events/event_detail.html', {'event': event, 'booking_form': booking_form, 'error': error})
        return render(request, 'events/event_detail.html', {'event': event, 'booking_form': booking_form})