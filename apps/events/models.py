from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from apps.orgs.models import Organization
import uuid


class Event(models.Model):
    class State(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        PUBLISHED = 'PUBLISHED', _('Published')
        CLOSED = 'CLOSED', _('Closed')
        ARCHIVED = 'ARCHIVED', _('Archived')

    class EventType(models.TextChoices):
        IN_PERSON = 'IN_PERSON', _('In Person')
        ONLINE = 'ONLINE', _('Online')
        HYBRID = 'HYBRID', _('Hybrid')

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    cover_image = models.ImageField(upload_to='event_covers/', blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    timezone = models.CharField(max_length=50, default='Africa/Douala')
    event_type = models.CharField(max_length=20, choices=EventType.choices, default=EventType.IN_PERSON)
    location = models.CharField(max_length=200, blank=True)
    venue_name = models.CharField(max_length=200, blank=True)
    address_line_2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Cameroon')
    online_url = models.URLField(blank=True)
    website = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    state = models.CharField(max_length=10, choices=State.choices, default=State.DRAFT)
    is_public = models.BooleanField(default=False)
    is_free = models.BooleanField(default=False)
    preview_token = models.CharField(max_length=32, blank=True, db_index=True)

    is_featured = models.BooleanField(default=False)
    feature_requested_at = models.DateTimeField(null=True, blank=True)
    feature_approved_at = models.DateTimeField(null=True, blank=True)
    feature_expires_at = models.DateTimeField(null=True, blank=True)
    feature_order = models.PositiveIntegerField(default=0)
    feature_rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['organization', 'state']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_public', 'state']),
            models.Index(fields=['is_featured', 'feature_order']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old = Event.objects.get(pk=self.pk)
                if old.title != self.title:
                    base_slug = slugify(self.title)
                    self.slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
            except Event.DoesNotExist:
                pass
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

    def generate_preview_token(self):
        self.preview_token = uuid.uuid4().hex[:16]
        self.save(update_fields=['preview_token'])
        return self.preview_token


class EventCustomization(models.Model):
    class LayoutTemplate(models.TextChoices):
        DEFAULT = 'DEFAULT', _('Default')
        MINIMAL = 'MINIMAL', _('Minimal')
        FULL_WIDTH = 'FULL_WIDTH', _('Full Width')
        CENTERED = 'CENTERED', _('Centered')

    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='customization')
    primary_color = models.CharField(max_length=7, default='#000000')
    secondary_color = models.CharField(max_length=7, default='#ffffff')
    background_color = models.CharField(max_length=7, default='#ffffff')
    text_color = models.CharField(max_length=7, default='#000000')
    heading_font = models.CharField(max_length=100, default='system-ui')
    body_font = models.CharField(max_length=100, default='system-ui')
    layout_template = models.CharField(
        max_length=20,
        choices=LayoutTemplate.choices,
        default=LayoutTemplate.DEFAULT
    )
    hero_image = models.ImageField(upload_to='event_heroes/', blank=True)
    logo = models.ImageField(upload_to='event_logos/', blank=True)
    custom_css = models.TextField(blank=True)
    hide_reckot_branding = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CheckoutQuestion(models.Model):
    class FieldType(models.TextChoices):
        TEXT = 'TEXT', _('Text')
        TEXTAREA = 'TEXTAREA', _('Long Text')
        SELECT = 'SELECT', _('Dropdown')
        RADIO = 'RADIO', _('Radio Buttons')
        CHECKBOX = 'CHECKBOX', _('Checkbox')
        EMAIL = 'EMAIL', _('Email')
        PHONE = 'PHONE', _('Phone Number')
        DATE = 'DATE', _('Date')
        NUMBER = 'NUMBER', _('Number')

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='checkout_questions')
    question = models.CharField(max_length=255)
    field_type = models.CharField(max_length=20, choices=FieldType.choices, default=FieldType.TEXT)
    options = models.JSONField(default=list, blank=True)
    is_required = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)
    per_ticket = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['event', 'order']),
        ]

    def __str__(self):
        return self.question


class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'PERCENTAGE', _('Percentage')
        FIXED = 'FIXED', _('Fixed Amount')

    class AssignmentType(models.TextChoices):
        PUBLIC = 'PUBLIC', _('Public (Anyone)')
        INDIVIDUAL = 'INDIVIDUAL', _('Assigned to Individual')
        GROUP = 'GROUP', _('Assigned to Group')

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='coupons'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='coupons',
        null=True,
        blank=True
    )
    code = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True)
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    assignment_type = models.CharField(
        max_length=20,
        choices=AssignmentType.choices,
        default=AssignmentType.PUBLIC
    )
    assigned_email = models.EmailField(blank=True)
    assigned_emails = models.JSONField(default=list, blank=True)
    max_uses = models.PositiveIntegerField(default=1)
    use_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_coupons'
    )

    class Meta:
        unique_together = ['organization', 'code']
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['code']),
            models.Index(fields=['event', 'is_active']),
        ]

    def __str__(self):
        return f'{self.code} - {self.organization.name}'

    @property
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.is_active:
            return False
        if self.max_uses > 0 and self.use_count >= self.max_uses:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return True

    @property
    def remaining_uses(self):
        if self.max_uses == 0:
            return None
        return max(0, self.max_uses - self.use_count)

    def can_be_used_by(self, email):
        if not self.is_valid:
            return False
        if self.assignment_type == self.AssignmentType.PUBLIC:
            return True
        if self.assignment_type == self.AssignmentType.INDIVIDUAL:
            return self.assigned_email.lower() == email.lower()
        if self.assignment_type == self.AssignmentType.GROUP:
            return email.lower() in [e.lower() for e in self.assigned_emails]
        return False

    def calculate_discount(self, amount):
        if self.discount_type == self.DiscountType.PERCENTAGE:
            return amount * (self.discount_value / 100)
        return min(self.discount_value, amount)

    def use(self):
        self.use_count += 1
        self.save(update_fields=['use_count'])


class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    booking = models.ForeignKey('tickets.Booking', on_delete=models.CASCADE, related_name='coupon_usages')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)
    used_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='used_coupons'
    )

    class Meta:
        indexes = [
            models.Index(fields=['coupon', 'used_at']),
            models.Index(fields=['booking']),
        ]


class EventFlyerConfig(models.Model):
    class PhotoShape(models.TextChoices):
        CIRCLE = 'CIRCLE', _('Circle')
        SQUARE = 'SQUARE', _('Square')
        ROUNDED = 'ROUNDED', _('Rounded Rectangle')

    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='flyer_config')
    is_enabled = models.BooleanField(default=False)
    pay_per_use_accepted = models.BooleanField(default=False)
    pay_per_use_accepted_at = models.DateTimeField(null=True, blank=True)
    template_change_count = models.PositiveSmallIntegerField(default=0)
    template_image = models.ImageField(upload_to='flyer_templates/')
    photo_x = models.PositiveIntegerField(default=50)
    photo_y = models.PositiveIntegerField(default=50)
    photo_width = models.PositiveIntegerField(default=200)
    photo_height = models.PositiveIntegerField(default=200)
    photo_shape = models.CharField(max_length=10, choices=PhotoShape.choices, default=PhotoShape.CIRCLE)
    photo_border_width = models.PositiveSmallIntegerField(default=0)
    photo_border_color = models.CharField(max_length=7, default='#ffffff')
    output_width = models.PositiveIntegerField(default=1080)
    output_height = models.PositiveIntegerField(default=1080)
    output_quality = models.PositiveSmallIntegerField(default=90)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Flyer config for {self.event.title}'


class FlyerTextField(models.Model):
    class TextAlign(models.TextChoices):
        LEFT = 'LEFT', _('Left')
        CENTER = 'CENTER', _('Center')
        RIGHT = 'RIGHT', _('Right')

    flyer_config = models.ForeignKey(EventFlyerConfig, on_delete=models.CASCADE, related_name='text_fields')
    label = models.CharField(max_length=50)
    placeholder = models.CharField(max_length=100, blank=True)
    is_required = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    x = models.PositiveIntegerField(default=0)
    y = models.PositiveIntegerField(default=0)
    max_width = models.PositiveIntegerField(default=400)
    font_size = models.PositiveSmallIntegerField(default=32)
    font_color = models.CharField(max_length=7, default='#ffffff')
    font_weight = models.CharField(max_length=10, default='bold')
    text_align = models.CharField(max_length=10, choices=TextAlign.choices, default=TextAlign.CENTER)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.label} - {self.flyer_config.event.title}'


class FlyerGeneration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='flyer_generations')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['event', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'Flyer generated for {self.event.title} at {self.created_at}'


class FlyerBilling(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        INVOICED = 'INVOICED', _('Invoiced')
        PAID = 'PAID', _('Paid')

    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='flyer_billing')
    generation_count = models.PositiveIntegerField(default=0)
    rate_per_flyer = models.DecimalField(max_digits=10, decimal_places=2, default=25)
    currency = models.CharField(max_length=3, default='XAF')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    invoiced_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['event']),
        ]

    def __str__(self):
        return f'Flyer billing for {self.event.title} - {self.generation_count} flyers'

    def update_totals(self):
        self.generation_count = self.event.flyer_generations.count()
        self.total_amount = self.generation_count * self.rate_per_flyer
        self.save(update_fields=['generation_count', 'total_amount', 'updated_at'])