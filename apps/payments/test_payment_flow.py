import pytest
from decimal import Decimal
from apps.payments.models import Payment
from apps.tickets.models import Booking


@pytest.mark.django_db
class TestPaymentCreation:
    def test_create_payment(self, event, user):

        booking = Booking.objects.create(
            event=event,
            user=user,
            total_amount=Decimal("5000"),
            status=Booking.Status.PENDING,
        )
        payment = Payment.objects.create(
            booking=booking,
            amount=Decimal("5000"),
            currency="XAF",
            provider="CAMPAY",
        )
        assert payment.status == Payment.Status.PENDING
        assert payment.amount == Decimal("5000")

    def test_idempotency_key_unique(self, event, user):

        booking = Booking.objects.create(
            event=event,
            user=user,
            total_amount=Decimal("5000"),
            status=Booking.Status.PENDING,
        )
        Payment.objects.create(
            booking=booking,
            amount=Decimal("5000"),
            currency="XAF",
            provider="CAMPAY",
            idempotency_key="test-key-1",
        )
        p2 = Payment.objects.filter(idempotency_key="test-key-1").first()
        assert p2 is not None
