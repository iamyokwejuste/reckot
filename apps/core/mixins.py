"""
Common mixins for views across the application.
"""

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from apps.events.models import Event
from apps.orgs.models import Organization


class EventPermissionMixin:
    """
    Mixin for views that require event access permission.
    Expects org_slug and event_slug in URL kwargs.
    Sets self.event and self.organization on the view.
    """

    required_permission = None

    def get_event(self, org_slug, event_slug):
        return get_object_or_404(
            Event.objects.select_related("organization"),
            organization__slug=org_slug,
            slug=event_slug,
        )

    def check_event_permission(self, request, event):
        """Check if user has access to the event's organization."""
        if not event.organization.members.filter(id=request.user.id).exists():
            return False
        if self.required_permission:
            return event.organization.user_can(request.user, self.required_permission)
        return True

    def dispatch(self, request, *args, **kwargs):
        org_slug = kwargs.get("org_slug")
        event_slug = kwargs.get("event_slug")

        if org_slug and event_slug:
            self.event = self.get_event(org_slug, event_slug)
            self.organization = self.event.organization

            if not self.check_event_permission(request, self.event):
                messages.error(
                    request, "You don't have permission to access this event."
                )
                return redirect("events:list")

        return super().dispatch(request, *args, **kwargs)


class OrgMemberQueryMixin:
    """
    Mixin providing common queryset filters for organization members.
    """

    def get_user_organizations(self, user):
        """Get organizations the user is a member of."""
        return Organization.objects.filter(members=user)

    def get_user_events(self, user):
        """Get events from organizations the user is a member of."""
        return Event.objects.filter(organization__members=user)

    def filter_by_user_orgs(self, queryset, user, org_lookup="organization__members"):
        """Filter any queryset by user's organization membership."""
        return queryset.filter(**{org_lookup: user})
