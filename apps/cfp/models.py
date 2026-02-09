from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.validators import ALLOWED_IMAGE_EXTENSIONS, validate_image_file_size
from apps.events.models import Event


class CallForProposals(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Draft")
        OPEN = "OPEN", _("Open")
        CLOSED = "CLOSED", _("Closed")
        REVIEWING = "REVIEWING", _("Reviewing")
        DECIDED = "DECIDED", _("Decided")

    event = models.OneToOneField(
        Event, on_delete=models.CASCADE, related_name="cfp"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    title = models.CharField(
        max_length=200, default="Call for proposals"
    )
    description = models.TextField(
        blank=True,
        help_text=_("Guidelines and what you are looking for in proposals"),
    )
    opens_at = models.DateTimeField()
    closes_at = models.DateTimeField()
    max_submissions_per_speaker = models.PositiveIntegerField(default=3)
    anonymous_review = models.BooleanField(
        default=True,
        help_text=_("Hide speaker information from reviewers"),
    )
    allow_edits_after_submit = models.BooleanField(default=True)
    notify_on_submission = models.BooleanField(
        default=True,
        help_text=_("Email organizers when a new proposal is submitted"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Call for proposals")
        verbose_name_plural = _("Calls for proposals")
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["closes_at"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.event.title}"

    @property
    def is_open(self):
        now = timezone.now()
        return (
            self.status == self.Status.OPEN
            and self.opens_at <= now <= self.closes_at
        )


class SessionFormat(models.Model):
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="session_formats"
    )
    name = models.CharField(max_length=100)
    duration_minutes = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    max_capacity = models.PositiveIntegerField(null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.name} ({self.duration_minutes}min)"


class Track(models.Model):
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="tracks"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(
        max_length=7, default="#09090b",
        help_text=_("Hex color code for track badge"),
    )
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class SpeakerProfile(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="speaker_profiles",
    )
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="speaker_profiles"
    )
    bio = models.TextField()
    tagline = models.CharField(max_length=200, blank=True)
    photo = models.ImageField(
        upload_to="speaker_photos/",
        blank=True,
        validators=[FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS), validate_image_file_size],
    )
    company = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    twitter = models.CharField(max_length=100, blank=True)
    linkedin = models.URLField(blank=True)
    github = models.CharField(max_length=100, blank=True)
    travel_assistance = models.BooleanField(default=False)
    accommodation_needed = models.BooleanField(default=False)
    dietary_requirements = models.CharField(max_length=200, blank=True)
    notes = models.TextField(
        blank=True,
        help_text=_("Private notes visible only to organizers"),
    )
    custom_fields = models.JSONField(
        default=dict, blank=True,
        help_text=_("Custom speaker data as key-value pairs"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "event")
        indexes = [
            models.Index(fields=["user", "event"]),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} - {self.event.title}"

    def get_photo_url(self):
        if self.photo:
            return self.photo.url
        return self.user.get_profile_image_url()


class CFPQuestion(models.Model):
    class FieldType(models.TextChoices):
        TEXT = "TEXT", _("Text")
        TEXTAREA = "TEXTAREA", _("Text area")
        SELECT = "SELECT", _("Select")
        RADIO = "RADIO", _("Radio")
        CHECKBOX = "CHECKBOX", _("Checkbox")
        NUMBER = "NUMBER", _("Number")

    cfp = models.ForeignKey(
        CallForProposals, on_delete=models.CASCADE, related_name="questions"
    )
    question = models.CharField(max_length=500)
    field_type = models.CharField(
        max_length=20, choices=FieldType.choices, default=FieldType.TEXT
    )
    options = models.JSONField(
        default=list, blank=True,
        help_text=_("Options for select, radio, or checkbox fields"),
    )
    is_required = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.question


class Proposal(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Draft")
        SUBMITTED = "SUBMITTED", _("Submitted")
        UNDER_REVIEW = "UNDER_REVIEW", _("Under review")
        ACCEPTED = "ACCEPTED", _("Accepted")
        REJECTED = "REJECTED", _("Rejected")
        WAITLISTED = "WAITLISTED", _("Waitlisted")
        WITHDRAWN = "WITHDRAWN", _("Withdrawn")
        CONFIRMED = "CONFIRMED", _("Confirmed")

    class Level(models.TextChoices):
        BEGINNER = "BEGINNER", _("Beginner")
        INTERMEDIATE = "INTERMEDIATE", _("Intermediate")
        ADVANCED = "ADVANCED", _("Advanced")
        ALL = "ALL", _("All levels")

    cfp = models.ForeignKey(
        CallForProposals, on_delete=models.CASCADE, related_name="proposals"
    )
    speaker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="proposals",
    )
    title = models.CharField(max_length=300)
    abstract = models.TextField(
        help_text=_("Short public-facing summary of your proposal"),
    )
    description = models.TextField(
        help_text=_("Detailed description for reviewers"),
    )
    outline = models.TextField(
        blank=True,
        help_text=_("Talk outline or structure"),
    )
    session_format = models.ForeignKey(
        SessionFormat, on_delete=models.SET_NULL,
        null=True, related_name="proposals",
    )
    track = models.ForeignKey(
        Track, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="proposals",
    )
    level = models.CharField(
        max_length=20, choices=Level.choices, default=Level.ALL
    )
    language = models.CharField(max_length=10, default="en")
    tags = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    co_speakers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="co_proposals"
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    speaker_notes = models.TextField(
        blank=True,
        help_text=_("Private notes to organizers"),
    )
    organizer_notes = models.TextField(
        blank=True,
        help_text=_("Internal notes visible only to organizers"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at", "-created_at"]
        indexes = [
            models.Index(fields=["cfp", "status"]),
            models.Index(fields=["speaker", "status"]),
            models.Index(fields=["cfp", "speaker"]),
        ]

    def __str__(self):
        return self.title

    @property
    def average_rating(self):
        reviews = self.reviews.filter(is_abstained=False)
        if not reviews.exists():
            return None
        return reviews.aggregate(avg=models.Avg("rating"))["avg"]

    @property
    def review_count(self):
        return self.reviews.filter(is_abstained=False).count()


class ProposalQuestionAnswer(models.Model):
    proposal = models.ForeignKey(
        Proposal, on_delete=models.CASCADE, related_name="question_answers"
    )
    question = models.ForeignKey(
        CFPQuestion, on_delete=models.CASCADE, related_name="answers"
    )
    answer = models.TextField()

    class Meta:
        unique_together = ("proposal", "question")

    def __str__(self):
        return f"{self.question.question}: {self.answer[:50]}"


class Review(models.Model):
    proposal = models.ForeignKey(
        Proposal, on_delete=models.CASCADE, related_name="reviews"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cfp_reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    content_score = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    relevance_score = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    speaker_score = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_("Hidden when anonymous review is enabled"),
    )
    comment = models.TextField(blank=True)
    is_abstained = models.BooleanField(
        default=False,
        help_text=_("Reviewer has a conflict of interest"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("proposal", "reviewer")

    def __str__(self):
        return f"Review by {self.reviewer} for {self.proposal.title}"

    @property
    def average_score(self):
        scores = [
            s for s in [self.content_score, self.relevance_score, self.speaker_score]
            if s is not None
        ]
        if not scores:
            return self.rating
        return sum(scores) / len(scores)


class Session(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Draft")
        SCHEDULED = "SCHEDULED", _("Scheduled")
        CANCELLED = "CANCELLED", _("Cancelled")

    proposal = models.OneToOneField(
        Proposal, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="session",
    )
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="sessions"
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    speaker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    co_speakers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="co_sessions"
    )
    session_format = models.ForeignKey(
        SessionFormat, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="sessions",
    )
    track = models.ForeignKey(
        Track, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="sessions",
    )
    room = models.CharField(max_length=200, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at", "display_order"]
        indexes = [
            models.Index(fields=["event", "starts_at"]),
            models.Index(fields=["event", "track"]),
            models.Index(fields=["event", "status"]),
        ]

    def __str__(self):
        return self.title
