from django import forms
from .models import Event
from apps.tickets.models import TicketType

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'start_at', 'end_at', 'location', 'capacity']

class TicketTypeForm(forms.ModelForm):
    class Meta:
        model = TicketType
        fields = ['name', 'price', 'quantity']