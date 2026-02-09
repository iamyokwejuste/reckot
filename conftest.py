import pytest
from django.test import Client
from django.utils import timezone

from apps.core.models import User
from apps.events.models import Event
from apps.orgs.models import Membership, MemberRole, Organization
from apps.tickets.models import TicketType


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="adminuser",
        email="admin@example.com",
        password="adminpass123",
    )


@pytest.fixture
def organization(db, user):
    org = Organization.objects.create(
        name="Test Org",
        owner=user,
    )
    Membership.objects.create(
        organization=org,
        user=user,
        role=MemberRole.OWNER,
    )
    return org


@pytest.fixture
def event(db, organization):
    return Event.objects.create(
        organization=organization,
        title="Test Event",
        description="A test event description.",
        start_at=timezone.now() + timezone.timedelta(days=7),
        end_at=timezone.now() + timezone.timedelta(days=7, hours=3),
        capacity=100,
        state=Event.State.DRAFT,
    )


@pytest.fixture
def ticket_type(db, event):
    return TicketType.objects.create(
        event=event,
        name="General Admission",
        price=5000,
        quantity=100,
    )


@pytest.fixture
def authenticated_client(db, user):
    client = Client()
    client.login(email="test@example.com", password="testpass123")
    return client
