from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.decorators import method_decorator
from apps.widgets.models import EmbedWidget


@method_decorator(xframe_options_exempt, name='dispatch')
class WidgetView(View):
    def get(self, request, widget_id):
        widget = get_object_or_404(EmbedWidget, widget_id=widget_id, is_active=True)
        event = widget.event

        if widget.allowed_domains:
            origin = request.META.get('HTTP_ORIGIN', '')
            referer = request.META.get('HTTP_REFERER', '')
            allowed = any(
                domain in origin or domain in referer
                for domain in widget.allowed_domains
            )
            if not allowed and origin:
                return HttpResponse('Domain not allowed', status=403)

        ticket_types = event.ticket_types.filter(is_active=True)

        return render(request, 'widgets/embed.html', {
            'widget': widget,
            'event': event,
            'ticket_types': ticket_types,
        })


class WidgetJSView(View):
    def get(self, request, widget_id):
        widget = get_object_or_404(EmbedWidget, widget_id=widget_id, is_active=True)

        base_url = request.build_absolute_uri('/').rstrip('/')
        iframe_url = f'{base_url}/widgets/{widget_id}/'

        js_content = f'''
(function() {{
    var container = document.getElementById('reckot-widget-{widget_id}');
    if (!container) return;

    var iframe = document.createElement('iframe');
    iframe.src = '{iframe_url}';
    iframe.style.width = '100%';
    iframe.style.minHeight = '400px';
    iframe.style.border = 'none';
    iframe.style.borderRadius = '8px';
    iframe.setAttribute('loading', 'lazy');
    iframe.setAttribute('title', 'Reckot Ticket Widget');

    container.appendChild(iframe);

    window.addEventListener('message', function(e) {{
        if (e.data && e.data.type === 'reckot-resize') {{
            iframe.style.height = e.data.height + 'px';
        }}
    }});
}})();
'''
        return HttpResponse(js_content, content_type='application/javascript')


class WidgetConfigView(View):
    def get(self, request, widget_id):
        widget = get_object_or_404(EmbedWidget, widget_id=widget_id)

        return JsonResponse({
            'event': {
                'title': widget.event.title,
                'description': widget.event.description if widget.show_description else None,
                'start_at': widget.event.start_at.isoformat(),
                'location': widget.event.location,
            },
            'settings': {
                'theme': widget.theme,
                'button_text': widget.button_text,
                'button_color': widget.button_color,
                'show_price': widget.show_price,
            },
        })
