from django.db.models import Q
from django.utils import timezone

from apps.cfp.models import Proposal, Session


def create_session_from_proposal(proposal):
    """Create a Session from a confirmed Proposal."""
    session = Session.objects.create(
        proposal=proposal,
        event=proposal.cfp.event,
        title=proposal.title,
        description=proposal.abstract,
        speaker=proposal.speaker,
        session_format=proposal.session_format,
        track=proposal.track,
    )
    if proposal.co_speakers.exists():
        session.co_speakers.set(proposal.co_speakers.all())
    return session


def bulk_create_sessions(proposal_ids):
    """Create Sessions for multiple confirmed proposals."""
    proposals = Proposal.objects.filter(
        id__in=proposal_ids,
        status=Proposal.Status.CONFIRMED,
    ).select_related("cfp__event", "session_format", "track")

    sessions = []
    for proposal in proposals:
        if not hasattr(proposal, "session"):
            sessions.append(create_session_from_proposal(proposal))
    return sessions


def detect_schedule_conflicts(event):
    """Find scheduling conflicts where the same speaker has overlapping sessions."""
    scheduled = Session.objects.filter(
        event=event,
        status=Session.Status.SCHEDULED,
        starts_at__isnull=False,
        ends_at__isnull=False,
    ).select_related("speaker")

    conflicts = []
    sessions_list = list(scheduled)

    for i, s1 in enumerate(sessions_list):
        for s2 in sessions_list[i + 1:]:
            if s1.speaker_id != s2.speaker_id:
                continue
            if s1.starts_at < s2.ends_at and s2.starts_at < s1.ends_at:
                conflicts.append((s1, s2))

    return conflicts


def get_cfp_stats(cfp):
    """Get statistics for a CFP."""
    proposals = cfp.proposals.all()
    total = proposals.count()
    if total == 0:
        return {
            "total": 0,
            "submitted": 0,
            "accepted": 0,
            "rejected": 0,
            "waitlisted": 0,
            "confirmed": 0,
            "under_review": 0,
            "acceptance_rate": 0,
            "reviewed_count": 0,
            "review_progress": 0,
        }

    submitted = proposals.exclude(status=Proposal.Status.DRAFT).count()
    accepted = proposals.filter(status=Proposal.Status.ACCEPTED).count()
    confirmed = proposals.filter(status=Proposal.Status.CONFIRMED).count()
    rejected = proposals.filter(status=Proposal.Status.REJECTED).count()
    waitlisted = proposals.filter(status=Proposal.Status.WAITLISTED).count()
    under_review = proposals.filter(status=Proposal.Status.UNDER_REVIEW).count()

    decided = accepted + confirmed + rejected
    acceptance_rate = round((accepted + confirmed) / decided * 100) if decided else 0

    reviewed_count = proposals.filter(reviews__isnull=False).distinct().count()
    reviewable = proposals.exclude(
        status__in=[Proposal.Status.DRAFT, Proposal.Status.WITHDRAWN]
    ).count()
    review_progress = round(reviewed_count / reviewable * 100) if reviewable else 0

    return {
        "total": total,
        "submitted": submitted,
        "accepted": accepted,
        "rejected": rejected,
        "waitlisted": waitlisted,
        "confirmed": confirmed,
        "under_review": under_review,
        "acceptance_rate": acceptance_rate,
        "reviewed_count": reviewed_count,
        "review_progress": review_progress,
    }
