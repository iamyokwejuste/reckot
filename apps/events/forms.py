from django import forms
from apps.events.models import Event
from apps.tickets.models import TicketType


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title',
            'short_description',
            'description',
            'cover_image',
            'event_type',
            'start_at',
            'end_at',
            'timezone',
            'venue_name',
            'location',
            'address_line_2',
            'city',
            'country',
            'online_url',
            'website',
            'contact_email',
            'contact_phone',
            'capacity',
            'is_free',
        ]

    def clean(self):
        cleaned_data = super().clean()
        contact_email = cleaned_data.get('contact_email')
        contact_phone = cleaned_data.get('contact_phone')

        if not contact_email and not contact_phone:
            raise forms.ValidationError(
                'At least one contact method (email or phone) is required.'
            )

        return cleaned_data


class TicketTypeForm(forms.ModelForm):
    class Meta:
        model = TicketType
        fields = ['name', 'price', 'quantity']