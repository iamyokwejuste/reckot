from django import forms
from apps.tickets.models import TicketType


class BookingForm(forms.Form):
    ticket_type = forms.ModelChoiceField(
        queryset=TicketType.objects.all(), empty_label=None
    )
    quantity = forms.IntegerField(min_value=1)
