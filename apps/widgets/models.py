from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.events.models import Event
import uuid


class EmbedWidget(models.Model):
    class Theme(models.TextChoices):
        LIGHT = 'LIGHT', _('Light')
        DARK = 'DARK', _('Dark')
        AUTO = 'AUTO', _('Auto (System)')

    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='embed_widget')
    widget_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_active = models.BooleanField(default=True)
    allowed_domains = models.JSONField(default=list, blank=True)
    theme = models.CharField(max_length=10, choices=Theme.choices, default=Theme.AUTO)
    button_text = models.CharField(max_length=50, default='Get Tickets')
    button_color = models.CharField(max_length=7, default='#000000')
    show_price = models.BooleanField(default=True)
    show_description = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['widget_id']),
        ]

    def get_embed_code(self, base_url):
        return f'''<div id="reckot-widget-{self.widget_id}"></div>
<script src="{base_url}/widgets/{self.widget_id}/embed.js" async></script>'''

    def get_iframe_url(self, base_url):
        return f'{base_url}/widgets/{self.widget_id}/'
