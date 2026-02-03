from django.db import models
from django.utils import timezone
from decimal import Decimal


class DailyMetrics(models.Model):
    date = models.DateField(unique=True, db_index=True)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    platform_fees = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tickets_sold = models.IntegerField(default=0)
    orders_count = models.IntegerField(default=0)
    events_created = models.IntegerField(default=0)
    new_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Daily Metrics"
        verbose_name_plural = "Daily Metrics"
        ordering = ["-date"]

    def __str__(self):
        return f"Metrics for {self.date}"


class EventMetrics(models.Model):
    event = models.OneToOneField("events.Event", on_delete=models.CASCADE, related_name="metrics")
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    platform_fees = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tickets_sold = models.IntegerField(default=0)
    tickets_checked_in = models.IntegerField(default=0)
    orders_count = models.IntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    page_views = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Event Metrics"
        verbose_name_plural = "Event Metrics"

    def __str__(self):
        return f"Metrics for {self.event.title}"

    def calculate_conversion_rate(self):
        if self.unique_visitors > 0:
            self.conversion_rate = (Decimal(self.orders_count) / Decimal(self.unique_visitors)) * Decimal("100")
        else:
            self.conversion_rate = Decimal("0.00")
        self.save()


class PaymentMetrics(models.Model):
    payment = models.OneToOneField("payments.Payment", on_delete=models.CASCADE, related_name="metrics")
    gateway_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    gateway_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    platform_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    platform_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    net_amount_to_organizer = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payment Metrics"
        verbose_name_plural = "Payment Metrics"

    def __str__(self):
        return f"Metrics for Payment #{self.payment.id}"


class OrganizationMetrics(models.Model):
    organization = models.OneToOneField("orgs.Organization", on_delete=models.CASCADE, related_name="metrics")
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_fees_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_tickets_sold = models.IntegerField(default=0)
    total_events = models.IntegerField(default=0)
    active_events = models.IntegerField(default=0)
    completed_events = models.IntegerField(default=0)
    total_attendees = models.IntegerField(default=0)
    average_ticket_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Organization Metrics"
        verbose_name_plural = "Organization Metrics"

    def __str__(self):
        return f"Metrics for {self.organization.name}"
