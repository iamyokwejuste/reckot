import logging

from celery import shared_task

from apps.tickets.models import Booking
from apps.tickets.services.ticket_service import generate_booking_tickets_pdf

logger = logging.getLogger(__name__)


@shared_task
def pregenerate_booking_pdf_task(booking_id):
    try:
        booking = Booking.objects.select_related(
            "event__organization"
        ).prefetch_related(
            "tickets__ticket_type__event__organization"
        ).get(id=booking_id)

        generate_booking_tickets_pdf(booking)
        logger.info(f"Pre-generated PDF for booking {booking_id}")

    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_id} not found")
    except Exception as e:
        logger.error(f"Failed to pre-generate PDF for booking {booking_id}: {e}")
