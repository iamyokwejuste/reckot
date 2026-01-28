from django.views import View
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from apps.events.models import Event
from .services import verify_and_checkin, collect_swag
from .queries import (
    search_tickets,
    get_event_checkin_stats,
    get_event_swag_items,
    get_recent_checkins,
    get_uncollected_swag_for_checkin
)


class CheckInDashboardView(LoginRequiredMixin, View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        stats = get_event_checkin_stats(event_id)
        recent = get_recent_checkins(event_id)
        swag_items = get_event_swag_items(event_id)
        return render(request, 'checkin/dashboard.html', {
            'event': event,
            'stats': stats,
            'recent_checkins': recent,
            'swag_items': swag_items,
        })


class CheckInVerifyView(LoginRequiredMixin, View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        stats = get_event_checkin_stats(event_id)
        return render(request, 'checkin/verify.html', {
            'event': event,
            'stats': stats,
        })

    def post(self, request, event_id):
        code = request.POST.get('code', '').strip()
        if not code:
            return render(request, 'checkin/_result_error.html', {
                'error': 'Please enter a ticket code'
            })
        result = verify_and_checkin(code, request.user)
        if result['valid']:
            swag_items = get_uncollected_swag_for_checkin(result['checkin'])
            return render(request, 'checkin/_result_success.html', {
                **result,
                'swag_items': swag_items,
            })
        return render(request, 'checkin/_result_error.html', result)


class CheckInSearchView(LoginRequiredMixin, View):
    def get(self, request, event_id):
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return HttpResponse('')
        results = search_tickets(event_id, query)
        return render(request, 'checkin/_search_results.html', {
            'results': results,
            'event_id': event_id,
        })


class CheckInTicketView(LoginRequiredMixin, View):
    def post(self, request, code):
        result = verify_and_checkin(code, request.user)
        if result['valid']:
            swag_items = get_uncollected_swag_for_checkin(result['checkin'])
            return render(request, 'checkin/_checked_in_row.html', {
                **result,
                'swag_items': swag_items,
            })
        return render(request, 'checkin/_error_row.html', result)


class CollectSwagView(LoginRequiredMixin, View):
    def post(self, request, checkin_id, item_id):
        result = collect_swag(checkin_id, item_id)
        if result['success']:
            return render(request, 'checkin/_swag_collected.html', {
                'collection': result['collection']
            })
        return render(request, 'checkin/_swag_error.html', result)


class CheckInStatsView(LoginRequiredMixin, View):
    def get(self, request, event_id):
        stats = get_event_checkin_stats(event_id)
        return render(request, 'checkin/_stats.html', {'stats': stats})
