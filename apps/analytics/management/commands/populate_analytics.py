from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random
from apps.payments.models import Payment, PaymentProvider, Currency
from apps.tickets.models import Booking, Event
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate analytics with sample payment data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=30,
            help='Number of payments to create'
        )

    def handle(self, *args, **options):
        count = options['count']
        today = timezone.now()

        events = Event.objects.all()
        if not events.exists():
            self.stdout.write(self.style.ERROR('No events found. Please create some events first.'))
            return

        users = User.objects.all()
        if not users.exists():
            self.stdout.write(self.style.ERROR('No users found. Please create some users first.'))
            return

        created_count = 0
        for i in range(count):
            event = random.choice(events)
            user = random.choice(users)
            days_ago = random.randint(1, 90)
            created_at = today - timedelta(days=days_ago)

            booking = Booking.objects.create(
                event=event,
                user=user,
                guest_email=user.email,
                guest_name=f"{user.first_name or 'Test'} {user.last_name or 'User'}",
                guest_phone='+237600000000',
                status='CONFIRMED',
                created_at=created_at,
                updated_at=created_at
            )

            amount = Decimal(random.randint(10000, 500000))
            service_fee = amount * Decimal('0.025')

            providers = [
                PaymentProvider.CAMPAY,
                PaymentProvider.PAWAPAY,
                PaymentProvider.FLUTTERWAVE,
                PaymentProvider.MTN_MOMO,
                PaymentProvider.ORANGE_MONEY,
            ]

            payment = Payment.objects.create(
                booking=booking,
                amount=amount,
                service_fee=service_fee,
                currency=Currency.XAF,
                provider=random.choice(providers),
                status='CONFIRMED',
                created_at=created_at,
                confirmed_at=created_at,
                expires_at=created_at + timedelta(minutes=30)
            )

            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample payments')
        )
