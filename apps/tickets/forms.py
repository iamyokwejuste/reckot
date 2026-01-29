from django import forms
from django.utils.translation import gettext_lazy as _
from apps.tickets.models import TicketType

class BookingForm(forms.Form):
    ticket_type = forms.ModelChoiceField(queryset=TicketType.objects.all(), empty_label=None)
    quantity = forms.IntegerField(min_value=1)
