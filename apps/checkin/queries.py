from django.db.models import Count, Q
from apps.tickets.models import Ticket
from .models import CheckIn, SwagItem


def get_ticket_by_code(code: str):
    return Ticket.objects.select_related(
        'ticket_type__event',
        'booking__user'
    ).filter(code=code).first()


def search_tickets(event_id: int, query: str, limit: int = 20):
    return Ticket.objects.filter(
        ticket_type__event_id=event_id
    ).filter(
        Q(code__icontains=query) |
        Q(booking__user__email__icontains=query) |
        Q(booking__user__first_name__icontains=query) |
        Q(booking__user__last_name__icontains=query)
    ).select_related(
        'ticket_type',
        'booking__user'
    )[:limit]


def get_event_checkin_stats(event_id: int) -> dict:
    stats = Ticket.objects.filter(
        ticket_type__event_id=event_id
    ).aggregate(
        total=Count('id'),
        checked_in=Count('id', filter=Q(is_checked_in=True))
    )
    return {
        'total': stats['total'],
        'checked_in': stats['checked_in'],
        'remaining': stats['total'] - stats['checked_in']
    }


def get_event_swag_items(event_id: int):
    return SwagItem.objects.filter(event_id=event_id).annotate(
        collected_count=Count('collections')
    )


def get_recent_checkins(event_id: int, limit: int = 10):
    return CheckIn.objects.filter(
        ticket__ticket_type__event_id=event_id
    ).select_related(
        'ticket__booking__user',
        'ticket__ticket_type',
        'checked_in_by'
    ).order_by('-checked_in_at')[:limit]


def get_uncollected_swag_for_checkin(checkin: CheckIn):
    collected_ids = checkin.swag_collections.values_list('item_id', flat=True)
    return SwagItem.objects.filter(
        event_id=checkin.ticket.ticket_type.event_id
    ).exclude(id__in=collected_ids)
