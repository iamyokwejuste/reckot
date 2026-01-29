from django.db.models import Sum
from apps.events.models import Event
from apps.tickets.models import Ticket, Booking
from apps.checkin.models import CheckIn, SwagCollection
from apps.payments.models import Payment


def mask_email(email: str) -> str:
    if not email or '@' not in email:
        return email
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + '*'
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    return f'{masked_local}@{domain}'


def get_event_summary(event_id: int) -> dict:
    event = Event.objects.filter(pk=event_id).first()
    if not event:
        return {}
    tickets = Ticket.objects.filter(ticket_type__event_id=event_id)
    total_tickets = tickets.count()
    checked_in = tickets.filter(is_checked_in=True).count()
    total_revenue = Payment.objects.filter(
        booking__tickets__ticket_type__event_id=event_id,
        status='CONFIRMED'
    ).aggregate(total=Sum('amount'))['total'] or 0
    return {
        'event': event,
        'total_tickets': total_tickets,
        'checked_in': checked_in,
        'check_in_rate': round(checked_in / total_tickets * 100, 1) if total_tickets else 0,
        'total_revenue': total_revenue,
    }


def get_rsvp_data(event_id: int, mask_emails: bool = True):
    tickets = Ticket.objects.filter(
        booking__event_id=event_id,
        booking__status=Booking.Status.CONFIRMED
    ).select_related(
        'booking__user', 'ticket_type'
    ).values(
        'code',
        'booking__user__email',
        'booking__user__first_name',
        'booking__user__last_name',
        'ticket_type__name',
        'attendee_name',
        'attendee_email',
        'is_checked_in',
        'checked_in_at',
        'booking__created_at'
    )
    result = []
    for row in tickets:
        email = row['attendee_email'] or row['booking__user__email']
        name = row['attendee_name'] or f"{row['booking__user__first_name'] or ''} {row['booking__user__last_name'] or ''}".strip()
        if mask_emails and email:
            email = mask_email(email)
        result.append({
            'code': str(row['code'])[:8],
            'name': name or 'N/A',
            'email': email or 'N/A',
            'ticket_type': row['ticket_type__name'],
            'checked_in': 'Yes' if row['is_checked_in'] else 'No',
            'checked_in_at': str(row['checked_in_at'] or ''),
            'booked_at': str(row['booking__created_at']),
        })
    return result


def get_payment_data(event_id: int, mask_emails: bool = True):
    payments = Payment.objects.filter(
        booking__tickets__ticket_type__event_id=event_id
    ).distinct().select_related('booking__user').values(
        'reference',
        'booking__user__email',
        'amount',
        'method',
        'status',
        'phone_number',
        'created_at',
        'confirmed_at',
    )
    result = []
    for row in payments:
        email = row['booking__user__email']
        phone = row['phone_number']
        if mask_emails:
            email = mask_email(email)
            phone = phone[:4] + '****' + phone[-2:] if len(phone) > 6 else phone
        result.append({
            'reference': str(row['reference']),
            'email': email,
            'amount': str(row['amount']),
            'method': row['method'],
            'status': row['status'],
            'phone': phone,
            'created_at': str(row['created_at']),
            'confirmed_at': str(row['confirmed_at'] or ''),
        })
    return result


def get_checkin_data(event_id: int, mask_emails: bool = True):
    checkins = CheckIn.objects.filter(
        ticket__ticket_type__event_id=event_id
    ).select_related(
        'ticket__booking__user', 'ticket__ticket_type', 'checked_in_by'
    ).values(
        'ticket__code',
        'ticket__booking__user__email',
        'ticket__ticket_type__name',
        'checked_in_at',
        'checked_in_by__email',
    )
    result = []
    for row in checkins:
        email = row['ticket__booking__user__email']
        if mask_emails:
            email = mask_email(email)
        result.append({
            'code': str(row['ticket__code']),
            'email': email,
            'ticket_type': row['ticket__ticket_type__name'],
            'checked_in_at': str(row['checked_in_at']),
            'checked_in_by': row['checked_in_by__email'] or '',
        })
    return result


def get_swag_data(event_id: int, mask_emails: bool = True):
    collections = SwagCollection.objects.filter(
        item__event_id=event_id
    ).select_related(
        'checkin__ticket__booking__user', 'item'
    ).values(
        'item__name',
        'checkin__ticket__booking__user__email',
        'checkin__ticket__code',
        'collected_at',
    )
    result = []
    for row in collections:
        email = row['checkin__ticket__booking__user__email']
        if mask_emails:
            email = mask_email(email)
        result.append({
            'item': row['item__name'],
            'email': email,
            'ticket_code': str(row['checkin__ticket__code']),
            'collected_at': str(row['collected_at']),
        })
    return result
