import uuid
from django.db import models
from django.conf import settings
from apps.events.models import Event
from apps.orgs.models import Organization


class SupportTicket(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    class Category(models.TextChoices):
        PAYMENT = "PAYMENT", "Payment Issue"
        TICKET = "TICKET", "Ticket Issue"
        EVENT = "EVENT", "Event Issue"
        ACCOUNT = "ACCOUNT", "Account Issue"
        TECHNICAL = "TECHNICAL", "Technical Issue"
        OTHER = "OTHER", "Other"

    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_tickets",
        null=True,
        blank=True,
    )
    guest_email = models.EmailField(blank=True)
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_tickets",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_tickets",
    )
    subject = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.OTHER
    )
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.MEDIUM
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )
    ai_summary = models.TextField(blank=True)
    ai_suggested_solution = models.TextField(blank=True)
    resolution_notes = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"#{self.reference} - {self.subject}"


class AIConversation(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_conversations",
        null=True,
        blank=True,
    )
    context = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]


class AIMessage(models.Model):
    class Role(models.TextChoices):
        USER = "USER", "User"
        ASSISTANT = "ASSISTANT", "Assistant"
        SYSTEM = "SYSTEM", "System"

    conversation = models.ForeignKey(
        AIConversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class AIUsageLog(models.Model):
    class Operation(models.TextChoices):
        CHAT = "CHAT", "Chat Message"
        GENERATE_DESCRIPTION = "GENERATE_DESCRIPTION", "Generate Description"
        GENERATE_IMAGE = "GENERATE_IMAGE", "Generate Image"
        IMPROVE_TEXT = "IMPROVE_TEXT", "Improve Text"
        TRANSLATE = "TRANSLATE", "Translate"
        SUMMARIZE = "SUMMARIZE", "Summarize"
        INSIGHT = "INSIGHT", "Generate Insight"
        QUERY = "QUERY", "Database Query"
        VOICE_TO_EVENT = "VOICE_TO_EVENT", "Voice to Event"
        VERIFY_EVENT = "VERIFY_EVENT", "Verify Event"
        PREDICT_SALES = "PREDICT_SALES", "Predict Sales"
        OPTIMIZE_PRICING = "OPTIMIZE_PRICING", "Optimize Pricing"
        MARKETING_STRATEGY = "MARKETING_STRATEGY", "Marketing Strategy"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_usage_logs",
        null=True,
        blank=True,
    )
    session_id = models.UUIDField(null=True, blank=True)
    operation = models.CharField(max_length=50, choices=Operation.choices)
    prompt = models.TextField()
    response = models.TextField(blank=True)
    tokens_used = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    execution_time = models.FloatField(help_text="Execution time in seconds")
    models_accessed = models.JSONField(default=list, blank=True)
    error = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["operation", "-created_at"]),
        ]


class AIRateLimit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_rate_limits",
    )
    date = models.DateField(auto_now_add=True)
    request_count = models.IntegerField(default=0)
    daily_limit = models.IntegerField(default=30)

    class Meta:
        unique_together = ["user", "date"]
        indexes = [
            models.Index(fields=["user", "date"]),
        ]
