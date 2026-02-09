import pytest
from django.utils import timezone
from apps.events.models import Event


@pytest.mark.django_db
class TestEventCreation:
    def test_create_event(self, organization):
        event = Event.objects.create(
            organization=organization,
            title="My Test Event",
            description="A test event for validation.",
            start_at=timezone.now() + timezone.timedelta(days=7),
            end_at=timezone.now() + timezone.timedelta(days=7, hours=3),
            capacity=200,
        )
        assert event.title == "My Test Event"
        assert event.slug is not None

    def test_event_defaults(self, organization):
        event = Event.objects.create(
            organization=organization,
            title="Default Event",
            description="Checking default values.",
            start_at=timezone.now() + timezone.timedelta(days=1),
            end_at=timezone.now() + timezone.timedelta(days=1, hours=2),
        )
        assert event.state == Event.State.DRAFT
        assert event.is_free is False
