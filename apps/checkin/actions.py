from django.views import View
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.db.models import Count
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.events.models import Event
from apps.checkin.models import CheckIn
from apps.checkin.services import verify_and_checkin, collect_swag
from apps.checkin.queries import (
    search_tickets,
    get_event_checkin_stats,
    get_event_swag_items,
    get_recent_checkins,
    get_uncollected_swag_for_checkin
)


class CheckInListView(LoginRequiredMixin, View):
    def get(self, request):
        checkins = CheckIn.objects.filter(
            ticket__booking__event__organization__members=request.user
        ).select_related(
            'ticket__booking__user',
            'ticket__booking__event',
            'ticket__ticket_type',
            'checked_in_by'
        ).order_by('-checked_in_at')[:100]

        stats = {
            'today': CheckIn.objects.filter(
                ticket__booking__event__organization__members=request.user,
                checked_in_at__date=timezone.now().date()
            ).count(),
            'total': CheckIn.objects.filter(
                ticket__booking__event__organization__members=request.user
            ).count(),
        }

        return render(request, 'checkin/list.html', {
            'checkins': checkins,
            'stats': stats,
        })


class CheckInDashboardView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        stats = get_event_checkin_stats(event.id)
        recent = get_recent_checkins(event.id)
        swag_items = get_event_swag_items(event.id)
        return render(request, 'checkin/dashboard.html', {
            'event': event,
            'stats': stats,
            'recent_checkins': recent,
            'swag_items': swag_items,
        })


class CheckInVerifyView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        stats = get_event_checkin_stats(event.id)
        return render(request, 'checkin/verify.html', {
            'event': event,
            'stats': stats,
        })

    def post(self, request, org_slug, event_slug):
        code = request.POST.get('code', '').strip()
        if not code:
            return render(request, 'checkin/_result_error.html', {
                'error': _('Please enter a ticket code')
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
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return HttpResponse('')
        results = search_tickets(event.id, query)
        return render(request, 'checkin/_search_results.html', {
            'results': results,
            'event': event,
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
    def post(self, request, checkin_ref, item_id):
        checkin = get_object_or_404(CheckIn, reference=checkin_ref)
        result = collect_swag(checkin.id, item_id)
        if result['success']:
            return render(request, 'checkin/_swag_collected.html', {
                'collection': result['collection']
            })
        return render(request, 'checkin/_swag_error.html', result)


class CheckInStatsView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        stats = get_event_checkin_stats(event.id)
        return render(request, 'checkin/_stats.html', {'stats': stats})
