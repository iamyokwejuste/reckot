from django.db import transaction
from django.utils import timezone
from apps.tickets.models import Ticket
from apps.checkin.models import CheckIn, SwagCollection, SwagItem


def verify_and_checkin(code: str, staff_user) -> dict:
    with transaction.atomic():
        ticket = Ticket.objects.select_for_update().filter(code=code).first()
        if not ticket:
            return {'valid': False, 'error': 'Ticket not found'}
        if ticket.is_checked_in:
            return {
                'valid': False,
                'error': 'Already checked in',
                'ticket': ticket,
                'checked_in_at': ticket.checked_in_at
            }
        ticket.is_checked_in = True
        ticket.checked_in_at = timezone.now()
        ticket.save()
        checkin = CheckIn.objects.create(
            ticket=ticket,
            checked_in_by=staff_user
        )
        return {
            'valid': True,
            'ticket': ticket,
            'checkin': checkin,
            'event': ticket.ticket_type.event
        }


def collect_swag(checkin_id: int, swag_item_id: int) -> dict:
    with transaction.atomic():
        checkin = CheckIn.objects.select_for_update().filter(pk=checkin_id).first()
        if not checkin:
            return {'success': False, 'error': 'Check-in not found'}
        swag_item = SwagItem.objects.select_for_update().filter(pk=swag_item_id).first()
        if not swag_item:
            return {'success': False, 'error': 'Swag item not found'}
        if swag_item.remaining <= 0:
            return {'success': False, 'error': 'Swag item out of stock'}
        existing = SwagCollection.objects.filter(
            checkin=checkin,
            item=swag_item
        ).exists()
        if existing:
            return {'success': False, 'error': 'Already collected'}
        collection = SwagCollection.objects.create(
            checkin=checkin,
            item=swag_item
        )
        return {
            'success': True,
            'collection': collection
        }


def create_swag_item(event_id: int, name: str, quantity: int, description: str = '') -> SwagItem:
    return SwagItem.objects.create(
        event_id=event_id,
        name=name,
        quantity=quantity,
        description=description
    )


def undo_checkin(checkin_id: int, staff_user) -> dict:
    with transaction.atomic():
        checkin = CheckIn.objects.select_for_update().filter(pk=checkin_id).first()
        if not checkin:
            return {'success': False, 'error': 'Check-in not found'}
        ticket = checkin.ticket
        ticket.is_checked_in = False
        ticket.checked_in_at = None
        ticket.save()
        checkin.delete()
        return {'success': True, 'ticket': ticket}
