import pytest
from django.utils import timezone
from apps.cfp.models import CallForProposals, Proposal, SpeakerProfile, SessionFormat


@pytest.mark.django_db
class TestCFPSubmission:
    def test_create_cfp(self, event):
        cfp = CallForProposals.objects.create(
            event=event,
            title="Call for Speakers",
            opens_at=timezone.now(),
            closes_at=timezone.now() + timezone.timedelta(days=30),
        )
        assert cfp.event == event
        assert cfp.title == "Call for Speakers"

    def test_create_proposal(self, event, user):
        cfp = CallForProposals.objects.create(
            event=event,
            title="Test CFP",
            opens_at=timezone.now(),
            closes_at=timezone.now() + timezone.timedelta(days=30),
        )
        profile = SpeakerProfile.objects.create(
            user=user,
            event=event,
            bio="Test speaker bio with enough content.",
        )
        session_format = SessionFormat.objects.create(
            event=event,
            name="Talk",
            duration_minutes=30,
        )
        proposal = Proposal.objects.create(
            cfp=cfp,
            speaker=user,
            title="My Talk",
            abstract="A great talk about testing.",
            description="Detailed description for reviewers.",
            session_format=session_format,
        )
        assert proposal.title == "My Talk"
        assert proposal.status == Proposal.Status.DRAFT
