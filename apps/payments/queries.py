from apps.payments.models import Payment


def get_payment_by_reference(reference: str):
    return (
        Payment.objects.select_related("booking__user")
        .filter(reference=reference)
        .first()
    )


def get_payment_by_id(payment_id: int):
    return Payment.objects.select_related("booking__user").filter(pk=payment_id).first()


def get_payment_status(payment_id: int) -> dict:
    payment = (
        Payment.objects.filter(pk=payment_id)
        .values("status", "confirmed_at", "reference")
        .first()
    )
    if not payment:
        return {"confirmed": False, "exists": False}
    return {
        "confirmed": payment["status"] == Payment.Status.CONFIRMED,
        "exists": True,
        **payment,
    }


def get_user_payments(user, limit: int = 20):
    return (
        Payment.objects.filter(booking__user=user)
        .select_related("booking")
        .order_by("-created_at")[:limit]
    )


def get_booking_payment(booking_id: int):
    return Payment.objects.filter(booking_id=booking_id).first()


def get_pending_payments_for_user(user):
    return Payment.objects.filter(
        booking__user=user, status=Payment.Status.PENDING
    ).select_related("booking")
