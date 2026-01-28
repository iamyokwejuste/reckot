import logging

logger = logging.getLogger(__name__)


def send_ticket_confirmation_task(booking_id: int):
    from .models import Booking
    from apps.core.services.notifications import NotificationService
    from apps.core.services.qrcode import QRCodeService

    try:
        booking = Booking.objects.select_related(
            'user',
            'payment'
        ).prefetch_related(
            'tickets__ticket_type__event'
        ).get(id=booking_id)

        tickets = list(booking.tickets.all())
        if not tickets:
            logger.warning(f"Booking {booking_id} has no tickets")
            return

        user = booking.user
        event = tickets[0].ticket_type.event

        qr_bytes = None
        if tickets:
            qr_buffer = QRCodeService.generate_ticket_qr(str(tickets[0].code))
            qr_bytes = qr_buffer.getvalue()

        if user.email:
            NotificationService.send_ticket_confirmation(
                to_email=user.email,
                booking=booking,
                tickets=tickets,
                event=event,
                qr_code_bytes=qr_bytes
            )

        if user.phone_number:
            NotificationService.send_ticket_sms(
                phone_number=user.phone_number,
                booking=booking,
                tickets=tickets,
                event=event
            )

        logger.info(f"Ticket confirmation sent for booking {booking_id}")

    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_id} not found")
    except Exception as e:
        logger.error(f"Failed to send ticket confirmation: {e}")


def generate_ticket_qr_task(ticket_id: int) -> str | None:
    from .models import Ticket
    from apps.core.services.qrcode import QRCodeService

    try:
        ticket = Ticket.objects.get(id=ticket_id)
        qr_base64 = QRCodeService.generate_ticket_qr_base64(str(ticket.code))
        logger.info(f"QR code generated for ticket {ticket_id}")
        return qr_base64

    except Ticket.DoesNotExist:
        logger.error(f"Ticket {ticket_id} not found")
        return None
    except Exception as e:
        logger.error(f"Failed to generate QR code: {e}")
        return None
