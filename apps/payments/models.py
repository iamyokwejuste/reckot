from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.tickets.models import Booking
from apps.orgs.models import Organization
import uuid
from datetime import timedelta
from django.utils import timezone


class Currency(models.TextChoices):
    XAF = "XAF", _("Central African CFA Franc")
    XOF = "XOF", _("West African CFA Franc")
    USD = "USD", _("US Dollar")
    EUR = "EUR", _("Euro")
    GBP = "GBP", _("British Pound")
    NGN = "NGN", _("Nigerian Naira")
    GHS = "GHS", _("Ghanaian Cedi")
    UGX = "UGX", _("Ugandan Shilling")


class PaymentProvider(models.TextChoices):
    CAMPAY = "CAMPAY", _("Campay")
    PAWAPAY = "PAWAPAY", _("PawaPay")
    FLUTTERWAVE = "FLUTTERWAVE", _("Flutterwave")
    MTN_MOMO = "MTN_MOMO", _("MTN Mobile Money")
    ORANGE_MONEY = "ORANGE_MONEY", _("Orange Money")
    STRIPE = "STRIPE", _("Stripe")
    PAYPAL = "PAYPAL", _("PayPal")
    OFFLINE = "OFFLINE", _("Offline Payment")


class PaymentGatewayConfig(models.Model):
    class ServiceFeeType(models.TextChoices):
        FIXED = "FIXED", _("Fixed Amount")
        PERCENTAGE = "PERCENTAGE", _("Percentage")
        BOTH = "BOTH", _("Fixed + Percentage")

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="payment_gateways"
    )
    provider = models.CharField(max_length=20, choices=PaymentProvider.choices)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    credentials = models.JSONField(default=dict, blank=True)
    supported_currencies = models.JSONField(default=list)
    service_fee_type = models.CharField(
        max_length=20, choices=ServiceFeeType.choices, default=ServiceFeeType.PERCENTAGE
    )
    service_fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_fee_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["organization", "provider"]
        indexes = [
            models.Index(fields=["organization", "is_active"]),
        ]

    def calculate_service_fee(self, amount):
        if self.service_fee_type == self.ServiceFeeType.FIXED:
            return self.service_fee_fixed
        elif self.service_fee_type == self.ServiceFeeType.PERCENTAGE:
            return amount * (self.service_fee_percentage / 100)
        else:
            return self.service_fee_fixed + (
                amount * (self.service_fee_percentage / 100)
            )


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        CONFIRMED = "CONFIRMED", _("Confirmed")
        FAILED = "FAILED", _("Failed")
        EXPIRED = "EXPIRED", _("Expired")

    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name="payment"
    )
    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(
        max_length=3, choices=Currency.choices, default=Currency.XAF
    )
    provider = models.CharField(
        max_length=20, choices=PaymentProvider.choices, default=PaymentProvider.MTN_MOMO
    )
    phone_number = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    external_reference = models.CharField(max_length=255, blank=True)
    redirect_url = models.URLField(blank=True)
    gateway_config = models.ForeignKey(
        PaymentGatewayConfig, on_delete=models.SET_NULL, null=True, blank=True
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["reference"]),
            models.Index(fields=["status", "expires_at"]),
            models.Index(fields=["booking"]),
            models.Index(fields=["provider"]),
        ]
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at and self.status == self.Status.PENDING

    @property
    def total_amount(self):
        return self.amount + self.service_fee

    def get_payment_method_display(self):
        if self.provider == PaymentProvider.CAMPAY and self.phone_number:
            phone = self.phone_number.replace("+", "").replace(" ", "")
            if phone.startswith("237"):
                phone = phone[3:]
            if phone.startswith("67") or phone.startswith("650") or phone.startswith("651") or phone.startswith("652") or phone.startswith("653") or phone.startswith("654"):
                return _("MTN Mobile Money")
            elif phone.startswith("69") or phone.startswith("655") or phone.startswith("656") or phone.startswith("657") or phone.startswith("658") or phone.startswith("659"):
                return _("Orange Money")
        return self.get_provider_display()


class OfflinePayment(models.Model):
    class VerificationStatus(models.TextChoices):
        PENDING = "PENDING", _("Pending Verification")
        VERIFIED = "VERIFIED", _("Verified")
        REJECTED = "REJECTED", _("Rejected")

    payment = models.OneToOneField(
        Payment, on_delete=models.CASCADE, related_name="offline_details"
    )
    method_description = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    proof_file = models.FileField(upload_to="payment_proofs/", blank=True)
    proof_notes = models.TextField(blank=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_payments",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["verification_status"]),
        ]


class Refund(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending Review")
        APPROVED = "APPROVED", _("Approved")
        PROCESSED = "PROCESSED", _("Processed")
        REJECTED = "REJECTED", _("Rejected")

    class Type(models.TextChoices):
        FULL = "FULL", _("Full Refund")
        PARTIAL = "PARTIAL", _("Partial Refund")

    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="refunds"
    )
    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    refund_type = models.CharField(
        max_length=10, choices=Type.choices, default=Type.FULL
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    reason = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="refund_requests",
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_refunds",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["reference"]),
            models.Index(fields=["status"]),
            models.Index(fields=["payment"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Refund {self.reference} - {self.status}"

    def approve(self, processed_by=None):
        self.status = self.Status.APPROVED
        self.processed_by = processed_by
        self.save(update_fields=["status", "processed_by", "updated_at"])

    def process(self, processed_by=None):
        self.status = self.Status.PROCESSED
        self.processed_by = processed_by
        self.processed_at = timezone.now()
        self.save(
            update_fields=["status", "processed_by", "processed_at", "updated_at"]
        )

    def reject(self, reason: str, processed_by=None):
        self.status = self.Status.REJECTED
        self.rejection_reason = reason
        self.processed_by = processed_by
        self.save(
            update_fields=["status", "rejection_reason", "processed_by", "updated_at"]
        )


class RefundAuditLog(models.Model):
    refund = models.ForeignKey(
        Refund, on_delete=models.CASCADE, related_name="audit_logs"
    )
    action = models.CharField(max_length=50)
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.refund.reference} - {self.action}"


class Invoice(models.Model):
    payment = models.OneToOneField(
        Payment, on_delete=models.CASCADE, related_name="invoice"
    )
    invoice_number = models.CharField(max_length=50, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=3, choices=Currency.choices, default=Currency.XAF
    )
    billing_name = models.CharField(max_length=255)
    billing_email = models.EmailField()
    billing_address = models.TextField(blank=True)
    organization_name = models.CharField(max_length=255)
    organization_address = models.TextField(blank=True)
    organization_email = models.EmailField(blank=True)
    organization_phone = models.CharField(max_length=50, blank=True)
    organization_logo = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    pdf_file = models.FileField(upload_to="invoices/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issued_at"]
        indexes = [
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["payment"]),
        ]

    def __str__(self):
        return f"Invoice {self.invoice_number}"

    @classmethod
    def generate_invoice_number(cls):
        now = timezone.now()
        prefix = f"INV-{now.strftime('%Y%m')}"
        last_invoice = (
            cls.objects.filter(invoice_number__startswith=prefix)
            .order_by("-invoice_number")
            .first()
        )
        if last_invoice:
            last_num = int(last_invoice.invoice_number.split("-")[-1])
            return f"{prefix}-{last_num + 1:04d}"
        return f"{prefix}-0001"


class Withdrawal(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        PROCESSING = "PROCESSING", _("Processing")
        COMPLETED = "COMPLETED", _("Completed")
        FAILED = "FAILED", _("Failed")
        CANCELLED = "CANCELLED", _("Cancelled")

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="withdrawals"
    )
    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    external_reference = models.UUIDField(default=uuid.uuid4, editable=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    gateway_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_commission = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=3, choices=Currency.choices, default=Currency.XAF
    )
    phone_number = models.CharField(max_length=20)
    description = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    provider = models.CharField(
        max_length=20, choices=PaymentProvider.choices, default=PaymentProvider.CAMPAY
    )
    gateway_response = models.JSONField(default=dict, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="requested_withdrawals",
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    failed_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["reference"]),
            models.Index(fields=["external_reference"]),
            models.Index(fields=["organization"]),
            models.Index(fields=["status"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Withdrawal {self.reference} - {self.organization.name} - "
            f"{self.amount} {self.currency}"
        )

    def mark_processing(self):
        self.status = self.Status.PROCESSING
        self.save(update_fields=["status", "updated_at"])

    def mark_completed(self):
        self.status = self.Status.COMPLETED
        self.processed_at = timezone.now()
        self.save(update_fields=["status", "processed_at", "updated_at"])

    def mark_failed(self, reason: str):
        self.status = self.Status.FAILED
        self.failed_reason = reason
        self.processed_at = timezone.now()
        self.save(
            update_fields=["status", "failed_reason", "processed_at", "updated_at"]
        )
