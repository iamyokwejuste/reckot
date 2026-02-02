import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from apps.core.models import Notification
from apps.core.services.notifications import NotificationService
from apps.core.services.qrcode import QRCodeService
from apps.orgs.models import MemberRole
from apps.tickets.models import Booking, Ticket
from apps.tickets.ticket_pdf_service import generate_single_ticket_pdf, generate_multi_ticket_pdf

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

        buyer_email = booking.buyer_email
        buyer_phone = (
            user.phone_number
            if user and hasattr(user, "phone_number")
            else booking.guest_phone
        )

        if booking.delivery_method == "EMAIL_INDIVIDUALLY":
            for ticket in tickets:
                attendee_email = ticket.attendee_email
                if attendee_email:
                    qr_buffer = QRCodeService.generate_ticket_qr(str(ticket.code))
                    qr_bytes = qr_buffer.getvalue()

                    try:
                        pdf_bytes = generate_single_ticket_pdf(ticket, booking, qr_bytes)
                    except Exception as e:
                        logger.error(f"Failed to generate PDF for ticket {ticket.code}: {e}")
                        pdf_bytes = None

                    NotificationService.send_ticket_confirmation(
                        to_email=attendee_email,
                        booking=booking,
                        tickets=[ticket],
                        event=event,
                        qr_code_bytes=qr_bytes,
                        pdf_attachment=pdf_bytes,
                    )
                    logger.info(
                        f"Individual ticket {ticket.code} sent to {attendee_email}"
                    )
                else:
                    logger.warning(
                        f"Ticket {ticket.code} has no attendee email, falling back to buyer email"
                    )
                    qr_buffer = QRCodeService.generate_ticket_qr(str(ticket.code))
                    qr_bytes = qr_buffer.getvalue()

                    try:
                        pdf_bytes = generate_single_ticket_pdf(ticket, booking, qr_bytes)
                    except Exception as e:
                        logger.error(f"Failed to generate PDF for ticket {ticket.code}: {e}")
                        pdf_bytes = None

                    NotificationService.send_ticket_confirmation(
                        to_email=buyer_email,
                        booking=booking,
                        tickets=[ticket],
                        event=event,
                        qr_code_bytes=qr_bytes,
                        pdf_attachment=pdf_bytes,
                    )
        else:
            qr_bytes = None
            if tickets:
                qr_buffer = QRCodeService.generate_ticket_qr(str(tickets[0].code))
                qr_bytes = qr_buffer.getvalue()

            pdf_bytes = None
            try:
                pdf_bytes = generate_multi_ticket_pdf(tickets, booking, qr_bytes)
            except Exception as e:
                logger.error(f"Failed to generate PDF for booking {booking_id}: {e}")

            if buyer_email:
                NotificationService.send_ticket_confirmation(
                    to_email=buyer_email,
                    booking=booking,
                    tickets=tickets,
                    event=event,
                    qr_code_bytes=qr_bytes,
                    pdf_attachment=pdf_bytes,
                )

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


@shared_task
def send_admin_sale_notifications_task(booking_id: int):
    try:
        booking = (
            Booking.objects.select_related("event__organization", "payment", "user")
            .prefetch_related("tickets__ticket_type")
            .get(id=booking_id)
        )

        event = booking.event
        organization = event.organization
        payment = booking.payment

        admin_users = organization.members.filter(
            membership__role__in=[MemberRole.OWNER, MemberRole.ADMIN]
        ).distinct()

        tickets = list(booking.tickets.all())
        ticket_summary = {}
        for ticket in tickets:
            ticket_type_name = ticket.ticket_type.name
            if ticket_type_name in ticket_summary:
                ticket_summary[ticket_type_name]["count"] += 1
            else:
                ticket_summary[ticket_type_name] = {
                    "count": 1,
                    "price": ticket.ticket_type.price
                }

        total_amount = payment.amount if payment else booking.total_amount
        currency = payment.currency if payment else organization.currency

        for admin in admin_users:
            notification_title = f"New sale for {event.title}"
            notification_message = f"{booking.buyer_name} purchased {len(tickets)} ticket(s) for {total_amount} {currency}"
            notification_link = f"/events/{organization.slug}/{event.slug}/dashboard/"

            Notification.objects.create(
                user=admin,
                notification_type=Notification.Type.SALE_MADE,
                title=notification_title,
                message=notification_message,
                link=notification_link,
                expires_at=timezone.now() + timedelta(days=30)
            )

            if admin.email:
                NotificationService.send_admin_sale_notification(
                    to_email=admin.email,
                    booking=booking,
                    event=event,
                    tickets=tickets,
                    ticket_summary=ticket_summary,
                    payment=payment,
                )

        logger.info(f"Admin sale notifications sent for booking {booking_id}")

    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_id} not found")
    except Exception as e:
        logger.error(f"Failed to send admin sale notifications: {e}")
