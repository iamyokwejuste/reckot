from django.shortcuts import get_object_or_404, render
from django.views import View

from apps.cfp.models import (
    CallForProposals,
    Proposal,
    Session,
    SpeakerProfile,
)
from apps.events.models import Event


def get_public_event(org_slug, event_slug):
    return get_object_or_404(
        Event.objects.select_related("organization"),
        organization__slug=org_slug,
        slug=event_slug,
    )


class PublicCFPView(View):
    def get(self, request, org_slug, event_slug):
        event = get_public_event(org_slug, event_slug)
        cfp = getattr(event, "cfp", None)

        formats = event.session_formats.filter(is_active=True)
        tracks = event.tracks.filter(is_active=True)

        submission_count = 0
        if cfp:
            submission_count = cfp.proposals.exclude(
                status=Proposal.Status.DRAFT
            ).count()

        return render(request, "cfp/public_cfp.html", {
            "event": event,
            "cfp": cfp,
            "formats": formats,
            "tracks": tracks,
            "submission_count": submission_count,
        })


class PublicScheduleView(View):
    def get(self, request, org_slug, event_slug):
        event = get_public_event(org_slug, event_slug)

        sessions = Session.objects.filter(
            event=event,
            status=Session.Status.SCHEDULED,
        ).select_related(
            "speaker", "session_format", "track"
        ).prefetch_related("co_speakers").order_by("starts_at", "display_order")

        tracks = event.tracks.filter(is_active=True)
        track_filter = request.GET.get("track")
        if track_filter:
            sessions = sessions.filter(track_id=track_filter)

        days = {}
        for session in sessions:
            if session.starts_at:
                day = session.starts_at.date()
                days.setdefault(day, []).append(session)

        return render(request, "cfp/public_schedule.html", {
            "event": event,
            "days": days,
            "tracks": tracks,
            "current_track": track_filter,
        })


class PublicSpeakerListView(View):
    def get(self, request, org_slug, event_slug):
        event = get_public_event(org_slug, event_slug)

        confirmed_speaker_ids = Proposal.objects.filter(
            cfp__event=event,
            status=Proposal.Status.CONFIRMED,
        ).values_list("speaker_id", flat=True)

        speakers = SpeakerProfile.objects.filter(
            event=event,
            user_id__in=confirmed_speaker_ids,
        ).select_related("user").order_by("user__first_name", "user__last_name")

        return render(request, "cfp/public_speakers.html", {
            "event": event,
            "speakers": speakers,
        })


class PublicSessionDetailView(View):
    def get(self, request, org_slug, event_slug, id):
        event = get_public_event(org_slug, event_slug)

        session = get_object_or_404(
            Session.objects.select_related(
                "speaker", "session_format", "track"
            ).prefetch_related("co_speakers"),
            id=id,
            event=event,
            status=Session.Status.SCHEDULED,
        )

        speaker_profile = SpeakerProfile.objects.filter(
            user=session.speaker, event=event
        ).first()

        return render(request, "cfp/public_session.html", {
            "event": event,
            "session": session,
            "speaker_profile": speaker_profile,
        })
