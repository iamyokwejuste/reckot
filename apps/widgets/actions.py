from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from apps.widgets.models import EmbedWidget
from apps.events.models import Event


@method_decorator(xframe_options_exempt, name="dispatch")
class WidgetView(View):
    def get(self, request, widget_id):
        widget = get_object_or_404(EmbedWidget, widget_id=widget_id, is_active=True)
        event = widget.event

        if widget.allowed_domains:
            origin = request.META.get("HTTP_ORIGIN", "")
            referer = request.META.get("HTTP_REFERER", "")
            allowed = any(
                domain in origin or domain in referer
                for domain in widget.allowed_domains
            )
            if not allowed and origin:
                return HttpResponse(_("Domain not allowed"), status=403)

        ticket_types = event.ticket_types.filter(is_active=True)

        return render(
            request,
            "widgets/embed.html",
            {
                "widget": widget,
                "event": event,
                "ticket_types": ticket_types,
            },
        )


class WidgetJSView(View):
    def get(self, request, widget_id):
        get_object_or_404(EmbedWidget, widget_id=widget_id, is_active=True)

        base_url = request.build_absolute_uri("/").rstrip("/")
        iframe_url = f"{base_url}/widgets/{widget_id}/"

        js_content = f"""
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
"""
        return HttpResponse(js_content, content_type="application/javascript")


class WidgetConfigView(View):
    def get(self, request, widget_id):
        widget = get_object_or_404(EmbedWidget, widget_id=widget_id)

        return JsonResponse(
            {
                "event": {
                    "title": widget.event.title,
                    "description": widget.event.description
                    if widget.show_description
                    else None,
                    "start_at": widget.event.start_at.isoformat(),
                    "location": widget.event.location,
                },
                "settings": {
                    "theme": widget.theme,
                    "button_text": widget.button_text,
                    "button_color": widget.button_color,
                    "show_price": widget.show_price,
                },
            }
        )


class WidgetManageView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related("organization"),
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user,
        )

        try:
            widget = event.embed_widget
        except EmbedWidget.DoesNotExist:
            widget = None

        base_url = request.build_absolute_uri("/").rstrip("/")

        return render(
            request,
            "widgets/manage.html",
            {
                "event": event,
                "widget": widget,
                "base_url": base_url,
            },
        )

    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event,
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user,
        )

        try:
            widget = event.embed_widget
        except EmbedWidget.DoesNotExist:
            widget = EmbedWidget(event=event)

        widget.is_active = request.POST.get("is_active") == "on"
        widget.theme = request.POST.get("theme", "AUTO")
        widget.button_text = request.POST.get("button_text", "Get Tickets")
        widget.button_color = request.POST.get("button_color", "#000000")
        widget.show_price = request.POST.get("show_price") == "on"
        widget.show_description = request.POST.get("show_description") == "on"

        domains_raw = request.POST.get("allowed_domains", "").strip()
        widget.allowed_domains = (
            [d.strip() for d in domains_raw.split("\n") if d.strip()]
            if domains_raw
            else []
        )

        widget.save()

        return redirect("widgets:manage", org_slug=org_slug, event_slug=event_slug)
