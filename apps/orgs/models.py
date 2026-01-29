from django.db import models
from django.conf import settings
from django.utils.text import slugify
import uuid
from datetime import timedelta
from django.utils import timezone


class Organization(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='org_logos/', blank=True)
    website = models.URLField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_organizations'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Membership',
        through_fields=('organization', 'user'),
        related_name='organizations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old = Organization.objects.get(pk=self.pk)
                if old.name != self.name:
                    base_slug = slugify(self.name)
                    self.slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
            except Organization.DoesNotExist:
                pass
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)

    def get_member_role(self, user):
        """Get user's role in this organization"""
        if user == self.owner:
            return MemberRole.OWNER
        try:
            membership = Membership.objects.get(organization=self, user=user)
            return membership.role
        except Membership.DoesNotExist:
            return None

    def user_can(self, user, permission):
        """Check if user has a specific permission"""
        role = self.get_member_role(user)
        if not role:
            return False
        return Membership.has_permission(role, permission)

    def user_is_admin(self, user):
        """Check if user is admin or above"""
        role = self.get_member_role(user)
        return role in [MemberRole.OWNER, MemberRole.ADMIN]

    def has_feature(self, feature_name):
        try:
            return self.subscription.has_feature(feature_name)
        except Exception:
            return PLAN_FEATURES.get(OrganizationPlan.FREE, {}).get(feature_name, False)

    @property
    def current_plan(self):
        try:
            return self.subscription.plan
        except OrganizationSubscription.DoesNotExist:
            return OrganizationPlan.FREE

    @property
    def service_fee_percent(self):
        try:
            return self.subscription.service_fee_percent
        except OrganizationSubscription.DoesNotExist:
            return 2


class MemberRole(models.TextChoices):
    """Role choices for organization members"""
    OWNER = 'OWNER', 'Owner'
    ADMIN = 'ADMIN', 'Admin'
    MANAGER = 'MANAGER', 'Manager'
    MEMBER = 'MEMBER', 'Member'
    VIEWER = 'VIEWER', 'Viewer'


# Permission definitions for each role
ROLE_PERMISSIONS = {
    MemberRole.OWNER: [
        'manage_organization', 'delete_organization',
        'manage_members', 'invite_members', 'remove_members',
        'manage_events', 'create_events', 'edit_events', 'delete_events', 'publish_events',
        'manage_tickets', 'view_reports', 'export_reports',
        'manage_payments', 'process_refunds',
        'manage_coupons', 'checkin_attendees',
    ],
    MemberRole.ADMIN: [
        'manage_organization',
        'manage_members', 'invite_members', 'remove_members',
        'manage_events', 'create_events', 'edit_events', 'delete_events', 'publish_events',
        'manage_tickets', 'view_reports', 'export_reports',
        'manage_payments', 'process_refunds',
        'manage_coupons', 'checkin_attendees',
    ],
    MemberRole.MANAGER: [
        'manage_events', 'create_events', 'edit_events', 'publish_events',
        'manage_tickets', 'view_reports', 'export_reports',
        'manage_coupons', 'checkin_attendees',
    ],
    MemberRole.MEMBER: [
        'create_events', 'edit_events',
        'manage_tickets', 'view_reports',
        'checkin_attendees',
    ],
    MemberRole.VIEWER: [
        'view_reports',
    ],
}


class CustomRole(models.Model):
    """Custom roles for organizations (optional advanced feature)"""
    name = models.CharField(max_length=100)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='custom_roles')
    permissions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class Membership(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=MemberRole.choices, default=MemberRole.MEMBER)
    custom_role = models.ForeignKey(CustomRole, on_delete=models.SET_NULL, null=True, blank=True, related_name='memberships')
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='invited_members'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('organization', 'user')
        indexes = [
            models.Index(fields=['organization', 'role']),
            models.Index(fields=['user', 'role']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.organization.name} ({self.get_role_display()})'

    @staticmethod
    def has_permission(role, permission):
        """Check if a role has a specific permission"""
        if not role:
            return False
        return permission in ROLE_PERMISSIONS.get(role, [])

    @property
    def permissions(self):
        """Get all permissions for this membership's role"""
        return ROLE_PERMISSIONS.get(self.role, [])

    def can(self, permission):
        """Check if this membership has a specific permission"""
        return self.has_permission(self.role, permission)


class Invitation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        DECLINED = 'DECLINED', 'Declined'
        EXPIRED = 'EXPIRED', 'Expired'
        CANCELLED = 'CANCELLED', 'Cancelled'

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=MemberRole.choices, default=MemberRole.MEMBER)
    custom_role = models.ForeignKey(CustomRole, on_delete=models.SET_NULL, null=True, blank=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    message = models.TextField(blank=True, help_text="Optional message to include in invitation email")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_invitations')
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['email', 'status']),
            models.Index(fields=['token']),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return self.status == self.Status.PENDING and not self.is_expired

    def accept(self, user):
        """Accept the invitation and create membership"""
        if not self.is_valid:
            return None

        membership, created = Membership.objects.get_or_create(
            organization=self.organization,
            user=user,
            defaults={
                'role': self.role,
                'invited_by': self.invited_by,
            }
        )

        self.status = self.Status.ACCEPTED
        self.accepted_at = timezone.now()
        self.save()

        return membership

    def decline(self):
        """Decline the invitation"""
        self.status = self.Status.DECLINED
        self.save()

    def cancel(self):
        """Cancel the invitation"""
        self.status = self.Status.CANCELLED
        self.save()

    def __str__(self):
        return f'Invitation for {self.email} to {self.organization} as {self.get_role_display()}'


class OrganizationPlan(models.TextChoices):
    FREE = 'FREE', 'Free (2% fee)'
    STARTER = 'STARTER', 'Starter (5% fee)'
    PRO = 'PRO', 'Pro (3% fee)'
    ENTERPRISE = 'ENTERPRISE', 'Enterprise (Custom)'


PLAN_FEATURES = {
    OrganizationPlan.FREE: {
        'service_fee_percent': 2,
        'max_events_per_month': 2,
        'max_tickets_per_event': 100,
        'flyer_generator': False,
        'custom_branding': False,
        'priority_support': False,
        'analytics_advanced': False,
        'export_formats': ['CSV'],
    },
    OrganizationPlan.STARTER: {
        'service_fee_percent': 5,
        'max_events_per_month': 10,
        'max_tickets_per_event': 500,
        'flyer_generator': True,
        'custom_branding': False,
        'priority_support': False,
        'analytics_advanced': True,
        'export_formats': ['CSV', 'EXCEL', 'PDF'],
    },
    OrganizationPlan.PRO: {
        'service_fee_percent': 3,
        'max_events_per_month': None,
        'max_tickets_per_event': None,
        'flyer_generator': True,
        'custom_branding': True,
        'priority_support': True,
        'analytics_advanced': True,
        'export_formats': ['CSV', 'EXCEL', 'PDF', 'JSON'],
    },
    OrganizationPlan.ENTERPRISE: {
        'service_fee_percent': 0,
        'max_events_per_month': None,
        'max_tickets_per_event': None,
        'flyer_generator': True,
        'custom_branding': True,
        'priority_support': True,
        'analytics_advanced': True,
        'export_formats': ['CSV', 'EXCEL', 'PDF', 'JSON'],
    },
}


class OrganizationSubscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        PAST_DUE = 'PAST_DUE', 'Past Due'
        CANCELLED = 'CANCELLED', 'Cancelled'
        EXPIRED = 'EXPIRED', 'Expired'

    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=20, choices=OrganizationPlan.choices, default=OrganizationPlan.FREE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    custom_service_fee = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f'{self.organization.name} - {self.get_plan_display()}'

    @property
    def features(self):
        return PLAN_FEATURES.get(self.plan, PLAN_FEATURES[OrganizationPlan.FREE])

    @property
    def service_fee_percent(self):
        if self.custom_service_fee is not None:
            return self.custom_service_fee
        return self.features.get('service_fee_percent', 2)

    def has_feature(self, feature_name):
        return self.features.get(feature_name, False)

    @property
    def is_active(self):
        if self.status != self.Status.ACTIVE:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True


# Backwards compatibility alias
Role = CustomRole
