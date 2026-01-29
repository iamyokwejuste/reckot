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
    sales_start = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text='Leave empty to start sales immediately'
    )
    sales_end = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text='Leave empty for no end date'
    )

    class Meta:
        model = TicketType
        fields = ['name', 'description', 'price', 'quantity', 'max_per_order', 'sales_start', 'sales_end', 'is_active']

    def clean(self):
        cleaned_data = super().clean()
        sales_start = cleaned_data.get('sales_start')
        sales_end = cleaned_data.get('sales_end')

        if sales_start and sales_end and sales_start >= sales_end:
            raise forms.ValidationError('Sales end date must be after sales start date.')

        return cleaned_data