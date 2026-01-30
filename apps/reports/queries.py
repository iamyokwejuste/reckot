from django.db.models import Case, Count, Sum, When
from apps.events.models import Event, CheckoutQuestion
from apps.tickets.models import Ticket, Booking, TicketQuestionAnswer
from apps.checkin.models import CheckIn, SwagCollection
from apps.payments.models import Payment


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def get_event_summary(event_id: int) -> dict:
    event = Event.objects.filter(pk=event_id).first()
    if not event:
        return {}
    tickets = Ticket.objects.filter(ticket_type__event_id=event_id)
    total_tickets = tickets.count()
    checked_in = tickets.filter(is_checked_in=True).count()
    total_revenue = (
        Payment.objects.filter(
            booking__tickets__ticket_type__event_id=event_id, status="CONFIRMED"
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )
    return {
        "event": event,
        "total_tickets": total_tickets,
        "checked_in": checked_in,
        "check_in_rate": round(checked_in / total_tickets * 100, 1)
        if total_tickets
        else 0,
        "total_revenue": total_revenue,
    }


def get_rsvp_data(event_id: int, mask_emails: bool = True):
    tickets = (
        Ticket.objects.filter(
            booking__event_id=event_id, booking__status=Booking.Status.CONFIRMED
        )
        .select_related("booking__user", "ticket_type", "booking__guest_session")
        .prefetch_related("answers__question")
    )

    questions = list(
        CheckoutQuestion.objects.filter(event_id=event_id).order_by("order")
    )

    result = []
    for ticket in tickets:
        booking = ticket.booking
        if booking.user:
            email = ticket.attendee_email or booking.user.email
            name = (
                ticket.attendee_name
                or f"{booking.user.first_name or ''} {booking.user.last_name or ''}".strip()
            )
        else:
            email = ticket.attendee_email or booking.guest_email
            name = ticket.attendee_name or booking.guest_name

        if mask_emails and email:
            email = mask_email(email)

        row_data = {
            "code": str(ticket.code)[:8],
            "name": name or "N/A",
            "email": email or "N/A",
            "ticket_type": ticket.ticket_type.name,
            "checked_in": "Yes" if ticket.is_checked_in else "No",
            "checked_in_at": str(ticket.checked_in_at or ""),
            "registered_at": str(booking.created_at),
        }

        answers_dict = {a.question_id: a.answer for a in ticket.answers.all}
        for q in questions:
            row_data[q.question] = answers_dict.get(q.id, "")

        result.append(row_data)
    return result


def get_payment_data(event_id: int, mask_emails: bool = True):
    payments = (
        Payment.objects.filter(booking__tickets__ticket_type__event_id=event_id)
        .distinct()
        .select_related("booking__user")
        .values(
            "reference",
            "booking__user__email",
            "amount",
            "provider",
            "status",
            "phone_number",
            "created_at",
            "confirmed_at",
        )
    )
    result = []
    for row in payments:
        email = row["booking__user__email"]
        phone = row["phone_number"]
        if mask_emails:
            email = mask_email(email)
            phone = phone[:4] + "****" + phone[-2:] if len(phone) > 6 else phone
        result.append(
            {
                "reference": str(row["reference"]),
                "customer": email,
                "provider": row["provider"],
                "date": str(row["created_at"]),
                "amount": str(row["amount"]),
                "status": row["status"],
                "phone": phone,
                "confirmed_at": str(row["confirmed_at"] or ""),
            }
        )
    return result


def get_checkin_data(event_id: int, mask_emails: bool = True):
    checkins = (
        CheckIn.objects.filter(ticket__ticket_type__event_id=event_id)
        .select_related("ticket__booking__user", "ticket__ticket_type", "checked_in_by")
        .values(
            "ticket__code",
            "ticket__booking__user__email",
            "ticket__ticket_type__name",
            "checked_in_at",
            "checked_in_by__email",
        )
    )
    result = []
    for row in checkins:
        email = row["ticket__booking__user__email"]
        if mask_emails:
            email = mask_email(email)
        result.append(
            {
                "code": str(row["ticket__code"]),
                "email": email,
                "ticket_type": row["ticket__ticket_type__name"],
                "checked_in_at": str(row["checked_in_at"]),
                "checked_in_by": row["checked_in_by__email"] or "",
            }
        )
    return result


def get_swag_data(event_id: int, mask_emails: bool = True):
    collections = (
        SwagCollection.objects.filter(item__event_id=event_id)
        .select_related("checkin__ticket__booking__user", "item")
        .values(
            "item__name",
            "checkin__ticket__booking__user__email",
            "checkin__ticket__code",
            "collected_at",
        )
    )
    result = []
    for row in collections:
        email = row["checkin__ticket__booking__user__email"]
        if mask_emails:
            email = mask_email(email)
        result.append(
            {
                "item": row["item__name"],
                "email": email,
                "ticket_code": str(row["checkin__ticket__code"]),
                "collected_at": str(row["collected_at"]),
            }
        )
    return result


def get_custom_responses_data(event_id: int, mask_emails: bool = True):
    answers = TicketQuestionAnswer.objects.filter(
        question__event_id=event_id, booking__status=Booking.Status.CONFIRMED
    ).select_related("ticket", "booking__user", "booking", "question")

    result = []
    for answer in answers:
        booking = answer.booking
        if booking.user:
            email = booking.user.email
            name = (
                f"{booking.user.first_name or ''} {booking.user.last_name or ''}".strip()
                or email
            )
        else:
            email = booking.guest_email
            name = booking.guest_name

        if mask_emails and email:
            email = mask_email(email)

        result.append(
            {
                "ticket_code": str(answer.ticket.code)[:8],
                "name": name or "N/A",
                "email": email or "N/A",
                "question": answer.question.question,
                "answer": answer.answer,
                "submitted_at": str(answer.created_at),
            }
        )
    return result


def get_questions_summary(event_id: int):
    questions = CheckoutQuestion.objects.filter(event_id=event_id).order_by("order").prefetch_related(
        "answers"
    )

    confirmed_answers = TicketQuestionAnswer.objects.filter(
        question__event_id=event_id,
        booking__status=Booking.Status.CONFIRMED
    ).select_related("question").values("question_id", "answer")

    answer_counts = {}
    answer_breakdowns = {}

    for ans in confirmed_answers:
        q_id = ans["question_id"]
        answer_counts[q_id] = answer_counts.get(q_id, 0) + 1

        if q_id not in answer_breakdowns:
            answer_breakdowns[q_id] = {}
        answer_text = ans["answer"]
        answer_breakdowns[q_id][answer_text] = answer_breakdowns[q_id].get(answer_text, 0) + 1

    result = []
    for q in questions:
        answer_count = answer_counts.get(q.id, 0)
        if q.field_type in ["SELECT", "RADIO", "CHECKBOX"]:
            breakdown = answer_breakdowns.get(q.id, {})
        else:
            breakdown = None
        result.append(
            {
                "question": q,
                "answer_count": answer_count,
                "breakdown": breakdown,
            }
        )
    return result
