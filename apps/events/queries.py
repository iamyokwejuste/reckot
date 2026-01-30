from apps.events.models import Event


def get_events_for_organization(organization):
    return Event.objects.filter(organization=organization).order_by("-start_at")


def get_user_events(user):
    return (
        Event.objects.filter(organization__members=user)
        .prefetch_related("organization")
        .order_by("-start_at")
    )
