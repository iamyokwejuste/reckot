import csv
import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Avg, Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View

from apps.cfp.forms import (
    CFPConfigForm,
    CFPQuestionForm,
    ReviewForm,
    SessionFormatForm,
    SessionForm,
    TrackForm,
)
from apps.cfp.models import (
    CallForProposals,
    CFPQuestion,
    Proposal,
    Review,
    Session,
    SessionFormat,
    SpeakerProfile,
    Track,
)
from apps.cfp.services.cfp_service import (
    create_session_from_proposal,
    detect_schedule_conflicts,
    get_cfp_stats,
)
from apps.cfp.tasks import (
    send_bulk_decision_emails_task,
    send_proposal_status_email_task,
)
from apps.events.models import Event
from apps.orgs.models import Organization


def get_event_for_organizer(request, org_slug, event_slug, permission=None):
    event = get_object_or_404(
        Event.objects.select_related("organization"),
        organization__slug=org_slug,
        slug=event_slug,
        organization__members=request.user,
    )
    if permission and not event.organization.user_can(request.user, permission):
        return None, event
    return event, None


class CFPConfigView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "manage_cfp"
        )
        if denied:
            messages.error(request, _("You don't have permission to manage the CFP."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        cfp = getattr(event, "cfp", None)
        form = CFPConfigForm(instance=cfp)
        return render(request, "cfp/manage/cfp_config.html", {
            "event": event,
            "cfp": cfp,
            "form": form,
        })

    def post(self, request, org_slug, event_slug):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "manage_cfp"
        )
        if denied:
            messages.error(request, _("You don't have permission to manage the CFP."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        cfp = getattr(event, "cfp", None)
        form = CFPConfigForm(request.POST, instance=cfp)

        if form.is_valid():
            cfp = form.save(commit=False)
            cfp.event = event
            cfp.save()
            messages.success(request, _("CFP settings saved."))
            return redirect(
                "cfp:cfp_config", org_slug=org_slug, event_slug=event_slug
            )

        return render(request, "cfp/manage/cfp_config.html", {
            "event": event,
            "cfp": cfp,
            "form": form,
        })


class SessionFormatManageView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "manage_cfp"
        )
        if denied:
            messages.error(request, _("You don't have permission to manage the CFP."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        formats = event.session_formats.all()
        form = SessionFormatForm()
        return render(request, "cfp/manage/session_formats.html", {
            "event": event,
            "formats": formats,
            "form": form,
        })

    def post(self, request, org_slug, event_slug):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "manage_cfp"
        )
        if denied:
            messages.error(request, _("You don't have permission to manage the CFP."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        action = request.POST.get("action", "create")
        format_id = request.POST.get("format_id")

        if action == "delete" and format_id:
            SessionFormat.objects.filter(id=format_id, event=event).delete()
            messages.success(request, _("Session format deleted."))
        elif action == "edit" and format_id:
            fmt = get_object_or_404(SessionFormat, id=format_id, event=event)
            form = SessionFormatForm(request.POST, instance=fmt)
            if form.is_valid():
                form.save()
                messages.success(request, _("Session format updated."))
        else:
            form = SessionFormatForm(request.POST)
            if form.is_valid():
                fmt = form.save(commit=False)
                fmt.event = event
                fmt.save()
                messages.success(request, _("Session format created."))
            else:
                messages.error(request, _("Please correct the errors below."))
                formats = event.session_formats.all()
                return render(request, "cfp/manage/session_formats.html", {
                    "event": event,
                    "formats": formats,
                    "form": form,
                })

        return redirect(
            "cfp:session_formats", org_slug=org_slug, event_slug=event_slug
        )


class TrackManageView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "manage_cfp"
        )
        if denied:
            messages.error(request, _("You don't have permission to manage the CFP."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        tracks = event.tracks.all()
        form = TrackForm()
        return render(request, "cfp/manage/tracks.html", {
            "event": event,
            "tracks": tracks,
            "form": form,
        })

    def post(self, request, org_slug, event_slug):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "manage_cfp"
        )
        if denied:
            messages.error(request, _("You don't have permission to manage the CFP."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        action = request.POST.get("action", "create")
        track_id = request.POST.get("track_id")

        if action == "delete" and track_id:
            Track.objects.filter(id=track_id, event=event).delete()
            messages.success(request, _("Track deleted."))
        elif action == "edit" and track_id:
            track = get_object_or_404(Track, id=track_id, event=event)
            form = TrackForm(request.POST, instance=track)
            if form.is_valid():
                form.save()
                messages.success(request, _("Track updated."))
        else:
            form = TrackForm(request.POST)
            if form.is_valid():
                track = form.save(commit=False)
                track.event = event
                track.save()
                messages.success(request, _("Track created."))
            else:
                messages.error(request, _("Please correct the errors below."))
                tracks = event.tracks.all()
                return render(request, "cfp/manage/tracks.html", {
                    "event": event,
                    "tracks": tracks,
                    "form": form,
                })

        return redirect("cfp:tracks", org_slug=org_slug, event_slug=event_slug)


class CFPQuestionsView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "manage_cfp"
        )
        if denied:
            messages.error(request, _("You don't have permission to manage the CFP."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        cfp = getattr(event, "cfp", None)
        if not cfp:
            messages.warning(request, _("Please create a CFP first."))
            return redirect("cfp:cfp_config", org_slug=org_slug, event_slug=event_slug)

        questions = cfp.questions.all()
        form = CFPQuestionForm()
        return render(request, "cfp/manage/questions.html", {
            "event": event,
            "cfp": cfp,
            "questions": questions,
            "form": form,
        })

    def post(self, request, org_slug, event_slug):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "manage_cfp"
        )
        if denied:
            messages.error(request, _("You don't have permission to manage the CFP."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        cfp = getattr(event, "cfp", None)
        if not cfp:
            messages.warning(request, _("Please create a CFP first."))
            return redirect("cfp:cfp_config", org_slug=org_slug, event_slug=event_slug)

        action = request.POST.get("action", "create")
        question_id = request.POST.get("question_id")

        if action == "delete" and question_id:
            CFPQuestion.objects.filter(id=question_id, cfp=cfp).delete()
            messages.success(request, _("Question deleted."))
        elif action == "edit" and question_id:
            question = get_object_or_404(CFPQuestion, id=question_id, cfp=cfp)
            form = CFPQuestionForm(request.POST, instance=question)
            if form.is_valid():
                form.save()
                messages.success(request, _("Question updated."))
        else:
            form = CFPQuestionForm(request.POST)
            if form.is_valid():
                question = form.save(commit=False)
                question.cfp = cfp
                question.save()
                messages.success(request, _("Question added."))

        return redirect("cfp:cfp_questions", org_slug=org_slug, event_slug=event_slug)


class ProposalListView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "review_proposals"
        )
        if denied:
            messages.error(request, _("You don't have permission to review proposals."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        cfp = getattr(event, "cfp", None)
        if not cfp:
            messages.warning(request, _("No CFP exists for this event."))
            return redirect("cfp:cfp_config", org_slug=org_slug, event_slug=event_slug)

        proposals = cfp.proposals.select_related(
            "speaker", "session_format", "track"
        ).annotate(
            avg_rating=Avg("reviews__rating", filter=Q(reviews__is_abstained=False)),
            review_count=Count("reviews", filter=Q(reviews__is_abstained=False)),
        )

        status_filter = request.GET.get("status")
        track_filter = request.GET.get("track")
        format_filter = request.GET.get("format")
        search = request.GET.get("q")
        sort = request.GET.get("sort", "-submitted_at")

        if status_filter:
            proposals = proposals.filter(status=status_filter)
        else:
            proposals = proposals.exclude(status=Proposal.Status.DRAFT)

        if track_filter:
            proposals = proposals.filter(track_id=track_filter)
        if format_filter:
            proposals = proposals.filter(session_format_id=format_filter)
        if search:
            proposals = proposals.filter(
                Q(title__icontains=search) | Q(speaker__email__icontains=search)
                | Q(speaker__first_name__icontains=search)
            )

        valid_sorts = {
            "-submitted_at", "submitted_at", "-avg_rating", "avg_rating",
            "title", "-title", "status",
        }
        if sort in valid_sorts:
            proposals = proposals.order_by(sort)

        stats = get_cfp_stats(cfp)

        return render(request, "cfp/manage/proposals_list.html", {
            "event": event,
            "cfp": cfp,
            "proposals": proposals,
            "stats": stats,
            "tracks": event.tracks.filter(is_active=True),
            "formats": event.session_formats.filter(is_active=True),
            "current_status": status_filter,
            "current_track": track_filter,
            "current_format": format_filter,
            "current_search": search or "",
            "current_sort": sort,
        })


class ProposalDetailView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug, id):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "review_proposals"
        )
        if denied:
            messages.error(request, _("You don't have permission to review proposals."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        proposal = get_object_or_404(
            Proposal.objects.select_related(
                "cfp__event", "speaker", "session_format", "track"
            ).prefetch_related("co_speakers", "question_answers__question", "reviews__reviewer"),
            id=id,
            cfp__event=event,
        )

        existing_review = proposal.reviews.filter(reviewer=request.user).first()
        review_form = ReviewForm(instance=existing_review)

        return render(request, "cfp/manage/proposal_detail.html", {
            "event": event,
            "proposal": proposal,
            "review_form": review_form,
            "existing_review": existing_review,
            "anonymous_review": proposal.cfp.anonymous_review,
        })


class ProposalReviewView(LoginRequiredMixin, View):
    def post(self, request, org_slug, event_slug, id):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "review_proposals"
        )
        if denied:
            messages.error(request, _("You don't have permission to review proposals."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        proposal = get_object_or_404(Proposal, id=id, cfp__event=event)
        existing_review = proposal.reviews.filter(reviewer=request.user).first()
        form = ReviewForm(request.POST, instance=existing_review)

        if form.is_valid():
            review = form.save(commit=False)
            review.proposal = proposal
            review.reviewer = request.user
            review.save()

            if proposal.status == Proposal.Status.SUBMITTED:
                proposal.status = Proposal.Status.UNDER_REVIEW
                proposal.save(update_fields=["status"])

            messages.success(request, _("Review submitted."))
        else:
            messages.error(request, _("Please correct the errors in your review."))

        return redirect(
            "cfp:proposal_detail",
            org_slug=org_slug, event_slug=event_slug, id=id,
        )


class ProposalDecideView(LoginRequiredMixin, View):
    def post(self, request, org_slug, event_slug, id):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "manage_cfp"
        )
        if denied:
            messages.error(request, _("You don't have permission to manage the CFP."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        proposal = get_object_or_404(Proposal, id=id, cfp__event=event)
        action = request.POST.get("decision")
        organizer_notes = request.POST.get("organizer_notes", "")

        valid_decisions = {
            "accept": Proposal.Status.ACCEPTED,
            "reject": Proposal.Status.REJECTED,
            "waitlist": Proposal.Status.WAITLISTED,
        }

        new_status = valid_decisions.get(action)
        if not new_status:
            messages.error(request, _("Invalid decision."))
            return redirect(
                "cfp:proposal_detail",
                org_slug=org_slug, event_slug=event_slug, id=id,
            )

        proposal.status = new_status
        proposal.decided_at = timezone.now()
        if organizer_notes:
            proposal.organizer_notes = organizer_notes
        proposal.save(update_fields=["status", "decided_at", "organizer_notes"])

        send_proposal_status_email_task.delay(proposal.id)

        messages.success(
            request,
            _("Proposal marked as %(status)s.") % {"status": proposal.get_status_display()},
        )
        return redirect(
            "cfp:proposal_detail",
            org_slug=org_slug, event_slug=event_slug, id=id,
        )


class BulkActionView(LoginRequiredMixin, View):
    def post(self, request, org_slug, event_slug):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "manage_cfp"
        )
        if denied:
            messages.error(request, _("You don't have permission to manage the CFP."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        proposal_ids = request.POST.getlist("proposal_ids")
        action = request.POST.get("action")

        valid_actions = {
            "accept": Proposal.Status.ACCEPTED,
            "reject": Proposal.Status.REJECTED,
            "waitlist": Proposal.Status.WAITLISTED,
        }

        new_status = valid_actions.get(action)
        if not new_status or not proposal_ids:
            messages.error(request, _("Invalid action or no proposals selected."))
            return redirect(
                "cfp:proposals_list", org_slug=org_slug, event_slug=event_slug
            )

        updated = Proposal.objects.filter(
            id__in=proposal_ids, cfp__event=event
        ).exclude(
            status__in=[Proposal.Status.WITHDRAWN, Proposal.Status.CONFIRMED]
        ).update(status=new_status, decided_at=timezone.now())

        send_bulk_decision_emails_task.delay(
            [int(pid) for pid in proposal_ids], action
        )

        messages.success(
            request,
            _("%(count)d proposals updated.") % {"count": updated},
        )
        return redirect(
            "cfp:proposals_list", org_slug=org_slug, event_slug=event_slug
        )


class ExportProposalsView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "manage_cfp"
        )
        if denied:
            return HttpResponse(status=403)

        cfp = getattr(event, "cfp", None)
        if not cfp:
            return HttpResponse(status=404)

        proposals = cfp.proposals.select_related(
            "speaker", "session_format", "track"
        ).annotate(
            avg_rating=Avg("reviews__rating", filter=Q(reviews__is_abstained=False)),
        ).exclude(status=Proposal.Status.DRAFT)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="{event.slug}-proposals.csv"'
        )

        writer = csv.writer(response)
        writer.writerow([
            "Title", "Speaker", "Speaker Email", "Status", "Track",
            "Format", "Level", "Average Rating", "Submitted At",
        ])

        for p in proposals:
            writer.writerow([
                p.title,
                p.speaker.get_full_name() or p.speaker.email,
                p.speaker.email,
                p.get_status_display(),
                p.track.name if p.track else "",
                p.session_format.name if p.session_format else "",
                p.get_level_display(),
                round(p.avg_rating, 2) if p.avg_rating else "",
                p.submitted_at.strftime("%Y-%m-%d %H:%M") if p.submitted_at else "",
            ])

        return response


class CFPAnalyticsView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "manage_cfp"
        )
        if denied:
            messages.error(request, _("You don't have permission to manage the CFP."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        cfp = getattr(event, "cfp", None)
        if not cfp:
            messages.warning(request, _("No CFP exists for this event."))
            return redirect("cfp:cfp_config", org_slug=org_slug, event_slug=event_slug)

        stats = get_cfp_stats(cfp)

        by_track = (
            cfp.proposals.exclude(status=Proposal.Status.DRAFT)
            .values("track__name", "track__color")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        by_format = (
            cfp.proposals.exclude(status=Proposal.Status.DRAFT)
            .values("session_format__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        by_level = (
            cfp.proposals.exclude(status=Proposal.Status.DRAFT)
            .values("level")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return render(request, "cfp/manage/cfp_analytics.html", {
            "event": event,
            "cfp": cfp,
            "stats": stats,
            "by_track": by_track,
            "by_format": by_format,
            "by_level": by_level,
        })


class ScheduleBuilderView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "manage_schedule"
        )
        if denied:
            messages.error(request, _("You don't have permission to manage the schedule."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        sessions = Session.objects.filter(event=event).select_related(
            "speaker", "session_format", "track", "proposal"
        ).prefetch_related("co_speakers")

        unscheduled = sessions.filter(starts_at__isnull=True)
        scheduled = sessions.exclude(starts_at__isnull=True)
        tracks = event.tracks.filter(is_active=True)
        conflicts = detect_schedule_conflicts(event)

        return render(request, "cfp/manage/schedule_builder.html", {
            "event": event,
            "sessions": scheduled,
            "unscheduled": unscheduled,
            "tracks": tracks,
            "conflicts": conflicts,
        })


class ScheduleUpdateView(LoginRequiredMixin, View):
    def post(self, request, org_slug, event_slug):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "manage_schedule"
        )
        if denied:
            return JsonResponse({"error": "Permission denied"}, status=403)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        session_id = data.get("session_id")
        session = get_object_or_404(Session, id=session_id, event=event)

        if "starts_at" in data:
            session.starts_at = data["starts_at"]
        if "ends_at" in data:
            session.ends_at = data["ends_at"]
        if "room" in data:
            session.room = data["room"]
        if "track_id" in data:
            session.track_id = data["track_id"] or None
        if "status" in data:
            session.status = data["status"]

        session.save()
        return JsonResponse({"status": "ok", "session_id": session.id})


class SessionEditView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug, id):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "manage_schedule"
        )
        if denied:
            messages.error(request, _("You don't have permission to manage the schedule."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        session = get_object_or_404(
            Session.objects.select_related("speaker", "track", "session_format"),
            id=id, event=event,
        )
        form = SessionForm(instance=session)
        form.fields["track"].queryset = event.tracks.filter(is_active=True)

        return render(request, "cfp/manage/session_edit.html", {
            "event": event,
            "session": session,
            "form": form,
        })

    def post(self, request, org_slug, event_slug, id):
        event, denied = get_event_for_organizer(
            request, org_slug, event_slug, "manage_schedule"
        )
        if denied:
            messages.error(request, _("You don't have permission to manage the schedule."))
            return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)

        session = get_object_or_404(Session, id=id, event=event)
        form = SessionForm(request.POST, instance=session)
        form.fields["track"].queryset = event.tracks.filter(is_active=True)

        if form.is_valid():
            form.save()
            messages.success(request, _("Session updated."))
            return redirect(
                "cfp:schedule_builder", org_slug=org_slug, event_slug=event_slug
            )

        return render(request, "cfp/manage/session_edit.html", {
            "event": event,
            "session": session,
            "form": form,
        })


class CFPDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        events = Event.objects.filter(
            organization__members=request.user
        ).select_related("organization").prefetch_related("cfp")

        cfp_events = []
        for event in events:
            cfp = getattr(event, "cfp", None)
            if cfp:
                proposal_count = cfp.proposals.exclude(
                    status=Proposal.Status.DRAFT
                ).count()
                speaker_count = SpeakerProfile.objects.filter(event=event).count()
                cfp_events.append({
                    "event": event,
                    "cfp": cfp,
                    "proposal_count": proposal_count,
                    "speaker_count": speaker_count,
                })

        stats = {
            "total_cfps": len(cfp_events),
            "open_cfps": sum(1 for e in cfp_events if e["cfp"].is_open),
            "total_proposals": sum(e["proposal_count"] for e in cfp_events),
            "total_speakers": sum(e["speaker_count"] for e in cfp_events),
        }

        return render(request, "cfp/manage/dashboard.html", {
            "cfp_events": cfp_events,
            "stats": stats,
        })


class SpeakerManagementView(LoginRequiredMixin, View):
    def get(self, request):
        speakers = SpeakerProfile.objects.filter(
            event__organization__members=request.user
        ).select_related("user", "event", "event__organization").annotate(
            proposal_count=Count(
                "user__proposals",
                filter=Q(
                    user__proposals__cfp__event=models.F("event"),
                ) & ~Q(user__proposals__status=Proposal.Status.DRAFT),
            )
        )

        event_filter = request.GET.get("event")
        search = request.GET.get("q")
        has_photo_filter = request.GET.get("has_photo")

        if event_filter:
            speakers = speakers.filter(event_id=event_filter)
        if search:
            speakers = speakers.filter(
                Q(user__email__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(company__icontains=search)
                | Q(job_title__icontains=search)
            )
        if has_photo_filter == "yes":
            speakers = speakers.exclude(photo="")
        elif has_photo_filter == "no":
            speakers = speakers.filter(photo="")

        speakers = speakers.order_by("-created_at")

        events = Event.objects.filter(
            organization__members=request.user,
            cfp__isnull=False,
        ).select_related("organization")

        paginator = Paginator(speakers, 50)
        page_obj = paginator.get_page(request.GET.get("page", 1))

        stats = {
            "total": paginator.count,
            "with_photo": SpeakerProfile.objects.filter(
                event__organization__members=request.user
            ).exclude(photo="").count(),
        }

        return render(request, "cfp/manage/speakers.html", {
            "speakers": page_obj.object_list,
            "page_obj": page_obj,
            "paginator": paginator,
            "stats": stats,
            "events": events,
            "current_event": event_filter or "",
            "current_search": search or "",
            "current_has_photo": has_photo_filter or "",
        })


class ExportSpeakersView(LoginRequiredMixin, View):
    HEADERS = [
        "Name", "Email", "Event", "Company", "Job Title",
        "Bio", "Website", "Twitter", "LinkedIn", "GitHub",
        "Has Photo", "Travel Assistance", "Accommodation",
        "Dietary Requirements", "Custom Fields",
    ]

    def _get_speakers(self, request):
        speakers = SpeakerProfile.objects.filter(
            event__organization__members=request.user
        ).select_related("user", "event")

        event_filter = request.GET.get("event")
        if event_filter:
            speakers = speakers.filter(event_id=event_filter)

        return speakers.order_by("event__title", "user__email")

    def _speaker_to_row(self, sp):
        return {
            "Name": sp.user.get_full_name() or sp.user.email,
            "Email": sp.user.email,
            "Event": sp.event.title,
            "Company": sp.company,
            "Job Title": sp.job_title,
            "Bio": sp.bio[:200] if sp.bio else "",
            "Website": sp.website,
            "Twitter": sp.twitter,
            "LinkedIn": sp.linkedin,
            "GitHub": sp.github,
            "Has Photo": "Yes" if sp.photo else "No",
            "Travel Assistance": "Yes" if sp.travel_assistance else "No",
            "Accommodation": "Yes" if sp.accommodation_needed else "No",
            "Dietary Requirements": sp.dietary_requirements,
            "Custom Fields": json.dumps(sp.custom_fields) if sp.custom_fields else "",
        }

    def get(self, request):
        export_format = request.GET.get("format", "csv").lower()
        speakers = self._get_speakers(request)
        rows = [self._speaker_to_row(sp) for sp in speakers]

        if export_format == "json":
            return self._export_json(rows)
        elif export_format == "pdf":
            return self._export_pdf(rows)
        return self._export_csv(rows)

    def _export_csv(self, rows):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="speakers.csv"'
        writer = csv.DictWriter(response, fieldnames=self.HEADERS)
        writer.writeheader()
        writer.writerows(rows)
        return response

    def _export_json(self, rows):
        response = HttpResponse(
            json.dumps(rows, indent=2, ensure_ascii=False),
            content_type="application/json",
        )
        response["Content-Disposition"] = 'attachment; filename="speakers.json"'
        return response

    def _export_pdf(self, rows):
        from io import BytesIO

        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )
        except ImportError:
            return HttpResponse(
                _("PDF export requires reportlab. Install it with: pip install reportlab"),
                status=501,
            )

        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=10 * mm, rightMargin=10 * mm)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(_("Speakers Export"), styles["Title"]))
        elements.append(Spacer(1, 6 * mm))

        display_cols = ["Name", "Email", "Event", "Company", "Job Title", "Bio"]
        table_data = [display_cols]
        for row in rows:
            table_data.append([
                Paragraph(str(row.get(col, "")), styles["BodyText"])
                for col in display_cols
            ])

        col_widths = [45 * mm, 55 * mm, 40 * mm, 35 * mm, 35 * mm, 60 * mm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#09090b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))

        elements.append(table)
        doc.build(elements)
        buf.seek(0)

        response = HttpResponse(buf.read(), content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="speakers.pdf"'
        return response
