from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum
from decimal import Decimal
from datetime import date

from apps.payments.models import Payment
from apps.tickets.models import Booking, Ticket
from apps.events.models import Event
from .models import DailyMetrics, EventMetrics, PaymentMetrics, OrganizationMetrics


@receiver(post_save, sender=Payment)
def update_payment_metrics(sender, instance, created, **kwargs):
    if instance.status == "CONFIRMED":
        today = date.today()
        daily_metrics, _ = DailyMetrics.objects.get_or_create(date=today)

        if created:
            daily_metrics.total_revenue += instance.amount
            daily_metrics.platform_fees += instance.service_fee or Decimal("0.00")
            daily_metrics.net_revenue = (
                daily_metrics.total_revenue - daily_metrics.platform_fees
            )
            daily_metrics.orders_count += 1
            daily_metrics.save()

        if hasattr(instance, "booking") and instance.booking and instance.booking.event:
            event_metrics, _ = EventMetrics.objects.get_or_create(
                event=instance.booking.event
            )
            event_metrics.total_revenue = Payment.objects.filter(
                booking__event=instance.booking.event, status="CONFIRMED"
            ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")
            event_metrics.platform_fees = Payment.objects.filter(
                booking__event=instance.booking.event, status="CONFIRMED"
            ).aggregate(Sum("service_fee"))["service_fee__sum"] or Decimal("0.00")
            event_metrics.net_revenue = (
                event_metrics.total_revenue - event_metrics.platform_fees
            )
            event_metrics.save()

            org_metrics, _ = OrganizationMetrics.objects.get_or_create(
                organization=instance.booking.event.organization
            )
            org_metrics.total_revenue = Payment.objects.filter(
                booking__event__organization=instance.booking.event.organization,
                status="CONFIRMED",
            ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")
            org_metrics.total_fees_paid = Payment.objects.filter(
                booking__event__organization=instance.booking.event.organization,
                status="CONFIRMED",
            ).aggregate(Sum("service_fee"))["service_fee__sum"] or Decimal("0.00")
            org_metrics.net_revenue = (
                org_metrics.total_revenue - org_metrics.total_fees_paid
            )
            org_metrics.save()

        if created:
            PaymentMetrics.objects.create(
                payment=instance,
                gateway_fee=Decimal("0.00"),
                platform_fee=instance.service_fee or Decimal("0.00"),
                net_amount_to_organizer=instance.amount
                - (instance.service_fee or Decimal("0.00")),
            )


@receiver(post_save, sender=Ticket)
def update_ticket_metrics(sender, instance, created, **kwargs):
    if created:
        today = date.today()
        daily_metrics, _ = DailyMetrics.objects.get_or_create(date=today)
        daily_metrics.tickets_sold += 1
        daily_metrics.save()

        if instance.booking and instance.booking.event:
            event_metrics, _ = EventMetrics.objects.get_or_create(
                event=instance.booking.event
            )
            event_metrics.tickets_sold = Ticket.objects.filter(
                booking__event=instance.booking.event
            ).count()
            event_metrics.save()

            org_metrics, _ = OrganizationMetrics.objects.get_or_create(
                organization=instance.booking.event.organization
            )
            org_metrics.total_tickets_sold = Ticket.objects.filter(
                booking__event__organization=instance.booking.event.organization
            ).count()
            org_metrics.save()

    if instance.checked_in_at:
        if instance.booking and instance.booking.event:
            event_metrics, _ = EventMetrics.objects.get_or_create(
                event=instance.booking.event
            )
            event_metrics.tickets_checked_in = Ticket.objects.filter(
                booking__event=instance.booking.event, checked_in_at__isnull=False
            ).count()
            event_metrics.save()


@receiver(post_save, sender=Booking)
def update_booking_metrics(sender, instance, created, **kwargs):
    if created:
        today = date.today()
        daily_metrics, _ = DailyMetrics.objects.get_or_create(date=today)
        daily_metrics.orders_count += 1
        daily_metrics.save()

        if instance.event:
            event_metrics, _ = EventMetrics.objects.get_or_create(event=instance.event)
            event_metrics.orders_count = Booking.objects.filter(
                event=instance.event
            ).count()
            event_metrics.save()


@receiver(post_save, sender=Event)
def update_event_creation_metrics(sender, instance, created, **kwargs):
    if created:
        today = date.today()
        daily_metrics, _ = DailyMetrics.objects.get_or_create(date=today)
        daily_metrics.events_created += 1
        daily_metrics.save()

        org_metrics, _ = OrganizationMetrics.objects.get_or_create(
            organization=instance.organization
        )
        org_metrics.total_events = Event.objects.filter(
            organization=instance.organization
        ).count()
        org_metrics.active_events = Event.objects.filter(
            organization=instance.organization, state="PUBLISHED"
        ).count()
        org_metrics.save()
