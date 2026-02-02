from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
import random
import string


class User(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    ai_features_enabled = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    social_avatar_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.email or self.username

    def get_profile_image_url(self):
        if self.profile_image:
            return self.profile_image.url
        return self.social_avatar_url if self.social_avatar_url else None

    def get_initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.first_name:
            return self.first_name[0].upper()
        elif self.email:
            return self.email[0].upper()
        return "U"


class OTPVerification(models.Model):
    class Type(models.TextChoices):
        EMAIL = "EMAIL", _("Email Verification")
        PHONE = "PHONE", _("Phone Verification")
        PASSWORD_RESET = "PASSWORD_RESET", _("Password Reset")

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="otp_verifications"
    )
    otp_type = models.CharField(max_length=20, choices=Type.choices)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["user", "otp_type", "is_used"]),
            models.Index(fields=["code", "expires_at"]),
        ]
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    @staticmethod
    def generate_code(length: int = 6) -> str:
        return "".join(random.choices(string.digits, k=length))

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired and self.attempts < 5

    def verify(self, code: str) -> bool:
        self.attempts += 1
        self.save(update_fields=["attempts"])

        if not self.is_valid:
            return False

        if self.code == code:
            self.is_used = True
            self.save(update_fields=["is_used"])
            return True

        return False

    @classmethod
    def create_for_user(cls, user: User, otp_type: str, expiry_minutes: int = 10):
        cls.objects.filter(user=user, otp_type=otp_type, is_used=False).update(
            is_used=True
        )

        return cls.objects.create(
            user=user,
            otp_type=otp_type,
            expires_at=timezone.now() + timedelta(minutes=expiry_minutes),
        )


class Notification(models.Model):
    class Type(models.TextChoices):
        TICKET_PURCHASE = "TICKET_PURCHASE", _("Ticket Purchase")
        PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED", _("Payment Confirmed")
        REFUND_APPROVED = "REFUND_APPROVED", _("Refund Approved")
        REFUND_PROCESSED = "REFUND_PROCESSED", _("Refund Processed")
        EVENT_UPDATE = "EVENT_UPDATE", _("Event Update")
        EVENT_CANCELLED = "EVENT_CANCELLED", _("Event Cancelled")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=20, choices=Type.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_read", "-created_at"]),
            models.Index(fields=["expires_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
