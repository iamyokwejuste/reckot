import logging
from celery import shared_task

from apps.core.services.notifications import NotificationService
from apps.core.services.qrcode import QRCodeService
from apps.tickets.models import Booking, Ticket

logger = logging.getLogger(__name__)


@shared_task
def send_ticket_confirmation_task(booking_id: int):
    try:
        booking = (
            Booking.objects.select_related("user", "payment")
            .prefetch_related("tickets__ticket_type__event")
            .get(id=booking_id)
        )

        tickets = list(booking.tickets.all())
        if not tickets:
            logger.warning(f"Booking {booking_id} has no tickets")
            return

        user = booking.user
        event = tickets[0].ticket_type.event

        # Determine buyer email and phone
        buyer_email = booking.buyer_email
        buyer_phone = (
            user.phone_number
            if user and hasattr(user, "phone_number")
            else booking.guest_phone
        )

        # Check delivery method
        if booking.delivery_method == "EMAIL_INDIVIDUALLY":
            # Send individual emails to each attendee
            for ticket in tickets:
                attendee_email = ticket.attendee_email
                if attendee_email:
                    qr_buffer = QRCodeService.generate_ticket_qr(str(ticket.code))
                    qr_bytes = qr_buffer.getvalue()

                    NotificationService.send_ticket_confirmation(
                        to_email=attendee_email,
                        booking=booking,
                        tickets=[ticket],  # Send only this ticket
                        event=event,
                        qr_code_bytes=qr_bytes,
                    )
                    logger.info(
                        f"Individual ticket {ticket.code} sent to {attendee_email}"
                    )
                else:
                    # If no attendee email, fallback to buyer email
                    logger.warning(
                        f"Ticket {ticket.code} has no attendee email, falling back to buyer email"
                    )
                    qr_buffer = QRCodeService.generate_ticket_qr(str(ticket.code))
                    qr_bytes = qr_buffer.getvalue()

                    NotificationService.send_ticket_confirmation(
                        to_email=buyer_email,
                        booking=booking,
                        tickets=[ticket],
                        event=event,
                        qr_code_bytes=qr_bytes,
                    )
        else:
            # EMAIL_ALL: Send all tickets to buyer email
            qr_bytes = None
            if tickets:
                qr_buffer = QRCodeService.generate_ticket_qr(str(tickets[0].code))
                qr_bytes = qr_buffer.getvalue()

            if buyer_email:
                NotificationService.send_ticket_confirmation(
                    to_email=buyer_email,
                    booking=booking,
                    tickets=tickets,
                    event=event,
                    qr_code_bytes=qr_bytes,
                )

        # Send SMS notification to buyer phone if available
        if buyer_phone:
            NotificationService.send_ticket_sms(
                phone_number=buyer_phone,
                booking=booking,
                tickets=tickets,
                event=event,
            )

        logger.info(f"Ticket confirmation sent for booking {booking_id}")

    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_id} not found")
    except Exception as e:
        logger.error(f"Failed to send ticket confirmation: {e}")


@shared_task
def generate_ticket_qr_task(ticket_id: int) -> str | None:
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
